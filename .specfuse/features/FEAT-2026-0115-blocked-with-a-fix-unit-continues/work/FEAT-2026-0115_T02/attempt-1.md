### tests: FAIL
```
$ python3 -m unittest tests.test_fix_unit_insertion_refused -v -b

======================================================================
ERROR: test_fix_unit_insertion_refused (unittest.loader._FailedTest.test_fix_unit_insertion_refused)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_fix_unit_insertion_refused
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
ModuleNotFoundError: No module named 'tests.test_fix_unit_insertion_refused'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/tests-20260926T162151783788Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/lint-20260926T162151798882Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/agent-policy-example-lint-20260926T162151876917Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 79 events.jsonl file(s), 2358 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/event-type-gate-20260926T162151996657Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/roadmap-link-gate-20260926T162152036274Z.log
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
evaluable=40 evaluated=40 could_not_evaluate=0 excluded_no_baseline=47
ok: 40 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/arm-sweep-gate-20260926T162152348910Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/monitoring-example-lint-20260926T162152391241Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b
test_blocked_with_blocked_next_under_review_autonomy_escalates (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_blocked_next_under_review_autonomy_escalates) ... ok
test_blocked_with_valid_blocked_next_inserts_and_continues (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_valid_blocked_next_inserts_and_continues) ... ok
test_blocked_without_blocked_next_escalates_unchanged (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_without_blocked_next_escalates_unchanged) ... ok

----------------------------------------------------------------------
Ran 3 tests in 1.068s

OK
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/feature_oracle-20260926T162153527930Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
index 157b977..ca487d7 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
@@ -1,14 +1,19 @@
 ---
 id: FEAT-2026-0115/T02
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 5.00
 produces_driver_helper:
   - evaluate_fix_unit_insertion
 produces:
   - specfuse/loop/loop.py
   - tests/test_fix_unit_insertion_refused.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.25.0
+started_at: 2026-09-26T16:19:40.839959+00:00
 ---
 
 # The arm predicate's stop classes and two caps decide whether the draft is inserted
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
index 1533839..dea190e 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
@@ -1,2 +1,6 @@
 {"timestamp": "2026-09-26T16:07:55.017630+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "41048ff7ee55ba7073d12340f9127755ea7868a8", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/41048ff7ee55ba7073d12340f9127755ea7868a8/specfuse/loop"}}
 {"timestamp": "2026-09-26T16:07:55.476395+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "cf216bce2d2e79559f3bcd3e9830291acde3f85c", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/cf216bce2d2e79559f3bcd3e9830291acde3f85c/specfuse/loop"}}
+{"timestamp": "2026-09-26T16:07:55.669080+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:19:40.764611+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 704.898, "cost_usd": 3.4867226, "input_tokens": 168, "output_tokens": 62635, "cache_read_input_tokens": 10972223, "cache_creation_input_tokens": 166398, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-01-insert-the-named-fix-unit.md", "specfuse/loop/data/schemas/driver-event.schema.json", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_e2e.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:19:40.764798+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 704.898, "cost_usd": 3.4867226, "input_tokens": 168, "output_tokens": 62635, "cache_read_input_tokens": 10972223, "cache_creation_input_tokens": 166398}], "type": "implementation", "re_arm_count": 0, "cost_usd": 3.486723, "cumulative_cost_usd": 3.486723, "attempts_lifetime": 1, "planned_cost_usd": 7.0}}
+{"timestamp": "2026-09-26T16:19:40.771267+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0115/T01", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "cf216bce2d2e79559f3bcd3e9830291acde3f85c", "next_pin_tree": "6c51f3a9fcb3496872bc74e3a21c67a5313de1c9"}}

```
