"""Terminal interface for Project Manager project memory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from project_manager import __version__
from project_manager.core import (
    ProjectManagerError,
    apply_change,
    apply_initialization,
    context_payload,
    feedback_change,
    handoff_clear_change,
    initial_files,
    load_change,
    preview_change,
    resolve_root,
    validate,
)


def _emit(payload: Any, *, as_json: bool = False) -> None:
    if as_json or not isinstance(payload, str):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)


def _write_plan(path: str | None, plan: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path).expanduser().resolve()
    target.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        }
        _emit(payload, as_json=args.json)
        return 1
    payload = validate(root).as_dict()
    _emit(payload, as_json=args.json)
    return 0 if payload["valid"] and not payload["stale_paths"] else 1


def cmd_check(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    result = validate(root)
    _emit(result.as_dict(), as_json=args.json)
    return 0 if result.valid and not result.stale_paths else 1


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


def cmd_change_preview(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = load_change(Path(args.change).expanduser().resolve())
    _emit(preview_change(root, change), as_json=args.json)
    return 0


def cmd_change_apply(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = load_change(Path(args.change).expanduser().resolve())
    receipt = apply_change(root, change, approval_ref=args.approval_ref)
    _emit(receipt, as_json=args.json)
    return 0


def cmd_handoff_show(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    print((root / ".ai-memory" / "HANDOFF.md").read_text(encoding="utf-8"), end="")
    return 0


def cmd_handoff_clear(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    change = handoff_clear_change(root)
    _write_plan(args.output, change)
    if args.apply:
        if not args.approval_ref:
            raise ProjectManagerError("--approval-ref is required with --apply")
        _emit(
            apply_change(root, change, approval_ref=args.approval_ref),
            as_json=args.json,
        )
    else:
        _emit(preview_change(root, change), as_json=args.json)
    return 0


def cmd_feedback_draft(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    input_path = Path(args.input).expanduser().resolve()
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectManagerError(f"missing feedback input: {input_path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectManagerError(f"invalid feedback JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectManagerError("feedback input must be a JSON object")
    change = feedback_change(root, payload)
    _write_plan(args.output, change)
    _emit(preview_change(root, change), as_json=args.json)
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

    change = commands.add_parser("change", help="preview or apply an exact change plan")
    change_commands = change.add_subparsers(dest="change_command", required=True)
    change_preview = change_commands.add_parser("preview")
    change_preview.add_argument("change")
    change_preview.add_argument("root", nargs="?", default=".")
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
    handoff_clear.add_argument("--json", action="store_true")
    handoff_clear.set_defaults(handler=cmd_handoff_clear)

    feedback = commands.add_parser("feedback", help="prepare bounded feedback evidence")
    feedback_commands = feedback.add_subparsers(dest="feedback_command", required=True)
    feedback_draft = feedback_commands.add_parser("draft")
    feedback_draft.add_argument("root", nargs="?", default=".")
    feedback_draft.add_argument("--input", required=True)
    feedback_draft.add_argument("--output")
    feedback_draft.add_argument("--json", action="store_true")
    feedback_draft.set_defaults(handler=cmd_feedback_draft)
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
