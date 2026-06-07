---
gate: 1
status: awaiting_review
---

# Gate 1 — Combined close for single-gate features

## Definition of done

- A new `close` work-unit type collapses the four closing ceremonies
  (retrospective + lessons + docs + terminal verdict) into one session.
- `lint_plan.py` accepts a gate's closing as **either** the existing
  `[retrospective, lessons, docs, plan-next]` sequence **or** a single `close`
  WU — and the single `close` is valid **only when the feature has exactly one
  gate** (rejected on multi-gate features).
- `loop.py` maps the `close` type to a verification gate set and treats a passing
  `close` WU as completing the gate.
- `WU.template.md` documents the `close` type and its single-gate-only constraint.
- Tests prove: lint accepts a single-gate `close`, rejects `close` on a
  multi-gate feature, and still accepts the four-WU sequence.
- A retrospective exists; lessons promoted; docs/roadmap reconciled.

This feature itself closes with the **four-WU** sequence (the `close` type does
not exist when this gate's driver loads `loop.py`). FEAT-2026-0006 is the first
to use the new `close` WU.

## Reflection notes

<Written by the human at review time.>
</content>
