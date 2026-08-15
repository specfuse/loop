### T12#1

- **criterion:** `tests/test_agent_queue_read.py::TestQueueWorkability::test_queue_entry_without_a_feature_folder_needs_drafting`
- **oracle:** `python3 -m unittest tests.test_agent_queue_read.TestQueueWorkability.test_queue_entry_without_a_feature_folder_needs_drafting`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#2

- **criterion:** `specfuse/agent/queue_read.py` exposes five disposition constants —
- **oracle:** `python3 -c "from specfuse.agent.queue_read import DISPOSITION_WORKABLE, DISPOSITION_NEEDS_DRAFTING, DISPOSITION_BLOCKED, DISPOSITION_DONE, DISPOSITION_UNREADABLE, classify_queue_entry, select_workable, resolve_wip_limit, resolve_gate_review" && python3 -m unittest tests.test_agent_queue_read.TestQueueWorkability -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_queue_read.TestQueueWorkability.test_queue_entry_without_a_feature_folder_needs_drafting`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#4

- **criterion:** `select_workable(queue, features, features_errors, *, wip_limit)` returns
- **oracle:** `python3 -m unittest tests.test_agent_queue_read.TestSelectWorkable -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#5

- **criterion:** `resolve_wip_limit(policy_path)` returns an `int >= 1` and
- **oracle:** `python3 -m unittest tests.test_agent_queue_read.TestResolveWipLimit tests.test_agent_queue_read.TestResolveGateReview -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#6

- **criterion:** `specfuse/agent/state.py` exposes `read_feature_summaries` as a public name
- **oracle:** `python3 -c "from specfuse.agent.state import read_feature_summaries, _read_features; assert read_feature_summaries is _read_features" && python3 -m unittest tests.test_agent_queue_read.TestStateAlias -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T12#7

- **criterion:** The module performs no write, issues no `gh` call, and reads no work-unit
- **oracle:** `python3 -m unittest tests.test_agent_queue_read.TestModuleStructure -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#1

- **criterion:** `tests/test_agent_driver_invoke.py::TestHaltClassification::test_awaiting_review_is_not_confused_with_feature_done`
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestHaltClassification.test_awaiting_review_is_not_confused_with_feature_done`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#2

- **criterion:** `specfuse/agent/driver_invoke.py` exposes
- **oracle:** `python3 -c "from specfuse.agent.driver_invoke import build_invocation, classify_halt, advance_feature, HALT_ADVANCED, HALT_AWAITING_REVIEW, HALT_NOT_ARMED, HALT_BLOCKED, HALT_FEATURE_DONE, HALT_DRIVER_ERROR" && python3 -m unittest tests.test_agent_driver_invoke.TestBuildInvocation tests.test_agent_driver_invoke.TestModuleStructure.test_no_in_process_driver_import -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestHaltClassification.test_awaiting_review_is_not_confused_with_feature_done`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#4

- **criterion:** `classify_halt(...)` returns one of six exported constants —
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestHaltClassification -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#5

- **criterion:** `HALT_BLOCKED` carries the blocked work unit's id and the `reason` field from
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestAdvanceFeature.test_blocked_reads_the_appended_human_escalation_row tests.test_agent_driver_invoke.TestAdvanceFeature.test_lock_held_stderr_reaches_detail_verbatim -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#6

- **criterion:** `advance_feature(runner, feature_id, *, features_root, command=...)` reads the
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestAdvanceFeature -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T13#7

- **criterion:** The module issues no `git` command, no `gh` command, and writes no file. A
- **oracle:** `python3 -m unittest tests.test_agent_driver_invoke.TestModuleStructure -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#1

- **criterion:** `tests/test_agent_provider_feature.py::TestFeatureProvider::test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised`
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#2

- **criterion:** `specfuse/agent/providers/feature.py` defines a provider whose `advertise`
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_item_id_shape_for_workable_entry tests.test_agent_provider_feature.TestFeatureProvider.test_advertise_rereads_live_state_and_item_id_changes_between_calls -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#3

- **criterion:** The same test passes after this WU's edits.
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#4

- **criterion:** `execute` invokes `driver_invoke.advance_feature` for `WORKABLE` items **only**
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_halt_advanced_completes_with_no_escalation tests.test_agent_provider_feature.TestFeatureProvider.test_halt_feature_done_completes_with_no_escalation tests.test_agent_provider_feature.TestFeatureProvider.test_halt_awaiting_review_under_human_escalates_gate_review tests.test_agent_provider_feature.TestFeatureProvider.test_halt_not_armed_escalates_gate_review tests.test_agent_provider_feature.TestFeatureProvider.test_halt_blocked_escalates_blocked_wu_with_wu_id_and_reason tests.test_agent_provider_feature.TestFeatureProvider.test_halt_driver_error_escalates_blocked_wu_with_stderr tests.test_agent_provider_feature.TestFeatureProvider.test_needs_drafting_reaches_no_driver_invocation -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#5

- **criterion:** A `NEEDS_DRAFTING` entry escalates with `category="drafting-needed"` and a
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_needs_drafting_reaches_no_driver_invocation tests.test_agent_provider_feature.TestFeatureProvider.test_blocked_entry_escalates_blocked_wu_with_disposition_in_detail tests.test_agent_provider_feature.TestFeatureProvider.test_unreadable_entry_escalates_blocked_wu_with_disposition_in_detail -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#6

- **criterion:** `rules.features.gate_review` decides what an `awaiting_review` halt does, read
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_wip_limit_dial_caps_workable_items tests.test_agent_provider_feature.TestFeatureProvider.test_gate_review_dial_switches_between_human_and_auto tests.test_agent_provider_feature.TestFeatureProvider.test_halt_awaiting_review_under_auto_completes_with_no_escalation -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#7

- **criterion:** The provider is registered in `default_providers()` (`run.py:385`) and
- **oracle:** `python3 -c "from specfuse.agent.run import default_providers; names=[type(p).__name__ for p in default_providers(repo='owner/repo')]; assert 'FeatureProvider' in names, names" && python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_registered_in_default_providers tests.test_agent_provider_feature.TestFeatureProvider.test_only_driver_invocation_no_git_or_mutating_gh -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T14#8

- **criterion:** `reconcile` returns `None` and issues no call — a test asserts it. This is the
- **oracle:** `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_reconcile_is_a_noop -b`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
