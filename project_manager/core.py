"""Deterministic mechanics for portable project memory."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
CHANGE_SCHEMA = "project-manager/change/1"
MEMORY_DIR = ".ai-memory"
REQUIRED_PATHS = (
    ".ai-memory/README.md",
    ".ai-memory/HANDOFF.md",
    ".ai-memory/manifest.json",
    ".ai-memory/rules/README.md",
)
MAX_CONTEXT_BYTES = 48 * 1024
MAX_CHANGE_BYTES = 64 * 1024
PROPOSAL_RE = re.compile(r"^PM-\d{8}-[A-Z0-9]{6}$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
)


class ProjectManagerError(RuntimeError):
    """A user-correctable project-memory error."""


@dataclass(frozen=True)
class ValidationResult:
    root: Path
    project_id: str | None
    generation: int | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    stale_paths: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "project-manager/status/1",
            "root": str(self.root),
            "initialized": (self.root / MEMORY_DIR).is_dir(),
            "valid": self.valid,
            "project_id": self.project_id,
            "generation": self.generation,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "stale_paths": list(self.stale_paths),
        }


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _template(relative: str) -> str:
    return (
        resources.files("project_manager")
        .joinpath("templates", "project-memory", relative)
        .read_text(encoding="utf-8")
    )


def _project_identity(root: Path) -> str:
    git_config = root / ".git" / "config"
    if git_config.is_file():
        text = git_config.read_text(encoding="utf-8", errors="replace")
        match = re.search(
            r'\[remote "origin"\][^\[]*?\n\s*url\s*=\s*(.+)', text, re.MULTILINE
        )
        if match:
            return f"git:{match.group(1).strip()}"
    return f"path:{root}"


def project_id_for(root: Path) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, _project_identity(root)))


def resolve_root(start: str | Path, *, require_memory: bool = True) -> Path:
    path = Path(start).expanduser().resolve()
    if path.is_file():
        path = path.parent
    if not path.exists() or not path.is_dir():
        raise ProjectManagerError(f"project root is not a directory: {path}")
    if not require_memory:
        return path
    for candidate in (path, *path.parents):
        if (candidate / MEMORY_DIR / "manifest.json").is_file():
            return candidate
    raise ProjectManagerError(
        f"no {MEMORY_DIR}/manifest.json found from {path}; run project-manager init"
    )


def _safe_memory_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProjectManagerError(f"unsafe project-memory path: {relative}")
    if not candidate.parts or candidate.parts[0] != MEMORY_DIR:
        raise ProjectManagerError(f"path must remain under {MEMORY_DIR}/: {relative}")
    resolved = (root / candidate).resolve()
    memory_root = (root / MEMORY_DIR).resolve()
    if resolved != memory_root and memory_root not in resolved.parents:
        raise ProjectManagerError(f"path escapes project memory: {relative}")
    return resolved


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def initial_files(root: Path) -> dict[str, str]:
    if (root / MEMORY_DIR).exists():
        raise ProjectManagerError(f"{root / MEMORY_DIR} already exists")
    files = {
        ".ai-memory/README.md": _template("README.md"),
        ".ai-memory/HANDOFF.md": _template("HANDOFF.md"),
        ".ai-memory/rules/README.md": _template("rules/README.md"),
    }
    manifest = json.loads(_template("manifest.json"))
    manifest["project_id"] = project_id_for(root)
    manifest["file_hashes"] = {
        relative: sha256_bytes(content.encode("utf-8"))
        for relative, content in files.items()
    }
    files[".ai-memory/manifest.json"] = json.dumps(
        manifest, indent=2, sort_keys=True
    ) + "\n"
    return files


def apply_initialization(root: Path, files: dict[str, str]) -> None:
    if (root / MEMORY_DIR).exists():
        raise ProjectManagerError(f"{root / MEMORY_DIR} appeared after preview")
    written: list[Path] = []
    try:
        for relative, content in files.items():
            target = _safe_memory_path(root, relative)
            _atomic_write(target, content)
            written.append(target)
    except Exception:
        for target in reversed(written):
            target.unlink(missing_ok=True)
        for directory in (
            root / MEMORY_DIR / "rules",
            root / MEMORY_DIR,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MEMORY_DIR / "manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectManagerError(f"missing manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectManagerError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ProjectManagerError("manifest must be a JSON object")
    return manifest


def validate(root: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    stale: list[str] = []
    project_id: str | None = None
    generation: int | None = None

    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    manifest: dict[str, Any] = {}
    try:
        manifest = load_manifest(root)
    except ProjectManagerError as exc:
        errors.append(str(exc))

    if manifest:
        project_id = manifest.get("project_id")
        generation = manifest.get("generation")
        if manifest.get("schema_version") != SCHEMA_VERSION:
            errors.append("unsupported manifest schema_version")
        if not isinstance(project_id, str) or not project_id:
            errors.append("manifest project_id must be a non-empty string")
        if not isinstance(generation, int) or generation < 0:
            errors.append("manifest generation must be a non-negative integer")
        tracked = manifest.get("tracked_paths")
        hashes = manifest.get("file_hashes")
        if not isinstance(tracked, list) or not all(
            isinstance(item, str) for item in tracked
        ):
            errors.append("manifest tracked_paths must be a string array")
            tracked = []
        if not isinstance(hashes, dict):
            errors.append("manifest file_hashes must be an object")
            hashes = {}
        for relative in tracked:
            try:
                target = _safe_memory_path(root, relative)
            except ProjectManagerError as exc:
                errors.append(str(exc))
                continue
            if not target.is_file():
                errors.append(f"tracked file is missing: {relative}")
                continue
            expected = hashes.get(relative)
            if not isinstance(expected, str):
                stale.append(relative)
            elif sha256_file(target) != expected:
                stale.append(relative)

    readme = root / MEMORY_DIR / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="replace")
        for link in ("](HANDOFF.md)", "](rules/README.md)"):
            if link not in text:
                errors.append(f"project-memory README omits direct link: {link[2:-1]}")

    for relative in REQUIRED_PATHS:
        target = root / relative
        if not target.is_file() or target.suffix not in {".md", ".json"}:
            continue
        content = target.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            errors.append(f"possible secret in project memory: {relative}")
        if target.stat().st_size > 16 * 1024 and target.name in {
            "README.md",
            "HANDOFF.md",
        }:
            warnings.append(f"review token size for {relative}")

    if stale:
        warnings.append("recorded hashes differ from current bytes")
    return ValidationResult(
        root=root,
        project_id=project_id if isinstance(project_id, str) else None,
        generation=generation if isinstance(generation, int) else None,
        errors=tuple(errors),
        warnings=tuple(warnings),
        stale_paths=tuple(sorted(set(stale))),
    )


def context_payload(root: Path) -> dict[str, Any]:
    result = validate(root)
    if result.errors:
        raise ProjectManagerError("project memory is invalid; run project-manager check")
    manifest = load_manifest(root)
    rule_paths = sorted(
        relative
        for relative in manifest.get("tracked_paths", [])
        if relative.startswith(".ai-memory/rules/")
        and relative != ".ai-memory/rules/README.md"
    )
    readme = (root / MEMORY_DIR / "README.md").read_text(encoding="utf-8")
    handoff = (root / MEMORY_DIR / "HANDOFF.md").read_text(encoding="utf-8")
    total = len(readme.encode()) + len(handoff.encode())
    if total > MAX_CONTEXT_BYTES:
        raise ProjectManagerError("README and HANDOFF exceed the context byte limit")
    return {
        "schema": "project-manager/context/1",
        "root": str(root),
        "project_id": manifest["project_id"],
        "generation": manifest["generation"],
        "fresh": not result.stale_paths,
        "stale_paths": list(result.stale_paths),
        "read_order": [
            ".ai-memory/README.md",
            ".ai-memory/HANDOFF.md",
            *rule_paths,
        ],
        "readme": readme,
        "handoff": handoff,
        "rule_paths": rule_paths,
    }


def load_change(path: Path) -> dict[str, Any]:
    try:
        change = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectManagerError(f"missing change file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectManagerError(f"invalid change JSON: {exc}") from exc
    if not isinstance(change, dict):
        raise ProjectManagerError("change plan must be a JSON object")
    return change


def _validated_change(root: Path, change: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = load_manifest(root)
    if change.get("schema") != CHANGE_SCHEMA:
        raise ProjectManagerError(f"change schema must be {CHANGE_SCHEMA}")
    proposal_id = change.get("proposal_id")
    if not isinstance(proposal_id, str) or not PROPOSAL_RE.fullmatch(proposal_id):
        raise ProjectManagerError("invalid proposal_id")
    if change.get("project_id") != manifest.get("project_id"):
        raise ProjectManagerError("change project_id does not match manifest")
    if change.get("base_generation") != manifest.get("generation"):
        raise ProjectManagerError("change base_generation is stale")
    operations = change.get("operations")
    if not isinstance(operations, list) or not 1 <= len(operations) <= 20:
        raise ProjectManagerError("change requires 1 to 20 operations")
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise ProjectManagerError("each operation must be an object")
        relative = operation.get("path")
        action = operation.get("operation")
        content = operation.get("content")
        current_hash = operation.get("current_sha256")
        if not isinstance(relative, str) or relative in seen:
            raise ProjectManagerError("operation paths must be unique strings")
        seen.add(relative)
        target = _safe_memory_path(root, relative)
        if target.name == "manifest.json":
            raise ProjectManagerError("manifest is updated automatically")
        if action not in {"add", "replace"}:
            raise ProjectManagerError("operation must be add or replace")
        if not isinstance(content, str) or len(content.encode()) > MAX_CHANGE_BYTES:
            raise ProjectManagerError("operation content is missing or too large")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            raise ProjectManagerError(f"possible secret in proposed content: {relative}")
        exists = target.is_file()
        if action == "add" and exists:
            raise ProjectManagerError(f"add target already exists: {relative}")
        if action == "replace" and not exists:
            raise ProjectManagerError(f"replace target is missing: {relative}")
        actual_hash = sha256_file(target) if exists else None
        if current_hash != actual_hash:
            raise ProjectManagerError(f"current bytes changed for: {relative}")
        checked.append(
            {
                "path": relative,
                "operation": action,
                "content": content,
                "current_sha256": current_hash,
            }
        )
    return checked


def preview_change(root: Path, change: dict[str, Any]) -> dict[str, Any]:
    operations = _validated_change(root, change)
    return {
        "schema": "project-manager/change-preview/1",
        "proposal_id": change["proposal_id"],
        "project_id": change["project_id"],
        "base_generation": change["base_generation"],
        "status": "awaiting-approval",
        "operations": operations,
    }


def _updated_manifest(
    root: Path, manifest: dict[str, Any], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    tracked = list(manifest.get("tracked_paths", []))
    for operation in operations:
        if operation["path"] not in tracked:
            tracked.append(operation["path"])
    manifest = dict(manifest)
    manifest["generation"] = int(manifest["generation"]) + 1
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["tracked_paths"] = sorted(tracked)
    manifest["file_hashes"] = {
        relative: sha256_file(_safe_memory_path(root, relative))
        for relative in manifest["tracked_paths"]
        if _safe_memory_path(root, relative).is_file()
    }
    return manifest


def apply_change(
    root: Path, change: dict[str, Any], *, approval_ref: str
) -> dict[str, Any]:
    operations = _validated_change(root, change)
    if approval_ref != change["proposal_id"]:
        raise ProjectManagerError("approval_ref must exactly match proposal_id")
    manifest_path = root / MEMORY_DIR / "manifest.json"
    original_manifest = manifest_path.read_text(encoding="utf-8")
    originals: dict[Path, bytes | None] = {}
    try:
        for operation in operations:
            target = _safe_memory_path(root, operation["path"])
            originals[target] = target.read_bytes() if target.exists() else None
            _atomic_write(target, operation["content"])
        manifest = _updated_manifest(root, json.loads(original_manifest), operations)
        _atomic_write(
            manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        result = validate(root)
        if result.errors or result.stale_paths:
            raise ProjectManagerError("post-write validation failed")
    except Exception:
        for target, original in originals.items():
            if original is None:
                target.unlink(missing_ok=True)
            else:
                _atomic_write(target, original.decode("utf-8"))
        _atomic_write(manifest_path, original_manifest)
        raise
    return {
        "schema": "project-manager/change-receipt/1",
        "proposal_id": change["proposal_id"],
        "result": "applied",
        "files": [operation["path"] for operation in operations],
        "generation": {
            "old": change["base_generation"],
            "new": change["base_generation"] + 1,
        },
        "validation": "passed",
    }


def make_proposal_id(seed: str) -> str:
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:6].upper()
    return f"PM-{date}-{suffix}"


def handoff_clear_change(root: Path) -> dict[str, Any]:
    manifest = load_manifest(root)
    target = root / MEMORY_DIR / "HANDOFF.md"
    content = _template("HANDOFF.md")
    return {
        "schema": CHANGE_SCHEMA,
        "proposal_id": make_proposal_id(
            f"{manifest['project_id']}:{manifest['generation']}:clear-handoff"
        ),
        "project_id": manifest["project_id"],
        "base_generation": manifest["generation"],
        "reason": "Clear the completed active handoff to its idle state.",
        "operations": [
            {
                "path": ".ai-memory/HANDOFF.md",
                "operation": "replace",
                "current_sha256": sha256_file(target),
                "content": content,
            }
        ],
    }


def feedback_change(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(root)
    required = (
        "scope",
        "initial_request_summary",
        "observed_response_summary",
        "user_correction",
        "desired_future_behavior",
    )
    for key in required:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ProjectManagerError(f"feedback input requires non-empty {key}")
    allowed_scopes = {
        "project",
        "protocol",
        "skill",
        "orchestrator",
        "host",
        "cross-project",
    }
    if payload["scope"] not in allowed_scopes:
        raise ProjectManagerError("invalid feedback scope")
    compact = json.dumps(payload, sort_keys=True)
    if len(compact.encode()) > 16 * 1024:
        raise ProjectManagerError("feedback input is too large")
    proposal_id = make_proposal_id(
        f"{manifest['project_id']}:{manifest['generation']}:{compact}"
    )
    suffix = proposal_id.rsplit("-", 1)[1]
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    relative = f".ai-memory/feedback/FB-{day}-{suffix}.md"
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) for item in evidence
    ):
        raise ProjectManagerError("feedback evidence must be a string array")
    for item in evidence:
        candidate = Path(item)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ProjectManagerError("feedback evidence must use project-relative paths")
    target = payload.get("target", "unspecified")
    if (
        not isinstance(target, str)
        or not target.strip()
        or len(target) > 128
        or "\n" in target
    ):
        raise ProjectManagerError("feedback target must be one short line")
    interpretation = payload.get("model_interpretation", "Not yet proposed.")
    content = f"""---
status: open
scope: {payload['scope']}
target: {target}
---

# Feedback case

## Initial request summary

{payload['initial_request_summary'].strip()}

## Observed response summary

{payload['observed_response_summary'].strip()}

## User correction

{payload['user_correction'].strip()}

## Desired future behavior

{payload['desired_future_behavior'].strip()}

## Model interpretation

Inference only; not promoted to a rule: {str(interpretation).strip()}

## Evidence

{chr(10).join(f'- `{item}`' for item in evidence) if evidence else '- None recorded.'}

## Privacy review

Bounded summaries only; no transcript, credentials, or hidden reasoning.

---

[⌂ Home](../README.md)
"""
    return {
        "schema": CHANGE_SCHEMA,
        "proposal_id": proposal_id,
        "project_id": manifest["project_id"],
        "base_generation": manifest["generation"],
        "reason": "Capture one bounded feedback case for later review.",
        "operations": [
            {
                "path": relative,
                "operation": "add",
                "current_sha256": None,
                "content": content,
            }
        ],
    }
