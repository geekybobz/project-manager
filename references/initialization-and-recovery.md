---
role: topic
summary: Create and recover the minimal repository-local project-memory structure.
read_when: Use for initialization, freshness checks, moved projects, corruption, or concurrent edits.
---

# Initialization and recovery

## Initialize

For `#> memory init`, identify the repository root and inspect only enough
authoritative files to draft a compact project overview. Propose these files:

```text
.ai-memory/
├── README.md
├── HANDOFF.md
├── manifest.json
└── rules/
    └── README.md
```

Do not create `feedback/` until the first approved feedback case. Copy the
package templates, replace placeholders, assign a stable project ID, compute
freshness metadata, and present the complete change proposal before writing.
Initialization registers no central path and starts no watcher. A future
explicit registry may store a project ID, path hint, and summary separately.

## Progressive recovery

1. Read `.ai-memory/README.md`.
2. Read `.ai-memory/HANDOFF.md`.
3. Check only relevant manifest hashes or revisions when freshness matters.
4. Load the complete applicable rule or repository authority file.
5. Inspect only evidence and artifacts needed for the next action.

Same-thread continuation may rely on retained context until an important
checkpoint changes. Compaction recovery reloads the front door and active
handoff. A new model or chat follows the complete progressive recovery path.

## Failure handling

- **Missing memory:** do not invent it; offer initialization.
- **Missing optional rule or feedback directory:** continue if no reference
  requires it.
- **Corrupt manifest:** treat prose as readable but freshness as unknown;
  propose manifest repair.
- **Stale hash or revision:** reload the changed authority file and propose a
  reconciled update.
- **Moved project:** resolve the current root from the located `.ai-memory/`;
  update path hints without changing project identity.
- **Concurrent generation:** if generation changed after preview, cancel the
  write, reread, and issue a new proposal.
- **Conflicting decisions:** do not silently choose; show both owners and ask
  which guidance supersedes the other.
- **Interrupted save:** write atomically through a same-directory temporary
  file, preserve the last good bytes, and report incomplete files.
- **Repair workspace:** record the active isolated root and source revision;
  never redirect a repair into the live root because memory is missing.
- **Repeated external action:** a prior receipt is evidence only; obtain fresh
  authority before repeating the action.

One timestamped backup of the last good memory generation is sufficient during
a multi-file update. Remove it after validation unless repository policy asks
for retention. Let Git track durable Markdown when appropriate; keep secrets,
host delivery state, temporary files, and local registries ignored.

---

[⌂ Home](../README.md) · [Topic index](../INDEX.md)
