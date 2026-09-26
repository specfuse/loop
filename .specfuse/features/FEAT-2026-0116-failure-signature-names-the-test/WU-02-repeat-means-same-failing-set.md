---
id: FEAT-2026-0116/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
produces_driver_helper:
  - detect_spinning_signature_repeat
produces:
  - specfuse/loop/loop.py
  - tests/test_spinning_repeat_same_failing_set.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T17:56:06.423393+00:00
duration_seconds: 534.82
cost_usd: 1.858836
input_tokens: 126
output_tokens: 32119
---

# A repeat is the same failing set; every spinning escalation carries its evidence

**Objective.** Make `detect_spinning_signature_repeat` compare failing sets so a
changed set is progress, and make every spinning-family escalation payload carry
the last attempt's class, signature and failing set.

**Context.** FEAT-2026-0116/T02. In `specfuse/loop/loop.py`, extend
`detect_spinning_signature_repeat(current, prior)` to take the two attempts'
`failing_tests` (thread them beside `prior_failure_signature` in `run()`): when
both sets are non-empty, repeat iff the sets are equal; when either is empty,
today's `(class, signature)` equality **and** an equal `failure_excerpt` (the
cheaper alternative #3414 names). The for-else exhaustion path that emits
`spinning_detected` (payload: reason, attempts, attempts_usage, message) gains
`failure_class`, `failure_signature` and `failing_tests` from the last
`attempt_outcome`; the `spinning_signature_repeat` escalation and the frontmatter
stamps the re-arm gate reads gain `failing_tests` too. The re-arm reproduction
gate (`tests/test_spinning_rearm_gate.py`) keeps comparing the recorded
signature. Red test first.

**Acceptance criteria.**

1. `tests/test_spinning_repeat_same_failing_set.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_spinning_repeat_same_failing_set -v -b`
   exits 0.
2. That module asserts, through `loop.run()` with a stubbed `verify` that fails
   attempt 1 on test A and attempt 2 on test B (both `tests`, both reports
   ending `FAIL: Tests run: …`): no `spinning_signature_repeat` escalation
   after attempt 2; and with A on both attempts: the escalation fires after
   attempt 2 with `failing_tests` naming A.
3. It also asserts that an exhausted unit's `spinning_detected` escalation
   payload carries `failure_class`, `failure_signature` and `failing_tests`,
   none null.
4. `python3 -m unittest tests.test_attempt_outcome_emission tests.test_spinning_rearm_gate tests.test_deterministic_refusal_repeat tests.test_failure_signature_names_the_test -v -b`
   exits 0 with no edit to the first three modules.

**Do not touch.** `extract_failing_tests` (T01); `detect_deterministic_refusal_repeat`;
`replay_spin.py` and `docs/` (T03); the re-arm reproduction gate's
comparison; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if `test_spinning_rearm_gate`
asserts a frontmatter key set that a new `failing_tests` stamp breaks (an arming
finding); or if the excerpt is not retained between attempts at the detector
call site — say where it is dropped.
