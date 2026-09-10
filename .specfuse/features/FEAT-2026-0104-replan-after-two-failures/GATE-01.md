---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_replan_end_to_end -v -b"
---

# Gate 1 — a unit that fails twice is re-planned, not re-run

## Definition of done

A work unit that has failed its second-to-last permitted attempt is re-planned
in place — a planning turn narrows its body, the driver reloads it and resets
its attempts — instead of being dispatched again with the identical prompt.
The gate's `events.jsonl` carries the `replan` event that
`gate_eval.evaluate_auto_close` already consumes as check 2.

The `feature_oracle` above is the executable proof. It is **red today**:
`tests/test_replan_end_to_end.py` does not exist. T01 is the tracer bullet
that makes it runnable and green by wiring the thinnest path end to end;
T02–T04 make each part correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- The next gate's work units are drafted, and `GATE-02-REVIEW.md` is written.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## What this gate must not break

`detect_deterministic_refusal_repeat` (`loop.py:1399`) already escalates
*earlier* than any ceiling: a byte-identical guard refusal over a provably
untouched tree halts before the next session is dispatched. Re-plan fires
later and on a different signal. A unit that trips the refusal-repeat check
must still escalate there — re-plan must not convert a known-unfixable
refusal into a planning turn that cannot help either.

FEAT-2026-0103 rewrote this same retry path days before this gate was drafted:
a guard refusal now retains the working tree and dispatches a repair. A repair
attempt and a re-plan attempt are different things and the gate must keep them
distinguishable in the attempt record.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** No WU in this gate flips
  a default or a severity — the trigger is new behaviour behind a new decision
  point, and `MAX_ATTEMPTS` keeps its value. If gate 2's drafted WUs introduce
  one, the probe applies to them.
- **Flag-scope table (§3).** T02 introduces the decision that selects between
  "retry" and "re-plan". Confirm its flag-scope table names every path that
  reaches a retry today.
- **Escalation-predicate satisfiability (§2).** No check is raised to `ERROR`
  in this gate.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
