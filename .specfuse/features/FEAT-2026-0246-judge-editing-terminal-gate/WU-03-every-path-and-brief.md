---
id: FEAT-2026-0246/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/loop.py
  - tests/test_terminal_judge_editing_end_to_end.py
model: sonnet
effort: medium
gate_set: code
oracle_env: macos_local
produces_driver_helper:
  - escalate_unit
driver_version: 0.30.0
started_at: 2026-10-29T12:01:35.096200+00:00
duration_seconds: 154.844
cost_usd: 0.521442
input_tokens: 38
output_tokens: 10188
---

# T03 — every autonomy level, both close paths, and a six-part brief

**Objective.** Prove the stop holds wherever a terminal close can start (PLAN
decisions 1 and 2), and replace T01's one-line halt message with the six-part operator
brief.

**Context.** `FEAT-2026-0246/T03`. Un-skip `EveryAutonomyLevelStops`,
`AutoClosePathStops` and `BriefHasSixParts` in the oracle module.

- `EveryAutonomyLevelStops` — the T01 firing fixture parameterised over
  `autonomy_default` `auto`, `review` and `supervised`: each halts with
  `judge_editing_terminal` and no terminal flip.
- `AutoClosePathStops` — a fixture the auto-close predicate would close (on-plan,
  close unit without `auto_close_disabled`): it halts before any
  `auto_close_decision` event is written; the same fixture without a judge path still
  auto-closes (positive control).
- `BriefHasSixParts` — the escalation `message` carries the six parts of
  `.specfuse/rules/operator-escalation.md` in plain English before any correlation ID,
  names each unit and path, and states the clearing steps: write
  `judge_edit_acknowledged` with your own reason, then run `/unblock-wu`.

The brief goes through `escalate_unit` (`loop.py`), like every other per-unit halt —
add `judge_editing_terminal` to whatever reason-to-text mapping it uses rather than a
parallel renderer. "Why it did not close automatically": the gate's own units change
the code or config that grades it.

**Acceptance criteria.**

1. The three oracle classes fail once un-skipped on the T01/T02 tree (no brief text;
   whichever autonomy or auto-close case the wiring misses) and pass after.
2. `grep -rn "judge_editing_terminal" specfuse/loop/loop.py` shows the reason used at
   the halt and in the brief mapping, and in no other renderer.
3. `python3 -m unittest tests.test_lifecycle_integration -b` passes.

**Do not touch.** `arm_eval.py` (T01/T02 own it). Docs (T04).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_lifecycle_integration -b`.

**Escalation triggers.** If a fixture shows a close path the T01 wiring does not
cover, fix the wiring here only when it sits in the same two branches T01 named;
a third entry point is T01's escalation trigger — stop and escalate.
