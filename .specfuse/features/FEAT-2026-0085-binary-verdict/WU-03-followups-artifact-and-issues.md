---
id: FEAT-2026-0085/T03
type: implementation
status: done
attempts: 2
planned_cost_usd: 6.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: assert_followups_recorded, file_followup_issues
produces:
  - specfuse/loop/closing_requirements.py
  - specfuse/loop/loop.py
  - specfuse/loop/escalation.py
  - tests/test_followups_artifact.py
duration_seconds: 2659.389
cost_usd: 6.816027
input_tokens: 362
output_tokens: 90025
---

# A not_met close writes FOLLOW-UPS.md, and the driver files one tracked issue per entry

**Objective.** Give unfinished work an honest home that is not the verdict:
on `not_met`, the close writes `FOLLOW-UPS.md` in the feature folder, one
`### ` entry per failed criterion; after the close passes, the driver files
one GitHub issue per entry and writes the issue number back.

**Context.** FEAT-2026-0085/T03; read `PLAN.md`. Entry shape: the criterion
verbatim, the evidence (command run and its exit or output line), and the
re-run condition. Registry: add `close-m` (`applies_when="verdict_not_met"`,
`enforced_by="assert_followups_recorded"`, pre-squash) so a `not_met` close
without at least one entry is refused as `closing_deliverable_missing`; add
the `applies_when` value and the `--closing` lint check beside it. Issue
filing: `file_followup_issues(feature_dir, repo_root, runner)` runs after a
`not_met` close's squash, calls `emit_issue_with_body` **if it exists in
`escalation.py`** (FEAT-2026-0082/T01 adds it; unmerged) and otherwise adds
that function over `_find_existing_issue` / `_correlation_marker` with the
same signature 0082 chose, labels `specfuse:follow-up` plus the feature id
marker, idempotent per entry; `gh` absent or failing leaves the file as the
record and emits one `followups_recorded` event with `filed` and `unfiled`
counts. Optional `## Post-merge checklist` section in `PLAN.md`: on `met`, the
same helper files one issue carrying it under `specfuse:post-merge`. Add the
two labels to `labels.py`. Red test first.

**Acceptance criteria.**

- `tests/test_followups_artifact.py::test_not_met_close_without_followups_is_refused` fails on HEAD and passes after: a fixture close with `verdict: not_met` and no `FOLLOW-UPS.md` makes `assert_closing_deliverables` report `close-m`.
- `tests/test_followups_artifact.py::test_one_issue_per_entry_body_verbatim`: two entries, injected runner; two `gh issue create` argv lists, each carrying `--label specfuse:follow-up` and the entry body byte-for-byte; a second call files nothing.
- `tests/test_followups_artifact.py::test_gh_failure_keeps_file_and_records_event`: a runner returning exit 1 leaves `FOLLOW-UPS.md` intact and the `followups_recorded` event says `filed: 0, unfiled: 2`.
- `python3 -c "from specfuse.loop.loop import assert_followups_recorded, file_followup_issues"` exits 0.
- `specfuse lint --closing` on the fixture reports `close-m` with the same pass/fail as the driver guard.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `emit_escalation`'s observable behaviour and its tests;
`render_escalation_body`; `VERDICT_VALUES` (T01); the auto-close stubs (T02);
type sets (T04); rules, docs, skills (T05); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if adding `emit_issue_with_body`
changes anything `emit_escalation`'s live caller in `specfuse/agent/run.py`
observes. Emit `status: blocked` if `assert_followups_recorded` is absent from
the files you edited.
