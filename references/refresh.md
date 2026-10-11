---
role: topic
summary: Re-anchor a long-running chat to current project memory without resetting task state or mode.
read_when: Use when the user invokes Project Manager refresh or retained project rules may be uncertain.
---

# Project Manager refresh

`#> project-manager refresh` is a read-only context re-anchoring operation for
an active chat. It is not a conversation reset, memory save, resume command, or
adherence mode. It never flushes existing context, changes mode, scans feedback,
or writes refresh state.

## Refresh procedure

1. Preserve the live user request, task phase, active files, current decisions,
   completed effects, pending approvals, controls, and mode before consulting
   saved memory. Do not let an older HANDOFF replace newer live facts.
2. Resolve only the known current project root. Run `project-manager refresh .
   --format json` or the equivalent library operation to validate memory and
   obtain its source identities. Never search historical folders for a project.
3. Read the applicable repository authority for the active path, then reread
   the complete `.ai-memory/README.md`, `.ai-memory/HANDOFF.md`, and
   `.ai-memory/rules/README.md` from the packet.
4. Use the current task and rule index to choose only applicable rule candidates;
   read every selected rule completely. Do not truncate a rule or load unrelated
   evidence merely to make the receipt look complete.
5. Reconcile rather than overwrite. Current higher instructions, current user
   instructions, and repository authority outrank saved memory. Preserve a clear
   current-user exception to an ordinary memory rule when authority permits;
   report its reason and request scope without saving it automatically. Ask once
   when the exception is ambiguous.
6. Return a compact receipt naming the project, generation, freshness, restored
   authority/core/rules, preserved live task, temporary exceptions, unchanged
   mode, and next action. Continue the active request.

## Efficiency and deduplication

The refresh packet contains a key derived from project identity, memory
generation, and current source hashes. A repeated request with the same key may
return `already current` only while every required complete file is reliably
retained. After compaction, transfer, revision change, or retention uncertainty,
reread the complete relevant sources even when the key matches. Keep the key in
current model context only; do not create a persistent log, hidden marker,
watcher, timer, or background refresh.

Refresh runs only on explicit request, known compaction/transfer recovery, or an
accepted recovery step after an observed retention failure. A long chat alone
does not trigger periodic refresh.

## Failure behavior

- Missing memory: report it and offer `#> memory init`; invent nothing.
- Invalid manifest: treat readable prose as advisory, freshness as unknown, and
  block memory mutation until repaired.
- Stale hashes: read current live bytes, name stale paths, and keep reconciliation
  separate from this read-only operation.
- Oversized core or rule: stop and report the limit; never silently truncate it.
- Stored approvals or external actions: restore them only as history, never as
  current permission or a reason to repeat an effect.
- Conflict with a live instruction: follow the authority order, report the
  scoped exception or ask once, and do not silently rewrite durable memory.

Strict mode remains independent. Refresh leaves the current mode unchanged;
the user may separately request strict adherence when appropriate.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
