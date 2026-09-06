---
id: FEAT-2026-0100/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 7.00
model: opus
effort: high
oracle_env: macos_local
produces_driver_helper: judge_close
produces:
  - specfuse/loop/loop.py
  - tests/test_judge_close_path.py
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-06T00:09:14.444616+00:00
duration_seconds: 2480.602
cost_usd: 8.729707
input_tokens: 176
output_tokens: 61946
---

# The driver dispatches the judge after the close's guards and honours only a lowered verdict

**Objective.** In the close path, after `assert_closing_deliverables` passes
and before the verdict is re-read for the terminal flips, dispatch the judge
with T01's bundle, write its verdict into the close WU's frontmatter when it
is lower than the close's own, write `FOLLOW-UPS.md` from its findings, and
emit a `judged` event carrying both verdicts.

**Context.** FEAT-2026-0100/T02; read `PLAN.md`. The close's verdict is
re-read at the terminal-flip site (`loop.py`, the `wu.type == "close"` branch
that calls `verdict_permits_terminal_flips`); `judge_close(wu, feature_dir,
repo_root, *, runner)` runs immediately before that re-read. Diff text:
`git diff <gate-start-sha>..HEAD` where the gate start is the baseline sha in
`GATE-NN.md` (fall back to the feature branch's merge-base with the
integration branch), capped to the failure-note limit with `--stat` always
included in full. Dispatch through the same argv builder `dispatch` uses
(model `sonnet`, effort `medium`, `--output-format json`) with a wall-clock
timeout of 15 minutes via the runner; a timeout or unparseable result leaves
the close's verdict standing and records `judge_verdict: null` with a reason.
Rules: judge `not_met` over close `met` lowers the verdict and writes
`FOLLOW-UPS.md` from the findings (one `### ` per finding, judge's words);
judge `met` over close `not_met` changes nothing. PLAN frontmatter
`judge_disabled: true` skips the dispatch with a printed notice. Terminal
closes only. Red test first, through `run()` with a patched dispatcher as
`tests/test_terminal_flips.py` does.

**Acceptance criteria.**

- `tests/test_judge_close_path.py::test_judge_lowers_met_to_not_met_and_writes_followups` fails on HEAD and passes after: a close session writing `met` plus an injected judge answering `not_met` with two findings leaves `verdict: not_met` on disk, two `FOLLOW-UPS.md` entries, gate `awaiting_review`, roadmap row `active`, and a `judged` event with both verdicts.
- `::test_judge_cannot_raise_not_met`: close `not_met`, judge `met` → verdict stays `not_met`, event records the disagreement.
- `::test_judge_agreeing_met_lets_flips_fire`: both `met` → PLAN `done`, gate `passed`.
- `::test_judge_timeout_or_garbage_leaves_close_verdict`: `judge_verdict: null` with reason; no crash; flips follow the close's verdict.
- `::test_judge_disabled_skips_dispatch`: the judge runner is never called; notice printed.
- `::test_judge_prompt_excludes_close_prose`: the prompt handed to the judge runner contains the criteria and diff and not the retrospective's `## Verdict` section.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `judge.py`'s pure functions (T01; call them); cost fields
(T03); `lint_plan.py` (T05); rules, templates, skills (T04); `arm_eval.py`;
`.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.loop.loop import judge_close"` exits 0.

**Escalation triggers.** Emit `status: blocked` if the gate-start sha cannot
be determined from `GATE-NN.md`'s baseline block or the merge-base on this
repository's own features; name which, do not diff against an arbitrary
commit.
