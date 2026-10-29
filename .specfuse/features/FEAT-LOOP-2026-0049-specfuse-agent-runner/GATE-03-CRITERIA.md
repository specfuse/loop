### T09#1

- **criterion:** `tests/test_agent_findings_seam.py::TestFindingKinds::test_finding_items_are_selected_not_escalated`
- **oracle:** `python3 -m unittest tests.test_agent_findings_seam.TestFindingKinds.test_finding_items_are_selected_not_escalated`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#2

- **criterion:** `specfuse/agent/run.py` exposes `KIND_FINDING_DIAGNOSE` and
- **oracle:** `python3 -c "from specfuse.agent.run import KIND_FINDING_DIAGNOSE, KIND_FINDING_AUTOFIX" && python3 -m unittest tests.test_agent_findings_seam.TestFindingKinds.test_finding_items_are_selected_not_escalated tests.test_agent_findings_seam.TestGate1Gate2OrderingUnchanged -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_findings_seam.TestFindingKinds.test_finding_items_are_selected_not_escalated`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#4

- **criterion:** **Gate 1's and gate 2's ranking is unchanged.** A test constructs items of all
- **oracle:** `python3 -m unittest tests.test_agent_findings_seam.TestGate1Gate2OrderingUnchanged -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#5

- **criterion:** `specfuse/agent/monitoring_read.py` exposes the three readers described above.
- **oracle:** `python3 -c "from specfuse.agent.monitoring_read import load_monitoring_config, component_for_finding, component_diagnose_dial" && python3 -m unittest tests.test_agent_findings_seam.TestMonitoringRead -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#6

- **criterion:** `main()` accepts `--monitoring-config`, defaulting to
- **oracle:** `python3 -m unittest tests.test_agent_findings_seam.TestMonitoringConfigFlag -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T09#7

- **criterion:** The module performs no writes: no issue comment, no label, no file. A test
- **oracle:** `python3 -m unittest tests.test_agent_findings_seam.TestMonitoringRead.test_no_gh_call_from_monitoring_read -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#1

- **criterion:** `tests/test_agent_provider_findings_diagnose.py::TestFindingsDiagnoseProvider::test_undiagnosed_finding_gets_one_diagnosis_comment`
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_undiagnosed_finding_gets_one_diagnosis_comment`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#2

- **criterion:** `specfuse/agent/providers/findings_diagnose.py` implements T05's protocol over
- **oracle:** `python3 -c "from specfuse.agent.providers.findings_diagnose import FindingsDiagnoseProvider; from specfuse.agent.diagnose_invoke import build_invocation, read_result" && python3 -m unittest tests.test_agent_provider_findings_diagnose -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_undiagnosed_finding_gets_one_diagnosis_comment`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#4

- **criterion:** **The rendered body is `diagnosis.render`'s, unaltered.** Criterion 1's test
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_undiagnosed_finding_gets_one_diagnosis_comment`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#5

- **criterion:** **An unparseable analysis posts nothing.** A session whose output raises
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_unparseable_analysis_escalates_and_posts_nothing -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#6

- **criterion:** **Already-diagnosed and dial-off findings are not advertised.** Two tests: an
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_already_diagnosed_finding_not_advertised tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_manual_diagnose_dial_not_advertised tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_no_monitoring_config_advertises_nothing -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T10#7

- **criterion:** The provider is registered in `default_providers()`, advertises T09's
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_registered_in_default_providers -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#1

- **criterion:** `tests/test_agent_provider_findings_autofix.py::TestFindingsAutofixProvider::test_decline_does_not_invoke_fix_bug`
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_decline_does_not_invoke_fix_bug`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#2

- **criterion:** `specfuse/agent/providers/findings_autofix.py` implements T05's protocol over
- **oracle:** `python3 -c "from specfuse.agent.providers.findings_autofix import FindingsAutofixProvider" && python3 -m unittest tests.test_agent_provider_findings_autofix -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_decline_does_not_invoke_fix_bug`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#4

- **criterion:** **The provider re-decides nothing.** A test asserts the module contains no
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_module_re_decides_nothing_of_its_own -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#5

- **criterion:** **Each row of the outcome table has a test**, each asserting the observable
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_fire_completed_reports_completed tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_fire_refused_escalates_with_no_second_label tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_fire_could_not_proceed_escalates_with_no_second_label tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_route_to_human_escalates_naming_the_finding_issue tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_decline_does_not_invoke_fix_bug -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#6

- **criterion:** **Undiagnosed findings and unresolvable components are not advertised.** Two
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_undiagnosed_finding_not_advertised tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_unresolvable_component_not_advertised tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_no_monitoring_config_advertises_nothing -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T11#7

- **criterion:** The provider is registered in `default_providers()`, advertises T09's
- **oracle:** `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_registered_in_default_providers -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
