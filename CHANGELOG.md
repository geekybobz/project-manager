# Changelog

## 0.4.0

Adds a visible, fixed review slot at `.ai-memory/review/pending.json` for one
validated but unapproved memory proposal. Change plans and feedback can arrive
through standard input, approvals bind to exact staged content, and
`project-manager review show|apply|discard` supports resumable review without
system-private staging files. Human output now leads with a compact outcome,
checks, pending state, and the exact next action; JSON remains available for
automation. Existing file inputs remain supported.

## 0.3.0

Adds read-only Project Manager refresh for re-anchoring a long-running chat to
current repository authority and project memory without flushing live task
state, changing mode, scanning feedback, or writing persistent refresh data.
The deterministic refresh packet reports freshness, source identities, core
memory, rule candidates, and a non-persistent deduplication key. Existing
`context` and `resume` behavior remains compatible.

## 0.2.1

Clarifies that mandatory Project Manager support applies to every project or
repository task, not only tasks judged non-trivial. Write approval and privacy
boundaries are unchanged.

## 0.2.0

Adds the dependency-free `project-manager`/`pmem` terminal interface for
initialization, status, validation, bounded context, exact change plans,
handoff clearing, and feedback drafting. Makes the capability always-on for
non-trivial project work while preserving preview and approval before writes.

## 0.1.0

Initial Project Manager protocol and templates: repository-local project
memory, one replaceable active HANDOFF, explicit two-phase memory changes,
bounded feedback capture, progressive recovery, privacy rules, and portable
Codex/Claude semantics.

---

[⌂ Home](README.md)
