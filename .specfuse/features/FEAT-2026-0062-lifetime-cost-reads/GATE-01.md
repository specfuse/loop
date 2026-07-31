---
gate: 1
status: passed
cost_budget_usd: 21.00
baseline:
  sha: 3e6c4d678743e8da11bae3a3fd0210da2ce83012
  probed_at: 2026-07-31T18:25:04.051249+00:00
  failing: []
---

# Gate 1 — both cost consumers read lifetime spend, and the brake can see a final-WU overrun

## Definition of done

`budget_projection` and the per-gate budget brake both report a work unit's lifetime
spend regardless of whether its re-arm folded, without double-counting the fold-ran
shape; and a gate that overruns its budget inside its final work unit reports the
breach instead of closing silently.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU, not
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Cost budget

`cost_budget_usd: 21.00` — the $16.00 sum of WU estimates ($4.00 / $3.50 / $3.50 /
$5.00) plus one re-attempt of the largest WU ($5.00, the close), per the defensive
padding the GATE template prescribes while the closing-WU retry defect (#260) is
open.

**This gate's brake is the thing T03 changes.** If the gate itself overruns inside
its final work unit, T03's own deliverable is what should surface it — a live test
of the feature by the feature. Record that in the close either way.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's WUs are armed at draft time (`status: pending`), so the discipline below
applies to this drafting rather than to a later arm:

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md` — unchanged on
  a never-re-armed work unit and on a gate within budget; the verdicts that change
  are the ones wrong today. Confirmed before drafting.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default
  value or severity is flipped. Two existing brakes begin firing correctly in cases
  they currently under-read; neither threshold (`BUDGET_PROJECTION_MULTIPLIER`,
  `cost_budget_usd`) changes.
- **Flag-scope table (§3).** Not applicable: no behavior flag is introduced.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
