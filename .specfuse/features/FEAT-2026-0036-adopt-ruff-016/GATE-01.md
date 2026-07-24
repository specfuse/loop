---
gate: 1
status: open
---

# Gate 1 — Adopt ruff 0.16 and lift the pin

Definition of done: the whole tree passes `ruff check` under ruff 0.16.x, the
full test suite is unchanged and green, and `pyproject.toml` no longer pins
`<0.16`. CI's lint gate resolves ruff 0.16 and passes.

## Arming discipline

No behavior flag, no runtime probe, no severity flip is introduced by this gate
— the flag-scope table and escalation-predicate checks are n/a (recorded in
PLAN.md). Before arming, confirm only that ruff ≥ 0.16 is installable in the
working venv (so T01 can verify against it) and that the current pin is still
`<0.16` (so T02 has something to lift). Both WUs are behavior-preserving
(import-formatting / dependency-constraint), so arming risk is low; the review
autonomy default exists to eyeball the mechanical import diff, not to gate a
behavior change.
