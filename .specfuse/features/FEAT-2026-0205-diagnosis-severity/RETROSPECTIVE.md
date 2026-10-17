# Retrospective — FEAT-2026-0205 gate 1 close

First and only close of gate 1. Four implementation units (T01–T04), each passed on
attempt 1; this session re-measured the oracles fresh and wrote the close
deliverables.

## Measurements

All commands were run in this session from the repository root, exit codes read
directly. HEAD was `9b1029df37a49d10e5436765d7a0e596cbcc8a46` with this close's own
working-tree edits (`CHANGELOG.md`, this file, `GATE-01-CRITERIA.md`, the `verdict`
field of `WU-90-gate-1-close.md`) uncommitted. This session may not run git, so the
tree state is HEAD plus those edits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_diagnosis_severity_end_to_end -v -b`
(exit 0): `Ran 9 tests` / `OK`, every class running, none skipped:

```
SeverityIsRecordedAndLabelled      2
OldAndUnknownSeverityReadAsAbsent  5
AutofixOrdersBySeverity            1
BugLaneIgnoresFindingSeverity      1
```

### No surviving skip

`grep -n 'unittest.skip' tests/test_diagnosis_severity_end_to_end.py` reports nothing
(exit 1, no output), and `grep -n 'skip' tests/test_diagnosis_severity_end_to_end.py`
likewise. T01 created the module with `AutofixOrdersBySeverity` and
`BugLaneIgnoresFindingSeverity` as `unittest.skip` naming T03 and T04; each owner
removed exactly its own, so no oracle class is hollow.

### Autofix eligibility is unchanged

`git diff main --stat -- specfuse/monitor/autofix.py specfuse/monitor/autofix_state.py`
prints nothing: neither file has a diff. T03 only sorts the list
`findings_autofix.advertise` returns (`items.sort(key=…)`); the confidence floor,
`fix_scope` routing, one attempt per fingerprint and the daily cap are read through
`run_autofix` as before. The escalation trigger ("a changed autofix eligibility
decision") does not apply.

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate. `events.jsonl` records one
`broad_run_result` at 19:14:33Z: `ok: true`, `failing: []`, on the tree recorded in
`GATE-01.md`'s `broad_run:` block. The `tests` gate log
(`work/gate-logs/tests-20261017T191357642408Z.log`) reads `Ran 4679 tests` /
`OK (skipped=4)`; none of the four skips is in the oracle module.

### Per-criterion oracles (11 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 11

All eleven were `unverified` on entry and each was run in this session; each now
records its oracle command, `kind: narrow`, `state: pass`, and `proved_at_sha`
`9b1029df37a49d10e5436765d7a0e596cbcc8a46`.

| criterion | oracle (exit 0 unless stated) |
| --- | --- |
| T01#1 | `unittest tests.test_diagnosis_severity_end_to_end.SeverityIsRecordedAndLabelled` OK |
| T01#2 | `unittest …OldAndUnknownSeverityReadAsAbsent` OK |
| T01#3 | `unittest tests.test_diagnose_headless tests.test_diagnose_fenced_analysis tests.test_agent_provider_findings_diagnose` OK |
| T02#1–#3 | `unittest tests.test_diagnosis_severity_rubric.TestRubric.test_one_line_per_value`, `…test_prompt_carries_the_rubric`, `…test_skill_copies_name_rubric_and_match`, each OK; `cmp plugins/specfuse/skills/diagnose-issue/SKILL.md .specfuse/skills/diagnose-issue/SKILL.md` identical (exit 0); `grep -c SEVERITY_RUBRIC` on the copy reports 1 |
| T03#1 | `unittest …AutofixOrdersBySeverity` OK |
| T03#2 | `unittest tests.test_agent_provider_findings_autofix tests.test_autofix_run` `Ran 23 tests` OK |
| T04#1 | `unittest …BugLaneIgnoresFindingSeverity` OK |
| T04#2 | `! grep -n 'unittest.skip' tests/test_diagnosis_severity_end_to_end.py` exit 0 |
| T04#3 | `unittest tests.test_flows_page tests.test_scaffold_data_in_sync tests.test_scaffold_doc_hygiene` `Ran 15 tests` OK |

Also run: `tests.test_diagnose_issue_skill tests.test_agent_provider_bugs` (with the
T01#3 modules, `Ran 44 tests`, OK); `tests.test_changelog_schema
tests.test_changelog_append_only tests.test_changelog_collection` (`Ran 38 tests`, OK)
after the `CHANGELOG.md` edit; `ruff check specfuse .specfuse/scripts tests scripts`
(`All checks passed!`); `python3 .specfuse/scripts/lint_plan.py <feature_dir>` (`OK —
… structurally valid`).

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. `"severity": "high"` posts a marker with `severity=high` and exactly one `severity:high` label; a later `"low"` leaves exactly `severity:low` | `SeverityIsRecordedAndLabelled.test_marker_carries_severity_and_label_is_added`, `test_new_severity_replaces_previous_label` | proven |
| 2. a marker without severity parses with it absent; an unknown value reads as absent; neither raises nor writes a label | `OldAndUnknownSeverityReadAsAbsent.test_pre_feature_marker_parses_without_severity`, `test_unknown_severity_marker_reads_absent` (the lookup in `diagnosis.parse`, not a caller's try/except), `test_unknown_severity_in_analysis_posts_no_label_call`, `test_absent_severity_posts_no_label_call`; `test_invalid_severity_is_a_construction_error` pins that building a `Diagnosis` with a bad value still raises | proven |
| 3. three eligible findings of severity `low`, `critical`, none are advertised `critical`, `low`, none; eligibility unchanged | `AutofixOrdersBySeverity.test_advertised_most_severe_first`; `tests.test_agent_provider_findings_autofix` and `tests.test_autofix_run` unchanged and green; `specfuse/monitor/autofix.py` has no diff (above) | proven |
| 4. a finding with a `severity:` label and no triage marker is not advertised by the bug lane | `BugLaneIgnoresFindingSeverity.test_severity_labelled_finding_is_not_advertised`; `tests.test_agent_provider_bugs` green | proven |
| 5. the headless prompt and `/diagnose-issue` ask for severity against one rubric defined once in code | `SEVERITY_RUBRIC` is defined once in `specfuse/monitor/diagnosis.py`; `diagnose_invoke.build_invocation` builds its prompt from it (`test_prompt_carries_the_rubric`); both `SKILL.md` copies name it, do not restate it, and are byte-identical (`test_skill_copies_name_rubric_and_match`, `cmp`) | proven |

Clause 5 is not part of the `feature_oracle` (the plan scopes the oracle to 1–4); it is
proven by T02's own tests, re-run above.

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's
`planned_cost_usd` (`PLAN.md` plans 13.00 = 2.50 + 2.00 + 1.50 + 2.00 + 5.00); no
figure is estimated. Every unit passed on attempt 1.

| unit | planned (USD) | actual (USD) | attempts | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 2.50 | 0.2921 | 1 | 51 |
| T02 | 2.00 | 0.1968 | 1 | 33 |
| T03 | 1.50 | 0.1345 | 1 | 22 |
| T04 | 2.00 | 0.1868 | 1 | 28 |
| T01–T04 | 8.00 | 0.8102 | 4 | 133 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 13.00 | **0.8102** | 4 | 133 |

The four recorded attempts spent $0.81 (10% of the $8.00 planned for them), and
`GATE-01.md` sets `cost_budget_usd: 24.00`. This close's own attempt is not in
`events.jsonl` while it runs (its `attempt_outcome` is written when the driver ends
the attempt), so it is not reconciled here and the total above excludes it.

### Failure-class breakdown

(no non-passing attempts in scope)

## Deferred verification

1. **The opt-in live headless diagnosis of a fixture finding
   (`[FEAT-2026-0204/G1-CLOSE]`) was not run.** It spawns a live model session
   (`claude -p` through `specfuse agent run`'s findings-diagnose provider) against a
   real finding issue, and the provider then comments on that issue and writes a
   `severity:` label to the repository: an outward-facing write plus a billed
   session. This close is a non-interactive dispatch and no operator opted in to
   either, so it did not make that write. No marker severity from a live model is
   recorded. What the loop did observe is the stub path: a stub headless result
   carrying `"severity": "high"` renders a marker with `severity=high` and an
   unknown value renders none (clause 1 and 2 tests). Where checked: item 2.
2. **The post-merge live check in `PLAN.md`.** After release, diagnose one real
   finding on the first consumer (by hand or `diagnose: auto`) and confirm the marker
   carries a severity, the issue gets exactly one `severity:` label, and a second
   diagnosis replaces it. This also covers what the stub `gh` cannot show: that
   `gh label create --force` and `gh issue edit --add-label/--remove-label` behave
   as the recorded argv assumes, and that a real model follows the rubric and
   returns a value in `SEVERITY_VALUES` (an unrecognised one reads as unrated, so a
   bad answer degrades to "no label", not an error). Checked as the one
   `specfuse:post-merge` issue filed at close.

## Consumer-visible contract changes

Enumerated across T01–T04 for acknowledgment; each is in `CHANGELOG.md`
`Unreleased` (`Added` ×1, FEAT-2026-0205).

- **Added — a diagnosis carries an optional `severity`** (`critical`, `high`,
  `medium`, `low`): a `severity=` field in the `<!-- specfuse:diagnosis … -->` marker
  and a `**Severity:**` line. A comment posted before this change parses unchanged,
  and an unknown value reads as absent.
- **Added — a finding issue gets one `severity:<value>` label** after a diagnosis
  that carries a severity, created on first use; a later diagnosis replaces it. A
  diagnosis without a severity writes no label.
- **Changed — the order autofix offers findings.** The findings-autofix provider
  advertises most severe first, unrated last, so the daily cap is spent on the
  highest severities. Which findings are eligible is unchanged.
- **Added — `specfuse.monitor.diagnosis.SEVERITY_RUBRIC` and `Diagnosis.severity`**,
  and the headless prompt and `/diagnose-issue` ask for a severity against the
  rubric.

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## Documentation pass

`docs/concepts/monitoring-to-fix.md` and `docs/flows.html` (with their
`specfuse/loop/data/docs/` copies) were checked against the shipped code:

- "a `severity` of `critical`, `high`, `medium` or `low`", the rubric summary
  (`critical`: users cannot complete a core action or data is lost now; `low`: noise
  or no user-visible effect) matches `SEVERITY_RUBRIC`.
- "one matching `severity:<value>` label" and "without a severity (older comments, or
  an unrecognised value) reads as unrated" match `findings_diagnose._label_severity`
  and `diagnosis.parse`.
- "Severity changes no rule above. It only orders the queue … most severe first and
  unrated ones last" matches `findings_autofix.advertise` and the unchanged
  `autofix.py`.
- "that `severity:<value>` label never brings it into the bug lane: the lane selects
  on the triage category" matches `BugLaneIgnoresFindingSeverity`.
- The "Planned (FEAT-2026-0205)" sentence is replaced by the shipped behaviour.

`tests.test_flows_page`, `tests.test_scaffold_data_in_sync` and
`tests.test_scaffold_doc_hygiene` pass, so the shipped copies are byte-identical.

## Retrospective

**What went well.** The walking skeleton did its job: the oracle module existed after
T01 with two classes skipped by owner name, T03 and T04 each removed exactly their
own, and the final tree has no hollow class. The fail-closed discipline held at the
reader: unknown severity is a membership lookup in `parse`, and the construction
error is pinned separately, so tolerance and strictness are two tests, not one
try/except. Eligibility stayed untouched by construction (T03 sorts a list it
already built; `autofix.py` has no diff). All four units passed on attempt 1 at 10%
of plan, and the broad run was green on its first attempt.

**What didn't.** Nothing in the loop can show that a real model follows the rubric or
that GitHub accepts the label writes; the one opt-in live diagnosis the carried
lesson asks for was deferred, not run, because it posts to a real issue and no
operator opted in. The cost of that is a post-merge check rather than a pre-close
one. T01 also left the rubric as a one-line placeholder for T02, which worked only
because the plan named T02 as its owner.

**Lessons.** Nothing generalizes beyond what `[FEAT-2026-0204/G1-CLOSE]` already
records: the carried live-render lesson was applied by naming in Deferred
verification why the live run was not made, which is the route it allows.

**Open follow-ups (not blockers).** The two Deferred verification items above.
