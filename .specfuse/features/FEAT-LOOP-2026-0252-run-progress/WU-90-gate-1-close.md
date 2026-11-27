---
id: FEAT-LOOP-2026-0252/G1-CLOSE
type: close
status: blocked_human
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
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
