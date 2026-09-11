---
id: FEAT-2026-0104/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces_driver_helper:
  - reload_unit_after_replan
produces:
  - tests/test_replan_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-10T19:19:50.315687+00:00
duration_seconds: 713.628
cost_usd: 2.321728
input_tokens: 120
output_tokens: 40563
---

# Wire the thinnest re-plan path end to end

**Objective.** Make gate 1's `feature_oracle` runnable and green by wiring a
failing unit through a re-plan turn and back into dispatch with a reloaded
body — the whole path, none of it well.

**Context.** FEAT-2026-0104/T01. This is the gate's **tracer bullet**
(`/authoring-work-units` §14): stubs are permitted in this unit and nowhere
else in the gate. The path crosses one hard constraint —
`units = [load_wu(feature_dir, ref) for ref in gate.refs]` at `loop.py:9202`
runs once per gate, *before* the `while True:` dispatch loop, so a re-planned
unit's rewritten body is invisible to the gate that re-planned it. Establishing
a reload point for a single unit is the point of this WU. The trigger's real
predicate is T02's, the turn's real contract is T03's, and the real event is
T04's; stub each to the thinnest thing that lets the oracle observe the path.

**Acceptance criteria.**

- `python3 -m unittest tests.test_replan_end_to_end -v -b` fails on HEAD
  before this unit's edits (the module does not exist) and passes after.
- The end-to-end test drives a unit to its second-to-last permitted attempt
  and asserts the next dispatch receives a **body that differs** from the one
  the prior attempt received — asserted on the dispatched prompt, not the file
  on disk, since the snapshot at `loop.py:9202` is exactly what this unit
  changes.
- A re-planned unit that then **passes** reaches `status: done` and the gate
  runs to completion without reporting it stranded. Reloading a unit must
  reconcile it with the list `ready()` iterates and with `done_ids`: a
  previous attempt reloaded the object but left the gate's bookkeeping
  pointing at the stale one, so a unit that had passed was reported as
  `never became ready` and stranded its gate.
- `python3 -m unittest tests.test_deterministic_refusal_repeat -v -b` still
  passes: a byte-identical refusal over an untouched tree escalates where it
  did before and does not become a re-plan.

**Do not touch.** `specfuse/loop/gate_eval.py` — its `replan` consumer is
already correct and T04 owns the emit side that meets it.
`driver-event.schema.json` is T04's. The sibling WU files in this gate.
`.specfuse/rules/never-touch.md` binds as always: the driver owns all git.

**Verification.** The narrow tier is NOT sufficient for this unit: it edits
the central dispatch loop, which 44 test modules drive through `loop.run()`,
so run the **full** suite — `python3 -m unittest discover -s tests -b`, OK on
3901 tests in ~151s on a clean tree — before reporting complete. Narrow tier for `implementation`: the `code` gates minus
`tier: broad`, plus `python3 -m unittest tests.test_replan_end_to_end -v -b`.
Symbol check for every new symbol this unit introduces (§9) — name it in the
attempt report and grep it in the tree you are handing over.

**Escalation triggers.** Stop with `status: blocked` if the reload point
cannot be established without changing `gate.refs` — that is out of scope by
PLAN.md's scope boundary and the shape of the feature would need to change.
Stop also if making the oracle green requires touching the attempt accounting
FEAT-2026-0103 just rewrote in a way its tests do not cover.
