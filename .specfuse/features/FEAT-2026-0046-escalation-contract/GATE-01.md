---
gate: 1
status: open
cost_budget_usd: 22.00
baseline:
  sha: 8710c4cd97ed36b922e8a56483c37d98c4caa30e
  probed_at: 2026-07-27T21:22:50.520483+00:00
  failing: []
---

# Gate 1 — an escalation has one format, one emitter, and one place to see it

## Definition of done

- The escalation issue format is a machine-checkable contract, not prose: a validator
  accepts what the renderer produces and names what is missing when it does not.
- A driver-side primitive can emit an escalation issue, idempotently, without the
  dispatch loop ever calling it.
- `/attention` presents everything needing the human — swept `.specfuse/` state plus
  the `needs-human` queue — in priority order.
- The claim that `/attention` cannot write state is proven by a test with a positive
  control, not asserted in the skill's own prose.
- `RETROSPECTIVE.md` exists; generalizable lessons are promoted to
  `.specfuse/LEARNINGS.md`; the roadmap reflects what was built.

This gate is terminal, so its closing sequence is the single `close` work unit —
retrospective, lessons, docs, and terminal verdict in one session. There is no
`plan-next`: no gate follows.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** Not applicable — no work unit
  in this gate flips a default value or raises a check's severity. Nothing existing
  changes behaviour; every check introduced is new and applies only to files this
  feature creates.
- **Flag-scope table (§3).** Not applicable — no work unit introduces or gates on a
  behavior flag. The one behavioural choice (emission is invoked, never automatic) is
  enforced by an asserted absence of a call site in T02, not by a runtime flag.
- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`: both
  predicate-shaped checks report zero on a correct input. T01's validator is held
  against its own renderer's output; T04's grep is proven capable of firing by a
  positive control, so its zero is evidence rather than a dead regex.

## Reflection notes

<Written by the human at review time.>
