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
