"""Terminal interface for Project Manager project memory."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

from project_manager import __version__
from project_manager.core import (
    ProjectManagerError,
    MAX_PENDING_BYTES,
    PENDING_REVIEW_PATH,
    apply_pending_change,
    apply_initialization,
    context_payload,
    discard_pending_change,
    feedback_change,
    handoff_clear_change,
    initial_files,
    load_pending_change,
    pending_matches_change,
    pending_review_status,
    preview_change,
    refresh_payload,
    resolve_root,
    stage_change,
    validate,
)


def _emit(payload: Any, *, as_json: bool = False) -> None:
    if as_json or not isinstance(payload, str):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)


def _read_json_source(source: str, *, label: str) -> dict[str, Any]:
    if source == "-":
        text = sys.stdin.read(MAX_PENDING_BYTES + 1)
        if len(text.encode("utf-8")) > MAX_PENDING_BYTES:
            raise ProjectManagerError(f"{label} input exceeds the size limit")
    else:
        path = Path(source).expanduser().resolve()
        try:
            if path.stat().st_size > MAX_PENDING_BYTES:
                raise ProjectManagerError(f"{label} input exceeds the size limit")
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ProjectManagerError(f"missing {label} input: {path}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProjectManagerError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectManagerError(f"{label} input must be a JSON object")
    return payload


def _output_target(root: Path, path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or any(part.startswith(".") for part in candidate.parts)
    ):
        raise ProjectManagerError(
            "--output must be a visible project-relative path"
        )
    target = (root / candidate).resolve()
    if root != target and root not in target.parents:
        raise ProjectManagerError("--output must remain inside the project")
    return target


def _write_plan(root: Path, path: str | None, plan: dict[str, Any]) -> None:
    target = _output_target(root, path)
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _preview_text(root: Path, preview: dict[str, Any]) -> str:
    operations = preview.get("operations", [])
    paths = [item["path"] for item in operations]
    lines = [
        "Memory change ready for review",
        "",
        f"Purpose: {preview.get('reason', 'Update project memory.')}",
        f"Will change: {len(paths)} file(s) — {', '.join(paths)}",
        "Memory changed: No; this is only a review proposal.",
        "Checked: Project identity, generation, paths, current bytes, size and secrets passed.",
        f"Inspect: {preview.get('pending_path', PENDING_REVIEW_PATH)}",
        'Approve: Reply “approve the pending memory change” or run '
        '`project-manager review apply .`.',
        "",
        "Exact proposal:",
    ]
    for operation in operations:
        relative = operation["path"]
        proposed = operation["content"]
        lines.extend(["", f"--- {relative} ({operation['operation']})"])
        if operation["operation"] == "add":
            lines.append(proposed.rstrip())
            continue
        current = (root / relative).read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            current.splitlines(),
            proposed.splitlines(),
            fromfile=f"current/{relative}",
            tofile=f"proposed/{relative}",
            lineterm="",
        )
        lines.extend(diff)
    return "\n".join(lines).rstrip() + "\n"


def _receipt_text(receipt: dict[str, Any]) -> str:
    files = receipt.get("files", [])
    generation = receipt.get("generation", {})
    return "\n".join(
        [
            "Memory updated",
            "",
            f"Changed: {', '.join(files) if files else 'Nothing'}",
            f"Checked: {receipt.get('validation', 'not reported')}",
            f"Generation: {generation.get('old', '?')} → {generation.get('new', '?')}",
            "Pending proposal: Removed.",
            "Next: No further memory action is required.",
        ]
    )


def cmd_init(args: argparse.Namespace) -> int:
    root = resolve_root(args.root, require_memory=False)
    files = initial_files(root)
    preview = {
        "schema": "project-manager/init-preview/1",
        "root": str(root),
        "status": "ready" if args.apply else "preview",
        "files": [
            {"path": relative, "content": content}
            for relative, content in files.items()
        ],
    }
    if not args.apply:
        _emit(preview, as_json=args.json)
        return 0
    apply_initialization(root, files)
    result = validate(root)
    receipt = {
        "schema": "project-manager/init-receipt/1",
        "root": str(root),
        "result": "applied",
        "files": list(files),
        "project_id": result.project_id,
        "generation": result.generation,
        "validation": "passed" if result.valid and not result.stale_paths else "failed",
    }
    _emit(receipt, as_json=args.json)
    return 0 if receipt["validation"] == "passed" else 1


def cmd_status(args: argparse.Namespace) -> int:
    try:
        root = resolve_root(args.root)
    except ProjectManagerError:
        root = resolve_root(args.root, require_memory=False)
        payload = {
            "schema": "project-manager/status/1",
            "root": str(root),
            "initialized": False,
            "valid": False,
            "project_id": None,
            "generation": None,
            "errors": ["project memory is not initialized"],
            "warnings": [],
            "stale_paths": [],
            "pending_review": {
                "status": "none",
                "path": PENDING_REVIEW_PATH,
                "proposal_id": None,
                "files": [],
            },
        }
        _emit(payload, as_json=args.json)
        return 1
    payload = validate(root).as_dict()
    if args.json:
        _emit(payload, as_json=True)
    else:
        pending = payload["pending_review"]
        print(f"Project memory: {'valid' if payload['valid'] else 'needs attention'}")
        print(f"Generation: {payload['generation']}")
        print(f"Fresh: {'yes' if not payload['stale_paths'] else 'no'}")
        print(f"Pending review: {pending['status']} — {pending['path']}")
        if payload["errors"]:
            print("Next: Run `project-manager check . --json` for the exact errors.")
        elif pending["status"] == "ready":
            print("Next: Run `project-manager review show .`.")
        elif pending["status"] in {"stale", "invalid"}:
            print("Next: Inspect or discard the pending review before continuing.")
        else:
            print("Next: No action required.")
    return 0 if (
        payload["valid"]
        and not payload["stale_paths"]
        and payload["pending_review"]["status"] in {"none", "ready"}
    ) else 1


def cmd_check(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    result = validate(root)
    payload = result.as_dict()
    _emit(payload, as_json=args.json)
    return 0 if (
        result.valid
        and not result.stale_paths
        and payload["pending_review"]["status"] in {"none", "ready"}
    ) else 1


def cmd_context(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    payload = context_payload(root)
    if args.format == "json":
        _emit(payload, as_json=True)
    else:
        print("# Project Manager context")
        print()
        print(f"Project ID: `{payload['project_id']}`")
        print(f"Generation: `{payload['generation']}`")
        print(f"Fresh: `{'yes' if payload['fresh'] else 'no'}`")
        print()
        print("## Project memory")
        print()
        print(payload["readme"].rstrip())
        print()
        print("## Active handoff")
        print()
        print(payload["handoff"].rstrip())
        if payload["rule_paths"]:
            print()
            print("## Additional rule paths")
            print()
            for relative in payload["rule_paths"]:
                print(f"- `{relative}`")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    payload = refresh_payload(root)
    if args.format == "json":
        _emit(payload, as_json=True)
        return 0
    print("# Project Manager refresh")
    print()
    print(f"Project ID: `{payload['project_id']}`")
    print(f"Generation: `{payload['generation']}`")
    print(f"Fresh: `{'yes' if payload['fresh'] else 'no'}`")
    print(f"Refresh key: `{payload['refresh_key']}`")
    print()
    print("## Core memory")
    print()
    for relative in payload["required_core_paths"]:
        print(f"- `{relative}`")
    if payload["authority_candidates"]:
        print()
        print("## Repository authority candidates")
        print()
        for item in payload["authority_candidates"]:
            print(f"- `{item['path']}`")
    if payload["rule_candidates"]:
        print()
        print("## Rule candidates")
        print()
        for item in payload["rule_candidates"]:
            print(f"- `{item['path']}`")
    if payload["stale_paths"]:
        print()
        print("## Freshness warnings")
        print()
        for relative in payload["stale_paths"]:
            print(f"- `{relative}`")
    print()
    print("Read-only: live task and mode stay unchanged; no persistent state was written.")
    return 0


def cmd_change_preview(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    _output_target(root, args.output)
    change = _read_json_source(args.change, label="change")
    preview = stage_change(root, change, replace_pending=args.replace_pending)
    _write_plan(root, args.output, load_pending_change(root))
    if args.json:
        _emit(preview, as_json=True)
    else:
        print(_preview_text(root, preview), end="")
    return 0


def cmd_change_apply(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = _read_json_source(args.change, label="change")
    pending_matches_change(root, change)
    receipt = apply_pending_change(root, approval_ref=args.approval_ref)
    if args.json:
        _emit(receipt, as_json=True)
    else:
        print(_receipt_text(receipt))
    return 0


def cmd_handoff_show(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    print((root / ".ai-memory" / "HANDOFF.md").read_text(encoding="utf-8"), end="")
    return 0


def cmd_handoff_clear(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    _output_target(root, args.output)
    change = handoff_clear_change(root)
    preview = stage_change(root, change, replace_pending=args.replace_pending)
    _write_plan(root, args.output, load_pending_change(root))
    if args.apply:
        if not args.approval_ref:
            raise ProjectManagerError("--approval-ref is required with --apply")
        receipt = apply_pending_change(root, approval_ref=args.approval_ref)
        _emit(receipt, as_json=args.json)
    else:
        _emit(preview, as_json=True) if args.json else print(
            _preview_text(root, preview), end=""
        )
    return 0


def cmd_feedback_draft(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    _output_target(root, args.output)
    payload = _read_json_source(args.input, label="feedback")
    change = feedback_change(root, payload)
    preview = stage_change(root, change, replace_pending=args.replace_pending)
    _write_plan(root, args.output, load_pending_change(root))
    _emit(preview, as_json=True) if args.json else print(
        _preview_text(root, preview), end=""
    )
    return 0


def cmd_review_show(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = load_pending_change(root, validate_current=False)
    pending_status = pending_review_status(root)["status"]
    preview = {
        "schema": "project-manager/change-preview/1",
        "proposal_id": change["proposal_id"],
        "project_id": change["project_id"],
        "base_generation": change["base_generation"],
        "reason": change.get("reason", "Update project memory."),
        "status": "awaiting-approval" if pending_status == "ready" else pending_status,
        "operations": change["operations"],
        "pending_path": PENDING_REVIEW_PATH,
        "staged": True,
    }
    _emit(preview, as_json=True) if args.json else print(
        _preview_text(root, preview), end=""
    )
    return 0


def cmd_review_apply(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = load_pending_change(root)
    approval_ref = args.approval_ref
    if not approval_ref:
        if not sys.stdin.isatty():
            raise ProjectManagerError(
                "interactive confirmation is unavailable; provide --approval-ref "
                "only after actual approval"
            )
        preview = preview_change(root, change) | {
            "pending_path": PENDING_REVIEW_PATH,
            "staged": True,
        }
        print(_preview_text(root, preview), end="")
        answer = input("Apply this exact memory change? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Not applied — the pending review remains unchanged.")
            return 0
        approval_ref = change["proposal_id"]
    receipt = apply_pending_change(root, approval_ref=approval_ref)
    _emit(receipt, as_json=True) if args.json else print(_receipt_text(receipt))
    return 0


def cmd_review_discard(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    status = pending_review_status(root)
    if status["status"] == "none":
        raise ProjectManagerError("no pending memory review to discard")
    if not args.confirm:
        if not sys.stdin.isatty():
            raise ProjectManagerError(
                "interactive confirmation is unavailable; rerun with --confirm "
                "after explicit rejection"
            )
        answer = input(
            f"Discard {PENDING_REVIEW_PATH} without changing memory? [y/N] "
        ).strip().lower()
        if answer not in {"y", "yes"}:
            print("Not discarded — the pending review remains unchanged.")
            return 0
    receipt = discard_pending_change(root)
    if args.json:
        _emit(receipt, as_json=True)
    else:
        print("Pending memory review discarded")
        print()
        print(f"Removed: {receipt['path']}")
        print("Memory changed: No.")
        print("Next: No further review action is required.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-manager",
        description="Initialize, inspect, validate, and safely update project memory.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="preview or apply minimal project memory")
    init.add_argument("root", nargs="?", default=".")
    init.add_argument("--apply", action="store_true")
    init.add_argument("--json", action="store_true")
    init.set_defaults(handler=cmd_init)

    status = commands.add_parser("status", help="show compact initialization and freshness state")
    status.add_argument("root", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=cmd_status)

    check = commands.add_parser("check", help="validate structure, hashes, links, and privacy markers")
    check.add_argument("root", nargs="?", default=".")
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=cmd_check)

    context = commands.add_parser("context", help="emit the minimum portable recovery context")
    context.add_argument("root", nargs="?", default=".")
    context.add_argument("--format", choices=("markdown", "json"), default="markdown")
    context.set_defaults(handler=cmd_context)

    refresh = commands.add_parser(
        "refresh", help="prepare a read-only active-context refresh packet"
    )
    refresh.add_argument("root", nargs="?", default=".")
    refresh.add_argument("--format", choices=("markdown", "json"), default="markdown")
    refresh.set_defaults(handler=cmd_refresh)

    change = commands.add_parser("change", help="preview or apply an exact change plan")
    change_commands = change.add_subparsers(dest="change_command", required=True)
    change_preview = change_commands.add_parser("preview")
    change_preview.add_argument("change")
    change_preview.add_argument("root", nargs="?", default=".")
    change_preview.add_argument("--replace-pending", action="store_true")
    change_preview.add_argument("--output")
    change_preview.add_argument("--json", action="store_true")
    change_preview.set_defaults(handler=cmd_change_preview)
    change_apply = change_commands.add_parser("apply")
    change_apply.add_argument("change")
    change_apply.add_argument("root", nargs="?", default=".")
    change_apply.add_argument("--approval-ref", required=True)
    change_apply.add_argument("--json", action="store_true")
    change_apply.set_defaults(handler=cmd_change_apply)

    handoff = commands.add_parser("handoff", help="inspect or clear the active handoff")
    handoff_commands = handoff.add_subparsers(dest="handoff_command", required=True)
    handoff_show = handoff_commands.add_parser("show")
    handoff_show.add_argument("root", nargs="?", default=".")
    handoff_show.set_defaults(handler=cmd_handoff_show)
    handoff_clear = handoff_commands.add_parser("clear")
    handoff_clear.add_argument("root", nargs="?", default=".")
    handoff_clear.add_argument("--output")
    handoff_clear.add_argument("--apply", action="store_true")
    handoff_clear.add_argument("--approval-ref")
    handoff_clear.add_argument("--replace-pending", action="store_true")
    handoff_clear.add_argument("--json", action="store_true")
    handoff_clear.set_defaults(handler=cmd_handoff_clear)

    feedback = commands.add_parser("feedback", help="prepare bounded feedback evidence")
    feedback_commands = feedback.add_subparsers(dest="feedback_command", required=True)
    feedback_draft = feedback_commands.add_parser("draft")
    feedback_draft.add_argument("root", nargs="?", default=".")
    feedback_draft.add_argument("--input", required=True)
    feedback_draft.add_argument("--output")
    feedback_draft.add_argument("--replace-pending", action="store_true")
    feedback_draft.add_argument("--json", action="store_true")
    feedback_draft.set_defaults(handler=cmd_feedback_draft)

    review = commands.add_parser("review", help="inspect, apply, or discard one pending change")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    review_show = review_commands.add_parser("show")
    review_show.add_argument("root", nargs="?", default=".")
    review_show.add_argument("--json", action="store_true")
    review_show.set_defaults(handler=cmd_review_show)
    review_apply = review_commands.add_parser("apply")
    review_apply.add_argument("root", nargs="?", default=".")
    review_apply.add_argument("--approval-ref")
    review_apply.add_argument("--json", action="store_true")
    review_apply.set_defaults(handler=cmd_review_apply)
    review_discard = review_commands.add_parser("discard")
    review_discard.add_argument("root", nargs="?", default=".")
    review_discard.add_argument("--confirm", action="store_true")
    review_discard.add_argument("--json", action="store_true")
    review_discard.set_defaults(handler=cmd_review_discard)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ProjectManagerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
