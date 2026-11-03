# Retrospective — FEAT-LOOP-2026-0249 gate 1 close

First and only close of gate 1 (single-gate feature, PLAN decision 8). Seven loop-dispatched
implementation units (T01–T07). This session re-measured the oracles fresh and wrote the close
deliverables, and wrote this feature's own changelog entries through the new flow.

## Measurements

Every command below was run in this session from the repository root, exit codes read
directly. HEAD was `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e` plus this close's own
uncommitted edits (`changelog.d/`, this file, `LEARNINGS-pending.md`, `GATE-01-CRITERIA.md`,
the `verdict` field of `WU-90-gate-1-close.md`). The close session may not run git commits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_changelog_fragments -v -b` (exit 0):
`Ran 28 tests` / `OK`, every class running, none skipped (the run prints no `skipped` marker).

```
TestClause1ConcurrentPrsDoNotConflict   3
TestClause2GuardsReadFragments          8
TestClause3CollateAtRelease             7
TestClause4CheckGate                    6
TestClause5NoModeKeyBehavesAsBefore     2
RepoOptInTests                          2
```

### No surviving skip (close criterion 1)

`grep -nE 'unittest\.skip|@skip|skipTest' tests/test_changelog_fragments.py` prints nothing
(exit 1). T01 created the module with clauses 2–4 and clause 5's release half skipped by owner
name; T02, T03 and T04 each removed their own.

### The changelog guard passes on fragments alone (close criterion 3)

`grep -c 'FEAT-LOOP-2026-0249' CHANGELOG.md` prints `0` (this branch's `CHANGELOG.md` carries no
entry tracing to this feature; the unit's own `Do not touch` also bars editing it).

`python3 -m specfuse.loop.changelog_fragments check` (exit 0): no output, the eight fragments
below are well formed.

The guard itself is `tests.test_changelog_fragments.TestClause2GuardsReadFragments`, which drives
`close-k`, `lint --closing` and the terminal auto-close guard with a fragment and no
`CHANGELOG.md` entry (exit 0, 8 tests), paired with `test_no_entry_in_either_form_fails_every_guard`.

### Closing lint (close criterion 6)

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments --closing`
is run last, after the verdict field is written; its result is recorded in the RESULT block of
this attempt. The bare `specfuse lint --closing` warns that it measures the pipx-installed
build and then requires a feature directory, so the checkout's script was run instead.

### Broad run (driver's, not re-run here)

`events.jsonl` records `broad_run_result` at 2026-11-03T13:06:22 with `ok: true`,
`failing: []`, on the tree recorded in `GATE-01.md`'s `broad_run:` block (the earlier gate-1
broad run at 2026-11-02T17:05:24 was also clean). `security` and `coverage` are `tier: broad`
and are the driver's.

### Per-criterion oracles (19 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 19

All nineteen were `unverified` on entry. Each was run in this session as its own command by
one script; each now records its oracle command, `kind: narrow`, `state: pass` and
`proved_at_sha` `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`, all exit 0.

| criterion | oracle | ran |
| --- | --- | --- |
| T01#1 | oracle clause-1 class (incl. the `single`-mode conflict control) | 3 tests, OK |
| T01#2 | clause-5 `test_add_without_mode_edits_changelog_md` | 1 test, OK |
| T01#3 | `tests.test_judge_path_registry tests.test_changelog_release_wiring` | 28 tests, OK |
| T02#1 | oracle clause-2 class | 8 tests, OK |
| T02#2 | `grep -c parse_changelog specfuse/loop/lint_closing.py` | `0` |
| T02#3 | `tests.test_terminal_auto_close_changelog tests.test_load_bearing_close_lint tests.test_judge_path_registry` | 30 tests, OK |
| T03#1 | oracle clause-3 class | 7 tests, OK |
| T03#2 | clause-5 `test_release_without_fragments_unchanged` | 1 test, OK |
| T03#3 | `tests.test_changelog_release_wiring tests.test_changelog_append_only` | 28 tests, OK |
| T04#1 | oracle clause-4 class | 6 tests, OK |
| T04#2 | `python3 -m specfuse.loop.changelog_fragments check` | exit 0 |
| T05#1 | `tests.test_ids_migrate_all` | 9 tests, OK |
| T05#2 | `tests.test_ids_migrate tests.test_ids_migrate_all` | 15 tests, OK |
| T06#1 | `grep -c 'changelog_fragments add' plugins/specfuse/skills/fix-bug/SKILL.md` | `1` (>= 1) |
| T06#2 | same grep on `.specfuse/rules/close-discipline.md` | >= 1 |
| T06#3 | `diff` of the rule against `specfuse/loop/data/rules/` copy | empty |
| T06#4 | `tests.test_plugin_prose_cross_refs` | 1 test, OK |
| T07#1 | `RepoOptInTests`; `layout get changelog.mode` / `get ids.key` | 2 tests OK; `fragments` / `LOOP` |
| T07#2 | `tests.test_changelog_schema tests.test_terminal_auto_close_changelog tests.test_changelog_fragments` | 45 tests, OK |

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. two branches each `add` in `fragments` mode; second merges clean with real `git merge`; `single` control conflicts | `TestClause1ConcurrentPrsDoNotConflict.test_fragments_mode_second_merge_is_clean`, `test_single_mode_control_conflicts`, `test_add_refuses_bad_input` | proven in temp git repos |
| 2. fragment-only entry passes `close-k`, `lint --closing` and the terminal auto-close guard; no entry in either form fails all three | `TestClause2GuardsReadFragments.test_fragment_only_without_changelog_md_passes_every_guard`, `test_no_entry_in_either_form_fails_every_guard`, plus `test_fragment_for_a_sub_wu_of_the_feature_counts`, `test_malformed_fragments_do_not_count`, `test_refusals_name_both_locations` | proven, positive control present |
| 3. release leaves every fragment in the new section, section parses, no consumed fragment remains; malformed fragment refuses with tree untouched | `TestClause3CollateAtRelease.test_release_folds_every_fragment_and_removes_them`, `test_invalid_fragment_refuses_naming_it_and_touches_nothing`, `test_double_stamp_refusal_leaves_every_fragment`, `test_output_is_deterministic_in_filename_order` | proven through `scripts/bump_version.py` `release()` |
| 4. `check` non-zero naming a malformed fragment, zero on valid or absent directory | `TestClause4CheckGate` (wrong class, bad trace, missing frontmatter, multi-line body each fail naming the file; `test_valid_fragments_pass`, `test_absent_directory_passes`) | proven |
| 5. no `changelog.mode` key behaves as before | `TestClause5NoModeKeyBehavesAsBefore.test_add_without_mode_edits_changelog_md`, `test_release_without_fragments_unchanged` | proven |

No `unittest.skip` survives in `tests/test_changelog_fragments.py` (grep above, exit 1).

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's `planned_cost_usd`.
The unit plans sum to **20.50** (15.50 for T01–T07 plus 5.00 for this close), matching
`PLAN.md`; `GATE-01.md` sets `cost_budget_usd: 26.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 3.00 | 0.4443 | 1 (passed) | 64.4 |
| T02 | 3.50 | 0.6812 | 1 (passed) | 124.0 |
| T03 | 3.00 | 0.3034 | 1 (passed) | 55.9 |
| T04 | 1.50 | 0.1825 | 1 (passed) | 33.1 |
| T05 | 1.50 | 0.1939 | 1 (passed) | 49.4 |
| T06 | 2.00 | 0.8242 | 3 (failed `tests`, failed `tests`, passed) | 1902.3 |
| T07 | 1.00 | 0.2240 | 2 (`produces_not_in_diff`, passed) | 61.9 |
| T01–T07 | 15.50 | 2.8535 | 11 recorded | 2291.0 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 20.50 | **2.8535** | 11 recorded | 2291.0 |

The eleven recorded attempts spent $2.85 (18.4% of the $15.50 planned for them, 11.0% of
`cost_budget_usd`). This close's own attempt is written when the driver ends it, so it is not
reconciled and the total excludes it. The broad runs are the driver's with no model session,
so they are not charged to a unit.

**T06's three attempts.** The first failed the baseline probe: `test_caller_check_ratchet`'s
`test_the_baseline_has_not_silently_shrunk` (T01's `append_entry` gaining a production caller
shrank the ratchet baseline; commit `915e05c` dropped it) plus `coverage` `no_gate_marker`,
so `baseline_attribution` attributed the failure to T06 and the driver raised
`human_escalation` `preexisting_gate_failure`. The re-dispatch failed `tests` again on
`test_changelog_collection.test_close_discipline_instructs_unreleased_append`, a test pinning
the old hand-edit wording T06 replaced, then passed on attempt 2. T06 cost 0.8242 of its 2.00
plan (41%) and 83% of the feature's recorded wall-clock (1902 s of 2291 s). T07's first
attempt was refused `produces_not_in_diff` (a hollow pass the FEAT-2026-0008 guard caught), $0.11.

**What the self-halt cost.** The terminal judge-editing stop fired at 2026-11-02T17:05:25 and
was acknowledged by the operator at 2026-11-03T13:06:22: wall-clock overnight, $0.00 driver
spend, ten acknowledged paths (`loop.py`, `closing_requirements.py`, `lint_closing.py` and
`close-discipline.md` among them), reason "guards not weakened, single-file behavior unchanged".

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `tests` | T06 dispatch 1 and the re-dispatch's attempt 1 | 2 | 0.5174 | ratchet baseline shrunk by T01's caller (fixed outside the unit, `915e05c`); then a test pinning the old close-discipline wording |
| `produces_not_in_diff` | T07 attempt 1 | 1 | 0.1078 | session finished without touching a `produces:` path; driver guard refused, attempt 2 passed |
| `judge_editing_terminal` halt | G1-CLOSE 2026-11-02T17:05:25 | 1 | $0.00 | expected (PLAN decision 8); acknowledged by the operator with a reason |

## Consumer-visible contract changes

Enumerated across T01–T07 for acknowledgment; each is a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0249` (`Added` ×4, `Changed` ×4), written with
`python3 -m specfuse.loop.changelog_fragments add`.

- **Added — `changelog.mode: single | fragments` in `.specfuse/layout.yml`.** Absent means
  `single`; any other value is an error from `layout validate`.
- **Added — the `python3 -m specfuse.loop.changelog_fragments` CLI**, subcommands `add`
  (the one writer, routes by mode), `collate` and `check`.
- **Added — the fragment file format**, `changelog.d/<trace>-<slug>.md` with `class` and
  `trace` frontmatter and a one-line body.
- **Added — the `changelog-fragments` gate** in this repository's `.specfuse/verification.yml`
  running `check`; adopters add the same gate themselves.
- **Changed — `close-k`, `specfuse lint --closing` and the terminal auto-close guard** accept
  an entry in `CHANGELOG.md` or a valid fragment through one shared reader; refusals name both.
- **Changed — `scripts/bump_version.py` `release()`** collates fragments into `Unreleased`
  before stamping and removes them after, all-or-nothing. An adopter's own release script must
  call `collate` before stamping.
- **Changed — `ids migrate --all --apply`** rewrites a fragment's `trace` to the new ID,
  filename unchanged.
- **Changed — close-discipline §3 and `/fix-bug`** tell agents to run `changelog_fragments add`
  rather than hand-edit `CHANGELOG.md`.

No removals or renames. A project that sets no `changelog.mode` is unaffected.

## What the loop did NOT verify

1. **GitHub's merge button.** Clause 1's oracle uses real `git merge` in temporary
   repositories. Whether GitHub marks two open PRs that each add a fragment as non-conflicting
   was not observed; `PLAN.md`'s Post-merge checklist, first item, carries it.
2. **An adopter's own release script calling `collate`.** Only this repository's
   `scripts/bump_version.py` `release()` is driven by the oracle. A custom release script that
   stamps without collating first would leave fragments unreleased; the only guard is the
   `docs/lifecycles.md` line T06 wrote, which no test exercises.
3. **A real adopter opting in.** `changelog.mode: fragments` has been exercised only in
   temporary repositories and this one; no consumer ran `specfuse upgrade` across the change.
4. **GitHub CI on the new `changelog-fragments` gate.** `check` exits 0 locally and through
   the driver's broad run; the CI workflow derives its gates from `verification.yml`, and was
   not run here.
5. **The "fails on HEAD" halves of the red-first criteria** were recorded by each unit's own
   attempt, not re-observed here; this close re-observed only the passing side.
6. **A real release.** No `release()` ran against this repository's real `changelog.d/`; the
   eight fragments written by this close will be the first real collation at the next release.

## Retrospective

**What went well.** Seven units, five passing first time, $2.85 against a $15.50 plan. The
walking skeleton again held: T01 created the module and the oracle with later clauses skipped
by owner name, each owner removed its own skip, and none survived to the close. Every clause
has its positive control (the `single`-mode conflict, the no-entry failure). T07 opting this
repository in last meant the feature's own close was the first real use of the writer.

**What didn't.** T06 cost three attempts and 83% of the wall-clock on a ratchet-baseline red and a stale wording test, and T07's first attempt was a hollow pass
caught only by the driver's produces-vs-diff guard.

**Lessons.** Nothing generalizes beyond what the plan already recorded (the close's `Do not
touch` must permit the surfaces its obligations write; the oracle drives the real boundary),
which both held. See `LEARNINGS-pending.md`.

**Open follow-ups (not blockers).** The two post-merge checklist items (two real PRs merged
through GitHub's button; decide FEAT-LOOP-2026-0200's optional re-apply), filed at close as
`specfuse:post-merge`.
