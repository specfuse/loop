---
id: FEAT-2026-0057/T02
type: implementation
status: done
attempts: 2
planned_cost_usd: 3.50
oracle_env: macos_local
generated_surfaces: []
produces:
  - specfuse/loop/prerun_capture.py
  - tests/test_prerun_capture.py
produces_driver_helper:
  - format_oracle_capture
  - ORACLE_CAPTURE_BUDGET_BYTES
duration_seconds: 1177.004
cost_usd: 1.673048
input_tokens: 70
output_tokens: 26110
---

# Bound the captured oracle output and inject it into the session prompt

**Objective.** Turn the oracle results captured by T01 into a bounded prompt
section whose verdict survives truncation.

**Context.** Correlation ID `FEAT-2026-0057/T02`, the second substantive unit in
this feature's only gate. It depends on `FEAT-2026-0057/T01`, which is `done` by
the time you run: `specfuse/loop/prerun.py` exists and `run_pre_dispatch` returns
oracle results carrying name, ok flag, and captured output. Read `PLAN.md` in this
folder for framing and the scope boundary.

Injecting raw oracle output into a prompt is not safe by default. A real oracle —
a scenario matrix, a full generator suite — emits far more than a session should
be handed, so the output needs a budget. The naive way to enforce a budget is a
positional tail, and that is precisely the defect FEAT-2026-0068 fixed for gate
failure reports: for this repository's `tests` and `coverage` gates, the last
fifteen lines reliably contained no verdict at all. Reusing that feature's
selection logic rather than writing a second truncation policy is the point of
this unit.

The grounding files:

- `specfuse/loop/prerun.py` — T01's runner and the shape of the results you
  format.
- `specfuse/loop/loop.py:2715` — `select_gate_report_lines(out, window=N)`,
  FEAT-2026-0068's verdict-aware selection. You **call** it; you do not change it.
  Read its docstring for what it treats as a verdict line.
- `specfuse/loop/loop.py:2819` — how `_run_gate_set` already uses it at
  `window=15`, for the precedent on call shape.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/correlation-ids.md`. See
`.specfuse/skills/verification/SKILL.md` for running and interpreting gates.

**Acceptance criteria.**

1. `tests/test_prerun_capture.py::TestCapture::test_verdict_survives_truncation`
   exists and **fails on HEAD before this work unit runs** — the file does not yet
   exist, which counts as red. Scoped run:
   `python3 -m unittest tests.test_prerun_capture.TestCapture.test_verdict_survives_truncation`.
2. `format_oracle_capture(results)` returns a section whose total size in bytes is
   less than or equal to `ORACLE_CAPTURE_BUDGET_BYTES`, for any input including
   one whose raw output is many multiples of the budget.
3. When an oracle's output exceeds its share of the budget, the retained lines are
   selected via `select_gate_report_lines`, so a verdict line near the top of the
   output survives while the middle is dropped. A positional tail fails this
   criterion: a test whose oracle emits a verdict first and 500 lines of noise
   after must still show the verdict.
4. Truncation is stated in the returned section by an explicit marker naming the
   number of bytes dropped. Silent truncation fails this criterion.
5. The formatted section is appended to the work-unit body handed to the session,
   and a work unit with no `oracles` receives no section and no marker.
6. The test named in criterion 1 **passes after this work unit's edits**
   (`python3 -m unittest tests.test_prerun_capture.TestCapture.test_verdict_survives_truncation`
   exits zero).
7. `python3 -c "from specfuse.loop.prerun_capture import format_oracle_capture, ORACLE_CAPTURE_BUDGET_BYTES"`
   exits zero.

**Do not touch.**

- `select_gate_report_lines` itself, and `_run_gate_set` / `verify()` in
  `specfuse/loop/loop.py`. You call the first and leave the rest alone; exit-time
  verification is out of scope for this feature.
- `specfuse/loop/prerun.py` and `tests/test_prerun_oracles.py` — T01's files,
  already `done`. If you believe T01's returned shape is wrong for your needs,
  that is an escalation, not an edit.
- `.specfuse/verification.yml` — owned by T03 in this gate.
- Generated directories, secrets (`.env`, `*.pem`, `*.key`, `credentials.json`),
  and `.git/` internals. See `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set as declared in `.specfuse/verification.yml`: `tests`,
  `lint`, `security`, `coverage` (≥ 90%), `leak-scan`, `event-type-gate`,
  `roadmap-link-gate`, `arm-sweep-gate`.
- The scoped red→green run named in criteria 1 and 6.
- The symbol-existence check in criterion 7.

**Escalation triggers.**

- **The budget value is deliberately unset in this spec.** If measurement does not
  support a defensible number, emit `status: blocked` with the measurements you
  took rather than picking one — the plan left this open on purpose, and a guessed
  constant is the thing worth blocking on.
- If preserving a verdict under the budget proves impossible for a plausible real
  oracle (the verdict itself exceeds the budget), block with the case rather than
  raising the budget silently.
- If T01's result shape cannot carry what formatting needs, block and name the
  missing field. Do not edit T01's files.
- If either `format_oracle_capture` or `ORACLE_CAPTURE_BUDGET_BYTES` is absent
  from the files you edited, emit `status: blocked` — do not claim complete.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
