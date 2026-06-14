---
gate: 1
status: open
cost_budget_usd: 14.00  # raised mid-flight from 8.00 — T01/T02 ran 1.6×/2.8× plan; predicate v1 self-fires gate_budget_exceeded against original 8.00 captured in retrospective
---

# Gate 1 — `gate_eval.py` module + tests + backtest CLI

## Definition of done

- `.specfuse/scripts/gate_eval.py` exists and is importable. Exposes
  `AutoCloseDecision` dataclass and `evaluate_auto_close(feature_dir,
  gate_id) -> AutoCloseDecision` function. Pure module: no imports
  from `loop.py`, no driver state mutation, no git commands.
- Hardcoded v1 predicate constants live at the top of the module
  (named constants, not magic numbers in conditionals).
- `tests/test_gate_eval.py` exists. One fixture per predicate
  criterion plus combined-scenario fixtures. Coverage on
  `gate_eval.py` ≥ 90% per-file.
- CLI entrypoint: `python3 .specfuse/scripts/gate_eval.py backtest
  <feature-id> [--gate N]` prints human-readable decision + reasons
  to stdout. Exit 0 always (read-only tool).
- Calibration regression test: CLI smoke-run against the 5 backtest
  features (0013, 0014, 0015, 0017, plus 0011 if completed) asserts
  the decision table matches the empirically-determined baseline
  (0013 + 0014 auto-eligible, 0015 + 0017 not). Test fixture pins
  the expected output; drift flags either predicate change or
  feature-data change.
- A retrospective exists (feature-local `RETROSPECTIVE.md`, written
  by G1-CLOSE-INTERMEDIATE).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- Next gate's work units are drafted, and `GATE-02-REVIEW.md` is
  written.

The closing sequence (close-intermediate → plan-next) is part of
every non-terminal gate and is enforced by the linter. The driver
runs the gate unattended, then stops here for human review-and-arm.

## Reflection notes

<Written by the human at review time. Predicate constants tuning
notes — anything the backtest signal didn't predict, edge cases
discovered, false-positives or false-negatives observed during
T03 calibration. Keep honest.>
