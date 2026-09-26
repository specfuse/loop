### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
AssertionError: True is not false
FAIL: test_doc_set_missing_for_retrospective_fails (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_doc_set_missing_for_retrospective_fails)
Traceback (most recent call last):
AssertionError: True is not false
FAIL: test_empty_list_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_empty_list_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false : empty 'code' list must fail, not pass
FAIL: test_failing_gate_failure_message_is_distinguishable_from_config_error (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_failing_gate_failure_message_is_distinguishable_from_config_error)
Traceback (most recent call last):
AssertionError: True is not false
FAIL: test_missing_set_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_missing_set_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false : missing 'code' set must fail, not pass
FAIL: test_null_value_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_null_value_for_type_fails_with_config_message)
Traceback (most recent call last):
... (10767 line(s) elided) ...
AssertionError: True is not false

======================================================================
FAIL: test_passing_gate_with_real_command_still_works (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_passing_gate_with_real_command_still_works)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christian/Specfuse/loop/tests/test_verify_empty_gate_set.py", line 86, in test_passing_gate_with_real_command_still_works
    self.assertIn("PASS", msg)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^
AssertionError: 'PASS' not found in '(stub)'

----------------------------------------------------------------------
Ran 4431 tests in 141.583s

FAILED (failures=32, errors=451, skipped=3)
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/tests-20260926T191252655176Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/lint-20260926T191252707197Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/agent-policy-example-lint-20260926T191252788686Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 81 events.jsonl file(s), 2438 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/event-type-gate-20260926T191252914139Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/roadmap-link-gate-20260926T191252954355Z.log
```

### arm-sweep-gate: PASS
```
$ python3 .specfuse/scripts/arm_sweep_gate.py
branch-observation table:
  budget_projection          observed=[clean, fired]; NEVER not_evaluable
  judge_editing              observed=[clean, fired]; NEVER not_evaluable
  decision_class_paths       observed=[clean, fired]; NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean, fired]; NEVER not_evaluable
evaluable=42 evaluated=42 could_not_evaluate=0 excluded_no_baseline=45
ok: 42 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/arm-sweep-gate-20260926T191253281158Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/monitoring-example-lint-20260926T191253324790Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b
test_carried_forward_and_reverify_partition_and_persist (tests.test_reclose_carries_narrow_greens_e2e.TestRearmCarriesNarrowGreensByDefault.test_carried_forward_and_reverify_partition_and_persist) ... ok
test_carry_forward_narrow_greens_false_resets_everything (tests.test_reclose_carries_narrow_greens_e2e.TestRearmCarryCanBeDisabled.test_carry_forward_narrow_greens_false_resets_everything) ... ok

----------------------------------------------------------------------
Ran 2 tests in 1.601s

OK
full output: .specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/work/gate-logs/feature_oracle-20260926T191255000805Z.log
```

NOTE: narrow_command declared on gate 'tests' did not fire this attempt: the selection resolved to nothing under narrow_selection.test_roots ['tests/'] (produces: offered .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example); ran the full command instead. Set `narrow_selection.test_roots` (and `format`) on that gate in .specfuse/verification.yml if this repo's tests live elsewhere.

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-04-document-the-contract.md b/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-04-document-the-contract.md
index ee1c113..53f24ac 100644
--- a/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-04-document-the-contract.md
+++ b/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-04-document-the-contract.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0117/T04
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - .specfuse/rules/close-discipline.md
@@ -11,6 +11,11 @@ produces:
   - specfuse/loop/data/docs/methodology.md
   - .specfuse/verification.yml.example
   - specfuse/loop/data/verification.yml.example
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.25.0
+started_at: 2026-09-26T19:08:57.766250+00:00
 ---
 
 # Document the carry-forward rule where closes and authors read it
diff --git a/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl b/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl
index 6ffeacd..d73ac98 100644
--- a/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl
@@ -8,3 +8,7 @@
 {"timestamp": "2026-09-26T19:01:19.122142+00:00", "correlation_id": "FEAT-2026-0117/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 534.972, "cost_usd": 1.9156398, "input_tokens": 106, "output_tokens": 51124, "cache_read_input_tokens": 4866579, "cache_creation_input_tokens": 107718, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-02-a-green-is-invalidated-by-its-covered-paths.md", ".specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl", "specfuse/loop/criteria_state.py", "specfuse/loop/loop.py", "tests/test_carried_green_invalidated_by_diff.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-09-26T19:01:19.122285+00:00", "correlation_id": "FEAT-2026-0117/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 534.972, "cost_usd": 1.9156398, "input_tokens": 106, "output_tokens": 51124, "cache_read_input_tokens": 4866579, "cache_creation_input_tokens": 107718}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.91564, "cumulative_cost_usd": 1.91564, "attempts_lifetime": 1, "planned_cost_usd": 5.0}}
 {"timestamp": "2026-09-26T19:01:19.128197+00:00", "correlation_id": "FEAT-2026-0117", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0117/T02", "driver_paths": ["specfuse/loop/criteria_state.py", "specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "72650ffc42745e5c32e76668e4b1a5c43058c046", "next_pin_tree": "3901c16e5f469219b28a1e4182a7568dc87d2e03"}}
+{"timestamp": "2026-09-26T19:01:19.168693+00:00", "correlation_id": "FEAT-2026-0117/T03", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T19:08:57.692701+00:00", "correlation_id": "FEAT-2026-0117/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 458.415, "cost_usd": 1.7065134, "input_tokens": 98, "output_tokens": 30002, "cache_read_input_tokens": 5012867, "cache_creation_input_tokens": 100931, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/WU-03-carried-and-re-measured-on-the-close-and-the-judge.md", ".specfuse/features/FEAT-2026-0117-re-close-measures-only-what-failed/events.jsonl", "specfuse/loop/closing_requirements.py", "specfuse/loop/judge.py", "specfuse/loop/lint_closing.py", "tests/test_carry_accounting_close_and_judge.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-09-26T19:08:57.692843+00:00", "correlation_id": "FEAT-2026-0117/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 458.415, "cost_usd": 1.7065134, "input_tokens": 98, "output_tokens": 30002, "cache_read_input_tokens": 5012867, "cache_creation_input_tokens": 100931}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.706513, "cumulative_cost_usd": 1.706513, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
+{"timestamp": "2026-09-26T19:08:57.698645+00:00", "correlation_id": "FEAT-2026-0117", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0117/T03", "driver_paths": ["specfuse/loop/closing_requirements.py", "specfuse/loop/judge.py", "specfuse/loop/lint_closing.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "72650ffc42745e5c32e76668e4b1a5c43058c046", "next_pin_tree": "21898601779afc0736ede5f6035597b37325bf17"}}
diff --git a/.specfuse/rules/close-discipline.md b/.specfuse/rules/close-discipline.md
index 48bea25..72b8af4 100644
--- a/.specfuse/rules/close-discipline.md
+++ b/.specfuse/rules/close-discipline.md
@@ -222,6 +222,20 @@ green would be an unsound coverage claim; it re-runs on every close attempt.
 inferred by a reader, the same posture §2 already takes on the hedged-record
 `kind:`. `specfuse lint --closing` is the check.
 
+**Carrying a `narrow` green forward is conditional, not automatic.** A `narrow`
+entry also carries `covers:` — the path(s) it proved, driver-seeded from the
+oracle's own scope; a criterion with no derivable `covers:` is never carried,
+it re-measures every attempt. On a re-close, a carried entry's green is
+invalidated the moment the gate diff since its `proved_at_sha` touches a path
+in its `covers:` — the earlier proof no longer describes the tree it is being
+read against. A carried entry additionally records `carried_from_attempt`, the
+attempt number whose measurement it is standing in for, so a reader can trace
+a green back to where it was actually taken. A re-close's `## Measurements`
+states the split explicitly: `carried forward: N criteria, re-measured: M`.
+This is a project-level default (`defaults.carry_forward_narrow_greens` in
+`verification.yml`, default `true`) — every `broad` oracle and the gate's
+`feature_oracle` re-run on every attempt regardless, per §1.
+
 ## Split with project-local rules
 
 These are the generic obligations. The concrete grounding — which command is
diff --git a/.specfuse/verification.yml.example b/.specfuse/verification.yml.example
index 347e43c..2488ff7 100644
--- a/.specfuse/verification.yml.example
+++ b/.specfuse/verification.yml.example
@@ -142,6 +142,14 @@
 #   max_fix_units_per_unit: 2  # cap on `fix_unit_inserted` insertions per
 #                               # blocked unit before it escalates instead
 #                               # (FEAT-2026-0115). Defaults to 2.
+#   carry_forward_narrow_greens: true  # whether a re-close may carry forward
+#                               # a `narrow` criterion's green from an earlier
+#                               # close attempt of the same gate instead of
+#                               # re-measuring it. Defaults to true; a carried
+#                               # green is invalidated when the gate diff since
+#                               # its `proved_at_sha` touches a path in its
+#                               # `covers:` (`.specfuse/rules/close-discipline.md`
+#                               # §5, FEAT-2026-0117).
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
@@ -150,6 +158,7 @@
 #   produces_amendable: false
 #   fix_unit_insertion: true
 #   max_fix_units_per_unit: 2
+#   carry_forward_narrow_greens: true
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's
diff --git a/docs/methodology.md b/docs/methodology.md
index 037d6ba..a939ddf 100644
--- a/docs/methodology.md
+++ b/docs/methodology.md
@@ -131,6 +131,21 @@ it mostly does not need. Author-set unless marked driver-owned.
   entries are accepted (`defaults.produces_amendable: true`): the paths dropped
   from this unit's recorded `produces:` (`.specfuse/rules/result-contract.md`).
 
+### 2.2 `GATE-NN-CRITERIA.md` entry fields (FEAT-2026-0117)
+
+Per-criterion state, driver-owned unless noted:
+
+- `covers:` — driver-seeded path(s) a `narrow` oracle proved; absent when no
+  scope is derivable, in which case the criterion is never carried forward.
+- `carried_from_attempt` — the attempt number a carried-forward green's
+  measurement actually ran against, written by the close that carries it.
+- `invalidated_by` — the path from `covers:` a later gate diff touched,
+  written when a carry is refused because the earlier proof no longer holds.
+- `defaults.carry_forward_narrow_greens` — project-level `verification.yml`
+  default (`true`) gating whether re-closes may carry a `narrow` green forward
+  at all; see `.specfuse/rules/close-discipline.md` §5 for the invalidation
+  rule and `## Measurements` line this drives.
+
 ## 3. Work unit types
 
 Nine types share one state machine; type affects only who handles the unit and
diff --git a/specfuse/loop/data/docs/methodology.md b/specfuse/loop/data/docs/methodology.md
index 037d6ba..a939ddf 100644
--- a/specfuse/loop/data/docs/methodology.md
+++ b/specfuse/loop/data/docs/methodology.md
@@ -131,6 +131,21 @@ it mostly does not need. Author-set unless marked driver-owned.
   entries are accepted (`defaults.produces_amendable: true`): the paths dropped
   from this unit's recorded `produces:` (`.specfuse/rules/result-contract.md`).
 
+### 2.2 `GATE-NN-CRITERIA.md` entry fields (FEAT-2026-0117)
+
+Per-criterion state, driver-owned unless noted:
+
+- `covers:` — driver-seeded path(s) a `narrow` oracle proved; absent when no
+  scope is derivable, in which case the criterion is never carried forward.
+- `carried_from_attempt` — the attempt number a carried-forward green's
+  measurement actually ran against, written by the close that carries it.
+- `invalidated_by` — the path from `covers:` a later gate diff touched,
+  written when a carry is refused because the earlier proof no longer holds.
+- `defaults.carry_forward_narrow_greens` — project-level `verification.yml`
+  default (`true`) gating whether re-closes may carry a `narrow` green forward
+  at all; see `.specfuse/rules/close-discipline.md` §5 for the invalidation
+  rule and `## Measurements` line this drives.
+
 ## 3. Work unit types
 
 Nine types share one state machine; type affects only who handles the unit and
diff --git a/specfuse/loop/data/rules/close-discipline.md b/specfuse/loop/data/rules/close-discipline.md
index 48bea25..72b8af4 100644
--- a/specfuse/loop/data/rules/close-discipline.md
+++ b/specfuse/loop/data/rules/close-discipline.md
@@ -222,6 +222,20 @@ green would be an unsound coverage claim; it re-runs on every close attempt.
 inferred by a reader, the same posture §2 already takes on the hedged-record
 `kind:`. `specfuse lint --closing` is the check.
 
+**Carrying a `narrow` green forward is conditional, not automatic.** A `narrow`
+entry also carries `covers:` — the path(s) it proved, driver-seeded from the
+oracle's own scope; a criterion with no derivable `covers:` is never carried,
+it re-measures every attempt. On a re-close, a carried entry's green is
+invalidated the moment the gate diff since its `proved_at_sha` touches a path
+in its `covers:` — the earlier proof no longer describes the tree it is being
+read against. A carried entry additionally records `carried_from_attempt`, the
+attempt number whose measurement it is standing in for, so a reader can trace
+a green back to where it was actually taken. A re-close's `## Measurements`
+states the split explicitly: `carried forward: N criteria, re-measured: M`.
+This is a project-level default (`defaults.carry_forward_narrow_greens` in
+`verification.yml`, default `true`) — every `broad` oracle and the gate's
+`feature_oracle` re-run on every attempt regardless, per §1.
+
 ## Split with project-local rules
 
 These are the generic obligations. The concrete grounding — which command is
diff --git a/specfuse/loop/data/verification.yml.example b/specfuse/loop/data/verification.yml.example
index 347e43c..2488ff7 100644
--- a/specfuse/loop/data/verification.yml.example
+++ b/specfuse/loop/data/verification.yml.example
@@ -142,6 +142,14 @@
 #   max_fix_units_per_unit: 2  # cap on `fix_unit_inserted` insertions per
 #                               # blocked unit before it escalates instead
 #                               # (FEAT-2026-0115). Defaults to 2.
+#   carry_forward_narrow_greens: true  # whether a re-close may carry forward
+#                               # a `narrow` criterion's green from an earlier
+#                               # close attempt of the same gate instead of
+#                               # re-measuring it. Defaults to true; a carried
+#                               # green is invalidated when the gate diff since
+#                               # its `proved_at_sha` touches a path in its
+#                               # `covers:` (`.specfuse/rules/close-discipline.md`
+#                               # §5, FEAT-2026-0117).
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
@@ -150,6 +158,7 @@
 #   produces_amendable: false
 #   fix_unit_insertion: true
 #   max_fix_units_per_unit: 2
+#   carry_forward_narrow_greens: true
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's

```
