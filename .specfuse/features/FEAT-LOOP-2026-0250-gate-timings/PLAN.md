---
feature_id: FEAT-LOOP-2026-0250
title: Record verification gate results and durations
slug: gate-timings
branch: feat/FEAT-LOOP-2026-0250-gate-timings
roadmap_goal: An operator who finds the loop slow can read from `specfuse stats` how much attempt time went to the agent versus the verification gates, and which gates cost the most.
autonomy_default: auto
status: done
planned_cost_usd: 18.50
---

# Plan: Record verification gate results and durations

`attempt_outcome.payload.duration_seconds` is one wall-clock timer around
`execute_unit_attempt()` (`loop.py`, the `t0 = time.monotonic()` in the attempt loop). It
covers the agent session and every verification gate together. No event says which gates
ran, how long each took, or which passed, and `broad_run_result` carries no duration either.
An operator report measured 184 attempts, about 17.5 hours of attempt time, with no way to
say how much was the agent and how much the gates. Without that split, every optimisation
is a guess: smaller work units, a different model or effort, a faster gate, or the parallel
gates and result cache proposed separately.

This feature records one `gate_result` event per gate per run (attempt, baseline probe,
broad run), splits `attempt_outcome` into `agent_seconds` and `verify_seconds`, and makes
`specfuse stats` report both. It measures; it speeds nothing up.

## Decisions (2026-11-25)

The operator said "take your recommendations" after the first interview question and then
accepted this list. Each item is a recommendation applied on that instruction.

1. **Events plus stats.** `events_stats.py` reports the agent/verify split per feature and
   the slowest gates. Events nobody can read without ad-hoc Python do not remove the guess
   (the reason `events_stats.py` exists, #271).
2. **Autonomy `auto`.** A fresh judge session writes the terminal verdict from evidence only.
   `loop.py` is a judge surface, so the terminal judge-editing stop fires before the close:
   acknowledge it with your own reason and `/unblock-wu`.
3. **One gate**, four substantive units and a terminal `close`, under the 12-unit threshold
   (`docs/methodology.md` §6).
4. **Attempt-phase `gate_result` events are buffered in `wu_events`** with `attempt_outcome`
   and flushed at the same point. A killed attempt loses them as it already loses its
   outcome (LEARNINGS `[FEAT-LOOP-2026-0070/G1-CLOSE-INTERMEDIATE]`); changing that is out of
   scope.
5. **Split definition.** `agent_seconds` is wall-clock around the agent-session call,
   `verify_seconds` wall-clock around the gate-set call, both inside `execute_unit_attempt()`.
   `duration_seconds` keeps its meaning (the total); the remainder is driver overhead and is
   not named. An attempt that never reached verification records `verify_seconds: 0`.
6. **How per-gate results leave `verify()` is the implementer's call**, under one constraint:
   every existing test that stubs `verify_fn` (e.g. `tests/test_dispatch_skeleton.py`) passes
   unchanged.

**Out of scope:** a live progress view or halt notification; parallel gates or a result
cache; backfilling old `events.jsonl` files; persisting events from killed attempts.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `git grep -nE "gate_duration|gate_seconds|verify_seconds|agent_seconds|gate_result|elapsed" -- 'specfuse/*.py'`
  and `grep -n "duration\|monotonic" specfuse/loop/loop.py`
- **Verdict:** no existing per-gate timing, building new. The only hits are `specfuse/agent/budget.py`'s
  run-level elapsed minutes and an unrelated `gate_result` local variable in
  `specfuse/agent/drafting_invoke.py` (an answer-gate result, not an event type). The
  persisted gate logs under `work/gate-logs/` (#3293) are gitignored scratch with no
  duration field, so they are not a record.
- **If reusing:** the registry `specfuse/loop/data/schemas/driver-event.schema.json` gains
  one event type, the same way `broad_run_result` was added (FEAT-2026-0109/T06).
  `_run_gate_set()` is the single runner all three phases already share.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — no check changes severity and nothing blocks on the new data.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0250/T01
        file: WU-01-attempt-gate-events.md
        depends_on: []
      - id: FEAT-LOOP-2026-0250/T02
        file: WU-02-agent-verify-split.md
        depends_on: [FEAT-LOOP-2026-0250/T01]
      - id: FEAT-LOOP-2026-0250/T03
        file: WU-03-baseline-and-broad.md
        depends_on: [FEAT-LOOP-2026-0250/T01]
      - id: FEAT-LOOP-2026-0250/T04
        file: WU-04-stats-and-docs.md
        depends_on: [FEAT-LOOP-2026-0250/T02, FEAT-LOOP-2026-0250/T03]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0250/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0250/T01, FEAT-LOOP-2026-0250/T02, FEAT-LOOP-2026-0250/T03, FEAT-LOOP-2026-0250/T04]
```

## Post-merge checklist

- Run one real feature and check that `agent_seconds + verify_seconds` is close to
  `duration_seconds` on real attempts (the oracle stubs the agent session).
- Run `specfuse stats` on the corpus that motivated this feature and confirm the slowest-gates
  view names real gates.

## Notes

- LEARNINGS `[FEAT-LOOP-2026-0053/G2-CLOSE]`: any aggregate over per-attempt duration must sum
  every field the lifetime is spread across; T04's per-feature split reads `events.jsonl`, which
  never loses a cycle.
- LEARNINGS `[FEAT-LOOP-2026-0057/G1-CLOSE]`: buffered events are flushed only at the unit's
  terminal outcome, so a close reading its own `gate_result` events mid-session sees none.
- `produces:` lists only `.py` files under `tests/` (#3539).
