# Follow-ups — FEAT-LOOP-2026-0251

Fourth close, 2026-11-26. One entry is open, below. The re-run conditions of #3608, #3609,
#3610 and #3612 hold.

### T03#1 — a kept file that an attempt deletes or reverts is missing from its retry note

**Criterion** (`GATE-01.md`, clause 4): "**Tree and note.** An early refusal keeps or resets
the tree per `defaults.retain_on_guard_refusal`, as the late refusal does; its retry note
states that verification did not run and lists the paths this attempt changed (or says it
changed none)."

**Evidence.** A probe drove `loop.run()` over the oracle's fixture with stubbed dispatch and
`verify` and a kept tree, with `fail_fast_deliverables` both true and false (same results).
It exited 0 and read the path list in the note for attempt 2:

- attempt 1 writes `docs/notes.md`, attempt 2 deletes it: "(none — this attempt changed no
  files)";
- attempt 1 edits tracked `docs/tracked.md`, attempt 2 restores its old content: the same
  "(none)" line;
- attempt 1 writes `docs/notes.md`, attempt 2 deletes it and writes `docs/second.md`: only
  `docs/second.md`.

`python3 -m unittest tests.test_fail_fast_deliverables -b` exits 0 (33 tests); no test
covers these cases. The cause is that `attempt_own_paths` filters the diff the guard judged,
and a removed or restored file has left that diff. The gap is not new with the #3612 fix:
by the code, the earlier listing used the same diff.

**Re-run condition.** Either of these:

- the note lists a kept file the attempt deleted or reverted, and does not say "changed no
  files" in that case, shown by a test for each, with fail-fast on and off. A likely fix:
  also take every path in the attempt-start snapshot that is no longer in the diff and whose
  digest has changed;
- or the operator amends clause 4 to say the list covers only paths still in the diff, and
  the note's "changed no files" wording is changed so that it does not claim more.

The first is recommended: it is a small change, and the current line tells the next session
something false.

## Resolved

#### A later attempt's note listed the earlier attempt's kept edits as its own

**Tracked as #3612.** **Re-run condition holds** for the case the entry describes. Attempt 2
writing nothing now gets "this attempt changed no files", and attempt 2 writing another file
gets only that file, with fail-fast on and off
(`test_later_attempt_that_changed_nothing_says_so`,
`test_kept_edits_of_an_earlier_attempt_are_not_listed`,
`test_editing_a_kept_file_again_lists_it`; probe cases R0 and R3). With the filter removed in
a scratch copy, `TestTreeAndNote` gives 4 failures. The entry named no deletion or revert;
that is the open entry above.

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

The fourth close reran the probes behind #3608 and #3610 and the tests behind #3609; all
three conditions still hold.
