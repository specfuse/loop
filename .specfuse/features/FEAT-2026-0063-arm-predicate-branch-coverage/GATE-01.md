---
gate: 1
status: passed
cost_budget_usd: 21.00
baseline:
  sha: 8015234bffe3244dcd0a0a1a07682e7271fe6502
  probed_at: 2026-08-03T15:45:54.981935+00:00
  failing: []
---

# Gate 1 — the sweep is honest, standing, and its unverified list is named

## Definition of done

A single mechanism answers "which arm-predicate branches have been observed on real
input, and which have not" — excluding features that structurally cannot be
evaluated, never silently dropping one that can, and failing when the sweep itself
becomes incomplete rather than when a branch has yet to fire.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU, not
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Cost budget

`cost_budget_usd: 21.00` — the $16.00 sum of WU estimates ($4.50 / $3.50 / $3.00 /
$5.00) plus one re-attempt of the largest WU ($5.00, the close), per the defensive
padding the GATE template prescribes while the closing-WU retry defect (#260) is
open. The close sits at the `.specfuse/rules/planning-discipline.md` §5 floor of
$5.00 rather than the $3.00 "it's just bookkeeping" estimate.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's WUs are armed at draft time (`status: pending`), so the discipline below
applies to this drafting rather than to a later arm:

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it is the
  load-bearing answer on this feature: a gate asserting branch *coverage* would be
  unsatisfiable today (five classes have never fired; no class has ever reported
  `not_evaluable`). T02 asserts sweep *completeness* instead. Confirmed before
  drafting.
- **Runtime probe for a default/severity flip (§4).** Not applicable: `arm_eval.py`
  is not modified. No default, threshold, or severity changes.
- **Flag-scope table (§3).** Not applicable: no behaviour flag is introduced.

## Known pre-existing condition, recorded so the close does not misread it

The sweep will report five stop classes as never-fired and eight as
never-`not_evaluable`. **That is this gate's correct output, not a failure.** A close
that reads the unverified list as a gate failure has misunderstood the feature; a
close that omits it has hidden the deliverable. It belongs in
`## What the loop did NOT verify` as a named, dated list.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
