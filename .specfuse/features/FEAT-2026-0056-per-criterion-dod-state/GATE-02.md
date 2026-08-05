---
gate: 2
status: open        # open | awaiting_review | passed
---

# Gate 2 — a re-dispatched close re-verifies only the worklist

## Definition of done

<Drafted by gate 1's `plan-next` (`G1-PLAN`) from gate 1's retrospective and
`.specfuse/LEARNINGS.md`. The intent recorded at draft time, for that session to
accept, revise, or reject:>

- A re-dispatched close reads the prior attempt's `GATE-NN-CRITERIA.md` and produces
  a re-verification worklist: every criterion whose state is `fail`, every criterion
  that did not exist on the prior attempt, and every criterion whose oracle is
  `broad`.
- Identical oracle commands across criteria run once per close attempt, not once per
  criterion.
- The close's feature-level question — the one no producing unit's criteria asked,
  per `close-discipline.md` §1 — is excluded from the cache and always runs.
- A close that skips a criterion says so in its own record, so a reader can tell a
  criterion that was re-proved this attempt from one carried forward.

Gate 2 is the terminal gate, so the closing sequence is the single `close` work unit.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

<Filled in by `G1-PLAN` when it drafts this gate's work units. The §4 runtime probe
applies if any drafted WU flips a default or a severity.>

## Reflection notes

<Written by the human at review time.>
