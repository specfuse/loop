---
id: FEAT-LOOP-2026-0253/G1-CLOSE
type: close
verdict: met
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
    - specfuse/loop/data/verification.yml.example
    - specfuse/loop/loop.py
  reason: "Driver changes reviewed"
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-11-27T12:11:21+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 0.0
    prior_duration_seconds: 0.0
    reason: "Driver changes reviewed"
cumulative_cost_usd: 0.0
cumulative_duration_seconds: 0.0
cumulative_input_tokens: 0
cumulative_output_tokens: 0
cumulative_attempts: 0
cost_usd: 2.061082
duration_seconds: 391.102
input_tokens: 74
output_tokens: 47619
folded_through_re_arm: 1
gate_set: plannext
driver_version: 0.33.2
started_at: 2026-11-27T12:11:24.880439+00:00
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: gates whose `needs:` are met can run concurrently under
`defaults.max_parallel`, and a gate declaring `inputs:` reuses its earlier PASS on a retry when
those inputs are unchanged, never on a path that writes a gate-level or terminal verdict.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven
   and by which test, and that no `unittest.skip` survives in
   `tests/test_gate_parallel_cache.py`. It lists every pre-existing test that was changed
   (clause 9), with why.
2. Each consumer-visible change (`defaults.max_parallel`, per-gate `inputs:` and
   `PASS (cached)`, `cached` on `gate_result`, `gates_running` in `STATUS.json`) is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0253`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`.
4. "What the loop did NOT verify" names, at minimum: wall-clock savings on a real project
   (stubs only), gates that interfere when run concurrently in one tree (a project concern
   `max_parallel` makes possible), and the Windows Git-Bash path under threads. Each points at
   `PLAN.md`'s post-merge checklist or a follow-up.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, a cached result reaching the broad run, the baseline
probe or the `feature_oracle` in any test, or a default (`max_parallel` 1, no `inputs:`) run
that differs from before: record `not_met` with a follow-up.
