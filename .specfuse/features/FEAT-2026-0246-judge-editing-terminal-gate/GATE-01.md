---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b"
cost_budget_usd: 20.00
---

# Gate 1 — a terminal gate that edits the judge cannot close unattended

## Definition of done

**Stated as an outcome.** Driven through the real driver with only the agent boundary
stubbed (the `tests/test_lifecycle_integration.py` style, `[FEAT-2026-0023/G1-CLOSE]`):

1. A single-gate feature whose done substantive unit declares a `produces:` path
   matching `arm_eval.JUDGE_PATHS` (or a non-empty `produces_driver_helper`) halts
   before the terminal close is dispatched or auto-closed: the close unit is
   `blocked_human`, a `human_escalation` event with reason `judge_editing_terminal`
   names each unit and path, and no terminal flip fires (gate not `passed`, roadmap
   row and `PLAN.md` not `done`).
2. A single-gate feature with no such unit closes exactly as on HEAD.
3. With `judge_edit_acknowledged: {paths, reason}` on the close unit covering every
   hit and the unit back at `pending`, a re-run proceeds to the close and emits an
   acknowledgement event carrying the reason; a hit outside the acknowledged paths
   re-fires the stop.
4. Clauses 1 and 3 hold under `autonomy_default` `auto`, `review` and `supervised`,
   and on a gate the auto-close predicate would close as well as on a dispatched
   close.
5. The escalation brief has the six parts `.specfuse/rules/operator-escalation.md`
   requires and states the clearing steps; no copy of `draft-feature`,
   `methodology.md` or `autonomy-stop-classes.md` recommends `review` as the
   safeguard for a terminal-gate judge edit.

The `feature_oracle` proves 1–5 end to end. It is red on the current tree (the module
does not exist); `FEAT-2026-0246/T01` is the walking skeleton that creates it and
turns clauses 1 and 2 green, with every other class `unittest.skip` naming its owner
(T02, T03, T04). A skip surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One definition of a judge surface.** Every unit reuses `arm_eval.JUDGE_PATHS` and
  `_matches_judge_path`; a second path list is a finding.
- **Pure check, impure wiring.** The check lives in `arm_eval.py` and reads files
  only; `loop.py` owns the status write, the event and the halt.
- **Positive control.** Every "closes unchanged" assertion is paired with a fixture
  that fires.
- **Expected self-halt.** This feature's own close is expected to trip the new stop
  (PLAN decision 8). That halt is the dogfood, not a defect: acknowledge it with
  your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
