---
id: FEAT-LOOP-2026-0251/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 2.00
produces:
  - specfuse/loop/loop.py
  - tests/test_fail_fast_deliverables.py
produces_driver_helper:
  - execute_unit_attempt
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-25T23:21:07.458266+00:00
duration_seconds: 365.44
cost_usd: 0.875979
input_tokens: 26
output_tokens: 19488
---

# T01 — walking skeleton: refuse `produces_not_in_diff` before `verify()`

**Objective.** Make the gate's `feature_oracle` runnable and turn Definition-of-done clause 1
green. This is the tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0251/T01`; decisions 4 and 5 in `PLAN.md`.

- Today the produces-in-diff decision (`prod_ok` / `_prod_remaining`, with its
  `produces_unchanged:` and `produces_amended:` handling) runs in `run()` after
  `execute_unit_attempt()` returns a passing verify. Lift that decision into one helper and
  call it after the agent session and before `verify_fn` in `execute_unit_attempt()`. A
  refusal there returns without calling `verify_fn`, and the attempt ends
  `produces_not_in_diff` with the same failure class, signature and summary as today.
- The late call site keeps working through the same helper (it still guards the
  `fail_fast_deliverables: false` path T02 adds), so the condition exists once.
- The early refusal's tree handling goes through `_resolve_guard_refusal_tree`, as the late one
  does. Where its note would say verification passed, it must say verification did not run.

Create `tests/test_fail_fast_deliverables.py`, one class per Definition-of-done clause in
`GATE-01.md`: `TestProducesNotInDiffEarly`, `TestPresenceEarly`, `TestOptOut`,
`TestTreeAndNote`, `TestArmTimeWarning`. Implement clause 1; skip the rest naming T02, T03, T04.

**Acceptance criteria.**

1. `tests.test_fail_fast_deliverables.TestProducesNotInDiffEarly` fails on HEAD and passes
   after. With a stubbed session leaving a declared `produces:` path untouched and no
   justification, the attempt ends `produces_not_in_diff`, `verify_fn`'s call counter is 0, the
   attempt's `verify_seconds` is 0 and no `gate_result` event is emitted. The same unit with the
   path changed calls `verify_fn` once and passes.
2. The early refusal's `failure_class`, `failure_signature` and `summary` equal what the late
   refusal records for the same input (asserted in the class).
3. `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` passes; any
   existing test that asserted verify runs before this guard is updated and listed in the
   RESULT's notes.

**Do not touch.** The `deliverable_missing` and `no_deliverable_files` sites and
`verification.yml.example` (T02). Retry-note wording beyond "verification did not run" (T03).
`lint_plan.py` and docs (T04).

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If the diff the late guard reads (the squash) cannot be reproduced
before `verify()` without committing, block with the evidence rather than committing early.
