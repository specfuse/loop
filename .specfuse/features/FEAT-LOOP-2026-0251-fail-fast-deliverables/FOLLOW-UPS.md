# Follow-ups — FEAT-LOOP-2026-0251

Third close, 2026-11-26. No entry is open. All three re-run conditions hold. Two wording
gaps that are not failed criteria are in `RETROSPECTIVE.md` under "Notes for the human
reviewer".

## Resolved

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

### T03#1

**Tracked as #3612.**

An attempt that changed nothing does not always say so. Under the default `retain_on_guard_refusal` (tree kept), attempt 1 writes `docs/notes.md` and is refused `produces_not_in_diff`. Attempt 2 writes nothing, yet its refusal note reads "Paths this attempt changed: - `docs/notes.md`" and not "this attempt changed no files". The list includes the retained edits of the earlier attempt, so definition-of-done clause 4 ("lists the paths this attempt changed, or says it changed none") does not hold. The same happens with `fail_fast_deliverables: false`. `test_attempt_that_changed_nothing_says_so` covers only a first attempt.

- command: `HOME="$TMPDIR/judgehome" PYTHONPATH="$PWD:$TMPDIR/probe" python3 "$TMPDIR/probe/p.py"` (probe calls loop.run() with stubbed dispatch and verify, and prints each refusal note's path list; for both fail_fast True and False, attempt 2 printed `docs/notes.md`)
- exit: 0
