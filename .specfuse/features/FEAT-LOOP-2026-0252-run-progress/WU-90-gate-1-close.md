---
id: FEAT-LOOP-2026-0252/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
judge_edit_acknowledged:
  paths:
    - .specfuse/verification.yml.example
    - produces_driver_helper
    - specfuse/loop/agent_policy.py
    - specfuse/loop/arm_eval.py
    - specfuse/loop/data/schemas/driver-event.schema.json
    - specfuse/loop/data/verification.yml.example
    - specfuse/loop/loop.py
  reason: "Driver changes reviewed and sound, accept them"
re_arm_count: 2
re_arm_history:
  -
    timestamp: 2026-11-27T03:36:01+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 0.0
    prior_duration_seconds: 0.0
    reason: "Driver changes reviewed and sound, accept them"
  -
    timestamp: 2026-11-27T04:09:24+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.889367
    prior_duration_seconds: 409.775
    reason: "Fixed the stop-reason offset, re-close it"
cumulative_cost_usd: 1.889367
cumulative_duration_seconds: 409.775
cumulative_input_tokens: 68
cumulative_output_tokens: 44336
cumulative_attempts: 1
cost_usd: 1.46683
duration_seconds: 276.577
input_tokens: 50
output_tokens: 30666
folded_through_re_arm: 2
gate_set: plannext
verdict: met
driver_version: 0.33.2
started_at: 2026-11-27T04:17:54.347623+00:00
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: phase events written as they happen, a status file with
a heartbeat, plain driver lines, `specfuse-loop --watch`, and one notification when the run
stops.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven
   and by which test, and that no `unittest.skip` survives in `tests/test_run_progress.py`. It
   lists every pre-existing test that was changed (clause 7), with why.
2. Each consumer-visible change (phase events and driver lines, the status file and
   `defaults.heartbeat_seconds`, `--watch`, the stop notification and
   `escalation.notify_command`) is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0252`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`.
4. "What the loop did NOT verify" names, at minimum: real desktop and chat delivery (stubs
   only), a real multi-minute attempt watched live, and a real driver crash (exceptions are
   simulated). Each points at `PLAN.md`'s post-merge checklist.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, a notification sent more or fewer than once per stop
in any test, or a change to `dispatch()` or the `attempt_outcome` payload: record `not_met` with
a follow-up.

**Re-close note (2026-11-26).** The first close recorded `not_met` on #3626: the stop reason was
read from `events.jsonl` past a byte offset taken before `run()` checks out the feature branch.
Fixed on the branch (`notify_stop` reads events stamped at or after the run's start; tests in
`TestStopNotification` with a real checkout both ways; see `PLAN.md` Notes). That close already
wrote `RETROSPECTIVE.md`, `FOLLOW-UPS.md`, `LEARNINGS-pending.md` and changelog fragments: update
them in place, do not duplicate fragments, and say in `FOLLOW-UPS.md` whether #3626's re-run
condition now holds.
