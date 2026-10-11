---
role: topic
summary: Capture user corrections as bounded evidence for later project or system improvement.
read_when: Use only when the user asks to save feedback or a correction should be proposed for durable capture.
---

# Feedback protocol

Feedback preserves a useful example without forcing normal workers to read task
history. It does not update a rule, skill, protocol, host, or orchestrator by
itself.

## Capture trigger

Use `#> feedback <correction>` or an equally explicit request. If the user gives
a reusable correction without asking to save it, propose whether it belongs in
project guidance, a feedback case, both, or neither. The user chooses scope.

Allowed scope values are `project`, `protocol`, `skill`, `orchestrator`, `host`,
and `cross-project`. A broad scope is a review target, not an automatic
generalization.

## File contract

Create `.ai-memory/feedback/` on first approved capture and add one
`FB-YYYYMMDD-NNN.md` containing:

- status and scope;
- target kind and identifier, if known;
- host/model context only when relevant;
- initial request summary;
- observed response summary;
- the user's correction, clearly attributed;
- desired future behavior;
- model interpretation, explicitly marked as inference;
- project-relative evidence pointers;
- privacy review and proposed disposition.

Summaries are preferred. Include exact prompt or response excerpts only when
the specific wording is necessary and the user approves it. Never include
hidden reasoning, credentials, unrelated personal data, or entire transcripts.

## Review and promotion

Normal task startup must not scan feedback. A separate explicit review may
classify a case as project-only guidance, a skill/protocol/orchestrator proposal,
a host issue, a documentation correction, insufficient evidence, or no change.
Any promoted edit has its own change proposal and approval. Preserve the
original user correction; do not rewrite it as a model conclusion.

Use `project-manager feedback draft . --input -` to accept the bounded JSON
payload through standard input. The generated feedback change uses the same
visible `.ai-memory/review/pending.json` slot and the same approval boundary as
any other memory edit; drafting never adds the feedback record directly.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
