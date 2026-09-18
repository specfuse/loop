---
gate: 2
status: open
feature_oracle: "python3 -m unittest tests.test_triage_severity_end_to_end -v -b"
---

# Gate 2 — triage classifies severity and writes it

## Definition of done

A triage run against an issue in a repository that defines `severity:*` labels
records a severity in the marker and projects the `severity:<value>` label, marker
first; the same run in a repository that defines none issues the identical `gh`
write sequence it issues today. Defining the labels is how a project opts in;
`LABEL_REGISTRY` gains no `severity:*` entry, so not defining them is how it opts out.

The `feature_oracle` above is **run-level, not `apply_triage`-level**, which is the
question this gate left to its drafting agent. `apply_triage` never reads a label
rubric, so it cannot observe the opt-out half of the milestone at all;
`TriageProvider.execute` is the one place a run both reads the repository's labels
and applies a decision. `FEAT-2026-0113/T06` is the unit that turns it green, and
`GATE-02-REVIEW.md` carries the rest of the drafting rationale.

Standard gate obligations (retrospective, lessons, docs, next-gate drafting,
per-criterion state and the narrow/broad oracle contract) are as
`close-discipline.md` §5 defines them; they are not restated here.

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
