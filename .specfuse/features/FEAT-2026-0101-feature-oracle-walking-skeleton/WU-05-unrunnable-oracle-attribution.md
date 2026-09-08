---
id: FEAT-2026-0101/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_oracle_unrunnable_attribution.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.16.0
started_at: 2026-09-08T01:59:22.101194+00:00
duration_seconds: 887.169
cost_usd: 0.563103
input_tokens: 36
output_tokens: 11439
---

# An oracle the shell cannot run is a configuration problem, not the unit's fault

**Objective.** When a gate's `feature_oracle` fails because the command could
not be executed at all, report it as a configuration problem naming the gate
file — instead of an ordinary gate `FAIL` that reads as the work unit's defect.

**Context.** FEAT-2026-0101/T05; read `PLAN.md`, T01, and issue #3260. This
unit exists because the gate's first close recorded `not_met`: the judge built a
feature declaring `feature_oracle: "totally-nonexistent-command-zzz"`, called
`verify()` directly, and got

```
### feature_oracle: FAIL ... /bin/sh: totally-nonexistent-command-zzz: command not found
```

T01 correctly treats an **empty** declaration as a CONFIGURATION ERROR; an
unrunnable one falls through to the ordinary failure path.

**Why this is worth a unit rather than a wording change.** Nothing passes
silently today — the oracle fails and the attempt fails with it. The damage is
**attribution**. A configuration error tells the operator "fix the gate
declaration"; an ordinary `FAIL` tells the next agent "your code is broken", so
a typo'd oracle burns attempts on code that was never at fault. That is the same
misattribution that cost T02 three attempts in this gate.

**Detect by exit status, not by message text.** A shell reports "command not
found" with exit status **127**, which is stable across shells and locales; the
message string is neither. If the oracle gate exits 127, re-report it as a
configuration problem. Do not pattern-match `command not found` as the primary
signal — a legitimate test that prints that phrase would be misclassified.
`_run_gate_set` currently returns `{"name", "ok", "report"}` and does not carry
the exit status out; extending what the **oracle path** knows is in scope,
changing the shared return contract is not (see escalation triggers).

**Scope.** The oracle gate only. A non-oracle gate exiting 127 keeps today's
behaviour — this feature does not own the general gate set's error taxonomy.

**Incremental edit to `specfuse/loop/loop.py`.** T01 already delivered this file
(the `feature_oracle` reader and the `verify()` append). This unit adds exactly
one branch on the oracle's result inside that same path: when the oracle gate
failed *and* its exit status was 127, re-report it in the configuration-problem
shape instead of the ordinary `FAIL` shape. T01's reader, its empty-declaration
CONFIGURATION ERROR, and the `_run_gate_set` call are otherwise untouched.

**Acceptance criteria.**

- `tests/test_oracle_unrunnable_attribution.py::test_unrunnable_oracle_reports_configuration_problem` fails on HEAD and passes after: a gate declaring an oracle naming a nonexistent binary makes `verify()` return `ok=False` with a report naming the **gate file** and identifying the declaration as the problem, not a bare `### feature_oracle: FAIL`.
- `::test_oracle_that_runs_and_fails_is_still_an_ordinary_failure`: an oracle that executes and exits non-zero for a real reason (e.g. `python3 -c "import sys; sys.exit(1)"`) is reported as an ordinary gate failure — this is the boundary that keeps the new branch from swallowing genuine red oracles.
- `::test_test_printing_command_not_found_is_not_misclassified`: an oracle that exits non-zero while printing the words `command not found` in its output is reported as an ordinary failure, proving the classification keys on exit status rather than message text.
- `::test_empty_declaration_path_unchanged`: T01's empty/whitespace CONFIGURATION ERROR behaviour is byte-identical to HEAD.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** `closing_requirements.py` / `lint_closing.py` (T02);
`lint_plan.py` (T03); templates, skills, `methodology.md` (T04); the shared
`_run_gate_set` return contract; `probe_baseline`; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the oracle's exit status
cannot be surfaced without changing `_run_gate_set`'s `{"name", "ok", "report"}`
return contract — `probe_baseline` and `verify` both destructure it, and
widening it is a design change for an operator, not a judgement call here. Also
block if exit 127 turns out not to be the signal on this platform; say what the
observed status was rather than falling back to string matching.
</content>
