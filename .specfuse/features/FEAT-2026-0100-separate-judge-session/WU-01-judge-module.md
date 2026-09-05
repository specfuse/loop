---
id: FEAT-2026-0100/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
produces_driver_helper: build_judge_bundle, parse_judge_result
produces:
  - specfuse/loop/judge.py
  - tests/test_judge_module.py
---

# The judge module: evidence bundle in, verdict out, nothing else

**Objective.** Add `specfuse/loop/judge.py` with three pure pieces: an
evidence bundle builder, a prompt renderer, and a RESULT parser. No dispatch,
no file writes, no driver state; T02 wires it.

**Context.** FEAT-2026-0100/T01; read `PLAN.md` § Existing-mechanism search.
`build_judge_bundle(feature_dir, gate_number, *, diff_text, measurements)`
collects: the gate's `## Definition of done` section from `GATE-NN.md`, the
entries of `GATE-NN-CRITERIA.md` via `criteria_state.parse_criteria_state`
(absent file yields an empty list, not an error), the diff text the caller
captured, and the close's `## Measurements` section text. `render_judge_prompt
(bundle)` produces the session prompt: it states the judge's job — decide
`met` or `not_met` from the evidence, re-run any oracle a criterion names,
report one `### <criterion>` finding per failure with the command and its
exit — and forbids reading `RETROSPECTIVE.md`'s `## Verdict` or
`## Retrospective` sections. `parse_judge_result(text) -> JudgeResult(verdict,
findings, raw)` reads a `result` block with `verdict: met | not_met` and the
findings; anything else yields `verdict=None` and a `reason`. Pure functions
with fixture inputs; the judge's escapes and truncation follow
`_yaml_double_quote` and the 8,000-character failure-note cap already in
`loop.py`. Red test first.

**Acceptance criteria.**

- `tests/test_judge_module.py::test_bundle_contains_dod_criteria_diff_and_measurements_only` fails on HEAD (module absent) and passes after: the rendered prompt contains the four evidence pieces and contains neither the string `## Verdict` nor `## Retrospective` when those sections exist in the fixture retrospective.
- `tests/test_judge_module.py::test_parse_met_and_not_met_with_findings`: a `not_met` block with two `### ` findings yields two findings with their text verbatim.
- `tests/test_judge_module.py::test_unparseable_output_yields_none_with_reason` for empty output, a block with `verdict: partially_met`, and prose with no block.
- `tests/test_judge_module.py::test_missing_criteria_artifact_is_an_empty_list_not_an_error`.
- `python3 -c "from specfuse.loop.judge import build_judge_bundle, render_judge_prompt, parse_judge_result"` exits 0.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `specfuse/loop/loop.py` (T02, T03); `criteria_state.py`;
`lint_plan.py` (T05); rules, templates, skills (T04); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
import check above.

**Escalation triggers.** Emit `status: blocked` if `GATE-NN-CRITERIA.md`'s
parser cannot be reused without changing its output for existing fixtures;
name the fixture rather than forking the parser.
