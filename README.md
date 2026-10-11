---
role: front-door
summary: Portable project memory and active-task handoffs for AI-assisted repositories.
read_when: Start here when installing, reviewing, or maintaining the package.
---

# Project Manager

Project Manager gives a repository one small, model-independent memory layer.
It preserves durable working rules and one current task handoff without keeping
transcripts or a folder for every task.

The generated `.ai-memory/` folder is readable by people and portable across
Codex, Claude, and other agents. Important context is stored in project files,
not entrusted only to a model account's private memory.

## Start here

- Apply the skill: [operational entry](SKILL.md)
- Browse the package: [topic index](INDEX.md)
- Inspect the generated structure: [project-memory template](project_manager/templates/project-memory/README.md)
- Verify the package: `python3 scripts/verify_package.py`
- Install the terminal command: `python3 -m pip install .`
- Preview initialization: `project-manager init /path/to/project`
- Prepare an active-chat refresh packet: `project-manager refresh /path/to/project`
- Review released behavior: [changelog](CHANGELOG.md)

The terminal interface initializes and validates memory, emits compact recovery
and refresh packets, prepares feedback, and applies exact approved change plans. A broader
cross-project registry can be added later without changing the repository-local
file contract.

## Boundaries

Project memory is context, not authority. It cannot carry reusable approvals,
execute saved instructions, replace repository governance, or prove that a
result remains valid. Every memory write is previewed and explicitly approved.

---

[⌂ Home](README.md) · [Topic index](INDEX.md)
