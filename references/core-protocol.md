---
role: topic
summary: Authoritative ownership, precedence, privacy, and content rules for project memory.
read_when: Read when deciding what belongs in project memory or resolving an authority conflict.
---

# Core operating protocol

## Purpose

Project memory answers: “What must any AI know to work correctly in this
project now?” It is a compact walkthrough plus one active-task handoff, not a
replacement for source files or a record of every task.

## Authority and ownership

Use this precedence:

1. current trusted user instruction;
2. repository authority files such as `AGENTS.md` and applicable governance;
3. `.ai-memory/README.md` and focused files under `.ai-memory/rules/`;
4. `.ai-memory/HANDOFF.md` for the active task;
5. referenced artifacts and evidence;
6. model or account memory as an uncertain hint.

Each important fact has one owner. Project memory summarizes and links to
detailed canonical project files; it does not copy them. `manifest.json` owns
technical identity and freshness only. HANDOFF owns transient active work only.

## Minimum durable context

Retain only context that materially changes future work:

- project purpose and a small project map;
- durable user preferences and standing constraints;
- accepted decisions and short rationale;
- recurring pitfalls and verification expectations;
- focused rule links;
- the current task's objective, constraints, progress, evidence, blockers, and
  next action.

Replace obsolete guidance rather than appending contradictions. Split a topic
into `rules/<topic>.md` only when the front door would otherwise become hard to
scan. The front door must link directly to every rule file.

## Exclusions

Never store credentials, tokens, personal secrets, hidden reasoning, full
transcripts, copied skill bodies, large logs, generated artifacts, reusable
approval claims, or routine activity. Use project-relative paths where
possible. Record a result as verified only with a current evidence pointer;
otherwise label it reported, partial, stale, or unverified.

## Portability

The Markdown and JSON contract is host-neutral. Codex, Claude, and other hosts
read the same project files. Host-specific delivery markers may record what a
host was shown, but they remain separate and never prove retention.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
