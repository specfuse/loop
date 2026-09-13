---
id: FEAT-2026-0106/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - append_progress_entry
produces:
  - tests/test_progress_lines_end_to_end.py
---

# Wire PROGRESS.md end to end from what the driver already receives

**Objective.** Make gate 1's `feature_oracle` runnable and green: the driver
writes one `PROGRESS.md` entry per dispatched unit, from the RESULT block it
already parses — the whole path, none of it well.

**Context.** FEAT-2026-0106/T01. This is the gate's **tracer bullet**
(`/authoring-work-units` §14): stubs are permitted here and nowhere else in
the gate. `parse_result_block` (`loop.py:4648`) already returns the agent's
entire RESULT block including `summary`, on every attempt with well-formed
output, and nothing persists it on the pass path. So this unit is a persist
plus a write, not a new mechanism. The forward-looking half of the note is
T02's and the conditional-reflection half is T03's; stub nothing of theirs
beyond what the oracle must observe.

**Acceptance criteria.**

- `python3 -m unittest tests.test_progress_lines_end_to_end -v -b` fails on
  HEAD before this unit's edits (the module does not exist) and passes after.
- The end-to-end test drives a real `loop.run()` through a gate of at least
  two units and asserts `PROGRESS.md` holds one entry per **dispatched** unit,
  in dispatch order, each naming the unit id — asserted against the file the
  run itself wrote, never one the test composed.
- An attempt whose RESULT block is missing or malformed still produces an
  entry, from the attempt record the driver holds rather than from the absent
  block. `parse_result_block` returns `None` by design on garbled output and
  the existing contract is that this degrades rather than crashes; a progress
  note that disappears exactly when a unit went wrong is worse than none.
- **How often a real agent emits `summary:` is recorded**, not assumed: the
  unit reports the count of dispatched attempts whose parsed RESULT carried a
  non-empty `summary` against the total, from this gate's own run. Measured
  across the existing corpus that figure is 8%, but every one of those is
  driver-set on a guard-refusal or smoke path — agent-supplied `summary` has
  never been measured, and T02 is scoped on the answer.

**Do not touch.** `judge.py` — the retrospective's `## Measurements` slice is
the judge's evidence path and is out of scope for the whole feature.
`closing_requirements.py`, which is T03's. `.specfuse/rules/result-contract.md`,
which is T02's. The sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient: this edits the driver's
attempt loop, which many modules drive through `loop.run()`, so run the
**full** suite — `python3 -m unittest discover -s tests -b` — before reporting
complete. Plus `python3 -m unittest tests.test_progress_lines_end_to_end -v -b`
and the symbol check (§9):
`python3 -c "from specfuse.loop.loop import append_progress_entry"`.

**Escalation triggers.** Stop with `status: blocked` if writing `PROGRESS.md`
cannot be done without changing what `parse_result_block` returns — its
forgiving contract is load-bearing for every unit's exit oracle and widening
it is not this unit's call.
