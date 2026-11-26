# Follow-ups — FEAT-LOOP-2026-0251

Sixth close, 2026-11-26. No entry is open. The re-run conditions of #3608, #3609, #3610,
#3612, #3613 and #3614 hold.

## Resolved

#### The retry note's path list missed renames, non-ASCII names and mode changes

**Tracked as #3614.** **Re-run condition holds** (first branch). In this close's probe the
note lists the right paths in R9 (both rename names), R10, R11, R13 and R15, and R7 and R14
say nothing changed, with fail-fast on and off. Tests cover each of R9, R10, R11, R13, R15
and R14 with both settings (`test_rename_lists_both_names`,
`test_writing_back_a_renamed_file_lists_it`, `test_mode_only_change_lists_it`, the three
`test_non_ascii_name_*` tests). R7 (a deleted tracked file, then nothing) rests on the probe.
Remaining limits that no entry named (git-ignored files, files named like driver
bookkeeping, non-UTF-8 names, and the older `git add -N` crash) are in `RETROSPECTIVE.md`.

#### A kept file that an attempt deletes or reverts is missing from its retry note

**Tracked as #3613.** **Re-run condition holds** (first branch). The note lists a deleted
kept file, a reverted tracked edit, and a deleted file plus a new one, with fail-fast on and
off (`test_deleting_a_kept_file_lists_it`,
`test_reverting_a_kept_tracked_edit_lists_it`,
`test_deleting_a_kept_file_and_writing_another_lists_both`; probe cases R1, R2, R5). With
the removed-path branch disabled in a scratch copy, `TestTreeAndNote` gives 6 failures. The
condition covers deletes and reverts of ordinary names; other kinds of change were #3614, above.

#### A later attempt's note listed the earlier attempt's kept edits as its own

**Tracked as #3612.** **Re-run condition holds** for the case the entry describes. Attempt 2
writing nothing now gets "this attempt changed no files", and attempt 2 writing another file
gets only that file, with fail-fast on and off
(`test_later_attempt_that_changed_nothing_says_so`,
`test_kept_edits_of_an_earlier_attempt_are_not_listed`,
`test_editing_a_kept_file_again_lists_it`; probe cases R0 and R3). With the filter removed in
a scratch copy, `TestTreeAndNote` gives 4 failures. The entry named no deletion or revert;
that was #3613, below.

#### The early refusal also outranks three other checks, and no precedence is stated for them

**Tracked as #3610.** **Re-run condition holds** (first branch). `GATE-01.md` ("Precedence
when two refusals apply") and the close unit's escalation trigger both state that a
deliverable refusal outranks every check that runs after the agent session, which covers
cases D to G. `docs/methodology.md` states it too, with the kept-tree side effect. The
third close reran D to G with the same results as before, plus controls; see
`RETROSPECTIVE.md` under "Early against late, same input". A test asserts only the
`files_changed_mismatch` pair; the other pairs rest on the probe.

#### An early refusal records a different outcome from the late order for one input

**Tracked as #3608.** **Re-run condition holds.** `GATE-01.md` ("Precedence when two
refusals apply") and the close unit's escalation trigger state that the deliverable refusal
takes precedence over `files_changed_mismatch`.
`test_deliverable_refusal_outranks_files_changed_mismatch` asserts both sides and passed in
this session; the probe's case A agrees.

#### Clause 6 does not hold literally for two pre-existing tests

**Tracked as #3609.** **Re-run condition holds.** `GATE-01.md` clause 6, widened on
2026-11-26, covers edits forced by moving code into a shared helper and by new lint wording.
The ten changed modules pass (68 tests, exit 0), and the two edits are named in
`RETROSPECTIVE.md`.

This sixth close reran the oracle (which holds the #3608, #3612, #3613 and #3614 tests), the
ten modules behind #3609 (68 tests, `OK`) and the unfiltered-list control. For #3610 the
condition is wording in `GATE-01.md`, the close unit and `docs/methodology.md`; the fifth
close found it present, and probe cases D to G were not run again.

### Definition of done clause 5 (arm-time warning)

**Tracked as #3617.**

The clause says lint warns when a `produces:` path appears nowhere in the unit body, by full path or file name. The code also stays silent when the body names only the parent directory.

I tested a `pending` unit with `produces: specfuse/loop/loop.py`. Its body mentioned only `specfuse/loop/data/docs`, so it had neither the full path nor `loop.py`. No WARN was printed. A body naming none of these did warn.

`test_parent_directory_mention_is_silent` asserts this silent behaviour. T04's text allowed narrowing the match, but clause 5 was never amended. Clause 6 and the precedence rule were amended explicitly, and no deliverable is recorded as dropped by amendment.

- command: `PYTHONPATH=. python3 $TMPDIR/p5.py` (calls `lint_plan.check_produces_mentioned` on temporary units; the "dir-only" case printed nothing)
- exit: 0

### Definition of done clause 4 (tree and note)

**Tracked as #3618.**

The clause says the retry note lists the paths this attempt changed, or says it changed none. In a kept tree, I had attempt 2 write only a new `docs/events.jsonl`, and separately only a new `docs/PROGRESS.md`. These are ordinary agent files, not the driver's bookkeeping files.

In both cases the note said "(none — this attempt changed no files)", which is false. This happened with fail-fast both on and off. The control file `docs/plain.md` was listed correctly. The cause is that `format_changed_paths` drops paths by base name only.

- command: `PYTHONPATH=. python3 $TMPDIR/p4.py` (uses `TestTreeAndNote._second_attempt_note`)
- exit: 0

### T04#3

**Tracked as #3619.**

I couldn't verify that T04's RESULT notes gave the measured count and total. I searched the feature's `events.jsonl`, `PROGRESS.md` and `work/` for the figures and found nothing.

The numbers themselves look right. My own count gave 402 `done` units with `produces:`. 81 would warn when matching only path or file name, and 35 when the parent directory also counts. The code docstring says 81 and 35 of 401. That doesn't show what the RESULT notes said.

- command: `grep -rnE "81 of 401|35 \(8\.7|20\.2%" <feature>/events.jsonl <feature>/PROGRESS.md <feature>/work`
- exit: 1
