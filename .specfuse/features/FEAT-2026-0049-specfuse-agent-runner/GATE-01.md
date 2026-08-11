---
gate: 1
status: open
cost_budget_usd: 36.00
baseline:
  sha: 83faca7e12fe6daa408b449c54b9af8fe0edb6c3
  probed_at: 2026-08-11T00:12:20.449955+00:00
  failing: []
---

# Gate 1 — the conductor drains an empty queue

## Definition of done

`specfuse-agent run` acquires `.specfuse/.agent.lock`, refuses to start when
another agent holds it, honours `--max-minutes` / `--max-tokens` / `--max-items`
at item boundaries, checks the PAUSE marker each iteration, reads repo state into
one snapshot, runs select→execute→reconcile to completion with **zero registered
action providers**, and prints a run summary naming actual elapsed time and the
reason it stopped.

No action class is wired in this gate. That is the point: the loop's stopping
properties — the lock, the caps, the kill switch — are what is most expensive to
get wrong and cheapest to prove in isolation, before any provider can spend money
on the other side of them.

Plus the methodology's own bar:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Under `autonomy_default: auto`, generalizable lessons stage to
  `LEARNINGS-pending.md` in this feature folder — **not** to
  `.specfuse/LEARNINGS.md`, which `assert_learnings_staged_under_auto` forbids
  touching under this autonomy level.
- The next gate's work units are drafted, and `GATE-02-REVIEW.md` is written.
- Per-criterion state and the narrow/broad oracle contract:
  `close-discipline.md` §5.

## Cost budget

`cost_budget_usd: 36.00` — the $29.50 sum of this gate's planned WU costs plus
one re-attempt of its largest work unit (T04, $6.50), per the planning-discipline
§5 padding rule.

## What this gate deliberately does not prove

The selector is exercised against an empty provider registry, so this gate cannot
show that it *picks well* — only that it terminates, respects its budget, and
stops when told. Selection quality is gate 2's to demonstrate, once real classes
compete. Any acceptance criterion here that claims otherwise is overclaiming.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`, apply §4's runtime probe to any WU
that flips a default or a severity. None is expected in gate 2 — the providers
consume existing predicates rather than changing them — but `G1-PLAN` should
confirm that explicitly rather than assume it.

## Driver-restart expectation

`T01` edits `specfuse/loop/_filelock.py`, which matches
`driver_edit.DRIVER_MODULE_PREFIXES`. The driver will halt for a restart after
that work unit's squash. This is expected, not a failure — see PLAN.md's "Where
the new code lives." No other gate-1 WU should trigger it; one that does has
placed code in the wrong package.
