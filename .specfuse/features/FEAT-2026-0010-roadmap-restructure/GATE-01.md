---
gate: 1
status: passed
---

# Gate 1 — Mechanics and migration

## Definition of done

- `.specfuse/roadmap-archive.md` exists with the documented anchor and
  back-link conventions.
- `.specfuse/roadmap.md`'s table carries a `Detail` column; the six rows
  for FEAT-2026-0003..0008 reference their archived sections via
  `[→ archive](roadmap-archive.md#feat-2026-000N)`.
- The six detail sections for FEAT-2026-0003..0008 have been moved out of
  `.specfuse/roadmap.md` and appended to `.specfuse/roadmap-archive.md`,
  byte-equivalent except for the prepended anchor.
- `.claude/skills/roadmap-archive/SKILL.md` and
  `.claude/skills/roadmap-add/SKILL.md` exist, are symlinked into
  `.specfuse/skills/`, and have green self-tests in `tests/`.
- A retrospective exists at `RETROSPECTIVE.md`.
- Generalizable lessons promoted to `.specfuse/LEARNINGS.md`.
- Docs and roadmap reflect what was built.
- Gate 2's work units are drafted (or the gate is explicitly closed out
  if Gate 1 covered everything required) and `GATE-01-REVIEW.md` is
  written.

## Reflection notes

<Written by the human at review time.>
