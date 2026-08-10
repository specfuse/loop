---
gate: 2
status: passed
cost_budget_usd: 19.50
baseline:
  sha: 1fc91fd3e841c9e5ab23132a568ee77f3e299d34
  probed_at: 2026-08-10T16:16:32.135396+00:00
  failing: []
---

# Gate 2 — an existing policy file can be reviewed and corrected

## Definition of done

Drafted by gate 1's `plan-next` against what gate 1 actually learned. The shape,
from the operator's decision 1:

- An existing `.specfuse/agent-policy.yml` can be read, its values presented with
  their provenance, and per-block corrections proposed without clobbering
  deliberate operator intent.

The mechanism for distinguishing an agent-chosen default from a deliberate
choice was **deliberately undecided** at drafting — see `PLAN.md` § *Open
question for gate 2*. `G1-PLAN` has now recommended one against the derivability
count gate 1 reported, and the operator arms this gate after reading
`GATE-02-REVIEW.md`.

Written as what **this gate can decide**, following gate 1's precedent:

- `review_agent_policy` reads an existing `.specfuse/agent-policy.yml` and
  returns, per in-scope key, the current value, the evidence-backed proposal,
  the shipped baseline, and a provenance classification — withholding rather
  than guessing wherever a source is missing.
- The classification's lossy direction is disclosed in the returned data, so a
  reader cannot pick up the hint without the disclaimer attached.
- The skill's prose describes that algorithm, naming its real API as exact
  literals, and keeps the staged per-block accept contract gate 1 established.
- Review mode is fenced against writing `queue`, `version`, and `rules.triage`,
  and against dropping a key the existing file carries — asserted by a test that
  fails if the prose widens.
- Every substantive work unit in this gate is `done`, and the terminal close has
  run.

## What this gate does NOT prove

The same deferral gate 1 could not close, verbatim from `PLAN.md` § *The oracle
problem*: **that an agent following the skill's prose reproduces the algorithm's
output on a repository it has not seen.** Its re-run condition is one operator
invocation of `/derive-agent-policy` against this repository's own
`.specfuse/agent-policy.yml` — which is now also the first real use of review
mode, so the deferral and the review the operator actually wants remain one
action. Gate 2 adds a second reference implementation and more prose; it does not
add an agent-executing-prose oracle, and a green gate here must not be read as
one.

## Cost budget

`cost_budget_usd: 19.50` — gate 2's four work units ($3.50 + $3.50 + $2.50 +
$5.00 = $14.50) plus one re-attempt of its largest ($5.00, the close), per
`planning-discipline.md` §5's corollary. The padding is defensive cover for a
known-open guard-contract defect, not a statement that retries are expected.

## Arming discipline

This gate is armed by a human (`autonomy_default: review`). Before flipping its
drafted work units to `pending`, read `GATE-02-REVIEW.md` — the checkpoint the
two-gate staging exists to create.
