---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b"
cost_budget_usd: 20.00
broad_run:
  tree: 054923b0bea95ba720a9a42a693f4da9e9ea960f:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:4acc6dfc5e8cece358c167d876515eba4a39a500:4ebc0fce17e68de94eb926c6e80d18001b9c2e05:5ff66b6e4d8a264f23709ea60706111a4c59ed11:7ea5e7205e93f2529b31fb335a5e68c612701128:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9b3386cac79ef7bbd03df4b421ab7dc4a900d9d6:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:da3f73481fc200f16e8ef4d9047e1eaf3232c07d:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:e53c32c1893ef61f35d7431054d17885daee73fa:e998fdd880f3c7212bc243bbced03ad2606a1a20:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-10-29T12:37:49.819469+00:00
  ok: true
  failing: []
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
