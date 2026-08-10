---
gate: 2
status: open
---

# Gate 2 — an existing policy file can be reviewed and corrected

## Definition of done

Drafted by gate 1's `plan-next` against what gate 1 actually learned. The shape,
from the operator's decision 1:

- An existing `.specfuse/agent-policy.yml` can be read, its values presented with
  their provenance, and per-block corrections proposed without clobbering
  deliberate operator intent.

The mechanism for distinguishing an agent-chosen default from a deliberate
choice is **deliberately undecided** at drafting — see `PLAN.md` § *Open question
for gate 2*. `G1-PLAN` decides it against the derivability count gate 1 reports,
and the operator arms this gate after reading `GATE-02-REVIEW.md`.

## Arming discipline

This gate is armed by a human (`autonomy_default: review`). Before flipping its
drafted work units to `pending`, read `GATE-02-REVIEW.md` — the checkpoint the
two-gate staging exists to create.
