---
id: FEAT-2026-0104/T08
type: implementation
status: draft
attempts: 0
planned_cost_usd: 1.50
produces_driver_helper:
  - persist_attempt_notes
produces:
  - tests/test_replan_note_collision.py
---

# Stop the re-plan transcript overwriting the attempt it re-planned

**Objective.** Keep both records for the re-planned attempt — the failure
that triggered the re-plan and the re-plan turn's transcript — so the brief's
evidence trail has no hole in it.

**Context.** FEAT-2026-0104/T08. Found by `G1-PLAN`'s probe, not by a failing
test. `persist_attempt_notes` (`loop.py:3383`) writes one
`work/<wu>/attempt-N.md` per buffered entry, and attempt N is buffered
**twice** on a re-planned attempt: the failure evidence at `loop.py:10558`
and the re-plan transcript at `loop.py:10820`. The second write clobbers the
first. Measured on a real `loop.run()` spin-out with `max_attempts: 3`:
`attempt-1.md` 757 bytes, `attempt-2.md` **59 bytes** (transcript only),
`attempt-3.md` 3491 bytes — attempt 2's failure evidence is not on disk
anywhere. This is gate 2's business because the brief T06 renders points the
operator at those files; a brief that cites a record with a hole in it is
worse than one that cites nothing. The evidence survives in memory in
`replan_history` and in the attempt's `attempt_outcome` event, so this is a
persistence bug, not a data-loss bug.

**Acceptance criteria.**

- `tests/test_replan_note_collision.py` fails on HEAD before this unit's
  edits and passes after.
- After a real `loop.run()` that re-plans a unit and then exhausts its
  attempts, the failure evidence for the re-planned attempt and that
  attempt's re-plan transcript are **both** readable on disk, in files whose
  names say which is which.
- Every persisted attempt note is named in the escalation's bookkeeping
  commit, as `persist_attempt_notes`' return value already guarantees for the
  paths it writes — a new path that is not committed is not evidence.
- No attempt note that exists today changes name: an unre-planned attempt
  still writes `work/<wu>/attempt-N.md`.

**Do not touch.** The re-plan trigger, `run_replan_turn`, and the buffering
at `loop.py:10558` and `loop.py:10820` — the entries are correct, only the
write is. `format_spinout_escalation_brief` and its tests (T06, T07).

**Verification.** Narrow tier for `implementation`: the `code` gates minus
`tier: broad`, plus
`python3 -m unittest tests.test_replan_note_collision tests.test_replan_end_to_end -v -b`
— gate 1's oracle must stay green. Run the full suite before reporting
complete: `persist_attempt_notes` is on both escalation paths.

**Escalation triggers.** Stop with `status: blocked` if keeping both records
requires changing what the escalation commit stages, rather than only what
`persist_attempt_notes` writes — that widens into the bookkeeping-commit path
and is a different unit.
