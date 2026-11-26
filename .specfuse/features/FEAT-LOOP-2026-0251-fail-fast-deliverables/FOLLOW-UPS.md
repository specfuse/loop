# Follow-ups — FEAT-LOOP-2026-0251

Seventh close, 2026-11-26. No entry is open. The re-run conditions of #3608, #3609, #3610,
#3612, #3613, #3614, #3617, #3618 and #3619 hold.

## Resolved

#### Definition of done clause 5 (arm-time warning)

**Tracked as #3617.** **Re-run condition holds.** The entry's gap was that clause 5 did not
allow the parent-directory match. `GATE-01.md` clause 5 now says the warning is silent when
the body names the path's parent directory, narrowed under `PLAN.md` decision 7. This
close's probe of `check_produces_mentioned` on `specfuse/loop/loop.py`: silent for the full
path, the file name and `specfuse/loop/data/docs` (the entry's case, which contains the
parent `specfuse/loop`); WARN for a body naming none. The entry's silent result is now the
stated behaviour. With the parent directory dropped from the check in a scratch copy,
`TestArmTimeWarning` gives 1 failure.

- command: `PYTHONPATH=. python3 $TMPDIR/close7/p5.py`
- exit: 0

#### Definition of done clause 4 (tree and note)

**Tracked as #3618.** **Re-run condition holds.** On a kept tree, attempt 2 writing only
`docs/events.jsonl`, or only `docs/PROGRESS.md`, now gets that file in its note, with
fail-fast on and off; so do the same names at the repository root and a `docs/WU-T01.md`.
Writing nothing still says "changed no files". Covered by
`test_agent_files_named_like_driver_bookkeeping_are_listed`. With the base-name filter put
back in a scratch copy, `TestTreeAndNote` gives 2 failures. The driver's own three files in
the feature folder are still left out. Git-ignored files are still not listed; the entry did
not name them (see `RETROSPECTIVE.md`).

- command: `PYTHONPATH=. python3 $TMPDIR/close7/p4.py` (uses
  `TestTreeAndNote._second_attempt_note`)
- exit: 0

#### T04#3

**Tracked as #3619.** **Re-run condition holds**, by amendment. T04's RESULT notes still have
not been seen: the driver keeps none for passed attempts. `GATE-01.md` clause 5 ("Measurement
record") accepts the `check_produces_mentioned` docstring and the sixth judge's recount. The
docstring reads 81 and 35 of 401, matching `GATE-01.md`. This close's own recount of `done`
units with `produces:` gave 81 and 35 of 402.

- command: `PYTHONPATH=. python3 $TMPDIR/close7/count.py`
- exit: 0

### Resolved at earlier closes

**Tracked as #3621.**

The text below is as the sixth close wrote it. Its "this close" and "this session" mean the
close named in each entry or the sixth. Where #3614 lists files named like driver bookkeeping
as a limit, #3618 above has since narrowed it.

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

This seventh close reran the oracle (which holds the #3608, #3612, #3613, #3614 and #3618
tests) and the ten modules behind #3609 (68 tests, `OK`). It did not repeat the earlier
mutation for #3612 and #3613 or probe cases D to G. For #3610 the condition is wording in
`GATE-01.md`, the close unit and `docs/methodology.md`; the fifth close found it present.
