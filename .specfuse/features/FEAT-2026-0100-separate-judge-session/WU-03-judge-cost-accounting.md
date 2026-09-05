---
id: FEAT-2026-0100/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: fold_judge_usage
produces:
  - specfuse/loop/loop.py
  - tests/test_judge_cost.py
---

# The judge's spend is the close's spend

**Objective.** Fold the judge session's usage envelope into the close WU's
`cost_usd`, `input_tokens`, `output_tokens` and into the close's
`attempt_outcome` event, so cost analysis, the auto-close predicate, and
`/gate-status` see what the verdict actually cost.

**Context.** FEAT-2026-0100/T03; read `PLAN.md`. `judge_close` (T02) returns
the JSON envelope the CLI prints under `--output-format json`; `loop.py`
already harvests `cost_usd`, `input_tokens`, `output_tokens`,
`cache_read_input_tokens`, `cache_creation_input_tokens` from a dispatch
(the block near the `dispatch` parse). Add `fold_judge_usage(attempt_usage, judge_envelope)` and apply it to the close
attempt's usage before `write_cost_to_wu` and before the `attempt_outcome`
event is emitted, and add `judge_cost_usd` to the `judged` event so the two
are separable later. Red test first.

**Acceptance criteria.**

- `tests/test_judge_cost.py::test_close_cost_includes_judge_usage` fails on HEAD and passes after: an injected judge envelope with `cost_usd: 0.42` makes the close WU's frontmatter `cost_usd` and its `attempt_outcome` payload each larger by 0.42 than the same run with the judge disabled.
- `::test_judged_event_carries_judge_cost`: `judge_cost_usd: 0.42` on the `judged` event.
- `::test_judge_without_envelope_adds_nothing`: a runner returning plain text leaves the close's cost unchanged.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `judge.py` (T01); the judge's decision logic (T02); rules,
templates (T04); `lint_plan.py` (T05); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if folding the cost changes
`evaluate_auto_close`'s reading of an existing fixture; name the test.
