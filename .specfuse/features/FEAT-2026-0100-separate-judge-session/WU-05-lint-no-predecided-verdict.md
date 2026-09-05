---
id: FEAT-2026-0100/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: lint_close_verdict_not_predecided
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_close_verdict_not_predecided.py
---

# Lint: a close that is told its verdict in advance is refused at arm time

**Objective.** Add `lint_close_verdict_not_predecided` to `lint_plan.py`: a
`close` WU body that instructs the session to write a specific verdict is
ERROR on `pending`/`ready`, WARN on `draft`, skipped on `done`.

**Context.** FEAT-2026-0100/T05; read `PLAN.md` § Escalation-predicate
satisfiability. FEAT-2026-0082's close body said "The verdict is hedged, and
this is the finding it exists to record"; the judge makes that shape
meaningless and the lint makes it visible. Patterns, in the body outside code
fences: `verdict: met`, `verdict: not_met`, `verdict is met`, `record met`,
`the verdict is`, `write met`, `write not_met`, case-insensitive, plus the
retired `met_locally` / `partially_met` / `hedged verdict`. A sentence that
says how the verdict is decided ("the judge writes the verdict") is not a
match. Reuse `_slice_section` and the WARN/ERROR plumbing the observability
lint (0084/T03) added. Fixtures copied from the shipped close template. Red
test first.

**Acceptance criteria.**

- `tests/test_lint_close_verdict_not_predecided.py::test_pending_close_naming_its_verdict_is_error` fails on HEAD and passes after.
- `::test_draft_is_warn_and_done_is_skipped`.
- `::test_describing_the_mechanism_is_not_a_match`: a body containing "the judge writes the verdict; measure, do not decide" yields nothing.
- `python3 -m specfuse.loop.lint_plan` over every folder under `.specfuse/features/` reports zero ERROR from this rule; the command and count appear in the RESULT block.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `lint_ac_observable` and `lint_gate_proportionality`;
`loop.py`; rules and templates (T04); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.loop.lint_plan import lint_close_verdict_not_predecided"` exits 0.

**Escalation triggers.** Emit `status: blocked` if the corpus sweep reports
an ERROR on a non-`done` close; paste the sentence, do not widen the skip.
