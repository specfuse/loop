---
id: FEAT-2026-0117/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces_driver_helper:
  - render_carry_summary
produces:
  - specfuse/loop/judge.py
  - specfuse/loop/closing_requirements.py
  - tests/test_carry_accounting_close_and_judge.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T19:01:19.168540+00:00
duration_seconds: 458.415
cost_usd: 1.706513
input_tokens: 98
output_tokens: 30002
---

# The close states what it carried; the judge sees it

**Objective.** Make inheritance visible where verdicts are decided: the close's
`## Measurements` states how many criteria were carried and how many
re-measured, and the judge bundle lists each carried entry with the sha it was
proved at.

**Context.** FEAT-2026-0117/T03. In `specfuse/loop/judge.py`,
`build_judge_bundle` already parses `GATE-NN-CRITERIA.md`; render carried
entries (those with `carried_from_attempt`) in their own sub-list with
`proved_at_sha` and `covers`, so the judge can lower a verdict on a carried
green it does not trust. In `specfuse/loop/closing_requirements.py`, extend the
close-n registry entry (the one that reads `## Measurements` when a
`feature_oracle` is declared): when any entry in the criteria file carries
`carried_from_attempt`, `## Measurements` must contain a line matching
`carried forward: <N> criteria, re-measured: <M>` — `render_carry_summary(entries)`
produces the expected line and the worklist prompt tells the close to paste it.
A first close (no carried entries) has no new obligation. Red test first.

**Acceptance criteria.**

1. `tests/test_carry_accounting_close_and_judge.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_carry_accounting_close_and_judge -v -b`
   exits 0.
2. That module asserts the judge bundle text for a criteria file with one
   carried and one re-measured entry names the carried one under its own
   heading with its `proved_at_sha`; and that `specfuse lint --closing` (via
   the registry check function) fails when `## Measurements` lacks the carry
   line and passes when it has it, and passes with no line when nothing was
   carried.
3. `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_lint_closing_criteria tests.test_lint_closing_criteria_pristine -v -b`
   exits 0 with no edit to those modules.

**Do not touch.** `loop.py` and `criteria_state.py` (T01/T02); the lower-only
rule; `.specfuse/rules/` and `docs/` (T04); plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the closing registry has
no conditional shape for "required only when the criteria file has X" (say
which existing entry is closest); or if the judge bundle's per-section cap
truncates the carried list on a realistic gate.
