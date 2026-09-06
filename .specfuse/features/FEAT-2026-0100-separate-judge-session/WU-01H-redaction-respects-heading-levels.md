---
id: FEAT-2026-0100/T01H
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
model: sonnet
effort: medium
oracle_env: macos_local
provenance: "G1-CLOSE attempt 1 (2026-09-06), FOLLOW-UPS.md entry 3 and the judged event's finding: strip_forbidden_sections closes a redacted run at the next heading of any level, so ### children of ## Retrospective re-open it and 100% of that section's lines reached the judge"
produces:
  - specfuse/loop/judge.py
  - tests/test_judge_module.py
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-06T15:57:03.734752+00:00
duration_seconds: 1474.697
cost_usd: 0.680552
input_tokens: 66
output_tokens: 7495
---

# Hygiene: a redacted section stays redacted through its own subsections

**Objective.** `strip_forbidden_sections` (`specfuse/loop/judge.py:135`) must
close a redacted run only at a heading of the same or higher level as the
heading that opened it. Today a `###` child of `## Retrospective` closes the
run, so every recent close's retrospective prose reaches the judge in full.

**Context.** FEAT-2026-0100/T01H, hygiene precursor to the close's re-run.
Measured by the close's first attempt on this feature's own `RETROSPECTIVE.md`
rendered as a `+`-prefixed diff hunk (the form `capture_gate_diff` hands to
`build_judge_bundle`): `## Verdict` with no subheadings lost 100% of its lines,
`## Retrospective` with `###` subsections lost 0%. Track the opening heading's
level; a heading at a deeper level continues the run, a heading at the same or
shallower level ends it. Handle both bare markdown lines and `+`-prefixed diff
lines, as the function already does for the opening heading. Red test first,
with a fixture that has `###` children under both forbidden sections and a
sibling `##` after them that must survive.

**Acceptance criteria.**

- `tests/test_judge_module.py::test_forbidden_section_with_subheadings_is_fully_stripped` fails on HEAD and passes after: zero non-blank lines of `## Retrospective` and its `###` children survive; the following `## Cost analysis` section survives in full.
- `::test_forbidden_section_in_diff_hunk_form_is_fully_stripped`: same fixture as `+`-prefixed lines.
- The existing `test_bundle_contains_dod_criteria_diff_and_measurements_only` passes unchanged.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `build_judge_bundle`'s inputs, `parse_judge_result`,
`loop.py` (T02H owns the gate-start sha); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if the heading-level rule
cannot be applied without changing which sections the existing tests expect
to survive; name the test.
