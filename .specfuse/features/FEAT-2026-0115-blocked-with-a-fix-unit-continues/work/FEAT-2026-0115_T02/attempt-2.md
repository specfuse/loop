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
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/tests-20260926T162942423823Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/lint-20260926T162942443924Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/agent-policy-example-lint-20260926T162942536429Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 79 events.jsonl file(s), 2360 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/event-type-gate-20260926T162942658007Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/roadmap-link-gate-20260926T162942694912Z.log
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
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/arm-sweep-gate-20260926T162943003965Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/monitoring-example-lint-20260926T162943046524Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b
test_blocked_with_blocked_next_under_review_autonomy_escalates (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_blocked_next_under_review_autonomy_escalates) ... ok
test_blocked_with_valid_blocked_next_inserts_and_continues (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_valid_blocked_next_inserts_and_continues) ... ok
test_blocked_without_blocked_next_escalates_unchanged (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_without_blocked_next_escalates_unchanged) ... ok

----------------------------------------------------------------------
Ran 3 tests in 1.089s

OK
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/feature_oracle-20260926T162944204690Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
index 2af381e..6d3cd38 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
@@ -3,6 +3,13 @@ gate: 1
 status: open
 feature_oracle: "python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b"
 cost_budget_usd: 40.00
+baseline:
+  sha: 7e07caf298c9e96888f2c3c6a8509c39dbe237ca
+  probed_at: 2026-09-26T16:21:53.659261+00:00
+  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:19e6172a5f8ed4e64796dcbec75a5c167dfaa326:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:612ca64d43e0122e585a31aafed54ab76f9c1edb:7236c0b74a800bb48cc28ab6dc46543c53a4dc90:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:912ded344993c8a5b83f67b92c7b5b2123b7d914:97bcab1bc7244262cec901f46035f51dfdd07278:9f955f7d0d0875a1252a7fedb2e56a6960f4abda:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
+  entry_sha: 7e07caf298c9e96888f2c3c6a8509c39dbe237ca
+  source: attributed:FEAT-2026-0115/T02
+  failing: []
 ---
 
 # Gate 1 — a block that names its fix unit continues the gate
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
index 157b977..4e2d0ec 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0115/T02
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 5.00
 produces_driver_helper:
   - evaluate_fix_unit_insertion
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
index 1533839..b3851c8 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
@@ -1,2 +1,8 @@
 {"timestamp": "2026-09-26T16:07:55.017630+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "41048ff7ee55ba7073d12340f9127755ea7868a8", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/41048ff7ee55ba7073d12340f9127755ea7868a8/specfuse/loop"}}
 {"timestamp": "2026-09-26T16:07:55.476395+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "cf216bce2d2e79559f3bcd3e9830291acde3f85c", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/cf216bce2d2e79559f3bcd3e9830291acde3f85c/specfuse/loop"}}
+{"timestamp": "2026-09-26T16:07:55.669080+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:19:40.764611+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 704.898, "cost_usd": 3.4867226, "input_tokens": 168, "output_tokens": 62635, "cache_read_input_tokens": 10972223, "cache_creation_input_tokens": 166398, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-01-insert-the-named-fix-unit.md", "specfuse/loop/data/schemas/driver-event.schema.json", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_e2e.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:19:40.764798+00:00", "correlation_id": "FEAT-2026-0115/T01", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 704.898, "cost_usd": 3.4867226, "input_tokens": 168, "output_tokens": 62635, "cache_read_input_tokens": 10972223, "cache_creation_input_tokens": 166398}], "type": "implementation", "re_arm_count": 0, "cost_usd": 3.486723, "cumulative_cost_usd": 3.486723, "attempts_lifetime": 1, "planned_cost_usd": 7.0}}
+{"timestamp": "2026-09-26T16:19:40.771267+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0115/T01", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "cf216bce2d2e79559f3bcd3e9830291acde3f85c", "next_pin_tree": "6c51f3a9fcb3496872bc74e3a21c67a5313de1c9"}}
+{"timestamp": "2026-09-26T16:19:40.840109+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:21:53.575161+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 132.687, "cost_usd": 0.4302788, "input_tokens": 22, "output_tokens": 10406, "cache_read_input_tokens": 643834, "cache_creation_input_tokens": 49352, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "ERROR: test_fix_unit_insertion_refused (unittest.loader._FailedTest.test_fix_unit_insertion_refused)", "failure_excerpt": "### tests: FAIL\nERROR: test_fix_unit_insertion_refused (unittest.loader._FailedTest.test_fix_unit_insertion_refused)\nImportError: Failed to import test module: test_fix_unit_insertion_refused\nTraceback (most recent call last):\nModuleNotFoundError:\n...\nve.md link graph \u2014 0 error(s), 1 warning(s)\nNO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output \u2014 the lines above are the tail only, and may be unrelated to the failure. Run the command directly.", "files_touched": [], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}

```
