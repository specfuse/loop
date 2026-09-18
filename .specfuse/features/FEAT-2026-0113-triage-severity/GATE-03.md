---
gate: 3
status: open
feature_oracle: "python3 -m unittest tests.test_severity_backfill_end_to_end -v -b"
---

# Gate 3 — backfill for issues already marked

## Definition of done

Drafted by gate 2's `plan-next`. The milestone: issues already carrying a triage
marker with no severity field can be re-read and labelled under an explicit mode,
never as part of a normal run.

Without this gate the feature classifies new issues and leaves the 31 measured
stranded issues exactly as they are — the marker is their idempotency key and it is
already written, so nothing else will ever revisit them.

The `feature_oracle` above drives the backfill mode end to end over an injected
runner: an open issue whose body carries a two-field triage marker and whose
labels are complete — the shape `list_untriaged` excludes and nothing revisits —
is re-read under `--backfill-severity --apply`, its marker amended with
`severity=` and the `severity:<value>` label projected after it; and the same
repository under a conductor run with no flag is left untouched, asserted by
argv. Both halves are in one module because the milestone is the pair: a backfill
that runs, and a normal run that does not.

`FEAT-2026-0113/T07` is the walking skeleton that turns it green and is the only
unit in this gate permitted to stub (`/authoring-work-units` §14). The oracle is
appended to every attempt's gate list, so a gate whose oracle module lands last
fails every earlier unit on `ModuleNotFoundError` — gate 2 paid four attempts for
that ordering and `GATE-03-REVIEW.md` records the correction.

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
