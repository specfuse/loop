---
id: FEAT-2026-0114/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces_driver_helper:
  - PRODUCES_REPAIR_EXAMPLE
produces:
  - specfuse/loop/loop.py
  - tests/test_produces_repair_note.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T15:03:21.734850+00:00
duration_seconds: 384.008
cost_usd: 1.229695
input_tokens: 94
output_tokens: 23386
---

# The repair note shows both escape hatches, and the second identical refusal is the last

**Objective.** Make a `produces_not_in_diff` refusal repairable in one attempt and
terminal after two: the note carries the exact RESULT YAML for
`produces_unchanged:` and `produces_amended:`, and the refusal is recorded in
`refusal_history` so `detect_deterministic_refusal_repeat` fires before a third
dispatch.

**Context.** FEAT-2026-0114/T02. Evidence: nine repair attempts across six units
in the 2026-09-10..26 window changed nothing and never used `produces_unchanged:`
(PLAN.md). Two edits in `specfuse/loop/loop.py`. (1) The note built inline at the
`produces_not_in_diff` site and `_RETRY_CLASS_HINT["produces_not_in_diff"]` name
the key but show no shape; add a module constant `PRODUCES_REPAIR_EXAMPLE` holding
the two-entry ```result fence from `.specfuse/rules/result-contract.md`'s schema
(one `produces_unchanged:` item, one `produces_amended:` item, each with the
unit's own first unmatched path substituted) and append it to the note after
the complaint and before the retained diff. (2) Every other guard site appends
`(summary, _refusal_touched)` to `refusal_history` before `continue`; the
produces site does not, which is why the short-circuit at the top of the attempt
loop never sees it. Append there too, so two identical refusals on the same
touched set end the unit as `deterministic_refusal_repeat` (#1415) instead of
running a third attempt.

**Acceptance criteria.**

1. `tests/test_produces_repair_note.py` fails on HEAD before this unit's edits
   (the module is absent); after, `python3 -m unittest tests.test_produces_repair_note -v -b`
   exits 0.
2. That module asserts, through `loop.run()` with a stubbed dispatch that
   returns the same unjustified RESULT on every attempt for a unit with
   `max_attempts: 3`: attempt 2's prompt contains a ```result fence with both
   `produces_unchanged:` and `produces_amended:` entries naming the unmatched
   path; the unit ends `blocked_human` with `escalation_reason:
   deterministic_refusal_repeat` after exactly two `attempt_outcome` events.
3. `python3 -m unittest tests.test_deterministic_refusal_repeat tests.test_guard_repair_e2e tests.test_guard_refusal_failure_excerpt -v -b`
   exits 0 with no edit to those modules.

**Do not touch.** `produces_amendments` / `apply_produces_amendment` (T01);
`detect_deterministic_refusal_repeat` itself; `.specfuse/rules/` and `docs/` (T04);
plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if `_refusal_touched` is not
in scope at the produces site (name where it is measured); or if the retained
tree (`retain_on_guard_refusal`) makes the second refusal's touched set differ
from the first so the repeat never matches — say what differed.
