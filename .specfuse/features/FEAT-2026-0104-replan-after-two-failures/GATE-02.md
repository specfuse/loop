---
gate: 2
status: open
feature_oracle: "TBD — drafted by FEAT-2026-0104/G1-PLAN with gate 1's evidence in hand"
---

# Gate 2 — a blocked_human escalation offers a re-plan

## Definition of done

After a work unit escalates with `blocked_human`, the operator-facing brief
presents re-planning the remaining gate as its default option, inside the
six-part framing `.specfuse/rules/operator-escalation.md` requires.

This gate is **skeletal by design**. Its substantive work units are drafted by
gate 1's `plan-next` (`FEAT-2026-0104/G1-PLAN`) once gate 1's retrospective
and lessons exist — the methodology's forward-design move. The lone
`G2-CLOSE` entry below it in `PLAN.md` exists so the linter reads gate 1 as
non-terminal; `G1-PLAN` inserts the substantive units before it.

## The question this gate must not answer prematurely

Whether the brief's re-plan option can **execute** the re-plan on the
operator's yes, or only recommend it and leave the flip manual, is open. It
turns on how gate 1's in-place re-scope behaves against real spins — how often
a re-planned unit then passes, and whether a re-plan an operator did not read
first is one they would have accepted. `G1-PLAN` will have that evidence; this
draft does not, and guessing it now would put a decision in the plan that
nothing measured.

Its `feature_oracle` is deliberately `TBD` for the same reason: the command
that proves this gate's definition of done depends on which of those two
shapes the gate takes. `G1-PLAN` sets it when it drafts the substantive units.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** If any drafted WU flips a
  default value or a severity, it may not be armed on "mechanical, nothing
  design-open": apply the change locally, run the exact command the WU's tests
  gate will run, and paste the failure list into `GATE-02-REVIEW.md`.
- **Flag-scope table (§3).** If a drafted WU introduces or flips a behaviour
  flag — an operator-facing default for how the brief presents its options is
  one — confirm it carries a flag-scope table.
- **Escalation-predicate satisfiability (§2).** If a drafted WU raises a check
  to `ERROR` or asserts a "zero issues" predicate, confirm PLAN.md answers what
  the rule reports on a correct input, and that the answer is zero.

## Reflection notes

<Written by the human at review time.>
