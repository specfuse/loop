### T01#1

- **criterion:** `tests/test_http_status_regression_end_to_end.py::HttpStatusRegressionEndToEnd::test_one_deployment_files_one_finding_per_code`
- **oracle:** python3 -m unittest tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_one_deployment_files_one_finding_per_code -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** tests/test_http_status_regression_end_to_end.py, specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/cli.py, specfuse/monitor/artifact.py, specfuse/loop/lint_monitoring.py

### T01#2

- **criterion:** `test_same_rows_same_fingerprint`: two cycles over the same stub rows yield
- **oracle:** python3 -m unittest tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_same_rows_same_fingerprint -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** tests/test_http_status_regression_end_to_end.py, specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/cli.py, specfuse/monitor/artifact.py, specfuse/loop/lint_monitoring.py

### T01#3

- **criterion:** `test_adapter_issues_one_query`: the stub transport records exactly one query per
- **oracle:** python3 -m unittest tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_adapter_issues_one_query -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** tests/test_http_status_regression_end_to_end.py, specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/cli.py, specfuse/monitor/artifact.py, specfuse/loop/lint_monitoring.py

### T01#4

- **criterion:** `GATE-01.md`'s `feature_oracle` command exits 0 at this unit's tree.
- **oracle:** python3 -m unittest tests.test_http_status_regression_end_to_end -v -b
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** tests/test_http_status_regression_end_to_end.py, specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/cli.py, specfuse/monitor/artifact.py, specfuse/loop/lint_monitoring.py

### T02#1

- **criterion:** `tests/test_lint_monitoring.py::TestQueueStalled::test_malformed_stall_after_is_a_lint_error`
- **oracle:** python3 -m unittest tests.test_lint_monitoring.TestQueueStalled.test_malformed_stall_after_is_a_lint_error -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/durations.py, specfuse/monitor/providers/azure_service_bus.py, specfuse/loop/lint_monitoring.py, tests/test_monitor_durations.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md

### T02#2

- **criterion:** `tests/test_monitor_durations.py` asserts `parse_duration_seconds` and
- **oracle:** python3 -m unittest tests.test_monitor_durations -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/durations.py, specfuse/monitor/providers/azure_service_bus.py, specfuse/loop/lint_monitoring.py, tests/test_monitor_durations.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md

### T02#3

- **criterion:** Migration check: every `stall_after` in `.specfuse/monitoring.yml.example`,
- **oracle:** python3 -m unittest tests.test_monitoring_example tests.test_monitoring_fenced_blocks -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/durations.py, specfuse/monitor/providers/azure_service_bus.py, specfuse/loop/lint_monitoring.py, tests/test_monitor_durations.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md

### T02#4

- **criterion:** `docs/concepts/monitoring-schema.md` states the grammar for `stall_after` and no
- **oracle:** grep -n 'stall_after' docs/concepts/monitoring-schema.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/durations.py, specfuse/monitor/providers/azure_service_bus.py, specfuse/loop/lint_monitoring.py, tests/test_monitor_durations.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md

### T03#1

- **criterion:** `tests/test_lint_monitoring.py::TestHttpStatusRegression::test_field_rules` fails
- **oracle:** python3 -m unittest tests.test_lint_monitoring.TestHttpStatusRegression.test_field_rules -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_monitoring.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md, .specfuse/monitoring.yml.example, specfuse/loop/data/monitoring.yml.example, .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md

### T03#2

- **criterion:** `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`
- **oracle:** python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example && cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_monitoring.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md, .specfuse/monitoring.yml.example, specfuse/loop/data/monitoring.yml.example, .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md

### T03#3

- **criterion:** `python3 -m unittest tests.test_monitoring_example tests.test_monitoring_fenced_blocks -b`
- **oracle:** python3 -m unittest tests.test_monitoring_example tests.test_monitoring_fenced_blocks -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_monitoring.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md, .specfuse/monitoring.yml.example, specfuse/loop/data/monitoring.yml.example, .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md

### T03#4

- **criterion:** `grep -c "http-status-regression" docs/concepts/monitoring-schema.md` is at least 2
- **oracle:** grep -c http-status-regression docs/concepts/monitoring-schema.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_monitoring.py, tests/test_lint_monitoring.py, docs/concepts/monitoring-schema.md, .specfuse/monitoring.yml.example, specfuse/loop/data/monitoring.yml.example, .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md

### T04#1

- **criterion:** `tests/test_http_status_regression_adapter.py::RegressionRule::test_share_threshold`
- **oracle:** python3 -m unittest tests.test_http_status_regression_adapter.RegressionRule.test_share_threshold -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_http_status_regression_adapter.py, tests/test_app_insights_query_schema_check.py

### T04#2

- **criterion:** `test_traffic_ramp_is_not_a_regression`: the after-window has 4× the total requests
- **oracle:** python3 -m unittest tests.test_http_status_regression_adapter.RegressionRule.test_traffic_ramp_is_not_a_regression -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_http_status_regression_adapter.py, tests/test_app_insights_query_schema_check.py

### T04#3

- **criterion:** `test_partial_window_is_not_evaluated`: aggregates for a deployment whose window
- **oracle:** python3 -m unittest tests.test_http_status_regression_adapter.RegressionRule.test_partial_window_is_not_evaluated -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_http_status_regression_adapter.py, tests/test_app_insights_query_schema_check.py

### T04#4

- **criterion:** `test_query_is_configuration_only`: the one query names `AppRequests`,
- **oracle:** python3 -m unittest tests.test_http_status_regression_adapter.QueryShape.test_query_is_configuration_only -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_http_status_regression_adapter.py, tests/test_app_insights_query_schema_check.py

### T04#5

- **criterion:** `python3 -m unittest tests.test_app_insights_query_schema_check -b` exits 0 with
- **oracle:** python3 -m unittest tests.test_app_insights_query_schema_check -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_http_status_regression_adapter.py, tests/test_app_insights_query_schema_check.py

### T05#1

- **criterion:** `tests/test_derive_monitoring_discovery.py::TestHttpStatusRegressionProposal::test_proposed_only_with_version_evidence`
- **oracle:** python3 -m unittest tests.test_derive_monitoring_discovery.TestHttpStatusRegressionProposal.test_proposed_only_with_version_evidence -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md, plugins/specfuse/skills/derive-monitoring/SKILL.md, plugins/specfuse/skills/derive-monitoring/PROMPT.md, .specfuse/skills/derive-monitoring/SKILL.md, .specfuse/skills/derive-monitoring/PROMPT.md, tests/test_derive_monitoring_discovery.py

### T05#2

- **criterion:** Both design-rule copies carry the new section and stay byte-identical, and the
- **oracle:** python3 -m unittest tests.test_design_for_diagnosis_rule -b && cmp .specfuse/rules/design-for-diagnosis.md specfuse/loop/data/rules/design-for-diagnosis.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md, plugins/specfuse/skills/derive-monitoring/SKILL.md, plugins/specfuse/skills/derive-monitoring/PROMPT.md, .specfuse/skills/derive-monitoring/SKILL.md, .specfuse/skills/derive-monitoring/PROMPT.md, tests/test_derive_monitoring_discovery.py

### T05#3

- **criterion:** `bash scripts/sync-scaffold.sh` leaves `git status --porcelain` unchanged after
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b && cmp .specfuse/skills/derive-monitoring/SKILL.md plugins/specfuse/skills/derive-monitoring/SKILL.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd`
- **attempt:** `1`
- **covers:** .specfuse/rules/design-for-diagnosis.md, specfuse/loop/data/rules/design-for-diagnosis.md, plugins/specfuse/skills/derive-monitoring/SKILL.md, plugins/specfuse/skills/derive-monitoring/PROMPT.md, .specfuse/skills/derive-monitoring/SKILL.md, .specfuse/skills/derive-monitoring/PROMPT.md, tests/test_derive_monitoring_discovery.py
