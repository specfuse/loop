---
id: FEAT-2026-0108/T05H
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
model: sonnet
effort: medium
oracle_env: macos_local
provenance: "G1-CLOSE attempt 1, RETROSPECTIVE.md § Verdict and FOLLOW-UPS.md entry 1 (2026-09-05): demo5_escalation_state.py exit 1; run_bug_lane returns pr_number=None on could_not_proceed while extract_pr_number reads 1532 from the same output"
produces:
  - specfuse/loop/bug_lane_run.py
  - tests/test_bug_lane_stopped_outcome_pr_number.py
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-05T15:51:09.737352+00:00
duration_seconds: 1104.54
cost_usd: 0.911953
input_tokens: 78
output_tokens: 8932
---

# Hygiene: a stopped `/fix-bug` outcome still carries the PR it opened

**Objective.** `run_bug_lane`'s escalating branch returns a literal
`pr_number=None` for `refused` and `could_not_proceed`, so the PR number T05
taught the lane to read from the RESULT block is thrown away on exactly the
outcomes T06 renders. Call `extract_pr_number(session_output)` on that branch
too, so a session that opened a PR and then stopped hands the number forward.

**Context.** FEAT-2026-0108/T05H, hygiene precursor to the close's re-run.
The close's first attempt recorded `not_met` on one criterion and isolated the
cause in `specfuse/loop/bug_lane_run.py:642-648`: `classify_outcome` says
`could_not_proceed`, `extract_pr_number` (T05, already imported in that
module) says `1532`, and `run_bug_lane` returns `pr_number=None`. T06's
payload branch `if result.pr_number:` is therefore unreachable from a real
run, and item #1481's escalation text ("never reached a guardrail or merge
decision", PR #1532 open) is still what the lane produces. Read
`FOLLOW-UPS.md` in this folder, entry 1, before editing. Red test first,
through `run_bug_lane` with an injected runner, not by constructing
`BugLaneResult` by hand.

**Acceptance criteria.**

- `tests/test_bug_lane_stopped_outcome_pr_number.py::test_could_not_proceed_carries_pr_number` fails on HEAD and passes after: a runner whose `/fix-bug` session output classifies `could_not_proceed` and carries `pr_number: 1532` yields `BugLaneResult(outcome="could_not_proceed", pr_number=1532)`.
- `::test_refused_carries_pr_number_when_present` and `::test_stopped_without_pr_number_stays_none`.
- `::test_provider_escalation_names_the_open_pr_end_to_end`: `BugsProvider.execute` with that same runner produces an escalation whose text contains `PR #1532` and not "never reached a guardrail".
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `extract_pr_number` and `classify_outcome` themselves; the
provider payload text (T06 owns it, and it already renders the number);
`bug_lane.py`; the WU driver module (everything under `specfuse/loop/` not
named in `produces:`); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if the escalating branch
cannot read the number without re-running `classify_outcome`'s parse in a
way that changes its result for any existing test; name the test.
