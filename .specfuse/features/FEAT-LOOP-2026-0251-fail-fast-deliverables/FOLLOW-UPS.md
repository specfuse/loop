# Follow-ups — FEAT-LOOP-2026-0251

Fifth close, 2026-11-26. One entry is open, below. The re-run conditions of #3608, #3609,
#3610, #3612 and #3613 hold.

### T03#1 — the retry note's path list still misses renames, non-ASCII names and mode changes

**Tracked as #3614.**

**Criterion** (`GATE-01.md`, clause 4): "**Tree and note.** An early refusal keeps or resets
the tree per `defaults.retain_on_guard_refusal`, as the late refusal does; its retry note
states that verification did not run and lists the paths this attempt changed (or says it
changed none)."

**In plain words.** After a refused attempt, the next session is told which files the last
one changed. For some kinds of change that list is incomplete, and sometimes it says
nothing changed when something did. Which attempts are refused is not affected.

**Evidence.** A probe drove `loop.run()` through the oracle's `_second_attempt_note` helper
(kept tree, stubbed dispatch and `verify`), with fail-fast on and off (same results), and
read the path list in the note for attempt 2:

- R9: attempt 2 renames a tracked file: only the new name is listed. A first attempt with a
  reset tree does the same.
- R10: attempt 1 renames a tracked file, attempt 2 writes the old name back: "(none — this
  attempt changed no files)".
- R11: attempt 2 only makes a kept new file executable: the same "(none)" line.
- R13: attempts 1 and 2 both edit tracked `docs/café.md`: "(none)".
- R15: attempt 2 restores that file: "(none)".

`python3 -m unittest tests.test_fail_fast_deliverables -b` exits 0 (36 tests); no test
covers these cases. With `attempt_own_paths` returning its input unchanged, R10, R11 and
R13 list a path, so the filter added for #3612 drops them. Causes: git's rename detection
reports only the new name; git returns non-ASCII names quoted, so `_path_digest` returns
`None` both times; the digest covers content only. The same quoted names make
`git add -N` crash the driver on a new non-ASCII file in a kept tree (probe R4; the fourth
close saw the pre-feature driver do the same).

**Why the loop did not fix it.** This close may not edit source files.

**Options.**

1. Fix the way the list is built. Record each path's state (content and mode) at the start
   and end of the attempt, with names read by `git diff --no-renames --name-only -z` and
   `git ls-files -z`, and list every path in either set whose state differs.
   For: covers all five cases at once, and the same `-z` reading can fix the crash.
   Against: more code on a judge surface, and another re-close (the four recorded closes
   cost 6.35 USD).
2. Amend clause 4 to say the list is best-effort and name these limits, and change the
   "this attempt changed no files" line so that it does not claim certainty.
   For: small; the list only informs the next session. Against: the definition of done is
   narrowed a third time on this gate, the wording change is still a source edit, and the
   crash stays.

**Recommendation:** option 1. The last two fixes each covered only the cases named so far;
comparing start and end states removes the dependence on the filtered diff.

**Re-run condition.** Either of these:

- the note lists the right paths in R9 (both names), R10, R11, R13 and R15, each shown by a
  test with fail-fast on and off, and R7 and R14 still say nothing changed;
- or the operator amends clause 4 as in option 2 and the "changed no files" wording is
  changed to match.

## Resolved

#### A kept file that an attempt deletes or reverts is missing from its retry note

**Tracked as #3613.** **Re-run condition holds** (first branch). The note lists a deleted
kept file, a reverted tracked edit, and a deleted file plus a new one, with fail-fast on and
off (`test_deleting_a_kept_file_lists_it`,
`test_reverting_a_kept_tracked_edit_lists_it`,
`test_deleting_a_kept_file_and_writing_another_lists_both`; probe cases R1, R2, R5). With
the removed-path branch disabled in a scratch copy, `TestTreeAndNote` gives 6 failures. The
condition covers deletes and reverts of ordinary names; other kinds of change are the open
entry above.

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

This fifth close reran the oracle (which holds the #3608 and #3612 tests), the ten modules
behind #3609 (68 tests, `OK`) and the removed-filter control. For #3610 the condition is the
wording in `GATE-01.md`, the close unit and `docs/methodology.md`, which is present; probe
cases D to G were not run again.
