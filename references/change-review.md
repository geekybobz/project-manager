---
role: topic
summary: Mandatory two-phase review contract for every project-memory write.
read_when: Read immediately before proposing or applying any `.ai-memory/` edit.
---

# Project Memory change review

Every creation, edit, clear, archive, restore, or deletion uses two phases.
Reading and validation are not durable-memory writes. A validated proposal may
be held at the fixed visible review path `.ai-memory/review/pending.json` so an
exact approval can survive a message, process, or context boundary.

## Phase 1: proposal

Accept plan JSON from standard input by default. Validate and content-bind it,
then place one normalized proposal at the fixed review path. Never silently
replace another pending proposal. Show a compact summary first:

```text
Memory change ready for review

Purpose: <why durable memory should change>
Will change: <count and project-relative paths>
Memory changed: No; this is only a review proposal.
Checked: <identity, generation, paths, bytes, size, privacy>
Inspect: .ai-memory/review/pending.json
Approve: Reply “approve the pending memory change” or run
`project-manager review apply .`.
```

Follow the summary with each exact proposed addition or a compact unified diff.
State whether durable rules, active handoff, feedback, manifest generation,
hashes, or inventory will change. Keep the internal full-content binding in
JSON; do not make the user interpret or copy a digest.

## Approval boundary

Apply only the exact approved proposal. Any content change, additional file,
different operation, or changed target invalidates approval and requires a new
proposal. Approval for a memory edit does not authorize Git operations or any
external effect.

The pending file is omitted from the memory manifest. New initialized projects
ignore it through the review-area template; an older project may show it as an
untracked file until the proposal is consumed. It is not approval or durable
context. `review show` may inspect it, `review apply` rechecks and consumes it,
and `review discard` removes it after explicit rejection. A stale or invalid
proposal remains visible and cannot be applied.

## Phase 2: write and receipt

Immediately before writing, confirm the recorded generation, project identity,
content binding, and current bytes still match the proposal. Use atomic
same-directory replacement; every transient write remains under `.ai-memory/`
and is removed after replacement or failure. Validate links, JSON, required
sections, inventory, and hashes proportionally.

Return:

```text
Memory updated

Changed: <project-relative paths>
Checked: <plain result>
Generation: <old> → <new>
Pending proposal: Removed.
Next: <exact action, or “No further memory action is required.”>
```

If interrupted or partially applied, stop, preserve the last known-good bytes,
identify exact files, and propose recovery. Never describe a partial write as
successful.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
