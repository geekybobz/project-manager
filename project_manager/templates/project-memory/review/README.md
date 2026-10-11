---
role: operational-review
summary: Visible fixed location for one unapproved Project Manager proposal.
read_when: Inspect when Project Manager reports that a memory change is awaiting review.
---

# Pending memory review

Project Manager may place one validated but unapproved proposal at
`pending.json`. The file is operational review material, not durable project
knowledge, and is intentionally excluded from Git and the memory manifest.

Use `project-manager review show .` to inspect it, `review apply` after actual
approval, or `review discard` to reject it. A different proposal never silently
replaces the pending one. Successful apply or explicit discard removes it.

---

[⌂ Home](../README.md)
