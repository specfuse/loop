---
id: FEAT-LOOP-2026-0205/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - tests/test_diagnosis_severity_end_to_end.py
  - docs/concepts/monitoring-to-fix.md
  - specfuse/loop/data/docs/concepts/monitoring-to-fix.md
  - docs/flows.html
  - specfuse/loop/data/docs/flows.html
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T19:08:57.394164+00:00
duration_seconds: 27.835
cost_usd: 0.186803
input_tokens: 12
output_tokens: 3013
---

# T04 — findings stay out of the bug lane; the docs say what severity does

**Objective.** A guard proves a severity label never brings a finding into the bug
lane, and the shipped docs describe severity on the diagnosis.

**Context.** `FEAT-LOOP-2026-0205/T04`; PLAN.md decision 5. The bug lane
(`specfuse/agent/providers/bugs.py`) advertises triaged bugs at or above
`min_severity`; findings are never triaged (`already_structured`), so they carry no
triage marker. Pin that a finding issue with a `severity:critical` label and a
`specfuse:finding` marker is not advertised. If it *is* advertised at this tree, stop
(escalation trigger) — that is a defect, not a doc change.

Docs: `docs/concepts/monitoring-to-fix.md` stage 3 (Diagnose) gains the severity
field and the rubric's one-line summary, stage 4 (Decide) says severity orders the
autofix queue and changes no eligibility rule, and the "human-issue path" comparison
says findings get severity from the diagnosis, not triage. `docs/flows.html`'s
monitoring Diagnose and Decide stage text matches (the simulator is unchanged). Both
shipped copies stay byte-identical; `tests.test_flows_page` must pass.

**Acceptance criteria.**

1. `tests/test_diagnosis_severity_end_to_end.py::BugLaneIgnoresFindingSeverity`
   (skipped by T01, naming this unit) has its skip removed and passes.
2. `grep -n 'unittest.skip' tests/test_diagnosis_severity_end_to_end.py` reports
   nothing at this unit's tree.
3. `python3 -m unittest tests.test_flows_page tests.test_scaffold_data_in_sync tests.test_scaffold_doc_hygiene -b`
   exits 0.

**Do not touch.** `bugs.py`'s selection logic. In the flows page, only the
monitoring Diagnose and Decide stage text changes; its simulator logic stays as is.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_agent_provider_bugs tests.test_flows_page tests.test_scaffold_data_in_sync -b`.

**Escalation triggers.** The bug lane advertising the guarded finding.
