### T01#1

- **criterion:** `tests/test_bug_lane_policy_contract.py::TestPolicyContract::test_resolve_bug_automerge_defaults_off`
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK) — the green half only; the "fails on HEAD before this WU runs" half is a point-in-time oracle a close cannot re-run (see RETROSPECTIVE.md § What the loop did NOT verify)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#2

- **criterion:** A test asserts every row of the assumed-surfaces table above: the module
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#3

- **criterion:** If any row of that table does not hold, this WU emits `status: blocked`
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK) — `TestAssumedSurfaces` green means no row diverged, so the escalation antecedent is false and the criterion is satisfied vacuously
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#4

- **criterion:** `specfuse/loop/agent_policy.py` gains
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#5

- **criterion:** `resolve_bug_automerge` returns `False` when the policy file is absent, when
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#6

- **criterion:** `specfuse/loop/agent_policy.py` gains
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#7

- **criterion:** `validate_agent_policy` accepts and validates `max_diff_lines` and
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#8

- **criterion:** `.specfuse/agent-policy.yml.example` documents both new dials with their
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#9

- **criterion:** This repo's live `.specfuse/agent-policy.yml` keeps
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK) plus this close's guardrail claim 1: `resolve_bug_automerge('.specfuse/agent-policy.yml')` returned `False`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#10

- **criterion:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` exits zero
- **oracle:** `python3 -m unittest tests.test_bug_lane_policy_contract -v` (exit 0, 22 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#11

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import resolve_bug_automerge, bug_lane_limits"`
- **oracle:** `python3 -c "from specfuse.loop.agent_policy import resolve_bug_automerge, bug_lane_limits"` (exit 0, re-run in this close)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_bug_lane_guardrails.py::TestEvaluateMergeGuardrails::test_all_guardrails_pass_is_eligible`
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK) — green half only; the red-on-HEAD half is not re-runnable
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#2

- **criterion:** `specfuse/loop/bug_lane.py` defines a frozen `MergeDecision` dataclass with
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#3

- **criterion:** Module-level reason constants exist, one per guardrail plus one for
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#4

- **criterion:** `evaluate_merge_guardrails` is **pure**: it opens no file, spawns no process,
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#5

- **criterion:** A `Protocol` for the merge-cap state reader is defined in this module,
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#6

- **criterion:** Each of the six guardrails has a test proving it **alone** declines, with the
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#7

- **criterion:** A test proves all six satisfied returns `eligible=True` with
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#8

- **criterion:** **Fail-closed tests:** `None`, a wrong-typed value, and a missing key for
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK) plus this close's guardrail claim 2: 43 malformed values across all seven inputs plus 7 omission cases, every one `eligible=False`, none raised, against a control fixture that returns `eligible=True`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#9

- **criterion:** `JUDGE_PATHS` is **imported** from `specfuse.loop.arm_eval`, not redefined. A
- **oracle:** `python3 -c "import specfuse.loop.bug_lane as bl, specfuse.loop.arm_eval as ae; assert bl.JUDGE_PATHS is ae.JUDGE_PATHS"` in a fresh interpreter (exit 0, identity not equality) plus `grep -n JUDGE_PATHS specfuse/loop/bug_lane.py` showing one import and no second definition
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#10

- **criterion:** A test asserts a changed path under each entry of `JUDGE_PATHS` declines,
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#11

- **criterion:** A test asserts CI conclusions `"pending"`, `"failure"`, `""`, and `None`
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#12

- **criterion:** `python3 -m unittest tests.test_bug_lane_guardrails -v` exits zero after
- **oracle:** `python3 -m unittest tests.test_bug_lane_guardrails -v` (exit 0, 35 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#13

- **criterion:** `python3 -c "from specfuse.loop.bug_lane import evaluate_merge_guardrails, MergeDecision"`
- **oracle:** `python3 -c "from specfuse.loop.bug_lane import evaluate_merge_guardrails, MergeDecision"` (exit 0, re-run in this close)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_bug_lane_state.py::TestGitHubMergeCapState::test_count_is_rederived_from_markers`
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK) — green half only; the red-on-HEAD half is not re-runnable
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#2

- **criterion:** `specfuse/loop/bug_lane_state.py` defines `GitHubMergeCapState` satisfying
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#3

- **criterion:** `ROLLING_WINDOW_SECONDS = 24 * 60 * 60` is a module-level constant.
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#4

- **criterion:** The merge marker literal is exactly
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#5

- **criterion:** The 24h count is **re-derived** by reading markers on each call — a test
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#6

- **criterion:** A malformed or unparseable marker is **ignored**, not fatal, and does not
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#7

- **criterion:** Every GitHub access goes through an injected `runner` callable — a test
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#8

- **criterion:** `record_merge(runner, repo, pr_number, *, at)` writes the marker onto the
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#9

- **criterion:** `triaged_bug_intake(runner, repo, *, limit) -> list` returns only issues
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#10

- **criterion:** A test asserts `triaged_bug_intake` re-uses triage's parser rather than
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#11

- **criterion:** An issue already carrying the `auto-fix-attempted-failed` label
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#12

- **criterion:** `python3 -m unittest tests.test_bug_lane_state -v` exits zero after this
- **oracle:** `python3 -m unittest tests.test_bug_lane_state -v` (exit 0, 11 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#13

- **criterion:** `python3 -c "from specfuse.loop.bug_lane_state import GitHubMergeCapState, triaged_bug_intake"`
- **oracle:** `python3 -c "from specfuse.loop.bug_lane_state import GitHubMergeCapState, triaged_bug_intake"` (exit 0, re-run in this close)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#1

- **criterion:** `tests/test_bug_lane_run.py::TestRunBugLane::test_dial_off_never_merges`
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK) — green half only; the red-on-HEAD half is not re-runnable
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#2

- **criterion:** `specfuse/loop/bug_lane_run.py` defines
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#3

- **criterion:** **Dial off never merges.** A test asserts that with
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK) plus this close's composite oracle: with the dial off in this repo's live policy, `resolve_bug_automerge` returns `False` and the single merge call site is unreachable
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#4

- **criterion:** **Guardrails cannot be bypassed by the dial.** A test asserts that with the
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK) plus this close's composite oracle: `run_bug_lane` driven end to end with the dial FORCED ON in a temporary policy, one guardrail failing at a time — six for six `outcome=declined`, zero `gh pr merge` calls, each PR labeled with its reason constant; a control with no guardrail failing did merge, proving the path was live
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#5

- **criterion:** A test asserts the module contains exactly **one** call site that issues a
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#6

- **criterion:** `pr_ci_conclusion(runner, repo, pr_number) -> str` exists and returns a
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#7

- **criterion:** On a declining path the PR is labeled with the guardrail's reason constant
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK) plus the composite oracle's per-case label observation (no `gh pr close` and no second `/fix-bug` invocation in the recorded argv)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#8

- **criterion:** A `/fix-bug` outcome of `refused` or `could_not_proceed` (per
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#9

- **criterion:** A test asserts `emit_escalation` is called with this WU's correlation ID
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#10

- **criterion:** After a successful merge, `bug_lane_state.record_merge` is called exactly
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#11

- **criterion:** Every GitHub interaction goes through the injected `runner`; a test
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#12

- **criterion:** `python3 -m unittest tests.test_bug_lane_run -v` exits zero after this WU's
- **oracle:** `python3 -m unittest tests.test_bug_lane_run -v` (exit 0, 31 tests, OK)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#13

- **criterion:** `python3 -c "from specfuse.loop.bug_lane_run import run_bug_lane, pr_ci_conclusion"`
- **oracle:** `python3 -c "from specfuse.loop.bug_lane_run import run_bug_lane, pr_ci_conclusion"` (exit 0, re-run in this close)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
