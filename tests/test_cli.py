from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from project_manager.core import (
    apply_change,
    apply_initialization,
    context_payload,
    feedback_change,
    initial_files,
    load_manifest,
    preview_change,
    refresh_payload,
    sha256_file,
    validate,
)


class ProjectManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def initialize(self) -> None:
        apply_initialization(self.root, initial_files(self.root))

    def test_initialization_is_complete_and_fresh(self) -> None:
        files = initial_files(self.root)
        self.assertFalse((self.root / ".ai-memory").exists())
        apply_initialization(self.root, files)
        result = validate(self.root)
        self.assertTrue(result.valid)
        self.assertEqual((), result.stale_paths)
        self.assertEqual(0, result.generation)

    def test_context_is_bounded_and_contains_handoff(self) -> None:
        self.initialize()
        payload = context_payload(self.root)
        self.assertEqual("project-manager/context/1", payload["schema"])
        self.assertIn("No task is active.", payload["handoff"])
        self.assertEqual(
            [".ai-memory/README.md", ".ai-memory/HANDOFF.md"],
            payload["read_order"],
        )

    def test_changed_bytes_are_reported_stale(self) -> None:
        self.initialize()
        readme = self.root / ".ai-memory" / "README.md"
        readme.write_text(readme.read_text() + "\nchanged\n", encoding="utf-8")
        result = validate(self.root)
        self.assertIn(".ai-memory/README.md", result.stale_paths)

    def test_refresh_is_read_only_stable_and_separates_rule_candidates(self) -> None:
        self.initialize()
        authority = self.root / "AGENTS.md"
        authority.write_text("# Project authority\n", encoding="utf-8")
        rule = self.root / ".ai-memory" / "rules" / "writing.md"
        rule.write_text("# Writing rule\n", encoding="utf-8")
        manifest_path = self.root / ".ai-memory" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        relative = ".ai-memory/rules/writing.md"
        manifest["tracked_paths"].append(relative)
        manifest["file_hashes"][relative] = sha256_file(rule)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        before = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        first = refresh_payload(self.root)
        second = refresh_payload(self.root)

        self.assertEqual("project-manager/refresh/1", first["schema"])
        self.assertEqual(first["refresh_key"], second["refresh_key"])
        self.assertEqual("unchanged", first["effects"]["mode"])
        self.assertFalse(first["effects"]["writes"])
        self.assertFalse(first["effects"]["persistent_state"])
        self.assertFalse(first["effects"]["feedback_scanned"])
        self.assertEqual(
            ["AGENTS.md"],
            [item["path"] for item in first["authority_candidates"]],
        )
        self.assertEqual(
            [relative], [item["path"] for item in first["rule_candidates"]]
        )
        self.assertNotIn("# Writing rule", first["core"]["rule_index"])
        after = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_refresh_key_changes_and_stale_path_is_reported(self) -> None:
        self.initialize()
        first = refresh_payload(self.root)
        readme = self.root / ".ai-memory" / "README.md"
        readme.write_text(readme.read_text() + "\nchanged\n", encoding="utf-8")
        second = refresh_payload(self.root)
        self.assertNotEqual(first["refresh_key"], second["refresh_key"])
        self.assertFalse(second["fresh"])
        self.assertIn(".ai-memory/README.md", second["stale_paths"])

    def test_refresh_does_not_scan_feedback(self) -> None:
        self.initialize()
        feedback = self.root / ".ai-memory" / "feedback"
        feedback.mkdir()
        (feedback / "FB-example.md").write_text("not tracked\n", encoding="utf-8")
        payload = refresh_payload(self.root)
        self.assertFalse(payload["effects"]["feedback_scanned"])
        self.assertFalse(
            any(item["path"].startswith(".ai-memory/feedback/") for item in payload["sources"])
        )

    def test_exact_change_updates_generation_and_hash(self) -> None:
        self.initialize()
        manifest = load_manifest(self.root)
        target = self.root / ".ai-memory" / "README.md"
        content = target.read_text(encoding="utf-8").replace(
            "<Durable user preference that materially changes future work.>",
            "Keep verification claims evidence-bounded.",
        )
        change = {
            "schema": "project-manager/change/1",
            "proposal_id": "PM-20261010-ABC123",
            "project_id": manifest["project_id"],
            "base_generation": 0,
            "operations": [
                {
                    "path": ".ai-memory/README.md",
                    "operation": "replace",
                    "current_sha256": sha256_file(target),
                    "content": content,
                }
            ],
        }
        preview = preview_change(self.root, change)
        self.assertEqual("awaiting-approval", preview["status"])
        receipt = apply_change(
            self.root, change, approval_ref="PM-20261010-ABC123"
        )
        self.assertEqual("applied", receipt["result"])
        self.assertEqual(1, load_manifest(self.root)["generation"])
        self.assertFalse(validate(self.root).stale_paths)

    def test_path_escape_is_rejected(self) -> None:
        self.initialize()
        manifest = load_manifest(self.root)
        change = {
            "schema": "project-manager/change/1",
            "proposal_id": "PM-20261010-ABC123",
            "project_id": manifest["project_id"],
            "base_generation": 0,
            "operations": [
                {
                    "path": ".ai-memory/../outside.md",
                    "operation": "add",
                    "current_sha256": None,
                    "content": "unsafe",
                }
            ],
        }
        with self.assertRaisesRegex(RuntimeError, "unsafe project-memory path"):
            preview_change(self.root, change)

    def test_feedback_draft_does_not_write_source_project(self) -> None:
        self.initialize()
        payload = {
            "scope": "project",
            "initial_request_summary": "Create a compact report.",
            "observed_response_summary": "The response duplicated context.",
            "user_correction": "Keep one authoritative owner.",
            "desired_future_behavior": "Link instead of duplicating.",
            "evidence": ["docs/report.md"],
        }
        change = feedback_change(self.root, payload)
        operation = change["operations"][0]
        self.assertTrue(operation["path"].startswith(".ai-memory/feedback/FB-"))
        self.assertFalse((self.root / ".ai-memory" / "feedback").exists())

    def test_feedback_rejects_absolute_evidence_path(self) -> None:
        self.initialize()
        payload = {
            "scope": "project",
            "initial_request_summary": "Create a compact report.",
            "observed_response_summary": "The response duplicated context.",
            "user_correction": "Keep one authoritative owner.",
            "desired_future_behavior": "Link instead of duplicating.",
            "evidence": ["/private/example.md"],
        }
        with self.assertRaisesRegex(RuntimeError, "project-relative"):
            feedback_change(self.root, payload)

    def test_cli_init_preview_is_read_only(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_manager",
                "init",
                str(self.root),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("preview", json.loads(result.stdout)["status"])
        self.assertFalse((self.root / ".ai-memory").exists())

    def test_cli_refresh_emits_json_packet_without_writing(self) -> None:
        self.initialize()
        manifest = self.root / ".ai-memory" / "manifest.json"
        before = manifest.read_bytes()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_manager",
                "refresh",
                str(self.root),
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("project-manager/refresh/1", payload["schema"])
        self.assertEqual(before, manifest.read_bytes())


if __name__ == "__main__":
    unittest.main()
