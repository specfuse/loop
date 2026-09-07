---
id: FEAT-2026-0100/T01H2
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
model: sonnet
effort: medium
oracle_env: macos_local
provenance: "G1-CLOSE attempt 2 (2026-09-06), the judge's second finding: slice_wu_section ended `## Measurements` at a `### Failure-class breakdown` child, so the judge's bundle carried 62 of the section's 87 non-blank lines"
produces:
  - specfuse/loop/_wu_sections.py
  - tests/test_judge_module.py
---

# Hygiene: slicing a `##` section ends at the next `##`, not at its own `###` children

**Objective.** `slice_wu_section` (`specfuse/loop/_wu_sections.py`) returns
the text between a named heading and the next heading of any level. A `##`
section that contains `###` subsections is therefore cut at its first child.
The judge's evidence bundle slices `## Measurements` with it and lost 25 of 87
lines on this feature's own close. End a section only at a heading of the
same or shallower level, the rule T01H applied to the redactor.

**Context.** FEAT-2026-0100/T01H2, hygiene precursor to the close's third
attempt. The slicer serves the WU-body five-section contract too (`**Context.**`
bold-preamble form and ATX form both), so the change must keep every existing
caller's result for bodies with no nested headings: the level rule only
changes behaviour when a deeper heading follows the opened one. Red test first
with a fixture shaped like this feature's retrospective: `## Measurements`,
a `### Failure-class breakdown` child, then `## Retrospective`.

**Acceptance criteria.**

- `tests/test_judge_module.py::test_measurements_section_with_child_headings_is_captured_whole` fails on HEAD and passes after: every non-blank line of `## Measurements` including its `###` child survives into the bundle, and the first line of `## Retrospective` does not.
- `tests/test_lint_boundary_extraction.py` and every other existing test that calls `slice_wu_section` passes unchanged.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `strip_forbidden_sections` (T01H); `loop.py` (T02H2);
`.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if an existing caller relies
on the any-level cut (a test asserts a `###` child is excluded); name it.
