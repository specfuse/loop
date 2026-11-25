---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_gate_timings -v -b"
cost_budget_usd: 22.00
---

# Gate 1 — per-gate timings are recorded, and `specfuse stats` reads them

## Definition of done

**Stated as an outcome.** In temporary feature folders, with real gate subprocesses (commands
that sleep a known time and exit 0 or 1) and a stubbed agent session:

1. **Attempt phase.** Each attempt emits one `gate_result` event per gate in its set, the
   `feature_oracle` included, carrying `attempt`, `gate`, `ok`, `duration_seconds` and
   `phase: attempt`. A gate's `duration_seconds` is at least its command's sleep. A gate skipped
   because a dependency failed records `ok: false`, `skipped: true`, `duration_seconds: 0`.
2. **Split.** `attempt_outcome` carries `agent_seconds` and `verify_seconds`, and
   `agent_seconds + verify_seconds <= duration_seconds`. An attempt that stopped before
   verification (the agent reported blocked) records `verify_seconds: 0`.
3. **Baseline and broad phases.** The baseline probe and the broad run each emit one
   `gate_result` per gate with `phase: baseline` or `phase: broad`. A broad run skipped because
   the tree is unchanged emits none.
4. **Stats.** `specfuse stats` (text and `--json`) reports the agent/verify split per feature and
   the slowest gates (runs, total, median, max seconds). On a corpus with no `gate_result` events
   and no split fields it says "not recorded", never zeros.
5. **Nothing existing changes.** `duration_seconds` keeps its meaning; every existing test that
   stubs `verify_fn` passes unchanged; `gate_result` is in `driver-event.schema.json` and every
   emitted event type validates against it.

The `feature_oracle` proves 1–5. It is red on the current tree; `FEAT-LOOP-2026-0250/T01` is the
walking skeleton that creates `tests/test_gate_timings.py` and turns clause 1 and clause 5's
schema half green, with every other class `unittest.skip` naming its owner (T02–T04). A skip
surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One runner.** Timing lives in `_run_gate_set()`; the three phases differ only in the `phase`
  tag and correlation ID they emit with.
- **Positive controls.** Clause 1 pairs a passing gate with a failing one and a skipped
  dependent; clause 3 pairs a fresh broad run with a tree-unchanged skip; clause 4 pairs a new
  corpus with an old one.
- **Real subprocesses, stubbed agent.** Gate durations come from real `sleep` commands, so a
  duration recorded as a constant fails the lower-bound check.
- **Expected self-halt.** `loop.py` and the event schema are judge surfaces; acknowledge the
  stop with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
