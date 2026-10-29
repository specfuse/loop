# Retrospective — FEAT-LOOP-2026-0248 gate 1 close

First and only close of gate 1 (single gate). Eight loop-dispatched implementation units:
T01–T04 as baselined, T06, T07 and T08 added mid-gate, and T05, which was re-armed three
times. This session re-measured the oracles fresh and wrote the close deliverables.

## Measurements

Every command below was run in this session from the repository root, with the sandbox off
(the rehearsal adds and removes a git worktree and runs the full suite in it), exit codes
read directly. HEAD was `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84` plus this close's own
uncommitted edits (`CHANGELOG.md`, this file, `LEARNINGS-pending.md`, `GATE-01-CRITERIA.md`,
the `verdict` field of `WU-90-gate-1-close.md`) and the driver's bookkeeping. The close
session may not run git commits, and this session ran no git command after its first
read-only status check.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_migrate_all_repo_stays_valid -v -b` (exit 0):
`Ran 19 tests in 6.819s` / `OK`, every class running, none skipped:

```
Clause1PolicyResolvesOldIds        2
Clause2ApplyValidatesResult        2
Clause3RewriteClassification       1
Clause4ProseScoping                6
Clause5Rehearse                    3
Clause6ValidatesWithOwnCode        3
Clause7AliasFollowsRoadmapRow      2
```

(`GATE-01.md` names clauses 1–5 as the oracle's; Clause6 and Clause7 are the classes T06
and T08 added. Definition-of-done clause 6, this repository's own rehearsal, is not in the
oracle by design; it is the next measurement.)

### No surviving skip (close criterion 1)

`grep -nE 'unittest\.skip|@skip|skipTest|skipIf|skipUnless' tests/test_migrate_all_repo_stays_valid.py`
prints nothing (exit 1). `grep -c skip` on the module counts one line, the name of
`test_exclude_id_dry_run_lists_skip`, which tests the dry-run listing of a skipped ID. The
verbose run above lists no `skipped` marker for any of the nineteen tests.

### This repository's rehearsal (close criterion 2, definition-of-done clause 6)

Re-run fresh, T05's command with its narrowed prose scope:

```
python3 -m specfuse.loop.ids migrate --all --include-prose '.specfuse/features/**' '.specfuse/roadmap.md' '.specfuse/roadmap-archive.md' '.specfuse/LEARNINGS*.md' --rehearse
```

**Exit status: 0** (the wrapper recorded `EXIT=0`). Validation result, quoted from its
output:

```
re-keyed 109 feature(s); alias map .specfuse/id-aliases.yml
validated: lint_plan, lint_roadmap, agent-policy clean
rehearse: migration validated
rehearse: running `coverage run --source=specfuse -m unittest discover -s tests -v -b`
rehearse: command exit status 0
rehearse: passed; real tree untouched
```

It started with `rehearse: migrating a throwaway copy of HEAD plus 2 modified and 0
untracked file(s)`, the driver's two bookkeeping files, so it rehearsed the working tree.

**Test summary line: not quoted, and that is a gap.** The command ran with `-b` and
reports only the command's exit status on success; the rehearsal printed no `Ran N tests`
line, so there is none to quote. The exit status of the full-suite command inside the
renamed copy is the evidence. Re-running with a `--rehearse-command` that prints the
summary would cost another ten-minute rehearsal and was not done. The same output lists
the prose mentions left unchanged (remaining by top-level directory: `.`: 10, `.claude`: 1,
`.specfuse`: 657, `docs`: 54, `plugins`: 73, `scripts`: 8, `specfuse`: 633, `tests`: 1403).

The real tree was not renamed: `.specfuse/id-aliases.yml` does not exist, and
`.specfuse/features/` holds 94 folders, one of them `FEAT-LOOP-…` (this feature).

### Closing lint (close criterion 6)

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe --closing`,
result recorded at the end of this session in the RESULT block. The bare `specfuse lint
--closing` warns that it measures the pipx-installed build and not this checkout, so the
checkout's script was run. `lint_plan.py <feature_dir>` is `OK — structurally valid`, with
one WARN: T05 declares no `produces:` (deliberate; its edit set is discovered by the
rehearsal).

### Broad run (driver's, not re-run here)

`events.jsonl` records one `broad_run_result`, 19:42:39 UTC, `ok: true`, `failing: []`, on
the tree recorded in `GATE-01.md`'s `broad_run:` block. This session ran only the narrow
tier plus the rehearsal; the full `code` gate set is the driver's.

### Per-criterion oracles (17 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 17

All seventeen were `unverified` on entry. Fourteen were run in this session as their own
commands (exit 0 each); T05#1 is the rehearsal above; T05#2 is the driver's broad run, not
re-run here; T05#3 stays `unverified` (see "did NOT verify").

| criterion | oracle | ran |
| --- | --- | --- |
| T01#1 | oracle `Clause1`, `Clause2` classes | 4 tests, OK |
| T01#2 | `test_agent_policy_queue test_agent_policy_schema test_ids_migrate test_ids_migrate_all` | 53 tests, OK |
| T02#1 | oracle `Clause3RewriteClassification` | 1 test, OK |
| T02#2 | `tests.test_ids_migrate_all` | 8 tests, OK |
| T03#1 | oracle `Clause4ProseScoping` | 6 tests, OK |
| T03#2 | `test_ids_migrate_all test_ids_migrate` | 14 tests, OK |
| T04#1 | oracle `Clause5Rehearse` | 3 tests, OK |
| T04#2 | `test_ids_migrate_all test_caller_check_ratchet test_judge_path_registry` | 25 tests, OK |
| T06#1 | oracle `Clause6ValidatesWithOwnCode` | 3 tests, OK |
| T06#2 | oracle module, `test_ids_migrate_all`, `test_caller_check_ratchet` | 32 tests, OK |
| T07#1 | `Clause5Rehearse.test_dirty_tree_is_rehearsed_not_refused` | 1 test, OK |
| T07#2 | oracle module, `test_ids_migrate_all` | 27 tests, OK |
| T08#1 | oracle `Clause7AliasFollowsRoadmapRow` | 2 tests, OK |
| T08#2 | oracle module, `test_ids_aliases`, `test_agent_policy_queue` | 41 tests, OK |
| T05#1 | the rehearsal above | exit 0 |
| T05#2 | `unittest discover -s tests -b` | driver broad run, `ok: true` |
| T05#3 | gate diff of the edited tests | not measured |

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. an `agent-policy.yml` queue naming an old ID validates clean after `--all --apply` | `Clause1PolicyResolvesOldIds.test_queue_with_old_id_validates_after_apply`, with the negative control `test_unknown_queue_entry_still_errors`; `Clause7AliasFollowsRoadmapRow.test_folderless_planned_row_queue_stays_valid` and `test_alias_target_with_neither_folder_nor_row_warns` (the folderless-row case T05 found); `tests.test_agent_policy_queue` | proven |
| 2. `--apply` runs `lint_plan`, `lint_roadmap` and agent-policy validation; exit zero on valid, non-zero naming each error and how to undo on invalid | `Clause2ApplyValidatesResult.test_clean_fixture_exits_zero` and `test_lint_plan_error_exits_nonzero_with_undo`; `Clause6ValidatesWithOwnCode` (validation runs in a fresh process with the target tree's own modules: `test_in_process_linter_would_report_stale_entry` shows the old behaviour is wrong, `test_apply_validates_with_the_trees_own_table` and `test_rehearse_validates_with_the_trees_own_table` show the fix on both paths) | proven |
| 3. a `features/<ID>-<slug>` path or `<ID>-<slug>` string is rewritten only when that exact folder exists; a fixture-only path is left alone; an exact folder name in a code table is rewritten | `Clause3RewriteClassification.test_only_existing_folder_names_are_structural` (real folder and fixture-only name, with and without a leading `features/`); `tests.test_ids_migrate_all` (8 tests) | proven |
| 4. `--include-prose <path>…` rewrites prose only under the named paths; bare flag means all; `--exclude-id` leaves every mention alone | `Clause4ProseScoping`: `test_path_scopes_prose`, `test_bare_flag_rewrites_all_prose`, `test_exclude_id_leaves_everything_untouched`, `test_exclude_id_dry_run_lists_skip`, `test_invalid_exclude_id_exits_nonzero`, `test_dry_run_counts_remaining_prose_by_directory` | proven |
| 5. `--rehearse` runs the rename in a throwaway worktree, runs the tests command there, reports pass or fail with failing tests, removes the worktree and leaves the real tree byte-identical | `Clause5Rehearse.test_passing_command_exits_zero_and_leaves_real_tree`, `test_failing_command_exits_nonzero_and_reports_lines`, `test_dirty_tree_is_rehearsed_not_refused` (T07: an uncommitted edit and an untracked file are seen by the command and the real tree is unchanged afterwards) | proven |
| 6. on this repository, `ids migrate --all` with key `LOOP` and this feature's prose scope, run with `--rehearse`, exits zero | the rehearsal re-run above: exit 0, "rehearse: passed; real tree untouched" | proven for the narrowed prose scope only; see "did NOT verify" for the wider scope |

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events (the only per-attempt record) and
each unit's `planned_cost_usd`. The unit plans sum to **18.50** for T01–T08 (3.00, 2.50,
2.00, 3.00, 4.00, 1.50, 1.50, 1.00); with the 5.00 close that is the 23.50 `PLAN.md`
states, so plan and units agree. `GATE-01.md` sets `cost_budget_usd: 28.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 3.00 | 0.3970 | 1 (passed) | 57.6 |
| T02 | 2.50 | 0.3358 | 2 (produces_not_in_diff, passed) | 73.2 |
| T03 | 2.00 | 0.6585 | 3 (produces_not_in_diff ×2, passed) | 159.9 |
| T04 | 3.00 | 0.3075 | 1 (passed) | 120.6 |
| T05 | 4.00 | 3.4147 | 5 (produces_not_in_diff, blocked ×3, passed) | 11319.8 |
| T06 | 1.50 | 0.2935 | 1 (passed) | 95.3 |
| T07 | 1.50 | 0.2429 | 1 (passed) | 128.2 |
| T08 | 1.00 | 0.2329 | 1 (passed) | 79.6 |
| T01–T08 | 18.50 | **5.8828** | 15 recorded | 12034.2 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 23.50 | **5.8828** | 15 recorded | 12034.2 |

Fifteen recorded attempts spent $5.88: 31.8% of the $18.50 planned for T01–T08 and 21.0%
of `cost_budget_usd`. T05 alone is 58% of it ($3.41 against its $4.00 plan, 189 minutes
of attempt time across five attempts) and every other unit finished under its plan.
**Two bookkeeping discrepancies.** T05's `task_completed` event and frontmatter
`cumulative_cost_usd` read **$2.3695**, which is the last two attempts only; the three
earlier attempts ($0.7142, $0.2120, $0.1189, together $1.0451) were not folded in across
its re-arms, so the driver's own total undercounts T05 by that amount. The table uses the
sum of `attempt_outcome` events. Likewise `cumulative_attempts: 4` on T05 against five
recorded outcomes. This close's own attempt is written when the driver ends it, so it is
not reconciled and the total excludes it. The broad run is the driver's with no model
session, so it is not charged to a unit.

**Where the wait went.** T05 blocked three times before it passed, and each block was a
planning or tool defect found by running the real command, not unit error: the prescribed
prose scope was too wide (T06 and the narrowing), `--rehearse` refused or ignored the
driver's own bookkeeping (T07), and `ids.resolve` ignored an alias target that was a
roadmap row with no folder (T08). Operator turnaround is not in `events.jsonl`; the
timestamps put T05's first dispatch at 15:20 and its pass at 19:36 UTC.

**What the self-halt cost.** The terminal judge-editing stop fired at 19:42:39 and the
acknowledgement was read at 19:57:52: **15 min 13 s**, $0.00 driver spend (`ids.py` and
`agent_policy.py`, PLAN decision 7).

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `produces_not_in_diff` | T02 (1), T03 (2), T05 (1) | 4 | 0.7143 + 0.1896 + 0.2546 + 0.1217 = 1.2802 | the unit's declared `produces:` paths were missing from the squash diff: the hollow-pass guard doing its job. T02 and T03 fixed it on the next attempt; T05's fixed produces list could not be known in advance, so the unit's `produces:` was removed in the re-plan |
| `blocked` (agent) | T05 ×3 | 3 | 0.2120 + 0.1189 + 1.3750 = 1.7059 | the three T05 escalations listed above; all three were correct escalations, not spinning |
| `judge_editing_terminal` halt | G1-CLOSE 19:42:39 | 1 | $0.00 | expected (PLAN decision 7); acknowledged by the operator with a reason |

## Consumer-visible contract changes

Enumerated across T01–T08; each is in `CHANGELOG.md` `Unreleased` (`Added` ×3, `Changed`
×2, FEAT-LOOP-2026-0248).

- **Added — post-apply validation.** `ids migrate --all --apply` ends by running
  `lint_plan`, `lint_roadmap` and agent-policy validation in a fresh process on the target
  tree, and exits non-zero on any error naming it and how to undo. A previously silent bad
  result is now a failing exit status.
- **Added — scoped `--include-prose`.** `--include-prose` takes optional paths or globs;
  the bare flag keeps its meaning (all prose).
- **Added — `--exclude-id`** (repeatable, validated), and a per-directory count of the
  prose mentions left unchanged at the end of a dry run.
- **Added — `--rehearse`** (and `--rehearse-command`): runs the rename on a throwaway
  worktree of a snapshot of the working tree and reports the command's result.
- **Changed — structural matching means a real folder.** A `features/<ID>-<slug>` path or
  `<ID>-<slug>` string in code, config or tests is rewritten only when that exact folder
  exists. A fixture-only path that was rewritten before is now left alone.
- **Changed — this repository sets `ids.key: LOOP`** in `.specfuse/layout.yml`; new
  features here are `FEAT-LOOP-YYYY-NNNN`. Existing features keep their IDs until an
  operator applies `ids migrate --all`.
- **Changed, internal — `ids.resolve`** follows an alias whose target is a roadmap row
  with no feature folder (T08). It has no new flag.

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## What the loop did NOT verify

1. **Applying the rename to `main`.** Nothing here ran `--apply` against this repository's
   working tree: that is an operator decision after this merges (PLAN decision 8). Every
   `--apply` ran in a temporary repository built by a test, and the one real-tree run is
   `--rehearse`, which acts on a throwaway copy. Where checked: `PLAN.md`'s post-merge
   checklist, run `--rehearse` on `main`, read the report, then decide.
2. **Prose mentions that cite another repository's feature.** The rehearsal's narrowed
   scope left 2,839 mentions unchanged (counts above), because telling a foreign citation
   from this repository's own needs the operator. The tool does not detect it: the
   operator names those IDs with `--exclude-id`, and this close did not try that flag on
   this repository's real corpus. A rename that includes `tests/`, `specfuse/`, `docs/` or
   `plugins/` prose was not proven to pass: two operator rehearsals of it failed 78 and 32
   tests and rewrote vendored core files, which is why the scope was narrowed, not fixed.
   Where checked: the operator's `--exclude-id` choice at the real apply, rehearsed first.
3. **GitHub and git-history references.** Issue and PR titles, commit subjects, branch
   names and other repositories keep the old IDs; the alias map is the only link, and only
   the loop's own lookups (`--feature`, `gate_eval`, `gh_features`) follow it. Nothing here
   checked a GitHub-side search by new ID.
4. **The test summary line of the rehearsal.** The tool reports the test command's exit
   status and no `Ran N tests` line on success (see Measurements). The pass is the exit
   status, not a counted test total.
5. **T05#3, that no assertion was deleted or loosened.** The criterion needs the gate
   diff of the ten test modules T05 edited (`files_touched` of its passing attempt), and
   this session ran no git. The rehearsal proves those modules pass on both the real and
   the renamed tree; it cannot show that they still fail on a regression. Where checked:
   PR review of the test diff.
6. **The "fails before" halves of the red-first criteria** (T01#1, T02#1, T03#1, T04#1,
   T06#1, T07#1, T08#1) were recorded by each unit's own attempt, not re-observed here;
   this close re-observed only the passing side.
7. **T05#2 was not re-run in this session.** The full `unittest discover` on the real tree
   is the driver's broad run (`ok: true`, 19:42:39 UTC); the edits since then are this
   close's documentation and bookkeeping files only.
8. **`--rehearse` on a platform other than macOS**, and a rehearsal whose test command
   needs the network: T05's own dispatch saw about 160 false errors inside the sandbox
   (git, build-dependency network fetch) that vanished unsandboxed, so the rehearsal's
   result depends on the environment it runs in.

## Documentation pass

`docs/methodology.md` and its `specfuse/loop/data/docs/methodology.md` copy are in T04's
`covers:`; `tests.test_scaffold_data_in_sync` and `test_caller_check_ratchet` are in the
broad run that passed. This close did not re-read the methodology prose for the new flags
beyond the changelog; the changelog entries were written from the tests above.

## Retrospective

**What went well.** The tool was fixed in `ids.py`, not by hand-editing this repository,
as PLAN decision 1 said, and the rehearsal that found the problems became the proof of the
fix: the same command that left 44 tests failing now exits zero. The walking skeleton held:
the oracle was created red, each owner removed its own skip, none survived. Every
"left alone" case has its rewritten pair. Every T05 block was a correct escalation with the
module and case named, which is the contract working.

**What didn't.** The original T05 was planned against a prose scope that was never
rehearsed: the plan prescribed `tests/`, `specfuse/`, `docs/` and `plugins/` and two
operator rehearsals showed that wrong. Three added units (T06, T07, T08) followed, each a
defect in a tool the plan treated as finished, found only by running it on the real
repository. Cost: T05 at $3.41 on a $4.00 plan, with 189 minutes of attempt time across five attempts.

**Lessons.** Staged in `LEARNINGS-pending.md` (`autonomy_default: auto`, so this close may
not append to `.specfuse/LEARNINGS.md`): rehearse a unit's real command before prescribing
its scope, and a `--rehearse` result is only as good as the code that validates it.

**Open follow-ups (not blockers).** Run the rehearsal on `main` and decide whether to
apply; choose the `--exclude-id` set; fold T05's cost across re-arms in the driver's
`cumulative_cost_usd`; make `--rehearse` print the test command's summary line.
