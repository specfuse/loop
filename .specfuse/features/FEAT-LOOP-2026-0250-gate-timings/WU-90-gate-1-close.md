---
id: FEAT-LOOP-2026-0250/G1-CLOSE
type: close
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 5.00
auto_close_disabled: true
judge_edit_acknowledged:
  paths:
    - produces_driver_helper
    - specfuse/loop/data/schemas/driver-event.schema.json
    - specfuse/loop/loop.py
  reason: "All test are passing and we can continue"
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-11-25T17:03:20+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 0.0
    prior_duration_seconds: 0.0
    reason: "All test are passing and we can continue"
model: sonnet
effort: high
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: every gate run records its result and duration, each
attempt splits agent time from verification time, and `specfuse stats` reports both.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven and
   by which test, and that no `unittest.skip` survives in `tests/test_gate_timings.py`.
2. Each consumer-visible change in the §3 enumeration is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0250`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`, and
   reports this feature's own agent/verify split from the `specfuse stats` output on this
   repository.
4. "What the loop did NOT verify" names, at minimum: real agent sessions (the oracle stubs the
   session, so `agent_seconds` on real dispatches is unchecked), and the external corpus that
   motivated the feature.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a stats figure that renders `0` where it should
render `not recorded`: record `not_met` with a follow-up.
