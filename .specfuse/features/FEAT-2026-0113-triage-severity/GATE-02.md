---
gate: 2
status: open
feature_oracle: "python3 -m unittest tests.test_triage_severity_end_to_end -v -b"
---

# Gate 2 — triage classifies severity and writes it

## Definition of done

A triage run records a severity in the marker and projects the `severity:<value>`
label, marker first — in **both** repository shapes, which is the revision this gate
took at its arm checkpoint. Where the repository defines its own `severity:*`
labels, its descriptions are the rubric and specfuse creates nothing. Where it
defines none, specfuse's published `DEFAULT_SEVERITY_RUBRIC` is the rubric and the
four labels are provisioned on first use.

The contract that replaced the old opt-out is **non-interference**: a repository
declaring its own severity scheme gets zero `gh label create` calls and none of its
descriptions overwritten. Reading label-absence as "this project opted out" was the
original draft and is withdrawn — it made the feature inert by default, which is the
failure #3352 measured. The degradation path remains: a label listing that cannot be
read leaves the run classifying and writing exactly as it does today.

The `feature_oracle` above is **run-level, not `apply_triage`-level**, which is the
question this gate left to its drafting agent. `apply_triage` never reads a label
rubric, so it cannot observe which repository shape it is in;
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
