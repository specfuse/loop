---
id: FEAT-2026-0106/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - tests/test_progress_forward_note.py
---

# Let a session say what the next unit should know

**Objective.** Add one optional RESULT field carrying the forward-looking half
of a progress note, and render it into `PROGRESS.md` when present.

**Context.** FEAT-2026-0106/T02. T01 writes what a unit *changed*, taken from
`summary`, which the result contract defines as backward-looking. The value
this feature claims is the other half — what surprised the session, what the
next unit should know — and only the session knows it. This lands as an
**optional** field on an interface that already exists rather than as an
append instruction in every work unit body: an append obligation enforced by a
guard is exactly what produced a 232-entry `LEARNINGS.md` that no dispatched
session reads (#3272).

Optional is load-bearing. If agents do not reliably fill it, this degrades to
T01's behaviour and `PROGRESS.md` is still written — which is why T01 measures
the `summary` emission rate before this unit is drafted against it.

**Acceptance criteria.**

- `python3 -m unittest tests.test_progress_forward_note -v -b` fails on HEAD
  before this unit's edits and passes after.
- A RESULT block carrying the new field produces a `PROGRESS.md` entry
  containing that text; a RESULT block without it produces the same entry T01
  produced, byte-for-byte. The absent-field path is asserted directly, because
  it is the one every existing project takes until they adopt the field.
- `.specfuse/rules/result-contract.md` documents the field as optional, in the
  same shape as its neighbours, and says plainly what happens when it is
  absent.
- The field is never required by any guard, and no gate fails for its absence
  — asserted by driving a full gate whose units emit no such field and
  observing a clean close.

**Do not touch.** `judge.py`. `closing_requirements.py` (T03's). The
`summary` field's own meaning or its parsing — this adds a field beside it
rather than redefining it. The sibling WU files in this gate.

**Verification.** Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_progress_forward_note tests.test_progress_lines_end_to_end -v -b`
— T01's oracle must stay green with the field both present and absent. Run the
full suite before reporting complete, for the same reason T01 does.

**Escalation triggers.** Stop with `status: blocked` if T01's recorded
`summary` emission rate says agents rarely emit RESULT fields at all — that
makes this unit's premise false, and the right response is a human deciding
whether to build it, not this session building it anyway.
