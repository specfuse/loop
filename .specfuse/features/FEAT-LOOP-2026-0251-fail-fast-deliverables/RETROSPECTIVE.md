# Retrospective — FEAT-LOOP-2026-0251, refuse a missing deliverable before verification

## Gate 1

## Verdict

`not_met` (advisory; the judge concludes). The #3613 cases are fixed: a kept file that the
attempt deletes or reverts is now listed. Definition-of-done clause 4 still does not hold.
The path list leaves out the old name of a renamed tracked file, and it says "this attempt
changed no files" after some later attempts that did change a file: a second edit or a
revert of a kept tracked file with a non-ASCII name, a restore of the old name of a file
an earlier attempt renamed, and a mode-only change (probe cases R9, R10, R11, R13, R15
below). This is the fifth close of the gate. Follow-up: `FOLLOW-UPS.md`.

## Measurements

All commands ran fresh in this fifth close on the working tree, unless a line says
otherwise. Test runs and probes used `HOME` under `$TMPDIR` with a stub git identity,
because with the real `HOME` the sandbox blocks the driver's preflight write (observed in
the fourth close). git version 2.53.0.

### feature_oracle: PASS

`python3 -m unittest tests.test_fail_fast_deliverables -v -b`: exit 0, `Ran 36 tests`, `OK`,
no skips. `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`. A search
of that file for `unittest.skip`, `skipIf`, `skipUnless`, `skipTest` and `@skip` finds nothing.
The oracle passes and does not cover the clause 4 gaps below.

### Retry note on a kept tree (#3613 and beyond it)

A throwaway probe drove `loop.run()` through the oracle's own helper
(`_second_attempt_note`, kept tree, stubbed agent session and `verify`) and read the path
list in the note recorded for attempt 2. Each case gave the same result with fail-fast on
and off. The last column repeats the case with `attempt_own_paths` replaced by a function
that returns its input, which is the listing without the #3612 and #3613 logic. A dash
means the case was not repeated that way.

| Case | Attempt 1 | Attempt 2 | Attempt 2's note lists | Correct | Without the filter |
|---|---|---|---|---|---|
| R0 | writes a new file | writes another | the second file | yes | — |
| R1 | writes a new file | deletes it | that file | yes | — |
| R2 | edits a tracked file | restores it | that file | yes | — |
| R3 | edits a tracked file | edits it again | that file | yes | — |
| R5 | writes a new file | deletes it, writes another | both | yes | — |
| R6 | deletes a tracked file | restores it | that file | yes | — |
| R7 | deletes a tracked file | nothing | "changed no files" | yes | — |
| R8 | writes a new file | renames it | both names | yes | — |
| R12 | writes a file with a space in its name | edits it | that file | yes | — |
| R9 | writes `docs/x.md` | renames tracked `docs/tracked.md` to `docs/moved.md` | `docs/moved.md` only | **no** | `moved.md`, `x.md`; old name still missing |
| R10 | renames tracked `docs/tracked.md` | writes the old name back, same content | "changed no files" | **no** | `docs/moved.md` |
| R11 | writes a new file | makes it executable | "changed no files" | **no** | that file |
| R13 | edits tracked `docs/café.md` | edits it again | "changed no files" | **no** | the file, in git's quoted form |
| R14 | edits tracked `docs/café.md` | nothing | "changed no files" | yes | lists it (the #3612 defect) |
| R15 | edits tracked `docs/café.md` | restores it | "changed no files" | **no** | "changed no files" |

A separate probe renamed a tracked file on a first attempt with a reset tree. The note
listed only the new name, with fail-fast on and off. So the missing old name does not need
a kept tree.

Causes, from the code together with the table:

- `git_diff_names` and `pending_squash_names` call `git diff --name-only` with git's
  default rename detection, which reports a rename under the new name only. The old name
  is then in neither the guard's diff nor the attempt-start snapshot (R9, R10).
- Both return git's quoted form for a non-ASCII name. `_path_digest` cannot open that
  string, so it returns `None` before and after, and the path never counts as changed
  (R13, R15). R13 is caused by the filter added for #3612.
- `_path_digest` hashes file content only (R11).

R4 (a new file with a non-ASCII name, kept tree): `loop.run()` raised
`CalledProcessError` from `git add -N` on the quoted path. The fourth close saw the
pre-feature `loop.py` raise the same error from the same function; that comparison was not
repeated.

### Other oracles

| Check | Result |
|---|---|
| `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` | 25 tests, `OK` |
| `python3 -m unittest tests.test_lint_plan -b` (named by T04) | **error: no such module** |
| the `tests/test_lint_plan*.py` modules that do exist | 46 tests, `OK` |
| the ten changed pre-existing test modules | 68 tests, `OK` |
| `.specfuse/scripts/lint_plan.py` over every feature folder with a `PLAN.md` | 97 linted, 0 non-zero exits |
| `diff` of `verification.yml.example` against its packaged copy | exit 0, empty |
| `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` | exit 0, empty |
| `python3 -m specfuse.loop.changelog_fragments check` | exit 0 |

This session did not run the full suite or coverage. The driver's broad run recorded at
2026-11-26T16:51:24Z has `ok: true` and no failing gate. Its tests log
(`work/gate-logs/`, stamp `20261126T165040`) shows `Ran 5150 tests`, `OK (skipped=4)`; its
coverage log shows 92% total.

### Controls: the oracle observes the feature

Each mutation ran in a scratch copy of the package, tests and `.specfuse/` (without the
feature folders). The unmodified copy ran the 36 oracle tests: `OK`.

| Mutation | Result |
|---|---|
| `resolve_fail_fast_deliverables` forced to return `False` | 13 failures, no errors: `TestOptOut` 4, `TestPresenceEarly` 3, `TestProducesNotInDiffEarly` 3, `TestTreeAndNote` 2, `TestEarlyRefusalRecovery` 1 |
| `attempt_own_paths` returns its input unfiltered (#3612 undone) | `TestTreeAndNote`, 12 tests: 10 failures (subtests counted) |
| only the removed-path branch disabled (#3613 undone) | `TestTreeAndNote`, 12 tests: 6 failures (subtests counted) |
| `check_produces_mentioned` made a no-op | `TestArmTimeWarning`, 6 tests: 2 failures (the other four expect silence) |
| `loop.py` replaced by the pre-feature one (`bd7e508`, no `fail_fast_deliverables`) | 36 tests: 12 failures, 24 errors (subtests counted) |

On the old driver, `TestProducesNotInDiffEarly` (6) and `TestPresenceEarly` (3) give only
errors, from a missing interface; the first mutation is the behaviour evidence for those two
classes. `TestOptOut` (3 failures, 1 error) and `TestTreeAndNote` (7 failures, 11 errors)
also fail on assertions. This is not a full pre-feature tree.

### Early against late, same input

A throwaway probe drove `loop.run()` over the oracle's fixture and read the first
`attempt_outcome` for T01, once with fail-fast on and once off. Verification is a stub. The
unit declares `src/rule.py`. "Untouched" means the attempt writes only `docs/notes.md`. Each
cell is outcome / failure class. Where one name is shown, both are equal. Every early
deliverable refusal recorded `verify_seconds: 0` and `tree_retained: true`.

Run again in this close:

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

Not run again, and carried only as the fourth close's observations. The only source change
named since then is in `attempt_own_paths`, which builds note text.

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

| Criterion | Result | Evidence |
|---|---|---|
| T01#1 | passes | `TestProducesNotInDiffEarly`; on the old driver errors only, behaviour shown by the first mutation |
| T01#2 | passes | `test_early_record_equals_late_record` (plain RESULT, passing stub) |
| T01#3 | passes | 25 tests, `OK` |
| T02#1 | passes | `TestPresenceEarly`; on the old driver errors only, behaviour shown by the first mutation |
| T02#2 | passes | `TestOptOut`; assertion failures on the old driver |
| T02#3 | passes | empty diff |
| T03#1 | the listed assertions pass; clause 4, which the unit exists to turn green, **fails** | `TestTreeAndNote`; probe cases R9, R10, R11, R13, R15 |
| T03#2 | passes | `test_list_is_capped_at_twenty` |
| T04#1 | passes | `TestArmTimeWarning`; no-op control |
| T04#2 | passes with the repository script | 97 folders, 0 non-zero exits |
| T04#3 | not observed | no close has seen T04's RESULT; the count is re-measured below |
| T04#4 | passes | empty diff |
| T04#5 | passes | prints `0` |

carried forward: 0 criteria, re-measured: 13

## Definition of done, clause by clause

| Clause | Proven | By |
|---|---|---|
| 1. `produces_not_in_diff` early | Refused with 0 `verify_fn` calls, `verify_seconds` 0, no attempt-phase `gate_result`; a changed path verifies once and passes; a justified path still verifies; class, signature and summary equal the late site's | `TestProducesNotInDiffEarly` (6 tests) |
| 2. Presence early | Absent, empty and bookkeeping-only diffs are refused with 0 calls | `TestPresenceEarly` (3) |
| 3. Opt-out | With the key `false`, each of the three cases verifies once; outcome, class, signature and summary equal the default's, for inputs that trip one refusal | `TestOptOut` (4), on plain-RESULT, passing-stub inputs; probe cases C, L, M |
| 4. Tree and note | **Not proven.** The note says verification did not run; lists written, edited, deleted (#3613) and reverted (#3613) paths with ordinary names; leaves out untouched kept edits (#3612); caps at 20; the tree is kept or reset. The list still omits the changes in probe cases R9, R10, R11, R13 and R15 | `TestTreeAndNote` (12). The kept/reset assertions use `produces_not_in_diff` only |
| 5. Arm-time WARN | Warns on an unmentioned path; silent on full path, file name or parent directory, and on `done` / `abandoned`; `lint()` calls it | `TestArmTimeWarning` (6) |
| 6. Nothing else changes | Holds as widened for #3609. See the list below | `diff -ru` of `tests/` against the recorded base; the ten modules pass |
| Precedence over every later check | Holds on every probed pair. A test asserts only the `files_changed_mismatch` pair | `test_deliverable_refusal_outranks_files_changed_mismatch`; probe cases A, B and K run again; D to J, P and Q carried from the fourth close |

Three review fixes made before the first close, outside any work unit, are covered by
`TestEarlyRefusalRecovery` (3: re-plan still fires; uncommitted tracked edits count as a
moved tree; an untouched tree still halts) and `TestEarlyRetainedNoteWording` (2).

## Pre-existing tests changed

This fifth close ran no git command and did not repeat the tree comparison. It listed the
files under `tests/`, `specfuse/`, `scripts/`, `.specfuse/scripts/` and `docs/` modified
after the fourth close last wrote `LEARNINGS-pending.md`: only `specfuse/loop/loop.py` and
the feature's own `tests/test_fail_fast_deliverables.py` (the #3613 fix and its three
tests). No pre-existing test is newer. The third and fourth closes did the same kind of
check, each against the close before, back to the second close's comparison, below. These
are modification-time checks, not content diffs. The ten modules were rerun in this
session. In the comparison text, "this session" means the second close.

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
the branch outside any work unit, and the operator re-armed this unit. This fourth close
probed removals on a kept tree and found that deleted and reverted files were missing.

The fourth close (2026-11-26T16:28Z) and the judge recorded `not_met`, and the driver filed
#3613. The fix to `attempt_own_paths` and three tests were made on the branch outside any
work unit, and the operator re-armed this unit. This fifth close confirmed that fix and
probed renames, non-ASCII names and a mode change. #3612, #3613 and the gaps now open are
all in one list, built by filtering a name-only diff; each fix so far covered the cases the
previous close had named.

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
| G1-CLOSE, fifth close | (same line) | not yet recorded | — | — | in progress |
| G1-CLOSE, four recorded closes | 5.00 | 6.35 | 1.84 | 127% | 4 |

Recorded unit spend is 9.03 USD against a plan of 11.00 and a gate budget of 14.00. The
close line is already past its 5.00 plan, and this session's cost and its judge's are
written later. The earlier `blocked_human` stop of this unit recorded 0.00. The independent
review, its fixes, both amendments and the #3612 and #3613 fixes happened outside the loop,
so `events.jsonl` has no cost for them. All four re-closes cost money for questions the
plan or the oracle had left open: two for an unstated precedence, one for the #3612 defect
and this one for #3613.

**T04's warning rate.** Re-measured this session over `done` units with `produces:`: the
shipped rule (path, file name or parent directory) would fire on 35 of 402, **8.7%**, under
the 10% limit. Path or file name alone would fire on 81 of 402, 20.1%. T04 recorded 81 and
35 of 401 in the check's docstring; the population has since grown by one. T04's progress
note does not carry the count that its criterion 3 asked for in the RESULT notes. The
parent-directory match is a plain substring test, so a short directory such as `tests` is
satisfied by almost any body. The WARN is weak for such paths.

## Consumer-visible contract changes

Pending human acknowledgment. Each has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0251`. This close added no fragment; it extended the retry-note one in place
with the kept-tree behaviour and its known limits.

1. **Changed:** the three deliverable refusals run before verification. They take precedence
   over every verification gate and later guard. An attempt that also would have failed one
   is reported as the deliverable refusal. By default its tree is kept, including where the
   old order reset it.
2. **Added:** `defaults.fail_fast_deliverables`, default `true`.
3. **Changed:** the retry note for the three refusals lists the changed paths, at most 20
   plus a count. Untouched edits kept from an earlier attempt are left out; kept files the
   attempt deleted or reverted are listed. Known limits: a renamed tracked file appears
   under its new name only; later changes to a kept non-ASCII-named file and mode-only
   changes to a kept file are not listed.
4. **Added:** a `specfuse lint` WARN for a `produces:` path the unit's body never mentions.

## Notes for the human reviewer

None of these is a failed criterion. This unit may edit none of the files concerned.

- **Older defect, worth its own bug.** A refused attempt that keeps its tree and has a
  changed file with a non-ASCII name stops the driver with `CalledProcessError`:
  `git_diff_names` returns git's quoted form and `git add -N` rejects it (probe R4). The
  fourth close saw the pre-feature `loop.py` do the same. `attempt_own_paths` reads the
  same names (cases R13, R15), so one fix should cover both. This close filed no issue for
  the crash itself; the follow-up entry mentions it.

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
- Early-against-late cases D to J (with the smoke-import line or `close` type), P, Q and N,
  and the other observations listed as not run again.
- Other ways to change a file that the note might miss, such as symlinks (the digest follows
  the link), submodules, a rename under a non-default `diff.renames` setting, or a name
  containing a quote or newline. None was probed.
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
