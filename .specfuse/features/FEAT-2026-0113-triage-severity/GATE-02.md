---
gate: 2
status: open
---

# Gate 2 — triage classifies severity and writes it

## Definition of done

Drafted by gate 1's `plan-next`. The milestone: a triage run against an issue in a
repository that defines `severity:*` labels records a severity in the marker and
projects the label; the same run in a repository that defines none behaves
byte-identically to today.

`feature_oracle` is set by the drafting agent, not now — gate 1's retrospective is
what will say whether the end-to-end proof belongs at `apply_triage` or one level up.

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
