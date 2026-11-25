---
id: FEAT-LOOP-2026-0250/T04
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/events_stats.py
  - docs/methodology.md
  - tests/test_gate_timings.py
model: sonnet
effort: medium
---

# T04 — `specfuse stats` reports the split and the slowest gates; docs

**Objective.** Make the recorded data readable without code, so clause 4 of `GATE-01.md` goes
green and no skip remains in `tests/test_gate_timings.py`.

**Context.** `FEAT-LOOP-2026-0250/T04`; decision 1 in `PLAN.md`. `events_stats.collect()` today
reads only `attempt_outcome`.

- `collect()` also reads `gate_result` events, under the same dedupe key.
- Per feature: total `agent_seconds`, total `verify_seconds`, and the share of attempt time
  each represents. Per gate name: runs, total, median and max `duration_seconds`, ordered by
  total, split by `phase`.
- `render()` prints both sections; `--json` carries them. When no attempt has the split fields
  or no `gate_result` exists, the section says `not recorded` — an old corpus must never read as
  zero verification time.
- `docs/methodology.md`, section "Per-attempt outcome events": document `gate_result` (payload,
  the three phases, buffering and the killed-attempt limit) and the two new `attempt_outcome`
  fields.

**Acceptance criteria.**

1. `tests.test_gate_timings.TestStatsReport` fails on HEAD and passes after: a corpus with
   `gate_result` events and split fields renders both sections with the right figures, and an
   old corpus renders `not recorded` for both.
2. `python3 -m unittest tests.test_events_stats -b` passes unchanged.
3. `grep -c "unittest.skip" tests/test_gate_timings.py` prints `0`.

**Do not touch.** The driver's event emission and the event schema (T01–T03).

**Verification.** The narrow tier for `implementation`, plus AC2's and AC3's commands.

**Escalation triggers.** If a T01–T03 event lacks a field this report needs, block naming the
field rather than inferring it.
