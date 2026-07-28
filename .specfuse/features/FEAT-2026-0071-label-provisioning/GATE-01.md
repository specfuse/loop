---
gate: 1
status: awaiting_review
cost_budget_usd: 19.50
baseline:
  sha: 2b98dee811c2684c85888f37d28d038ddb65dcb6
  probed_at: 2026-07-28T11:27:51.780848+00:00
  failing: []
---

# Gate 1 — every label specfuse reads is declared once and created automatically

## Definition of done

- One registry declares all seven labels specfuse currently reads, sourcing the
  escalation names from `escalation.py` rather than restating them, with a test
  that fails if the two ever drift.
- `provision_labels` creates missing labels, skips existing ones, and survives
  every degradation path — no `gh`, no auth, non-GitHub remote, no git repo, a
  per-label failure — without raising.
- `init` and `upgrade_specfuse` provision labels, and neither can fail because
  provisioning did. The opt-out works.
- `RETROSPECTIVE.md` exists; lessons are promoted to `.specfuse/LEARNINGS.md`;
  the roadmap reflects what was built.

Terminal gate, so the closing sequence is the single `close` work unit.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** Not applicable — no work
  unit flips a default value or raises a check's severity. T03 changes what
  `init` and `upgrade_specfuse` *do*, but adds behaviour rather than altering an
  existing default: the new keyword argument defaults to provisioning on, and no
  existing caller's file-writing behaviour changes.
- **Flag-scope table (§3).** **Required on T03**, which introduces the
  `SPECFUSE_NO_LABELS` opt-out. Its table must list every code path the opt-out
  is claimed to gate, so the arming review can check the headline claim
  ("provisioning can be turned off") against what the flag actually reaches.
- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`: the
  registry-coverage check reports zero on a correct tree, and provisioning
  against an already-provisioned repository creates nothing.

## Reflection notes

<Written by the human at review time.>
