---
role: index
summary: Route to Project Manager protocols and reusable project-memory templates.
read_when: Use when the operational entry points to a specific workflow.
---

# Project Manager topic index

## Protocols

- [Core operating protocol](references/core-protocol.md): ownership,
  precedence, privacy, and minimum saved context.
- [Initialization and recovery](references/initialization-and-recovery.md):
  create, inspect, move, recover, and handle concurrent changes.
- [Handoff protocol](references/handoff.md): task receipt, checkpoints, resume,
  and completion.
- [Refresh protocol](references/refresh.md): read-only active-chat re-anchoring,
  selective rule recovery, reconciliation, and deduplication.
- [Feedback protocol](references/feedback.md): capture bounded examples for
  later improvement without changing behavior automatically.
- [Change review](references/change-review.md): mandatory preview, approval,
  atomic write, and receipt format.

## Reusable output templates

- [Project memory front door](project_manager/templates/project-memory/README.md)
- [Active handoff](project_manager/templates/project-memory/HANDOFF.md)
- [Machine manifest](project_manager/templates/project-memory/manifest.json)
- [Rules index](project_manager/templates/project-memory/rules/README.md)

## Terminal interface

- `project-manager init`: deterministic initialization preview and apply.
- `project-manager status`, `check`, `context`, and `refresh`: read-only inspection
  and active-context recovery packets.
- `project-manager change`: exact preview and atomic approved apply.
- `project-manager handoff` and `feedback`: focused lifecycle helpers.
- `pmem`: short alias for the same executable.

---

[⌂ Home](README.md)
