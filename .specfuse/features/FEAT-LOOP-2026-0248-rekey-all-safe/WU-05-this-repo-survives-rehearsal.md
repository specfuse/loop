---
id: FEAT-LOOP-2026-0248/T05
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 4.00
max_attempts: 3
produces:
  - tests/test_ids.py
  - tests/test_ids_call_sites.py
  - tests/test_keyed_feature_ids_end_to_end.py
  - tests/test_agent_policy_queue.py
  - tests/test_done_feature_gates.py
  - tests/test_learnings_weights.py
  - tests/test_lint_correlation_id.py
  - tests/test_lint_plan_errors.py
  - tests/test_lint_close_wu.py
  - tests/test_validate_event.py
  - tests/test_gh_features.py
---

# T05 — this repository's full suite passes a rehearsal of the rename

**Objective.** The rehearsal from 2026-10-29 is re-run with the fixed tool and comes back
green: with key `LOOP`, this repository can be fully renamed without a failing test.

**Context.** `FEAT-LOOP-2026-0248/T05`. This unit **edits** existing test modules only.
Run, from the repository root:

```
python3 -m specfuse.loop.ids migrate --all --include-prose '.specfuse/**' 'tests/**' 'specfuse/**' 'docs/**' 'plugins/**' --rehearse
```

`ids.key: LOOP` is set in `.specfuse/layout.yml` on this branch. The 2026-10-29 rehearsal
failed 44 tests in: `test_deliverable_presence_gate`, `test_empty_files_escalation` (fixture
paths; expected fixed by T02), `test_ids_migrate_all`, `test_keyed_feature_ids_end_to_end`,
`test_ids`, `test_ids_call_sites`, `test_agent_policy_queue`, `test_done_feature_gates`,
`test_learnings_weights`, `test_lint_correlation_id`, `test_lint_plan_errors`,
`test_lint_close_wu`, `test_validate_event`, `test_gh_features`.

For each test still failing in the rehearsal, fix the **assumption**, not the assertion: a
test that reads a real feature folder by a hard-coded legacy path resolves it through
`ids.resolve` or by ordinal; a real-corpus test that asserts the legacy pattern extracts
every ID accepts either shape via `ids.parse`; a sentinel string the rename legitimately
rewrites is matched in whichever form the tree holds. Each fixed test must still pass on
the unrenamed tree.

`produces:` lists every module the 2026-10-29 rehearsal flagged; T02–T04 may already have
fixed some. For each listed module the rehearsal no longer flags, leave it unedited and name
it under `produces_unchanged:` in the RESULT block with "rehearsal passes without an edit".

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
