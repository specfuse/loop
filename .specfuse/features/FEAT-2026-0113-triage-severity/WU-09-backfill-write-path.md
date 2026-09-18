---
id: FEAT-2026-0113/T09
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/agent/severity_backfill.py
  - tests/test_severity_backfill_apply.py
---

# T09 — the backfill write path: marker amended first, label projected second

**Objective.** `apply_severity_backfill` records a backfilled severity against
each selected issue — amended marker first, `severity:<value>` label second —
writes nothing at all for an issue whose marker already carries one, and retires
T07's `_amend_marker` stub by switching the call site to T08's
`amend_marker_severity`.

**Context.** `FEAT-2026-0113/T09`, gate 3. `PLAN.md`'s **Record precedence** is
binding and is not a variation point: the marker's `severity=` field is the
authoritative record, the label is a projection re-derived from it, and the
marker is written first. A failed label write then leaves an issue correctly
classified and merely lacking a swatch; the reverse order leaves an issue
labelled that still scans as carrying no severity.

`apply_triage` (`specfuse/loop/triage.py:181`) is the shape to follow and **not**
the function to change: its marked branch never rewrites a marker — "the marker
write is the idempotency key" — which is exactly why the measured 31 issues are
stranded, and why backfill needs its own write path rather than a new branch in
that one.

This unit does no classification and no selection: it takes the decisions T10
will hand it (`{number, body, severity}`) and writes them. It is not a tracer
bullet; a stub here is a hollow pass.

**Acceptance criteria.**

1. `tests/test_severity_backfill_apply.py::BackfillApply::test_marker_is_amended_before_the_label_is_added`
   fails on HEAD before this unit runs and passes after: for each decision,
   `apply_severity_backfill(runner, repo, decisions)` issues
   `gh issue edit <n> --repo <r> --body <amended marker>` **before**
   `gh issue edit <n> --repo <r> --add-label severity:<value>`, asserted on the
   order of the recorded calls; and the amended body's `category=` /
   `confidence=` values are byte-identical to the ones it read.
2. `test_an_issue_already_carrying_a_severity_is_never_written`: a decision whose
   body's marker already carries `severity=` produces **zero** `gh` calls for
   that issue — not a marker write, not a label write — and is reported as
   skipped on the returned row. This is the stop condition that bounds a repeat
   run, asserted by argv over the whole sequence rather than by a return value
   alone.
3. A failed label write is recorded on the returned row and never raised, with
   the amended marker left in place; a failed marker write leaves the label
   unwritten, so no issue is ever labelled with a severity its marker does not
   carry.
4. The write path neither lists nor classifies: `grep -c '"issue", "list"'` and
   `grep -c "run_claude"` over `specfuse/agent/severity_backfill.py` both report
   `0` at this unit's tree, and `grep -c "def _amend_marker"` over the same file
   reports `0` — T07's stub is gone and `amend_marker_severity` has one
   definition repo-wide (`grep -rn "def amend_marker_severity" specfuse/` reports
   exactly one hit).

**Do not touch.** `specfuse/loop/triage.py` (T08) — including `apply_triage`,
whose marked-issue branch stays exactly as it is; backfill is a second write
path, not a new branch in the first one. The label-repair branch
(`[FEAT-2026-0045/T01/marker-label-desync]`): an issue whose marker already
carries a severity but whose `severity:<value>` label is missing is gate 2's
repair case and is out of scope here. `specfuse/agent/run.py` — the conductor is not edited by
any unit in this gate (the Q1 arm-checkpoint decision; T07's criterion 2 asserts an
empty diff on it), so there is nothing here to extend or complete. `specfuse/loop/labels.py` and `specfuse/agent/triage_invoke.py`
(gate 2's). `rules.bugs.min_severity`.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`GATE-03.md`'s `feature_oracle`, and
`python3 -m unittest tests.test_severity_backfill_marker tests.test_triage_apply -b`.

**Escalation triggers.** If the marker-first order cannot be held — if amending
the marker requires reading back a label state written first — stop and
escalate: the order is what makes a partial failure safe, and an implementation
that satisfies "both calls happen" without the order has lost the only property
this unit exists for. If a decision's body turns out to disagree with the issue's
body at write time (the body was edited between selection and write), stop rather
than amending a body you did not read: a bulk marker rewrite over stale bodies is
the failure mode `autonomy_default: review` was set for.
