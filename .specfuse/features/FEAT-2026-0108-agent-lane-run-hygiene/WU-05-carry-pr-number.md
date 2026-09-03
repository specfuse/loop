---
id: FEAT-2026-0108/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: sonnet
effort: medium
oracle_env: macos_local
produces:
  - specfuse/loop/bug_lane_run.py
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - tests/test_bug_lane_pr_number_carried.py
---

# The lane evaluates the PR `/fix-bug` opened, not one it re-discovers

**Objective.** Three items in the 2026-09-02 run escalated `pr_not_found` for
PRs that existed (#3180). The lookup is already off the search index (#1984)
and the payload no longer claims a PR exists (#3180 fix), but the number is
still re-discovered from a list. Carry it from `/fix-bug`'s own RESULT block
and fall back to the list only when the block carried none.

**Context.** FEAT-2026-0108/T05; read `PLAN.md`. `/fix-bug` headless mode
(canonical `plugins/specfuse/skills/fix-bug/SKILL.md` § Headless mode) ends
with a RESULT block per `result-contract.md`; add an optional `pr_number:`
line the skill writes when it opened a PR (step 7 already captures the URL).
`classify_outcome` / a sibling `extract_pr_number(session_output)` in
`bug_lane_run.py` reads it; `run_bug_lane` uses it first and calls
`_find_pr_for_issue` only when absent, retrying the list once after a short
sleep before reporting `pr_not_found`. The result-contract rule itself is not
edited: the field is skill-local and optional, and the driver ignores unknown
RESULT lines. Red test first.

**Acceptance criteria.**

- `tests/test_bug_lane_pr_number_carried.py::test_result_block_pr_number_is_used_without_list_lookup` fails on HEAD and passes after: a session output carrying `pr_number: 42` evaluates guardrails on 42 and the runner sees no `gh pr list` call.
- `tests/test_bug_lane_pr_number_carried.py::test_absent_pr_number_falls_back_to_list_with_one_retry`: no `pr_number:` line, first list empty, second list finds it; the runner sees exactly two list calls.
- `tests/test_bug_lane_pr_number_carried.py::test_still_pr_not_found_after_retry`.
- `grep -c "pr_number:" plugins/specfuse/skills/fix-bug/SKILL.md` reports at least 1 in the headless RESULT description; `bash scripts/sync-scaffold.sh` leaves `git status --porcelain .specfuse/skills` empty.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `.specfuse/rules/result-contract.md`; the WU driver module (everything under `specfuse/loop/` not named in `produces:`);
`bug_lane.py` (T04); escalation payload text (T06); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.loop.bug_lane_run import extract_pr_number"` exits 0.

**Escalation triggers.** Emit `status: blocked` if the driver's RESULT parser
rejects an unknown `pr_number:` line rather than ignoring it; that would make
the field a contract change and this unit must not make one.
