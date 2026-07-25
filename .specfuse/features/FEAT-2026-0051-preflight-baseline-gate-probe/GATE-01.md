---
gate: 1
status: awaiting_review
cost_budget_usd: 32.00
---

# Gate 1 — Pre-flight baseline gate probe

Definition of done: a gate whose base tree is already red halts with
`preexisting_gate_failure` having dispatched **zero** work units; the baseline
(sha, timestamp, failing gate names + signatures) is recorded in the gate file
and not re-measured until the tree moves; `--no-baseline-probe` restores today's
behavior exactly; and the halt message tells a non-expert operator which gate is
red, the exact failing signature, that the base tree is unchanged so no WU caused
it, and what their options are.

## Arming discipline

Three WUs change the driver's dispatch control flow, and the driver runs from
repo source — so from T01 onward the driver executing this gate's *own* remaining
WUs is running the probe code T01 wrote. Before arming, confirm:

- The escalation-predicate check in PLAN.md holds: on a green base tree the probe
  reports zero and dispatch is byte-identical to today. T01's acceptance carries
  a green-baseline test for exactly this.
- This repo's `code` gates are green on the feature's base commit — otherwise the
  driver will halt itself on its own probe at the next gate entry, which is
  correct behavior but a confusing first encounter.
- `--no-baseline-probe` (T02) is the recovery path if the probe misfires
  mid-feature. Know it exists before starting.

The `review` autonomy default is load-bearing: a bug in a pre-dispatch halt
does not fail loudly in a test, it silently stops work from being dispatched.
That wants human eyes on the diff, not auto-close.
