---
id: FEAT-2026-0007/T02
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Add effort field and wire `claude -p --effort`

**Objective.** WU frontmatter gains an `effort: low|medium|high|xhigh|max`
field; the loop passes the declared value to `claude -p` via `--effort` at
dispatch.

**Context.** This is `FEAT-2026-0007/T02`. `CLAUDE_CMD` lives at
`loop.py:67`; `dispatch()` builds the command from per-WU substitution.
`claude -p --help` confirms `--effort <level>` accepts exactly the five
values `low | medium | high | xhigh | max`. Depends on T01 (so the
`WorkUnit` dataclass already has the model alias change landed). Telemetry
of the `effort_used` field per attempt is Gate 2's T08; here only the
declared-value wire-through. Reference `.specfuse/rules/result-contract.md`
and `never-touch.md`. The driver owns git; edit files only.

**Acceptance criteria.**
1. `WorkUnit` dataclass gains `effort: str = "medium"`.
2. `load_wu` reads `fm.get("effort", "medium")` and raises `ValueError`
   naming the offending value when the field is set to anything outside
   `{low, medium, high, xhigh, max}`.
3. `CLAUDE_CMD` is extended to include `"--effort", "{effort}"`; `dispatch`
   substitutes `{effort}` with `wu.effort` alongside the existing `{model}`
   substitution.
4. `lint_plan.py` validates the `effort` field against the same set when it
   is present (absent is valid; default applies).
5. `WU.template.md`'s frontmatter notes document the `effort:` field, the
   five levels, and the default (`medium`).
6. Two new unit tests in `tests/`: one positive (`effort: low` loads and
   dispatch invoked with `--effort low`); one negative (`effort: xxx`
   raises `ValueError` mentioning the invalid value).

**Do not touch.** Exactly 4 files change: `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py`, `.specfuse/templates/WU.template.md`, and
one new test file under `tests/` (suggested
`tests/test_loop_effort.py`). No edits to: existing WU files under
`.specfuse/features/`, `.specfuse/verification.yml`, binding rules,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`.

**Escalation triggers.** If changing `dispatch()`'s call site to thread the
effort value breaks existing cost-tracking tests' signature contract, stop
and emit `status: blocked` naming the conflict rather than reshaping the
signature silently — same pattern that FEAT-2026-0006/T01 followed.
