### T01#1

- **criterion:** `tests/test_diagnosis_severity_end_to_end.py::SeverityIsRecordedAndLabelled` fails
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_end_to_end.SeverityIsRecordedAndLabelled -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, specfuse/monitor/diagnosis.py, specfuse/monitor/diagnose_cli.py, specfuse/agent/providers/findings_diagnose.py

### T01#2

- **criterion:** `OldAndUnknownSeverityReadAsAbsent`: a pre-feature marker and a marker with
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_end_to_end.OldAndUnknownSeverityReadAsAbsent -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, specfuse/monitor/diagnosis.py, specfuse/monitor/diagnose_cli.py, specfuse/agent/providers/findings_diagnose.py

### T01#3

- **criterion:** The existing `tests.test_diagnose_headless`, `tests.test_diagnose_fenced_analysis`
- **oracle:** python3 -m unittest tests.test_diagnose_headless tests.test_diagnose_fenced_analysis tests.test_agent_provider_findings_diagnose -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, specfuse/monitor/diagnosis.py, specfuse/monitor/diagnose_cli.py, specfuse/agent/providers/findings_diagnose.py

### T02#1

- **criterion:** `tests/test_diagnosis_severity_rubric.py::TestRubric::test_one_line_per_value`
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_rubric.TestRubric.test_one_line_per_value -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** specfuse/monitor/diagnosis.py, specfuse/agent/diagnose_invoke.py, plugins/specfuse/skills/diagnose-issue/SKILL.md, .specfuse/skills/diagnose-issue/SKILL.md, tests/test_diagnosis_severity_rubric.py

### T02#2

- **criterion:** `test_prompt_carries_the_rubric`: the prompt `diagnose_invoke.build_invocation`
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_rubric.TestRubric.test_prompt_carries_the_rubric -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** specfuse/monitor/diagnosis.py, specfuse/agent/diagnose_invoke.py, plugins/specfuse/skills/diagnose-issue/SKILL.md, .specfuse/skills/diagnose-issue/SKILL.md, tests/test_diagnosis_severity_rubric.py

### T02#3

- **criterion:** Both SKILL.md copies name `SEVERITY_RUBRIC` and are byte-identical, and
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_rubric.TestRubric.test_skill_copies_name_rubric_and_match -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** specfuse/monitor/diagnosis.py, specfuse/agent/diagnose_invoke.py, plugins/specfuse/skills/diagnose-issue/SKILL.md, .specfuse/skills/diagnose-issue/SKILL.md, tests/test_diagnosis_severity_rubric.py

### T03#1

- **criterion:** `tests/test_diagnosis_severity_end_to_end.py::AutofixOrdersBySeverity` (skipped by
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_end_to_end.AutofixOrdersBySeverity -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** specfuse/agent/providers/findings_autofix.py, tests/test_diagnosis_severity_end_to_end.py

### T03#2

- **criterion:** `tests.test_agent_provider_findings_autofix` and `tests.test_autofix_run` pass
- **oracle:** python3 -m unittest tests.test_agent_provider_findings_autofix tests.test_autofix_run -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** specfuse/agent/providers/findings_autofix.py, tests/test_diagnosis_severity_end_to_end.py

### T04#1

- **criterion:** `tests/test_diagnosis_severity_end_to_end.py::BugLaneIgnoresFindingSeverity`
- **oracle:** python3 -m unittest tests.test_diagnosis_severity_end_to_end.BugLaneIgnoresFindingSeverity -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, docs/concepts/monitoring-to-fix.md, specfuse/loop/data/docs/concepts/monitoring-to-fix.md, docs/flows.html, specfuse/loop/data/docs/flows.html

### T04#2

- **criterion:** `grep -n 'unittest.skip' tests/test_diagnosis_severity_end_to_end.py` reports
- **oracle:** ! grep -n 'unittest.skip' tests/test_diagnosis_severity_end_to_end.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, docs/concepts/monitoring-to-fix.md, specfuse/loop/data/docs/concepts/monitoring-to-fix.md, docs/flows.html, specfuse/loop/data/docs/flows.html

### T04#3

- **criterion:** `python3 -m unittest tests.test_flows_page tests.test_scaffold_data_in_sync tests.test_scaffold_doc_hygiene -b`
- **oracle:** python3 -m unittest tests.test_flows_page tests.test_scaffold_data_in_sync tests.test_scaffold_doc_hygiene -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `9b1029df37a49d10e5436765d7a0e596cbcc8a46`
- **attempt:** `1`
- **covers:** tests/test_diagnosis_severity_end_to_end.py, docs/concepts/monitoring-to-fix.md, specfuse/loop/data/docs/concepts/monitoring-to-fix.md, docs/flows.html, specfuse/loop/data/docs/flows.html
