---
id: FEAT-2026-0113/T10
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/agent/severity_backfill.py
  - tests/test_severity_backfill_run.py
---

# T10 — a backfill run: rubric once, classify each, write only under `--apply`

**Objective.** `backfill_severity` reads the repository's rubric once per run,
classifies each selected issue against it — replacing T07's injected severity
with the real classification step — fails closed without a usable answer, and
writes nothing at all unless `--apply` is given.

**Context.** `FEAT-2026-0113/T10`, gate 3. This is the unit that makes the mode
real: T07 wired the path, T08 set what may be touched, T09 wrote the writes.
Nothing here is stubbable.

**The rubric is gate 2's and is not re-derived.** `labels.read_severity_rubric`
(`specfuse/loop/labels.py:405`) already returns `{severity_value: description}`,
already provisions the four `SEVERITY_LABEL_SPECS` labels **only** on the
declares-none branch (fail-soft, `gh label create … --force`, idempotent), and
already returns `{}` when the listing cannot be read. A backfill run therefore
finds the labels present in a declares-none repository and creates nothing in a
repository declaring its own scheme — because it calls that function and writes
no provisioning code of its own. Gate 2's retrospective measured both branches by
argv; this unit inherits that contract rather than restating it.

Classification is `triage_invoke.build_invocation` +
`triage_invoke.classify_severity` (`specfuse/agent/triage_invoke.py:41`, `:108`),
which already fails closed on a missing field, a value outside the rubric, and a
`confidence` that is not `high`. The severity a backfill records is the same
severity a fresh triage would record; the only difference is that the category
and confidence already exist and are preserved.

**Dry run is the default.** A backfill amends markers in bulk against real
issues, so the mode prints its selection and writes nothing unless the operator
passes `--apply`. `T11` is the human unit that runs the dry-run form against the
repository where the 31 issues were measured.

**Acceptance criteria.**

1. `tests/test_severity_backfill_run.py::BackfillRun::test_rubric_is_read_once_and_each_candidate_is_classified`
   fails on HEAD before this unit runs and passes after: a run over three
   candidates issues exactly one `gh label list`, three `claude` invocations, and
   three marker/label pairs — the listing is once per run, not once per issue,
   the bound `test_listing_and_provisioning_happen_once_per_run` asserts for the
   normal path.
2. `test_a_low_confidence_or_out_of_rubric_answer_writes_nothing`: for a
   classification answer naming no severity, a severity outside the rubric, or a
   `confidence` that is not `high`, the run issues zero `gh issue edit` calls for
   that issue and the issue keeps failing closed under a floor exactly as it does
   today — reusing `triage_invoke.classify_severity`, with
   `grep -c "def classify_severity" specfuse/agent/severity_backfill.py`
   reporting `0`.
3. `test_an_empty_rubric_makes_the_run_a_no_op`: when `read_severity_rubric`
   returns `{}` — a failed listing, or a repository whose whole `severity:*`
   scheme lies outside `agent_policy.SEVERITY_VALUES` — the run issues zero
   `claude` invocations and zero `gh issue edit` calls, and reports why. The
   second case is gate 2's measured coverage hole, and a backfill meets those
   repositories first.
4. `test_without_apply_nothing_is_written`: over the same three candidates, a run
   with no `--apply` issues zero `gh issue edit` calls, prints one line per
   selected issue, and exits 0 — the read-only form `T11` runs against a real
   repository.
5. `test_backfill_creates_no_labels`: across every case above,
   `grep -c '"label", "create"' specfuse/agent/severity_backfill.py` reports `0`
   and a run against a repository declaring its own `severity:*` scheme issues
   zero `gh label create` calls, asserted by argv over the whole sequence — the
   non-interference contract gate 2 established, re-measured on this new run
   shape rather than assumed to carry over.

**Do not touch.** `specfuse/loop/labels.py` — `read_severity_rubric`,
`_ensure_severity_labels`, `SEVERITY_LABEL_SPECS` and `DEFAULT_SEVERITY_RUBRIC`
are gate 2's and are called, never edited or copied.
`specfuse/agent/triage_invoke.py` — the prompt and the readers are gate 2's; a
backfill uses them unchanged. `specfuse/loop/triage.py` (T08).
`specfuse/agent/providers/triage.py` — the normal triage path stays as it is,
including its `_rubric_for_run` cache. `rules.bugs.min_severity` and
`rules.bugs.severity_aliases` — read-only vocabulary, never written.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`GATE-03.md`'s `feature_oracle`, and
`python3 -m unittest tests.test_severity_rubric tests.test_triage_severity_classify tests.test_triage_severity_end_to_end -b`
(gate 2's oracles, unedited).

**Escalation triggers.** If a backfill run turns out to create any label against
a repository declaring its own `severity:*` scheme, or to overwrite a description
it did not author, stop and escalate — that is the contract gate 2 measured and
gate 3 has no premise without. If recording a backfilled severity appears to
require changing the issue's `category` or `confidence`, stop: a backfill adds a
field, it does not re-triage, and re-deciding a category under an explicit
maintenance mode is a different feature.
