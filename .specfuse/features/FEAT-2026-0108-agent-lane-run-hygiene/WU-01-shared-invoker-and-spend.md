---
id: FEAT-2026-0108/T01
type: implementation
status: done
attempts: 2
planned_cost_usd: 6.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: run_claude
produces:
  - specfuse/agent/invoke.py
  - specfuse/agent/run.py
  - tests/test_agent_invoke_usage.py
duration_seconds: 2924.833
cost_usd: 7.807955
input_tokens: 428
output_tokens: 88701
---

# One shared invoker returns the usage envelope; every provider reports what it spent

**Objective.** Add `specfuse/agent/invoke.py` with `run_claude(argv, prompt,
*, runner, timeout) -> InvokeResult(text, usage, returncode)` that appends
`--output-format json`, parses the CLI's JSON envelope, and returns the usage
block. The three agent invoke modules build their argv through it; every
provider sets `ActionOutcome.spend` from the returned usage so
`budget.record_tokens` records real numbers and `max_tokens_per_run` can fire.

**Context.** FEAT-2026-0108/T01; read `PLAN.md` § Existing-mechanism search.
`loop.py:3243` passes `--output-format json` and `loop.py:1391-1396` reads
`cost_usd`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`,
`cache_creation_input_tokens` from the envelope; mirror that field list, do not
import from `loop.py`. Invoke sites: `agent/diagnose_invoke.py:46`,
`agent/drafting_invoke.py:61`, `agent/triage_invoke.py:41`, and
`monitor/autofix_invoke.py:32` (the `/fix-bug` argv the bug lane runs). `spend`
is `input_tokens + output_tokens` (cache reads excluded, matching the driver's
cost line). A CLI that returns non-JSON (older CLI, `cost_tracking: false`)
yields `usage=None` and `spend=0`, never an exception. Red test first.

**Acceptance criteria.**

- `tests/test_agent_invoke_usage.py::test_run_claude_parses_usage_envelope` fails on HEAD (module absent) and passes after: an injected runner returning the driver's envelope shape yields `usage["input_tokens"]`, `usage["output_tokens"]`, `usage["cost_usd"]` and the session text.
- `tests/test_agent_invoke_usage.py::test_non_json_output_yields_no_usage_and_text_intact`.
- `grep -rn --include="*.py" "output-format" specfuse/agent/ specfuse/monitor/autofix_invoke.py | wc -l` reports at least 4, all via `run_claude` or its argv builder (`grep -rn "argv = \[\"claude\"" specfuse/agent/ specfuse/monitor/autofix_invoke.py | wc -l` reports 0).
- `tests/test_agent_invoke_usage.py::test_budget_token_cap_fires_after_one_item`: a run over two fixture items whose provider reports `spend=1200` with `max_tokens=1000` starts one item and stops with `STOP_CAP`; the summary line `tokens spent:` reads `1200`.
- `grep -rn --include="*.py" "spend=" specfuse/agent/providers/ | wc -l` reports at least 1 per provider that dispatches a session (`bugs`, `feature`, `triage`, `findings_diagnose`, `findings_autofix`, `answers`).
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** the WU driver module (everything under `specfuse/loop/` not named in `produces:`); `bug_lane.py` (T04); the worktree
module (T02); escalation payload text (T06); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.agent.invoke import run_claude"` exits 0.

**Escalation triggers.** Emit `status: blocked` if any invoke module needs an
argv shape `run_claude` cannot express without a per-site special case; name
it rather than adding a fifth copy of the parse.
