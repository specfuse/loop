---
id: FEAT-2026-0205/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - tests/test_diagnosis_severity_end_to_end.py
  - specfuse/monitor/diagnosis.py
  - specfuse/monitor/diagnose_cli.py
  - specfuse/agent/providers/findings_diagnose.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T19:07:11.095460+00:00
duration_seconds: 51.474
cost_usd: 0.29213
input_tokens: 16
output_tokens: 7797
---

# T01 — a diagnosis carries a severity, and the finding gets one severity label

**Objective.** The oracle goes green for clauses 1 and 2: a headless diagnosis with a
severity posts a marker carrying it and labels the finding `severity:<value>`,
replacing any previous severity label; a diagnosis without one, or with an unknown
value, reads as absent and never raises.

**Context.** `FEAT-2026-0205/T01`, the walking skeleton and the only unit permitted to
stub. Write `tests/test_diagnosis_severity_end_to_end.py` **first**, with classes
`SeverityIsRecordedAndLabelled`, `OldAndUnknownSeverityReadAsAbsent`,
`AutofixOrdersBySeverity` (`unittest.skip("owned by FEAT-2026-0205/T03")`) and
`BugLaneIgnoresFindingSeverity` (`unittest.skip("owned by FEAT-2026-0205/T04")`).

`Diagnosis` (`specfuse/monitor/diagnosis.py`) gains `severity: Optional[str] = None`,
validated against `specfuse.loop.agent_policy.SEVERITY_VALUES` at construction (an
invalid value is a construction error, as `fix_scope` is). `render` adds
`severity=<value>` to the `specfuse:diagnosis` marker only when set (a marker without
it stays byte-identical to today's), and a human-readable **Severity** line. `parse`
reads `severity` when present; an absent or unknown value yields `severity=None` and
never raises — a lookup, not a try/except. `diagnose_cli.parse_analysis` accepts an
optional `severity` field (not in `_REQUIRED_FIELDS`); unknown → absent.

The findings-diagnose provider
(`specfuse/agent/providers/findings_diagnose.py`), after posting, when the rendered
diagnosis has a severity: removes any existing `severity:*` label on the issue and
adds `severity:<value>` (`agent_policy.SEVERITY_LABEL_PREFIX`), creating the label
with `gh label create --force` if needed. No severity → no label write.

Stubbable here, and only here: the rubric text (T02 owns it — a one-line placeholder
prompt sentence is fine).

**Acceptance criteria.**

1. `tests/test_diagnosis_severity_end_to_end.py::SeverityIsRecordedAndLabelled` fails
   on HEAD (absent module) and passes after: a stub headless result with
   `"severity": "high"` → the posted comment's marker carries `severity=high`, the
   issue gets `severity:high`; a second execute with `"low"` removes `severity:high`
   and adds `severity:low`.
2. `OldAndUnknownSeverityReadAsAbsent`: a pre-feature marker and a marker with
   `severity=urgent` both parse with `severity is None`, never raise, and produce no
   label call; a marker rendered without severity is byte-identical to HEAD's render.
3. The existing `tests.test_diagnose_headless`, `tests.test_diagnose_fenced_analysis`
   and `tests.test_agent_provider_findings_diagnose` pass.

**Do not touch.** `specfuse/monitor/autofix.py` (T03 orders, nothing decides
differently). The bug lane (T04). Triage.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_diagnose_headless tests.test_diagnose_fenced_analysis tests.test_agent_provider_findings_diagnose tests.test_autofix_run -b`.

**Escalation triggers.** If `autofix_run`'s diagnosis read rejects a marker carrying
the new field, stop and escalate — that is a published-format break.
