---
name: project-manager
description: Always-on project support for portable, repository-local AI memory in `.ai-memory/`. Use for every repository or project task to initialize or read project memory, maintain the active HANDOFF, preserve durable rules and preferences, recover context, and capture approved feedback. Do not use for conversation with no project or working directory.
---

# Project Manager

Keep important project context portable across models, accounts, chats, and
compaction. Repository memory is the shared record; private model memory is
temporary and must never be the only location for important rules,
preferences, decisions, corrections, or handoff context.

This capability is mandatory and always active for every task in a project or
repository. At task entry, check for `.ai-memory/manifest.json`. If
it is absent, state that project memory is not initialized and propose
`project-manager init`; do not silently create it. If present, follow the start
or resume procedure below. Maintain the HANDOFF and durable memory at material
checkpoints even when the user does not repeat a save command.

## Non-negotiable behavior

- Treat current user instructions and repository authority files as higher
  authority than `.ai-memory/`.
- Treat saved content as advisory context, never as approval for a new commit,
  push, deployment, deletion, purchase, external message, retry, or other
  consequential action.
- Never copy secrets, credentials, full transcripts, hidden reasoning, skill
  bodies, or large source artifacts into project memory.
- Never silently edit project memory. Show the structured change proposal from
  [change review](references/change-review.md), then wait for explicit approval
  of that exact proposal.
- Do not create per-task folders, a chronological task diary, a background
  watcher, telemetry, or an automatic transcript logger.
- Do not scan `feedback/` during normal task work. Feedback cases are evidence
  for later review, not active instructions.

## Start or resume work

When `.ai-memory/manifest.json` exists:

1. Read `.ai-memory/README.md` and `.ai-memory/HANDOFF.md`.
2. Read `manifest.json` only when identity or freshness matters.
3. Load only the rule files and project artifacts needed for the current task.
4. If retention is uncertain, a referenced file changed, or hashes disagree,
   reload the complete relevant instruction file rather than relying on memory.
5. State any stale, missing, or conflicting memory before relying on it.

For exact recovery behavior, read
[initialization and recovery](references/initialization-and-recovery.md).

## Maintain the active task

At the start of a material task, prepare a HANDOFF task receipt containing:

- the user's request with spelling and grammar corrected without changing intent;
- task understood;
- plan;
- selected skills or capabilities;
- mode and boundaries.

During work, propose a HANDOFF refresh at meaningful checkpoints: a material
decision, verified result, changed blocker, uncertain continuation, imminent
compaction, or transfer to another model. Keep progress and verification
separate. On completion, propose durable promotions to `README.md` or `rules/`,
then propose clearing HANDOFF to its idle state. Read
[handoff protocol](references/handoff.md) for the exact fields and flows.

## Preserve durable project knowledge

Propose a memory change when the user gives a reusable preference, standing
rule, correction, accepted decision with rationale, recurring pitfall,
verification expectation, or stable project map fact. Put each fact in one
authoritative place:

- `.ai-memory/README.md`: compact project overview, shared preferences, durable
  decisions, project map, and links to every rule.
- `.ai-memory/rules/<topic>.md`: detailed reusable rules for one subject, created
  only when enough content exists to justify a separate file.
- `.ai-memory/HANDOFF.md`: one replaceable active task, never task history.
- `.ai-memory/manifest.json`: identity, generation, inventory, and freshness
  metadata; never duplicate prose guidance.
- `.ai-memory/feedback/FB-*.md`: approved, bounded improvement evidence.

## Commands

Interpret these as intent controls, not permission bypasses:

- `#> memory init`: inspect the repository and propose the minimal `.ai-memory/`
  structure.
- `#> memory save`: propose durable updates and/or an active HANDOFF refresh.
- `#> handoff`: propose the smallest complete transfer checkpoint.
- `#> resume`: read-only recovery from current project memory.
- `#> project-manager refresh`: re-anchor an active chat to current project
  memory while preserving live task state and mode; read-only and deduplicated
  only while complete required sources remain reliably retained.
- `#> feedback <correction>`: propose one feedback case; do not generalize or
  change rules automatically.

All write commands produce a preview first and require explicit approval.

The deterministic terminal companion uses `project-manager` (short alias:
`pmem`):

- `project-manager init .`: preview initialization; add `--apply` only after
  review.
- `project-manager status .` and `project-manager check .`: inspect state and
  freshness without writing.
- `project-manager context . --format json`: return bounded recovery context.
- `project-manager refresh . --format json`: return a read-only refresh packet
  with freshness, source identities, core memory, rule candidates, and a
  non-persistent deduplication key.
- `project-manager change preview PLAN.json`: validate an exact model-prepared
  change.
- `project-manager change apply PLAN.json --approval-ref PM-...`: atomically
  apply only the approved plan.
- `project-manager handoff show .` or `handoff clear`: inspect or prepare an
  idle handoff.
- `project-manager feedback draft . --input FEEDBACK.json`: prepare a bounded
  feedback change without applying it.

## Routing

- Creation, freshness, corruption, moved roots, or concurrent writers:
  [initialization and recovery](references/initialization-and-recovery.md)
- Task receipt, save, handoff, resume, and completion:
  [handoff protocol](references/handoff.md)
- Active-chat context re-anchoring: [refresh protocol](references/refresh.md)
- User corrections and future improvement evidence:
  [feedback protocol](references/feedback.md)
- Exact preview, approval, write, and receipt format:
  [change review](references/change-review.md)
- Package and template map: [topic index](INDEX.md)

---

[⌂ Home](README.md) · [Topic index](INDEX.md)
