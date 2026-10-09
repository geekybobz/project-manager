---
role: topic
summary: Mandatory two-phase review contract for every project-memory write.
read_when: Read immediately before proposing or applying any `.ai-memory/` edit.
---

# Project Memory change review

Every creation, edit, clear, archive, restore, or deletion uses two phases.
Reading and validation are not writes.

## Phase 1: proposal

Use one stable proposal ID and show:

```text
Project Memory change — PM-YYYYMMDD-NNN

Reason: <why durable memory should change>
Operation: add | update | replace | clear | archive | delete
Files:
- <project-relative path>
Scope: project | handoff | feedback | technical metadata
Status: awaiting approval

Current:
<exact current text, or "file does not exist">

Proposed:
<exact replacement/addition, with no hidden edits>

Effect:
<what future models will do differently>

Reply: Approve PM-YYYYMMDD-NNN, request changes, or reject.
```

For several files, give each file its own Current and Proposed block. A compact
unified diff may replace those blocks only when it is easier to review. State
whether durable rules, active handoff, feedback, manifest generation, hashes,
or inventory will change.

## Approval boundary

Apply only the exact approved proposal. Any content change, additional file,
different operation, or changed target invalidates approval and requires a new
proposal. Approval for a memory edit does not authorize Git operations or any
external effect.

## Phase 2: write and receipt

Immediately before writing, confirm the recorded generation and current bytes
still match the proposal. Use atomic same-directory replacement and private
permissions for untracked operational files. Validate links, JSON, required
sections, inventory, and hashes proportionally.

Return:

```text
Project Memory receipt — PM-YYYYMMDD-NNN

Result: applied | not applied | partially recovered
Files:
- <project-relative path>
Validation: <checks and honest result>
Generation: <old> -> <new>
Backup: <none, removed, or exact retained path>
```

If interrupted or partially applied, stop, preserve the last known-good bytes,
identify exact files, and propose recovery. Never describe a partial write as
successful.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
