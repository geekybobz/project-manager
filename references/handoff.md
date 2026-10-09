---
role: topic
summary: Define task receipts, checkpoints, completion, resume, and cross-model handoff.
read_when: Use when starting, saving, transferring, resuming, or completing a material task.
---

# Handoff protocol

`HANDOFF.md` contains exactly one replaceable active task. It is not a task
archive. When no task is active, retain the idle skeleton.

## Task receipt

At task start, prepare:

- **User request:** the user's request corrected for spelling and grammar while
  preserving scope and intent;
- **Task understood:** a concise operational interpretation;
- **Plan:** the next few bounded steps;
- **Skills or capabilities:** selected packages and why;
- **Mode:** active modes and whether they are chat-scoped;
- **Boundaries:** explicit exclusions, approval gates, and working root.

Show the receipt to the user. Any HANDOFF write still follows the separate
change-review approval protocol.

## Active checkpoint

Store the minimum continuation state:

- objective and current phase;
- constraints and accepted decisions with rationale;
- active working root and relevant revisions;
- completed effects, separate from attempted work;
- verification performed, evidence pointers, and known limitations;
- selected skills or modes still relevant;
- unresolved issues and blockers;
- one concrete next action.

Never label implementation complete because a plan exists, or verified because
a command was attempted. A completed external effect should have a compact
receipt sufficient to avoid accidental repetition, but the receipt grants no
future authority.

## Flow by situation

- **Same thread:** refresh only after a material change; do not rewrite on every
  message.
- **Compaction recovery:** reread the project front door and active handoff,
  then reload complete relevant instructions when retention is uncertain.
- **New thread or model:** read front door, handoff, relevant freshness, then
  only the linked rules and artifacts needed for the next action.
- **Completion:** propose lasting knowledge for `README.md` or `rules/`, record
  final verification accurately, then propose clearing HANDOFF to idle.

## Flowcharts

```mermaid
flowchart TD
    A[Material checkpoint] --> B[Draft minimal changes]
    B --> C[Show proposal and exact files]
    C --> D{Approved unchanged?}
    D -- No --> E[Do not write]
    D -- Yes --> F[Check generation and freshness]
    F --> G{Still current?}
    G -- No --> B
    G -- Yes --> H[Atomic write and validate]
    H --> I[Return change receipt]
```

```mermaid
flowchart TD
    A[Resume] --> B[Read README]
    B --> C[Read HANDOFF]
    C --> D[Check relevant freshness]
    D --> E[Load only applicable rules and evidence]
    E --> F[State current objective and next action]
```

```mermaid
flowchart TD
    A[New model or chat] --> B[Locate .ai-memory]
    B --> C[Read README and HANDOFF]
    C --> D{Missing, stale, or conflicting?}
    D -- Yes --> E[Report and recover progressively]
    D -- No --> F[Load required complete instructions]
    E --> F
    F --> G[Continue from concrete next action]
```

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
