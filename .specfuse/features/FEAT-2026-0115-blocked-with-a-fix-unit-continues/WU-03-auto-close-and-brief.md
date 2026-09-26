---
id: FEAT-2026-0115/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces_driver_helper:
  - render_insertion_refused_option
produces:
  - specfuse/loop/gate_eval.py
  - specfuse/loop/loop.py
  - tests/test_fix_unit_insertion_bookkeeping.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T16:29:44.413825+00:00
duration_seconds: 225.451
cost_usd: 1.335851
input_tokens: 96
output_tokens: 23777
---

# An inserted unit is off-plan for auto-close, and the brief says why insertion did not happen

**Objective.** Make the rest of the driver honest about an insertion: the gate
does not auto-close, the escalation brief names the drafted fix and the refusing
class when insertion was refused, and the progress line records it.

**Context.** FEAT-2026-0115/T03. Two edits. (1) `gate_eval.evaluate_auto_close`
check 2 reads `replan` events to disable auto-close; read `fix_unit_inserted`
the same way, and add the count to `metrics`. (2) `escalate_unit` /
`REPLAN_OPTION_SCOPE["agent_reported_blocked"]` in `specfuse/loop/loop.py`: when
the escalation payload carries `insertion_refused` (T02) or the feature is under
`review`, the brief's options part names the drafted file, the refusing class
and reason (or "review mode"), and the one command that arms it
(`/arm-gate`-style flip `draft → pending` plus the resume command). Keep the
six-part shape `operator-escalation.md` binds.

**Acceptance criteria.**

1. `tests/test_fix_unit_insertion_bookkeeping.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_fix_unit_insertion_bookkeeping -v -b` exits 0.
2. That module asserts `evaluate_auto_close` returns `auto: False` with a
   reason naming `fix_unit_inserted` for an events log carrying one, and
   `auto: True` for the same log without it.
3. It also asserts the escalation brief for a refused insertion contains the
   draft's file name, the refusing class and the arming command, and that the
   brief for a plain block (no `blocked_next`) is byte-identical to today's.
4. `python3 -m unittest tests.test_gate_eval tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option -v -b`
   exits 0 with no edit to those modules.

**Do not touch.** T01's insertion path and T02's checks; `arm_eval.py`;
`.specfuse/rules/` and `docs/` (T04); plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if `tests.test_gate_eval`
pins the exact `metrics` key set so adding a count breaks it (that is an arming
finding); or if the brief's six-part assertions
(`SpinoutBriefEveryPartHasContent`) reject the added option text.
