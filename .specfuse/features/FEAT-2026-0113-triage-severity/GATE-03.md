---
gate: 3
status: open
---

# Gate 3 — backfill for issues already marked

## Definition of done

Drafted by gate 2's `plan-next`. The milestone: issues already carrying a triage
marker with no severity field can be re-read and labelled under an explicit mode,
never as part of a normal run.

Without this gate the feature classifies new issues and leaves the 31 measured
stranded issues exactly as they are — the marker is their idempotency key and it is
already written, so nothing else will ever revisit them.

`feature_oracle` is set by the drafting agent.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's drafted work units to `pending`:

- **Runtime probe (§4).** Any unit here that flips a default or a severity is armed
  only after the change is applied locally and the unit's full tests gate is run —
  the whole oracle, not a subset — with the failure list pasted into this gate's
  `GATE-NN-REVIEW.md`. "Mechanical, nothing design-open" is not a basis to skip it.
- **Flag scope (§3).** Any unit introducing a flag or a policy key carries its
  flag-scope table.
- **Record precedence.** `PLAN.md` fixes marker-authoritative, label-as-projection,
  marker-written-first. A drafted unit that reorders those is wrong, not a variant.
- **Existing-mechanism search (§1).** `labels.py:267` already lists labels with
  their descriptions. A drafted unit that issues its own `gh label list` has not
  done the search.
