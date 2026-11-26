# Retrospective — FEAT-LOOP-2026-0251, refuse a missing deliverable before verification

## Gate 1

## Verdict

`met` (advisory; the judge concludes). This is the seventh close of the gate. The re-run
conditions of #3617, #3618 and #3619 hold: lint is silent on a parent-directory mention, as
amended clause 5 says; an agent's own `docs/events.jsonl` or `docs/PROGRESS.md` is now in the
retry note; and `GATE-01.md` records the warning-rate measurement and its accepted evidence,
which an independent recount in this session agrees with. The oracle passes (43 tests, no
skips). This session did not rerun the early-against-late probe; its tables below are the
fourth and fifth closes' observations.

Limits that remain under clause 4: the note does not list files git ignores, and it leaves out
the driver's own three files in the feature folder (the unit file, `events.jsonl`,
`PROGRESS.md`) even if an agent edits one. Non-UTF-8 names and an older crash are under
"Notes for the human reviewer".

## Measurements

Commands in this section ran fresh in this seventh close on the working tree, unless a line
says otherwise. Test runs and probes used `HOME` under `$TMPDIR` with a stub git identity,
because with the real `HOME` the sandbox blocks the driver's preflight write (observed in
the fourth close).

### feature_oracle: PASS

`python3 -m unittest tests.test_fail_fast_deliverables -v -b`: exit 0, `Ran 43 tests`, `OK`,
no skips. `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`. A search
of that file for `unittest.skip`, `skipIf`, `skipUnless`, `skipTest` and `@skip` finds nothing.

### Retry note: files named like driver bookkeeping (#3618)

A throwaway probe drove `loop.run()` through the oracle's `_second_attempt_note` (kept tree,
stubbed agent session and `verify`) and read attempt 2's path list. Every row gave the same
list with fail-fast on and off.

| Attempt 2 does | Note lists |
|---|---|
| writes a new `docs/events.jsonl` | that file |
| writes a new `docs/PROGRESS.md` | that file |
| writes a new `events.jsonl` at the repository root | that file |
| writes a new `PROGRESS.md` at the repository root | that file |
| writes a new `docs/WU-T01.md` (the unit file's name) | that file |
| writes `docs/plain.md` (control) | that file |
| edits a tracked `docs/PROGRESS.md` that attempt 1 had edited | that file |
| nothing | "changed no files" |
| appends to the feature folder's own `events.jsonl` | "changed no files" (driver file, left out by design) |
| writes a git-ignored file | "changed no files" (**ignored file not listed**) |

The guard itself still filters by base name (`assert_implementation_touched_files`, read from
the code). So an `implementation` attempt whose only new file is, say, `docs/events.jsonl`
can be refused as `no_deliverable_files` while its note lists that file. The note is right
about what changed; the guard rule is older than this feature and clause 6 leaves it alone.

### Retry note on a kept tree (#3614 and beyond it), as run in the sixth close

This table is the sixth close's observation, not run again. The oracle's tests for these
kinds of change passed in this session. Row N2 is superseded by the table above.

A throwaway probe drove `loop.run()` through the oracle's own helper
(`_second_attempt_note`, kept tree, stubbed agent session and `verify`) and read the path
list in the note recorded for attempt 2. Every row below gave the same list with fail-fast on
and off.

| Case | Attempt 1 | Attempt 2 | Attempt 2's note lists | Matches what attempt 2 changed |
|---|---|---|---|---|
| R0 | writes a new file | writes another | the second file | yes |
| R1 | writes a new file | deletes it | that file | yes |
| R2 | edits a tracked file | restores it | that file | yes |
| R3 | edits a tracked file | edits it again | that file | yes |
| R5 | writes a new file | deletes it, writes another | both | yes |
| R6 | deletes a tracked file | restores it | that file | yes |
| R7 | deletes a tracked file | nothing | "changed no files" | yes |
| R8 | writes a new file | renames it | both names | yes |
| R9 | writes `docs/x.md` | renames tracked `docs/tracked.md` to `docs/moved.md` | both rename names, not `x.md` | yes |
| R10 | renames a tracked file | writes the old name back | the old name | yes |
| R11 | writes a new file | makes it executable | that file | yes |
| R12 | writes a name with a space | edits it | that file | yes |
| R13 | edits tracked `docs/café.md` | edits it again | the file, unquoted | yes |
| R14 | edits tracked `docs/café.md` | nothing | "changed no files" | yes |
| R15 | edits tracked `docs/café.md` | restores it | the file | yes |
| S1 | writes a new file | `chmod` on a tracked file | the tracked file | yes |
| S2 | edits a tracked name holding `"` | edits it again | that file | yes |
| S3 | creates a symlink | retargets it | the link | yes |
| S4 | writes a file, sets `diff.renames=copies` | renames a tracked file | both names | yes |
| S5 | writes a new file | replaces it with a symlink | that file | yes |
| S6 | writes a new file | only `git add`s it | "changed no files" | yes (no content or mode change) |
| S7 | writes a new file | nothing | "changed no files" | yes |
| S8 | edits a tracked name holding a newline | edits it again | the file, split over two lines | yes, badly formatted |
| S9 | renames a tracked file | nothing | "changed no files" | yes |
| S10 | writes a new file | writes a git-ignored file | "changed no files" | **ignored file not listed** |
| N2 | writes a new file | writes `docs/events.jsonl` | "changed no files" | **file not listed** |

N2 was true on the sixth close's tree, where `format_changed_paths` dropped by base name.
It now matches the three driver files by full path (#3618). `git_diff_names` still drops
`PROGRESS.md` by base name from the guard's diff, but the note's list is built from the
attempt-start comparison, so the table above shows the file listed.

First attempt, reset tree, fail-fast on and off: a new `docs/ñ.md` is listed unquoted, and a
rename of the tracked deliverable `src/rule.py` lists both names (in the presence-refusal
note, under "Files this attempt touched").

With the opt-out, a stub gate that writes `gate-out.txt` during a late refusal gets that file
listed although the agent wrote nothing. This is the late order, not the early refusal that
clause 4 describes.

Two probes crashed the driver:

- R4, a new non-ASCII file in a kept tree: `CalledProcessError` from `git add -N` on the
  quoted path, with fail-fast on and off. The close unit records this as older than the
  feature.
- A nested repository with no commit: `CalledProcessError` from `git add -A`. This shows
  nothing about the note.

### Non-UTF-8 file names

`_paths_differing_from` reads `git ... -z` output as strict UTF-8. In a temporary repository
with one tracked name holding byte `0xff` (made through the index, since macOS refuses such a
name on disk), `snapshot_dirty_tree` raised `UnicodeDecodeError`, while `git_diff_names` over
the same tree returned the quoted name.

Through `loop.run()`, a simulated attempt that deletes that tracked file and writes nothing
else raised `UnicodeDecodeError` from `attempt_own_paths`. The pre-feature `loop.py`
(`bd7e508` pin) raised `UnicodeDecodeError` on the same input too, from
`retain_tree_after_refusal` with a kept tree and `reset_preserving_events` with a reset one.
So this input stops both builds. A case that stops only the new build was **not** shown
through `loop.run()`: a file already dirty at the start is refused by the branch guard (both
builds) when tracked, and an untracked one cannot be created on macOS.

### Other oracles

| Check | Result |
|---|---|
| `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` | 25 tests, `OK` |
| `python3 -m unittest tests.test_lint_plan -b` (named by T04) | **import error: no such module** |
| the `tests/test_lint_plan*.py` modules that do exist | 46 tests, `OK` |
| the ten changed pre-existing test modules | 68 tests, `OK` |
| `.specfuse/scripts/lint_plan.py` over every feature folder with a `PLAN.md` | 97 linted, 0 non-zero exits |
| `diff` of `verification.yml.example` against its packaged copy | exit 0, empty |
| `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` | exit 0, empty |
| `python3 -m specfuse.loop.changelog_fragments check` | exit 0 |

This session did not run the full suite or coverage. The log of the driver's latest broad run
(`work/gate-logs/`, stamps `20261126T2143`) shows `Ran 5157 tests`, `OK (skipped=4)`, and 92%
total coverage. `GATE-01.md` records that run with `ok: true` and no failing gate.

### Controls: the oracle observes the feature

Each mutation ran in a scratch copy of the package, scripts, tests, docs and `.specfuse/`
(without the feature folders). The unmodified copy ran the 43 oracle tests: `OK`.

| Mutation | Result |
|---|---|
| `resolve_fail_fast_deliverables` forced to return `False` | 43 tests: 13 failures |
| note filter turned back to base names | `TestTreeAndNote`, 19 tests: 2 failures |
| parent directory no longer accepted by the lint check | `TestArmTimeWarning`, 6 tests: 1 failure |

Earlier controls, from the sixth close and not repeated: an unfiltered `attempt_own_paths`
(20 failures), rename pairing turned back on (3), mode bits left out of `_path_state` (2),
mangled non-ASCII names (4), attempt-start paths left out of the compared set (10), a no-op
`check_produces_mentioned` (2), and the pre-feature `loop.py` (`bd7e508` pin; 12 failures and
30 errors in 42 tests). On the old driver every failing `TestProducesNotInDiffEarly` and
`TestPresenceEarly` entry was an error, so the first mutation is the behaviour evidence for
those two classes. That substitution was not a full pre-feature tree.

### Early against late, same input

These tables are earlier closes' observations. **Neither the sixth nor this seventh close
ran the probe again.** The source changes named since are in the path-list code, reached only
through `format_changed_paths`, whose three call sites build retry notes (checked by `grep`).
This session reran the oracle, which holds the `files_changed_mismatch` pair (case A) and the
single-refusal pairs in `TestOptOut`.

The probe drove `loop.run()` over the oracle's fixture and read the first `attempt_outcome`
for T01, once with fail-fast on and once off. Verification is a stub. The unit declares
`src/rule.py`. "Untouched" means the attempt writes only `docs/notes.md`. Each cell is
outcome / failure class. Where one name is shown, both are equal. Every early deliverable
refusal recorded `verify_seconds: 0` and `tree_retained: true`.

As run in the fifth close:

| Case | fail-fast on | fail-fast off | Differs because |
|---|---|---|---|
| A: RESULT claims `src/rule.py` in `files_changed` | `produces_not_in_diff` | `files_changed_mismatch` | outranks a later guard |
| B: verify stub fails, untouched | `produces_not_in_diff` | `failed` / `other` | outranks a gate |
| C: untouched, nothing else wrong | `produces_not_in_diff` | same | same |
| G without the smoke-import line: `src/rule.py` emptied | `deliverable_missing` / `guard_refusal` | same | same |
| K: verify stub fails, nothing written | `no_deliverable_files` / `guard_refusal` | `failed` / `other` | outranks a gate |
| L: nothing written (two deliverable refusals apply) | `no_deliverable_files` / `guard_refusal` | same | same |
| M: only `src/rule.py` deleted (two apply) | `deliverable_missing` / `guard_refusal` | same | same |
| O: RESULT `status: blocked`, untouched | `blocked`, no failure class | same | same |

As run in the fourth close:

| Case | fail-fast on | fail-fast off |
|---|---|---|
| D: failing smoke-import line, untouched | `produces_not_in_diff` | `smoke_import_failed` |
| E: also declares a report written with a `BLOCKED` verdict heading; untouched | `produces_not_in_diff` | `failed` / `guard_refusal` |
| F: unit typed `close`, untouched | `produces_not_in_diff` | `closing_deliverable_missing` / `guard_refusal` |
| G: failing smoke-import line, `src/rule.py` emptied | `deliverable_missing` / `guard_refusal` | `smoke_import_failed` |
| H: squash commit rejected (stub), untouched | `produces_not_in_diff` | `squash_commit_failed` |
| I: failing smoke-import line, nothing written | `no_deliverable_files` / `guard_refusal` | `smoke_import_failed` |
| J: `close` unit, nothing written | `produces_not_in_diff` | `closing_deliverable_missing` / `guard_refusal` |
| P: squash commit rejected (stub), `src/rule.py` emptied | `deliverable_missing` / `guard_refusal` | `squash_commit_failed` |
| Q: verify stub writes `src/rule.py`; the attempt did not | `produces_not_in_diff` | `passed` |

Also not repeated, from earlier closes: case N (zero-token session), each second check
firing alone when every declared path is changed, and early presence refusals with
`retain_on_guard_refusal: false`.

### Per-criterion results

All 13 criteria were looked at again. `GATE-01-CRITERIA.md` is left as the driver seeded it,
because it is not one of this unit's permitted closing surfaces.

| Criterion | Result | Evidence from this session |
|---|---|---|
| T01#1 | passes | `TestProducesNotInDiffEarly` in the oracle; first mutation. "Fails on HEAD" rests on the sixth close's old-driver run |
| T01#2 | passes | `test_early_record_equals_late_record` (plain RESULT, passing stub) |
| T01#3 | passes | 25 tests, `OK` |
| T02#1 | passes | `TestPresenceEarly` in the oracle; first mutation. "Fails on HEAD" as for T01#1 |
| T02#2 | passes | `TestOptOut` in the oracle |
| T02#3 | passes | empty diff |
| T03#1 | passes; limit: ignored files | `TestTreeAndNote` (19); lookalike probe; base-name mutation |
| T03#2 | passes | `test_list_is_capped_at_twenty` |
| T04#1 | passes | `TestArmTimeWarning`; parent-directory mutation; lint probe |
| T04#2 | passes with the repository script | 97 folders, 0 non-zero exits |
| T04#3 | accepted under clause 5's measurement record | T04's RESULT notes were not seen by any close; `GATE-01.md` accepts the docstring (81 and 35 of 401) and the sixth judge's recount. This session's recount agrees: 81 and 35 of 402 |
| T04#4 | passes | empty diff |
| T04#5 | passes | prints `0` |

carried forward: 0 criteria, re-measured: 13

## Definition of done, clause by clause

| Clause | Proven | By |
|---|---|---|
| 1. `produces_not_in_diff` early | Refused with 0 `verify_fn` calls, `verify_seconds` 0, no attempt-phase `gate_result`; a changed path verifies once and passes; a justified path still verifies; class, signature and summary equal the late site's | `TestProducesNotInDiffEarly` (6 tests) |
| 2. Presence early | Absent, empty and bookkeeping-only diffs are refused with 0 calls | `TestPresenceEarly` (3) |
| 3. Opt-out | With the key `false`, each of the three cases verifies once; outcome, class, signature and summary equal the default's, for inputs that trip one refusal | `TestOptOut` (4), on plain-RESULT, passing-stub inputs; probe cases C, L, M |
| 4. Tree and note | Proven, with the ignored-file limit. The note says verification did not run; lists written, edited, deleted, reverted, renamed (both names), mode-changed and non-ASCII-named paths, and agent files named like driver bookkeeping; leaves out untouched kept edits and the driver's own three files; caps at 20; the tree is kept or reset | `TestTreeAndNote` (19); this session's lookalike probe; sixth close's cases R0 to R15 and S1 to S9. The kept/reset assertions use `produces_not_in_diff` only |
| 5. Arm-time WARN | Warns on an unmentioned path; silent on full path, file name or parent directory (as amended, #3617), and on `done` / `abandoned`; `lint()` calls it. The measurement record is in `GATE-01.md` (#3619) | `TestArmTimeWarning` (6), including `test_parent_directory_mention_is_silent`; lint probe; recount |
| 6. Nothing else changes | Holds as widened for #3609. See the list below | `diff -ru` of `tests/` against the recorded base; the ten modules pass |
| Precedence over every later check | Holds on every probed pair. A test asserts only the `files_changed_mismatch` pair | `test_deliverable_refusal_outranks_files_changed_mismatch`; this session, the oracle test only; probe cases carried from the fourth and fifth closes |

Three review fixes made before the first close, outside any work unit, are covered by
`TestEarlyRefusalRecovery` (3: re-plan still fires; uncommitted tracked edits count as a
moved tree; an untouched tree still halts) and `TestEarlyRetainedNoteWording` (2).

## Pre-existing tests changed

This seventh close ran no git command on the repository and did not repeat the tree comparison.
It listed the files under `tests/`, `specfuse/`, `scripts/`, `.specfuse/scripts/` and `docs/`
modified after the sixth close last wrote `LEARNINGS-pending.md`: only
`specfuse/loop/loop.py` and the feature's own `tests/test_fail_fast_deliverables.py` (the
#3618 fix and its tests). No pre-existing test is newer. The third to sixth closes
did the same kind of check, each against the close before, back to the second close's
comparison, below. These are modification-time checks, not content diffs. The ten modules
were rerun in this session. In the comparison text, "this session" means the second close.

Compared against the public tarball of `a89373d119f8e2d8003a8956dbd4bd27dde8057f`, the
merge base recorded on the first close's `judged` event, and against public `main` as
fetched in this session. No git command was run. Against `main`, besides the new oracle
file, exactly ten test modules differ. Against the older base the same ten differ; three
further test files absent from that base are identical to `main`. The `.claude` directory
under `tests/` was left out of the comparison.

Changed because of the order of verify and guard:

| Test module | Change | Why |
|---|---|---|
| `test_files_changed_auto_repair` | `test_untouched_deliverable_still_refuses` now expects `produces_not_in_diff`, not `files_changed_mismatch`, and reads `payload["remaining"]` | The early check pre-empts the post-verify guard. The expected outcome changed; this is the stated precedence (#3608) |
| `test_guard_repair_e2e` | Patches `early_produces_refusal` to return `None` in one test | The absent `src/extra.py` would be refused early, so the guard under test would never run. The test now exercises the late order only |
| `test_arm_wiring` | Two dispatch stubs wrapped in `with_deliverable` | The stubs wrote nothing and relied on `verify` failing first |
| `test_loop_files_changed_guard` | One stub wrapped in `with_deliverable` | Same: it must get past the presence refusal to reach `verify` |
| `test_replan_end_to_end` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_event_emission` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_note_collision` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_trigger` | One stub writes `deliverable.txt`; one comment rewritten | Attempts must reach `verify`; the comment's claim that the re-plan trigger is never consulted became false |

Forced by the shared helper or the new lint wording (the widened clause 6):

| Test module | Change | Why |
|---|---|---|
| `test_deterministic_refusal_repeat` | The source-text anchor moved from `"deliverable_missing",` to `if not deliv_ok:` | The emit call moved into the shared `refuse_deliverable_missing` helper. Both assertions are unchanged. They cover the late branch only |
| `test_produces_shape` | Two negative tests filter findings on `assert_declared_deliverables`, not `directory` | The new WARN text contains "directory". `lint_plan.py` puts the new marker in the shape ERROR, and the two positive tests are unchanged, so the negative tests still catch a shape ERROR on a file or glob |

## What happened

T01 to T04 each passed on the first attempt. The gate's first broad run
(2026-11-25T23:44Z) failed: `tests` with 5125 tests and 2 failures, both in
`test_produces_shape`, and `coverage` with `no_gate_marker`. The T04 WARN text caused the
two test failures. No unit's narrow tier selected that module. A later broad run was clean.
The terminal judge-editing stop then fired, as `GATE-01.md` expected. An independent review
found three behaviour changes, fixed test-first on the branch, and the operator
acknowledged the judge edits and re-armed this unit.

The first close (2026-11-26T13:42Z) and the judge both recorded `not_met`, and the driver
filed #3608 and #3609. The operator amended `GATE-01.md` for both (precedence over
`files_changed_mismatch`; a wider clause 6), added a test for the precedence, and re-armed
this unit. The first close had noted the other overtaken checks from reading the code but
did not probe them or put them in a follow-up entry, so the amendment named only one. The second
close probed them (cases D to G).

The second close (2026-11-26T14:10Z) and the judge recorded `not_met`, and the driver filed
#3610. The operator replaced the single named exception with a general precedence rule in
`GATE-01.md`, the close unit's trigger and `docs/methodology.md`, and re-armed this unit.
No source or test change accompanied it.

The third close (2026-11-26T15:45Z) recorded `met`. The judge lowered it to `not_met` on
clause 4, and the driver filed #3612: the note listed an earlier attempt's kept edits as the
later attempt's own. That close, like the two before it, tested "changed nothing" only on a
first attempt. The fix (`snapshot_dirty_tree`, `attempt_own_paths`, three tests) was made on
the branch outside any work unit, and the operator re-armed this unit. The fourth close
probed removals on a kept tree and found that deleted and reverted files were missing.

The fourth close (2026-11-26T16:28Z) and the judge recorded `not_met`, and the driver filed
#3613. The fix to `attempt_own_paths` and three tests were made on the branch outside any
work unit, and the operator re-armed this unit. The fifth close confirmed that fix and
probed renames, non-ASCII names and a mode change. #3612, #3613 and the gaps then open were
all in one list, built by filtering a name-only diff; each fix so far covered the cases the
previous close had named.

The fifth close (2026-11-26T17:03Z) and the judge recorded `not_met`, and the driver filed
#3614. The fix replaced filtering of the guard's diff with a comparison of each path's state
at the start and end of the attempt, which is the first option that close recommended. It was
made on the branch outside any work unit, and the operator re-armed this unit. The sixth
close confirmed it on the whole earlier matrix and ten further cases.

The sixth close (2026-11-26T18:04Z) recorded `met`. The judge lowered it to `not_met` on three
findings, and the driver filed #3617 (clause 5 never amended for the parent directory), #3618
(the note dropped agent files by base name; the sixth close had probed this as case N2 and
judged it acceptable, wrongly) and #3619 (T04's measurement not visible in its RESULT notes).
The operator fixed #3618 on the branch outside any work unit, amended clause 5 for the other
two, and re-armed this unit.

T04 passed although its Verification section names `tests.test_lint_plan`, which does not
exist.

## Cost analysis

Unit costs are from the `task_completed` events in `events.jsonl`. For a close, the figure
includes its judge: `record_judge_cost_fold` adds the judge's usage to the attempt before
`attempt_outcome` is emitted.

| Unit | Planned USD | Actual USD | Of which judge | Actual / planned | Attempts |
|---|---|---|---|---|---|
| T01 | 2.00 | 0.88 | — | 44% | 1 |
| T02 | 1.50 | 0.77 | — | 51% | 1 |
| T03 | 1.00 | 0.55 | — | 55% | 1 |
| T04 | 1.50 | 0.47 | — | 32% | 1 |
| Substantive total | 6.00 | 2.67 | — | 45% | 4 |
| G1-CLOSE, first close | 5.00 (one plan line for all closes) | 1.69 | 0.44 | 34% | 1 |
| G1-CLOSE, second close | (same line) | 1.49 | 0.48 | 30% | 1 |
| G1-CLOSE, third close | (same line) | 1.73 | 0.57 | 35% | 1 |
| G1-CLOSE, fourth close | (same line) | 1.44 | 0.36 | 29% | 1 |
| G1-CLOSE, fifth close | (same line) | 1.35 | 0.47 | 27% | 1 |
| G1-CLOSE, sixth close | (same line) | 1.66 | 0.48 | 33% | 1 |
| G1-CLOSE, seventh close | (same line) | not yet recorded | — | — | in progress |
| G1-CLOSE, six recorded closes | 5.00 | 9.36 | 2.80 | 187% | 6 |

Recorded unit spend is 12.03 USD. That is over the plan of 11.00 (109%) and under the gate
budget of 14.00, with this session's cost and its judge's still to be written. The earlier
`blocked_human` stop of this unit recorded 0.00. The independent review, its fixes, the
amendments and the #3612, #3613, #3614 and #3618 fixes happened outside the loop, so
`events.jsonl` has no cost for them. All six re-closes cost money for questions the plan or
the oracle had left open: two for an unstated precedence, one each for #3612, #3613 and
#3614, and this one for #3617 to #3619.

**T04's warning rate.** T04 recorded, in the check's docstring, 81 of 401 `done` units with
`produces:` for path or file name alone (20.2%) and 35 with the parent directory (8.7%).
Re-measured this session: the shipped rule would fire on 35 of 402, **8.7%**, under the 10%
limit; path or file name alone on 81 of 402, 20.1%. The population has grown by one. T04's
progress note does not carry the count. The parent-directory match is a plain substring
test, so a short directory such as `tests` is satisfied by almost any body, and a mention of
a subdirectory (`specfuse/loop/data/docs`) also silences `specfuse/loop/loop.py`. The WARN is
weak for such paths.

## Consumer-visible contract changes

Pending human acknowledgment. Each has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0251`. This close added no fragment; it corrected the retry-note one in
place, replacing the base-name limit that #3618 fixed.

1. **Changed:** the three deliverable refusals run before verification. They take precedence
   over every verification gate and later guard. An attempt that also would have failed one
   is reported as the deliverable refusal. By default its tree is kept, including where the
   old order reset it.
2. **Added:** `defaults.fail_fast_deliverables`, default `true`.
3. **Changed:** the retry note for the three refusals lists the changed paths, at most 20
   plus a count. Untouched edits kept from an earlier attempt are left out; deletes,
   reverts, both names of a rename, mode-only changes and non-ASCII names are listed. Not
   listed: git-ignored files, and the driver's own unit file, `events.jsonl` and
   `PROGRESS.md` in the feature folder.
4. **Added:** a `specfuse lint` WARN for a `produces:` path the unit's body never mentions.

## Notes for the human reviewer

None of these is a failed criterion. This unit may edit none of the files concerned.

- **Non-UTF-8 names in the new reader.** `_paths_differing_from` decodes `-z` output
  strictly and catches only `OSError` and `CalledProcessError`. It runs before every
  attempt. From the code and the function-level probe, an untracked non-UTF-8 name (possible
  on Linux) would raise there, where the old listing got an ASCII quoted form. Whether the
  old driver would have finished such a run was not shown. Passing
  `errors="surrogateescape"` is a likely fix; printing such a name into the note would need
  checking too. Worth fixing with the crash below.

- **Older defect, worth its own bug.** A refused attempt that keeps its tree and has a
  changed file with a non-ASCII name stops the driver with `CalledProcessError`:
  `git_diff_names` returns git's quoted form and `git add -N` rejects it (probe R4). The
  fourth close saw the pre-feature `loop.py` do the same. R4 reproduced in the sixth close. No
  close has filed an issue for it, and with no open follow-up entry the driver will file none.

- **One sentence in `docs/methodology.md` is too strong.** It says "What is refused does not
  change, only when." Probe case Q is an attempt that passes with the key `false` and is
  refused with the default, because a gate writes the declared file. `PLAN.md` decision 6,
  `verification.yml.example` and a changelog fragment describe the opt-out for this; that
  paragraph of the methodology does not say when to set it. `PLAN.md` has the same sentence.
- **The side-effect list is incomplete.** `GATE-01.md` and `docs/methodology.md` name the
  smoke-import and closing-deliverable refusals as ones that used to reset the tree. The
  probe also saw the old order remove the attempt's file after a rejected squash commit, the
  blocked-verdict check and a failed gate. The new behaviour follows clause 4 in each case.
- The rule's words "every check that runs after the agent session" mean, as `GATE-01.md`
  goes on to say, the gates and later guards. A zero-token session and a `blocked` RESULT
  are still decided first, in both orders (cases N and O).

## What the loop did NOT verify

- **A real project whose gates write a declared deliverable.** The opt-out is tested only
  with stubs, probe case Q included. With the default, such a unit is refused early on every
  attempt.
- **Real refused attempts on the new build.** T01 to T04 ran on a build pinned before the
  change (`bd7e508`). Later pins exist and the closes were dispatched after them, but every
  `attempt_outcome` in `events.jsonl` before this close is `passed`. No real early refusal
  has happened, so no real saving in gate time is measured.
- The probes stubbed the agent session, `verify`, and (for H and P) the squash rejection.
- Every early-against-late probe case, the sixth close's path-list matrix, its crash and
  non-UTF-8 probes, and the other observations listed as not run again.
- A non-UTF-8 name on a real filesystem, and any run on Linux.
- Submodules and nested repositories (the one nested probe crashed in `git add -A`), changes
  to an empty directory, `core.filemode=false`, and special files such as a named pipe.
- That cases A to Q are the whole list of overtaken checks. The list comes from reading
  `execute_unit_attempt()` and the post-squash guards in `run()`. The general rule does not
  depend on the list being complete; the claim that it holds rests on the early check running
  before all of them.
- `learnings_not_staged` and the judge run after the three deliverable guards in the late
  order too. This is read from the code, not probed.
- A full pre-feature tree: only the old `loop.py` was substituted.
- Whether the pending-diff computation matches the squash diff for renames, submodules or
  ignored files.
- The content of the pre-existing test edits was not compared again by this close.
- `specfuse lint` as the installed command. The installed build differs from this tree, so
  the repository scripts were used.
