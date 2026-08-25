---
id: FEAT-2026-0082/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: emit_issue_with_body
produces:
  - specfuse/loop/escalation.py
  - tests/test_emit_issue_with_body.py
model: sonnet
effort: medium
---

# One idempotent issue emitter that takes a body somebody else rendered

**Objective.** Add `emit_issue_with_body` to `specfuse/loop/escalation.py`: file
a GitHub issue from a pre-rendered body under a caller-supplied label set,
idempotent on a correlation marker, reusing the find-then-create seam that module
already ships — so the question-issue poster (T02) does not grow a second copy of
it.

**Context.** First WU of FEAT-2026-0082; read `PLAN.md` in this folder for the
scope boundary and the existing-mechanism verdict. This unit ships a seam; T02 is
its first caller.

**Almost all of this exists. Read it before writing.** `escalation.py` already
carries `_find_existing_issue`, `_correlation_marker`, `_extract_issue_number`,
`_default_runner` and `CREATED_NUMBER_UNKNOWN`. `emit_escalation`'s docstring
states the property to preserve:

> Idempotent: searches for an open issue carrying the ``needs-human`` label and
> this correlation ID's marker before creating; a second call for the same
> ``correlation_id`` returns the existing issue's identifier instead of filing a
> duplicate.

What `emit_escalation` cannot do is accept a body it did not render — it calls
`render_escalation_body` itself. That is the entire gap. Three hard-won
behaviours in that module must hold in the new function too, and each cost a
real defect to learn: the assignee flag is **omitted** rather than passed empty
(#1762 — an unassignable placeholder made `gh issue create` exit 1 and the whole
escalation was lost); the runner is called with `check=False` and a raising
runner is caught (#2170 — a reporting failure must never destroy the run it
reports on); and a created issue whose number could not be parsed is **not** the
same as an uncreated one.

**Refactor `emit_escalation` onto the new function rather than leaving two
paths** — but only if its observable behaviour is unchanged. It has a live caller
(`specfuse/agent/run.py:293`) and shipped tests. If the refactor cannot be done
without changing what that caller sees, leave `emit_escalation` alone and say so
in your RESULT; two paths is a worse outcome than a stated deferral, but a broken
caller is worse than both.

**Note for a later reader.** FEAT-2026-0052/T03 (merged, unarmed) was drafted to
add `emit_tracking_issue` as a sibling and has since been told to call this
function instead if it exists. Do not add `emit_tracking_issue` here — that is
0052's unit, not this one.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`) apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_emit_issue_with_body.py::test_second_call_same_marker_files_no_duplicate`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). Two calls with the same correlation ID file one issue; the second
  returns the first's identifier. Driven through an injected runner, no live `gh`.
- After this WU's edits that same test passes, and so does
  `tests/test_emit_issue_with_body.py::test_body_is_passed_through_verbatim` —
  the body handed to the function is the body handed to `gh issue create`,
  byte-for-byte. A poster whose body gets rewritten cannot carry the
  `<!-- specfuse:question id=... -->` markers a reply is bound by.
- The label set is caller-supplied and **not** forced to `needs-human`. A test
  passes a label set omitting it and asserts the runner's argv omits it too.
  T02 supplies its own labels; a function that hardcodes them cannot serve both
  callers.
- `emit_issue_with_body` is importable: `python3 -c "from
  specfuse.loop.escalation import emit_issue_with_body"` exits 0.
- The three preserved behaviours each have a test: an empty/whitespace assignee
  **omits** the flag rather than passing `--assignee ""`; a non-zero `gh` exit
  returns the not-filed value and raises nothing; a raising runner is caught and
  returns the not-filed value.
- A created-but-unparseable result returns `CREATED_NUMBER_UNKNOWN`, distinct
  from the not-filed value. A test asserts the two are not equal — conflating
  them sends an operator looking for an issue that exists, or fails to.
- `emit_escalation`'s observable behaviour is unchanged: its existing tests pass
  untouched, whether or not you refactored it onto this function. State in your
  RESULT which you did.
- Every new `subprocess.run` declares `check=` explicitly (`PLW1510`).

**Do not touch.** `render_escalation_body`, `annotate_escalation`,
`NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`; `specfuse/agent/` (T02 and T03 own the
callers); `specfuse/loop/labels.py`. `.git/`, secrets. The driver owns git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests, lint,
security, coverage ≥ 90%, leak-scan, the bats suites) plus the symbol-import
check above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if refactoring `emit_escalation`
onto this function changes anything its live caller in `specfuse/agent/run.py`
observes — that caller is the autonomous agent's only escalation path, and
silently altering it while adding a helper is not a trade this WU may make. If
`emit_issue_with_body` is absent from the files you edited, emit
`status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
