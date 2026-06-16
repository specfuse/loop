---
id: FEAT-2026-0022/T01
type: implementation
model: opus
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
produces_driver_helper: produces
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Add the `produces:` WU frontmatter field

**Objective.** Introduce a new optional WU frontmatter field `produces:` —
a string or list of strings naming the deliverable file path(s) the WU is
contracted to yield — parsed by `load_wu` onto a new `WorkUnit.produces`
attribute, with an advisory lint WARN when an `implementation` WU declares
none, and a reference entry in `WU.template.md`.

**Context.** This is `FEAT-2026-0022/T01`, the field that the T02 presence
gate consumes. `produces:` is distinct from two existing fields:

- `files_changed` (RESULT block, `loop.py` `verify_files_changed` at
  `loop.py:957`) is the agent's **post-hoc runtime claim** of what it touched,
  checked against the git diff. `produces:` is the **author-declared contract**
  set at WU-draft time, checked against disk existence by T02.
- `produces_driver_helper` (FEAT-2026-0017, parsed at `loop.py:302`) names
  driver **symbols** for a lint WARN only; it is never machine-enforced.
  `produces:` names **files** and IS machine-enforced (by T02).

Parse it exactly like `produces_driver_helper` (string → one-element list;
list → as-is; anything else → `ValueError`). The `WorkUnit` dataclass is at
`loop.py:133`; `produces_driver_helper` is the last field (`loop.py:153`) and
its parse block is `loop.py:302–313`, returned at `loop.py:328`. The lint WARN
pattern to mirror is the `produces_driver_helper` WARN at
`.specfuse/scripts/lint_plan.py:384–392`.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_produces_field.py::test_load_wu_parses_produces_list` builds a
   minimal WU with `produces: ["a.md", "b.md"]` in frontmatter and asserts
   `load_wu(...).produces == ["a.md", "b.md"]`. This **fails on HEAD** because
   `WorkUnit` has no `produces` attribute (`AttributeError`).
2. `WorkUnit` (loop.py:133) gains `produces: list[str] = field(default_factory=list)`.
3. `load_wu` parses `produces:` from frontmatter mirroring
   `produces_driver_helper` (loop.py:302–313): `None`/absent → `[]`; a bare
   string → one-element list; a list → as-is; any other type raises
   `ValueError` naming the field and the offending type. The parsed value is
   passed to the `WorkUnit(...)` constructor (loop.py:328).
4. After the edits, `test_load_wu_parses_produces_list` **passes**, plus:
   `test_load_wu_produces_accepts_bare_string` (`produces: a.md` →
   `["a.md"]`), `test_load_wu_produces_absent_is_empty` (no field → `[]`),
   and `test_load_wu_produces_rejects_non_string` (`produces: 5` → `ValueError`).
5. `lint(feature_dir)` in `lint_plan.py` emits a non-blocking
   `WARN: <wu>: implementation WU declares no 'produces:' deliverable list`
   for an `implementation`-type WU whose `produces:` is absent or empty. The
   WARN never raises and never appends to the errors list (exit code stays 0),
   matching the `produces_driver_helper` WARN's posture. Closing-type WUs
   (`close`, `close-intermediate`, `plan-next`, `retrospective`, `lessons`,
   `docs`) are exempt. Tested by
   `test_produces_field.py::test_lint_warns_on_missing_produces` and
   `::test_lint_silent_when_produces_declared`.
6. `WU.template.md` gains a `produces` entry in its frontmatter-notes block,
   stating: optional; string or list of file paths the WU is contracted to
   produce; each must exist and be non-empty at completion or the driver
   blocks the WU (T02); distinct from `files_changed` (runtime claim) and
   `produces_driver_helper` (driver symbols, lint-only). Cross-reference
   FEAT-2026-0022.
7. **Existence check.** `python3 -c "from loop import WorkUnit; WorkUnit.produces"`
   is not meaningful on a dataclass default; instead assert via AC 1's test that
   a loaded WU exposes `.produces`. No separate smoke import needed beyond the
   red→green test.

**Do not touch.** Exactly these files change: `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py`, `.specfuse/templates/WU.template.md`, and one
new test file `tests/test_produces_field.py`. Do NOT wire any presence
enforcement into the acceptance path — that is T02's job; this WU only adds the
field, its parse, the advisory WARN, and the doc entry. Do NOT touch existing WU
files, `.specfuse/verification.yml`, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
lint, security, coverage ≥ 90%), plus the red→green proof in AC 1 and 4.

**Escalation triggers.**
1. **Completeness.** If `WorkUnit` has no `produces` attribute or `load_wu`
   does not populate it after your edits, emit `status: blocked` — do not claim
   complete.
2. **Scope leak.** If you find yourself editing the acceptance path in `loop.py`
   (around the `outcome == "passed"` branch, ~loop.py:2715) to enforce presence,
   stop and emit `status: blocked` — that enforcement belongs to T02; T01 ends
   at the field, its parse, the WARN, and the doc.
3. **Spec ambiguity.** If the `produces_driver_helper` parse block has changed
   shape from the line references above (code evolves), locate the current
   block by symbol and mirror it; do not invent a different parse contract.
