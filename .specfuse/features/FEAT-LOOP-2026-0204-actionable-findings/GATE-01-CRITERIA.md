### T01#1

- **criterion:** `tests/test_monitor_finding_lifecycle_end_to_end.py::ClosedFindingReopens::test_closed_issue_is_reopened_not_refiled`
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.ClosedFindingReopens.test_closed_issue_is_reopened_not_refiled -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_lifecycle_end_to_end.py, tests/test_monitor_finding_context_end_to_end.py, specfuse/monitor/issues.py

### T01#2

- **criterion:** `test_open_issue_still_updates` and `test_new_fingerprint_still_files`: the open
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.ClosedFindingReopens.test_open_issue_still_updates tests.test_monitor_finding_lifecycle_end_to_end.ClosedFindingReopens.test_new_fingerprint_still_files -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_lifecycle_end_to_end.py, tests/test_monitor_finding_context_end_to_end.py, specfuse/monitor/issues.py

### T01#3

- **criterion:** `test_listing_is_bounded`: the listing argv carries the 90-day bound derived from
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.ClosedFindingReopens.test_listing_is_bounded -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_lifecycle_end_to_end.py, tests/test_monitor_finding_context_end_to_end.py, specfuse/monitor/issues.py

### T01#4

- **criterion:** `grep -rn '"issue", "close"\|issue close' specfuse/monitor` reports nothing, and
- **oracle:** ! grep -rn '"issue", "close"\|issue close' specfuse/monitor
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_lifecycle_end_to_end.py, tests/test_monitor_finding_context_end_to_end.py, specfuse/monitor/issues.py

### T01#5

- **criterion:** `GATE-01.md`'s `feature_oracle` exits 0 at this unit's tree (skipped classes
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end tests.test_monitor_finding_context_end_to_end -v -b
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `3b002bcd28928c16a40b1819a715e3f046837f10`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_lifecycle_end_to_end.py, tests/test_monitor_finding_context_end_to_end.py, specfuse/monitor/issues.py

### T02#1

- **criterion:** `tests/test_monitor_finding_meta.py::TestRoundTrip::test_new_fields_round_trip`
- **oracle:** python3 -m unittest tests.test_monitor_finding_meta.TestRoundTrip.test_new_fields_round_trip -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_meta.py, specfuse/monitor/issues.py

### T02#2

- **criterion:** `TestFailClosed`: each of `occurrences=abc`, `last_seen=`, `first_seen=x`,
- **oracle:** python3 -m unittest tests.test_monitor_finding_meta.TestFailClosed -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_meta.py, specfuse/monitor/issues.py

### T02#3

- **criterion:** `test_cycle_survives_a_malformed_meta`: a `run_cycle` whose `gh` listing returns a
- **oracle:** python3 -m unittest tests.test_monitor_finding_meta.TestCycleSurvivesMalformedMeta -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_meta.py, specfuse/monitor/issues.py

### T02#4

- **criterion:** The reopen comment and the updated body name first and last seen as ISO-8601 UTC
- **oracle:** python3 -m unittest tests.test_monitor_finding_meta -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** tests/test_monitor_finding_meta.py, specfuse/monitor/issues.py

### T03#1

- **criterion:** `tests/test_monitor_finding_lifecycle_end_to_end.py::DlqAcknowledgement`, skipped
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.DlqAcknowledgement -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, specfuse/monitor/artifact.py, specfuse/monitor/issues.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T03#2

- **criterion:** `test_fingerprint_ignores_message_id`: two artifacts differing only in message id
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.DlqAcknowledgement.test_fingerprint_ignores_message_id -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, specfuse/monitor/artifact.py, specfuse/monitor/issues.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T03#3

- **criterion:** A non-`dlq` artifact never carries a message id, and its path is unchanged
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.DlqAcknowledgement.test_non_dlq_artifact_carries_no_message_id tests.test_monitor_finding_lifecycle_end_to_end.ClosedFindingReopens -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, specfuse/monitor/artifact.py, specfuse/monitor/issues.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T03#4

- **criterion:** The existing `tests.test_service_bus_dlq_adapter` passes unchanged except where a
- **oracle:** python3 -m unittest tests.test_service_bus_dlq_adapter -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, specfuse/monitor/artifact.py, specfuse/monitor/issues.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T04#1

- **criterion:** `tests/test_monitor_finding_lifecycle_end_to_end.py::HeartbeatGrace`, skipped by
- **oracle:** python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end.HeartbeatGrace -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_heartbeat_adapter.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T04#2

- **criterion:** `tests/test_heartbeat_adapter.py::TestHeartbeatGrace::test_missed_firing_after_emission_still_fires`:
- **oracle:** python3 -m unittest tests.test_heartbeat_adapter.TestHeartbeatGrace.test_missed_firing_after_emission_still_fires -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_heartbeat_adapter.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T04#3

- **criterion:** `tests/test_heartbeat_adapter.py::TestHeartbeatGrace::test_component_without_any_heartbeat_files_nothing` passes.
- **oracle:** python3 -m unittest tests.test_heartbeat_adapter.TestHeartbeatGrace.test_component_without_any_heartbeat_files_nothing -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_heartbeat_adapter.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T04#4

- **criterion:** The query passes `tests/test_app_insights_query_schema_check.py`'s
- **oracle:** python3 -m unittest tests.test_app_insights_query_schema_check tests.test_heartbeat_adapter -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_heartbeat_adapter.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T04#5

- **criterion:** The `observed_text` of a real silent finding still names the expected firing and
- **oracle:** python3 -m unittest tests.test_heartbeat_adapter.TestHeartbeatGrace -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_heartbeat_adapter.py, tests/test_monitor_finding_lifecycle_end_to_end.py

### T05#1

- **criterion:** `tests/test_monitor_finding_context_end_to_end.py::ErrorLogsContext` and
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.ErrorLogsContext tests.test_monitor_finding_context_end_to_end.EveryFinding -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/artifact.py, specfuse/monitor/issues.py, specfuse/monitor/cli.py, specfuse/monitor/redaction.py, specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T05#2

- **criterion:** `test_fingerprint_unchanged_by_context`: two artifacts differing only in `context`
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.EveryFinding.test_fingerprint_unchanged_by_context -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/artifact.py, specfuse/monitor/issues.py, specfuse/monitor/cli.py, specfuse/monitor/redaction.py, specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T05#3

- **criterion:** `_error_logs_query` passes `schema_violations` with no new findings, the adapter
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.ErrorLogsContext.test_query_has_no_schema_violations tests.test_monitor_finding_context_end_to_end.EveryFinding.test_secret_in_context_value_is_redacted_in_body -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/artifact.py, specfuse/monitor/issues.py, specfuse/monitor/cli.py, specfuse/monitor/redaction.py, specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T06#1

- **criterion:** `tests/test_monitor_finding_context_end_to_end.py::Http5xxContext` (skipped by T01,
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.Http5xxContext -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T06#2

- **criterion:** A 5xx with no exception and no dependency still files, with those sections absent
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.Http5xxContext.test_no_exception_and_no_dependency_still_files_without_those_sections -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T06#3

- **criterion:** `_http_5xx_query` passes `schema_violations` and the adapter issues exactly one
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.Http5xxContext.test_query_has_no_schema_violations tests.test_monitor_finding_context_end_to_end.Http5xxContext.test_sections_present -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, tests/test_monitor_finding_context_end_to_end.py

### T07#1

- **criterion:** `tests/test_monitor_finding_context_end_to_end.py::DlqContext` (skipped by T01,
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.DlqContext -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py

### T07#2

- **criterion:** A message with no application properties and a non-JSON body still files, with
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.DlqContext.test_bare_message_still_files -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py

### T07#3

- **criterion:** The existing `tests.test_service_bus_dlq_adapter` passes, and the transport still
- **oracle:** python3 -m unittest tests.test_service_bus_dlq_adapter -b && ! grep -nE "\.(receive_messages|complete_message|abandon_message|dead_letter_message|defer_message)\(" specfuse/monitor/providers/azure_service_bus.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py

### T08#1

- **criterion:** `tests/test_monitor_finding_context_end_to_end.py::HeartbeatContext` and
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.HeartbeatContext tests.test_monitor_finding_context_end_to_end.QueueStalledContext -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py

### T08#2

- **criterion:** `_heartbeat_query` passes `schema_violations` and the heartbeat adapter still issues
- **oracle:** python3 -m unittest tests.test_monitor_finding_context_end_to_end.HeartbeatContext.test_query_is_one_bounded_schema_clean_query tests.test_heartbeat_adapter tests.test_app_insights_query_schema_check -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py

### T08#3

- **criterion:** `grep -n 'unittest.skip' tests/test_monitor_finding_context_end_to_end.py tests/test_monitor_finding_lifecycle_end_to_end.py`
- **oracle:** ! grep -n 'unittest.skip' tests/test_monitor_finding_context_end_to_end.py tests/test_monitor_finding_lifecycle_end_to_end.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`
- **attempt:** `1`
- **covers:** specfuse/monitor/providers/azure_app_insights.py, specfuse/monitor/providers/azure_service_bus.py, tests/test_monitor_finding_context_end_to_end.py
