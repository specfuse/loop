---
id: FEAT-LOOP-2026-0250/T03
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.50
produces:
  - specfuse/loop/loop.py
  - tests/test_gate_timings.py
produces_driver_helper:
  - probe_baseline
  - gate_broad_run_check
model: sonnet
effort: medium
---

# T03 — `gate_result` events for the baseline probe and the broad run

**Objective.** Record per-gate results for the two runs outside an attempt, so clause 3 of
`GATE-01.md` goes green.

**Context.** `FEAT-LOOP-2026-0250/T03`. Both runs already go through `_run_gate_set()`, which T01
made time each gate.

- **Broad run.** When `gate_broad_run_check` actually runs (the case that already emits
  `broad_run_result`), also emit one `gate_result` per gate with `phase: "broad"`, correlation ID
  the feature's, alongside `broad_run_result` in `_broad_events`. A tree-unchanged skip emits none.
- **Baseline probe.** When `probe_baseline()` runs fresh, emit one `gate_result` per gate with
  `phase: "baseline"`, correlation ID the same one the `baseline_attribution` event on that path
  uses, through the same event list. A skip on an unchanged tree emits none.
- `attempt` is `null` on both phases.

**Acceptance criteria.**

1. `tests.test_gate_timings.TestBaselineAndBroadPhases` fails on HEAD and passes after. It
   asserts one `gate_result` per gate with the right `phase` for a fresh broad run and a fresh
   baseline probe, and none for a broad run on an unchanged tree.
2. `broad_run_result` and `baseline_attribution` payloads are unchanged; the same class asserts
   their keys.
3. The narrow tier passes with no existing broad-run or baseline test edited.

**Do not touch.** `execute_unit_attempt()` and `emit_attempt_outcome()` (T02). `events_stats.py`
and docs (T04).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If the baseline probe has no event list to emit into on one of its call
paths, block naming that path rather than adding a second flush point.
