---
gate: 1
status: open
---

# Gate 1 — Mechanics: new WU types + driver dispatch + lint + templates

## Definition of done

- `close-intermediate` WU type registered in `loop.py` (`VALID_TYPES`,
  `MODEL_BY_TYPE`, `EFFORT_BY_TYPE`, `GATES_FOR_TYPE`).
- `close` type extended to any-terminal-gate (not just single-gate
  features).
- `lint_plan.py` accepts new shapes: 2-WU intermediate
  (`close-intermediate → plan-next`) on non-terminal gates; `close`
  on any terminal gate. Grandfathers old 4-WU sequence with WARNING.
  Mixed shapes within a feature: ERROR.
- `.specfuse/templates/PLAN.template.md` and `WU.template.md` updated
  to document the new shapes + `close-intermediate` type alongside
  existing types.
- `/draft-feature` skill updated to emit the new shapes by default.
- Gate 1 closing sequence uses OLD 4-WU (grandfathered).
- `RETROSPECTIVE.md` exists with G1 section, `LEARNINGS.md` appended
  if any G1-generalizable rules, `GATE-01-REVIEW.md` written by
  G1-PLAN to draft Gate 2.

## Reflection notes

<Written by the human at review time.>
