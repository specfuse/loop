---
id: FEAT-2026-0205/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.50
produces:
  - specfuse/agent/providers/findings_autofix.py
  - tests/test_diagnosis_severity_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T19:08:35.678886+00:00
duration_seconds: 21.534
cost_usd: 0.13445
input_tokens: 8
output_tokens: 2493
---

# T03 — autofix spends its daily cap on the most severe findings first

**Objective.** The findings-autofix provider advertises eligible findings most severe
first, so the daily cap goes to the highest severities; eligibility is unchanged.

**Context.** `FEAT-2026-0205/T03`; PLAN.md decision 4. `specfuse agent run` ranks
items by tier with a stable sort (`specfuse/agent/run.py`), so within the findings
tier the provider's advertise order is the execution order. In
`FindingsAutofixProvider.advertise`, sort the items it already selects by the
severity of their latest diagnosis (`critical`, `high`, `medium`, `low`, then none),
keeping the current order within a severity. Read severity through
`specfuse.monitor.diagnosis.parse` (T01), never by re-parsing the marker here.

**Acceptance criteria.**

1. `tests/test_diagnosis_severity_end_to_end.py::AutofixOrdersBySeverity` (skipped by
   T01, naming this unit) has its skip removed and passes: findings diagnosed `low`,
   `critical` and without severity are advertised `critical`, `low`, none.
2. `tests.test_agent_provider_findings_autofix` and `tests.test_autofix_run` pass
   unchanged, and `git diff` shows no change to `specfuse/monitor/autofix.py`.

**Do not touch.** `specfuse/monitor/autofix.py`, `autofix_state.py`.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_agent_provider_findings_autofix tests.test_autofix_run tests.test_agent_run -b`.

**Escalation triggers.** If `agent run` does not preserve advertise order within a
tier at this tree, stop and escalate with the evidence rather than changing the
conductor.
