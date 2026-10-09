#!/usr/bin/env python3
"""Verify the standalone Project Manager skill package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "SKILL.md",
    "README.md",
    "INDEX.md",
    "agents/openai.yaml",
    "references/core-protocol.md",
    "references/initialization-and-recovery.md",
    "references/handoff.md",
    "references/feedback.md",
    "references/change-review.md",
    "assets/project-memory/README.md",
    "assets/project-memory/HANDOFF.md",
    "assets/project-memory/manifest.json",
    "assets/project-memory/rules/README.md",
    "VERSION",
    "CHANGELOG.md",
    "LICENSE",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\nname: project-manager\n"):
        errors.append("SKILL.md frontmatter does not declare project-manager")
    if "[TODO" in skill:
        errors.append("SKILL.md still contains TODO text")
    for command in (
        "#> memory init",
        "#> memory save",
        "#> handoff",
        "#> resume",
        "#> feedback",
    ):
        if command not in skill:
            errors.append(f"SKILL.md omits command: {command}")

    manifest_path = ROOT / "assets/project-memory/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in (
        "schema_version",
        "project_id",
        "generation",
        "entrypoint",
        "handoff",
        "rules_dir",
        "feedback_dir",
        "tracked_paths",
        "file_hashes",
    ):
        if key not in manifest:
            errors.append(f"manifest template omits key: {key}")

    front_door = (ROOT / "assets/project-memory/README.md").read_text(
        encoding="utf-8"
    )
    for link in ("HANDOFF.md", "rules/README.md"):
        if f"]({link})" not in front_door:
            errors.append(f"project-memory README omits direct link: {link}")

    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if path.name != "LICENSE" and "[⌂ " not in text:
            errors.append(
                f"authored Markdown omits Home footer: {path.relative_to(ROOT)}"
            )
        for target in MARKDOWN_LINK.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).resolve().exists():
                errors.append(
                    f"broken relative link in {path.relative_to(ROOT)}: {target}"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "Project Manager package verification passed "
        f"({len(REQUIRED)} required files)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
