---
id: FEAT-2026-0056/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
produces_driver_helper:
  - specfuse.loop.lint_closing.check_criteria_state_well_formed
produces:
  - tests/test_lint_closing_criteria.py
generated_surfaces: []
---

# Refuse a close whose criteria-state artifact is malformed

**Objective.** Declare the criteria-state requirement in
`specfuse/loop/closing_requirements.py` and implement it in
`specfuse/loop/lint_closing.py`, so `specfuse-lint --closing` refuses a close whose
`GATE-NN-CRITERIA.md` carries an entry the driver cannot trust.

**Context.** This is `FEAT-2026-0056/T03`, gate 1 of this feature. T01 built the
schema module (`specfuse/loop/criteria_state.py`); T02 makes the driver seed the
artifact at dispatch. This unit is the check on what the close writes back. Read
`PLAN.md` in this folder — especially § *Escalation-predicate satisfiability*, which
is the reasoning that makes this severity flip safe — and `GATE-01.md`.

`closing_requirements.py` is the registry of record: `close-discipline.md` §4 states
that module and `lint_closing.py` are "the one place these requirements are
enumerated," and that a second copy of the requirements drifts. So the requirement is
**declared as a `Requirement` record**, not hard-coded in the lint body. Read the
existing records before writing — `close-a` through `close-k` for `close`, and
`close-intermediate-a` through `close-intermediate-e` — and follow their shape. The
next free IDs are `close-l` and `close-intermediate-f`.

The requirement needs a new `applies_when` value, `criteria_artifact_present`. The
existing values are `always`, `verdict_met`, `verdict_hedged`, `failures_present`,
and `autoclose_debt_marker`, enumerated in the `Requirement` docstring — extend that
docstring when you add the value. **This gating is what makes the severity flip
satisfiable**: no feature currently in `.specfuse/features/` has a criteria artifact,
so the requirement fires on none of them, and a legacy close lints exactly as it does
today.

Three things make an entry untrustworthy, and each is a separate finding so a single
failure attributes to a single line:

- a missing or unrecognized `kind:` — not in `criteria_state.ORACLE_KINDS`;
- a missing or unrecognized `state:` — not in `criteria_state.CRITERION_STATES`;
- a `broad` entry reading `state: pass` whose `attempt:` is not the current attempt.

The third is the substantive one and the reason the feature is sound. A `broad`
oracle — the full test suite, a full regeneration, a scenario matrix — has no
knowable scope, so its green may never be carried forward from a prior attempt. The
lint is what makes that a contract rather than an intention.

Read `kind` and `state` from `criteria_state`'s frozensets; do not re-list the
allowed values here. `[FEAT-2026-0069/G2]` rejected a permissive fall-through for
exactly this reason — two competing sources for one enumeration is a defect waiting
for a divergence.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_lint_closing_criteria.py::test_missing_kind_is_a_finding` exists and
   **fails on HEAD before this WU's edits**. Record the failing output before
   editing.
2. `CLOSING_REQUIREMENTS["close"]` gains a record with `id="close-l"` and
   `CLOSING_REQUIREMENTS["close-intermediate"]` gains one with
   `id="close-intermediate-f"`, both with `phase="pre-squash"`,
   `applies_when="criteria_artifact_present"`, and
   `enforced_by="check_criteria_state_well_formed"`.
3. The `Requirement` docstring's enumeration of `applies_when` values includes
   `criteria_artifact_present`.
4. `check_criteria_state_well_formed` in `specfuse/loop/lint_closing.py` returns
   **zero findings** when the artifact is absent — asserted by a test.
5. It returns zero findings on an artifact whose every entry carries a `kind:` in
   `ORACLE_KINDS` and a `state:` in `CRITERION_STATES`, with every `broad` `pass`
   entry's `attempt:` equal to the current attempt.
6. It returns exactly one finding for an entry with a missing `kind:`, and exactly
   one for an entry whose `kind:` is not in `ORACLE_KINDS` — each naming the
   offending `criterion_id`.
7. It returns exactly one finding for an entry with a missing or unrecognized
   `state:`, naming the offending `criterion_id`.
8. It returns exactly one finding for a `broad` entry with `state: pass` whose
   `attempt:` differs from the current attempt, and **zero** findings for a `narrow`
   entry with `state: pass` whose `attempt:` differs — the carry-forward that is the
   point of the feature.
9. The allowed values are read from `criteria_state.ORACLE_KINDS` and
   `criteria_state.CRITERION_STATES`; a grep of `lint_closing.py` for the literals
   `"narrow"` and `"unverified"` returns no match outside a docstring or comment.
10. `specfuse-lint --closing` run across every existing feature's closing WUs
    reports **zero** new findings attributable to `close-l` or
    `close-intermediate-f`. Paste the command and its full output into the RESULT
    block. If the output is non-empty, emit `status: blocked` — see the escalation
    triggers.
11. `python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"`
    exits 0.
12. The test named in criterion 1 **passes** after this WU's edits.

**Do not touch.** `specfuse/loop/criteria_state.py` (T01 owns it — import it).
`specfuse/loop/loop.py` (T02's scope; this unit does not wire a driver-side
`assert_*`, the requirement is enforced through the existing registry-driven path).
`.specfuse/rules/` and `.specfuse/templates/` (T04's scope).
`.specfuse/verification.yml`. Any other feature's folder under
`.specfuse/features/` — including any criteria artifact belonging to one. Generated
directories, secrets, `.git/`. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run the
symbol-existence check in criterion 11 verbatim, and criterion 10's corpus sweep —
that sweep is the evidence the severity flip is satisfiable, and per
`[FEAT-2026-0055/G1-CLOSE]` a criterion of the form "reports zero findings over
corpus C" is only as reliable as the run behind it. Paste the real output; do not
summarize it.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 10's sweep returns any finding attributable to the two new requirement
records — that means the `applies_when` gating does not hold and the scope is wrong,
which is an operator decision, not something to reconcile inside this WU; adding
`criteria_artifact_present` requires changing how `applies_when` is dispatched for
the existing values (a change to shipped enforcement behaviour is out of scope here);
`check_criteria_state_well_formed` is absent from the files you edited, or the import
in criterion 11 fails — do not claim complete; or satisfying criterion 9 would
require duplicating the enumerations into `lint_closing.py`.
