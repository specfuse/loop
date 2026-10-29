---
id: FEAT-LOOP-2026-0248/T05
type: implementation
status: pending
attempts: 0
unsandboxed: true
unsandboxed_rationale: "--rehearse runs git worktree add/remove and the full test suite in a temp worktree; inside the sandbox the previous dispatch saw about 160 false errors (git, build-dependency network fetch) that vanished unsandboxed. Memory/LEARNINGS: run the suite unsandboxed."
re_arm_count: 3
re_arm_history:
  -
    timestamp: 2026-10-29T17:04:06+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 4.00
    prior_duration_seconds: 5059.215
    reason: "Planning error, not the unit's work: the prescribed --include-prose scope included tests/, specfuse/, docs/ and plugins/, whose mentions are mostly fixtures and illustrative example IDs (78, then 32 failures in operator rehearsals), and the fixed produces list could not be known in advance. Scope narrowed to this repository's own history; produces removed; T06 added for the stale in-process validation."
  -
    timestamp: 2026-10-29T17:32:06+00:00
    prior_status: blocked_human
    prior_attempts: 1
    prior_cost_usd: 0.118917
    prior_duration_seconds: 5059.215
    reason: "Blocked correctly: --rehearse refused the driver's own bookkeeping as a dirty tree and rehearsed HEAD, not the unit's uncommitted edits. T07 makes it rehearse the working tree; re-armed behind T07 (operator: 'go ahead, add T07 and re-arm T05')."
  -
    timestamp: 2026-10-29T18:42:44+00:00
    prior_status: blocked_human
    prior_attempts: 1
    prior_cost_usd: 1.374982
    prior_duration_seconds: 5059.215
    reason: "Escalation 1 was real (ids.resolve ignored folderless alias targets) and is fixed by T08. Escalation 2 was a misdiagnosis: the vendored schema already accepts keyed IDs; test_validate_event validates real events against its own fixture schema hard-coding ^FEAT-\\d{4}-\\d{4}, which is a test assumption in scope. Re-armed behind T08, unsandboxed (operator chose option A)."
oracle_env: macos_local
planned_cost_usd: 4.00
max_attempts: 3
duration_seconds: 3076.528
cost_usd: 1.374982
input_tokens: 96
output_tokens: 21996
---

# T05 — this repository's full suite passes a rehearsal of the rename

**Objective.** The rehearsal from 2026-10-29 is re-run with the fixed tool and comes back
green: with key `LOOP`, this repository can be fully renamed without a failing test.

**Context.** `FEAT-LOOP-2026-0248/T05`. This unit **edits** existing test modules only;
which ones is discovered by the rehearsal, so it declares no `produces:`. Run, from the
repository root:

```
python3 -m specfuse.loop.ids migrate --all --include-prose '.specfuse/features/**' '.specfuse/roadmap.md' '.specfuse/roadmap-archive.md' '.specfuse/LEARNINGS*.md' --rehearse
```

`ids.key: LOOP` is set in `.specfuse/layout.yml` on this branch. After T07, `--rehearse`
snapshots the working tree, so your uncommitted test edits are in each rehearsal and the
driver's bookkeeping files do not block it; do not write your own copy script. The prose scope is this
repository's own history only. `tests/`, `specfuse/`, `docs/` and `plugins/` are left
out on purpose: their mentions are fixtures and illustrative example IDs that happen to
share numbers with real features (two operator rehearsals that included them failed 78
and 32 tests, and rewrote vendored core files). Real feature folder names in those
trees are still rewritten by T02's structural rule.

Operator rehearsals with the wider scope failed in, among others: `test_ids` (RealCorpus),
`test_ids_call_sites`, `test_keyed_feature_ids_end_to_end`, `test_agent_policy_queue`,
`test_feature_id_resolution`, `test_gate_eval_calibration`, `test_gh_features`,
`test_lint_correlation_id`, `test_validate_event`, `test_monitoring_bootstrap_artifacts`,
`test_layout_no_layout_goldens`. Re-run with the scope above first; fix only what still
fails.

For each failing test, fix the **assumption**, not the assertion: a test that reads a real
feature folder, roadmap row or event by a hard-coded legacy ID resolves it through
`ids.resolve` or by ordinal; a real-corpus test that asserts the legacy pattern extracts
every ID accepts either shape via `ids.parse`; a golden or sentinel the rename
legitimately rewrites is matched in whichever form the tree holds. Each fixed test must
still pass on the unrenamed tree. Never edit `specfuse/`; a failure that needs a code
change is an escalation (name the module and case).

**Known from the previous dispatch (do not re-diagnose):**

- `ids.resolve` now follows an alias to a feature that exists only as a roadmap row (T08),
  which fixes `FEAT-2026-0078`'s queue entry and `test_agent_policy_queue`'s live check.
- `test_validate_event.TestValidateEventValid.test_driver_event_from_feat_0008_is_accepted`
  is a **test** fix, not a schema one: `.specfuse/schemas/event.schema.json` already
  accepts keyed IDs. The test validates the real `FEAT-2026-0008` events against its own
  fixture schema (`_ENVELOPE_SCHEMA`, `correlation_id` pattern `^FEAT-\d{4}-\d{4}(/T\d{2})?$`
  at line ~62). Build that fixture pattern from `ids.FEATURE_ID_PATTERN`, or resolve the
  event file through `ids.resolve`, so it holds in both trees.
- This dispatch is unsandboxed; rehearsals take about 10 minutes each. Run them in the
  background and keep working while they run.
- Record in your RESULT `notes` every test you edited and why, so a later re-arm does not
  start from zero.

**Acceptance criteria.**

1. The command above exits zero, and its output (validation result plus the test
   command's summary line) is quoted in this unit's RESULT `notes`.
2. `python3 -m unittest discover -s tests -b` passes on the real, unrenamed tree.
3. No assertion is deleted or loosened to pass; every edited test still fails if the
   behaviour it guards regresses (state, per edited module, the regression it still
   catches).

**Do not touch.** `specfuse/` code (T01–T04 own it; a needed code change is an
escalation). The real tree's feature folders, roadmap and policy: nothing is applied here.

**Verification.** The narrow tier for `implementation`, plus AC1's command.

**Escalation triggers.** A failure whose fix needs `ids.py` or another `specfuse/` module:
stop, name the module and the case. A failure that only a foreign-ID exclusion would fix:
stop and ask the operator which ID to pass to `--exclude-id`.
