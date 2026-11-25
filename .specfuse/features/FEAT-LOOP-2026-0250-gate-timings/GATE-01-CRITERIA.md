### T01#1

- **criterion:** `tests.test_gate_timings.TestAttemptGateEvents` fails on HEAD and passes after. It drives one
- **oracle:** python3 -m unittest tests.test_gate_timings.TestAttemptGateEvents -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T01#2

- **criterion:** `TestNothingExistingChanges` asserts `gate_result` is in the schema's `event_types`.
- **oracle:** python3 -m unittest tests.test_gate_timings.TestNothingExistingChanges.test_gate_result_in_schema_event_types -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton tests.test_loop_worklist_injection -b`
- **oracle:** python3 -m unittest tests.test_dispatch_skeleton tests.test_loop_worklist_injection -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T02#1

- **criterion:** `tests.test_gate_timings.TestAttemptSplit` fails on HEAD and passes after. With a stubbed
- **oracle:** python3 -m unittest tests.test_gate_timings.TestAttemptSplit -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T02#2

- **criterion:** The same class asserts an attempt whose agent reports `blocked` records `verify_seconds: 0`.
- **oracle:** python3 -m unittest tests.test_gate_timings.TestAttemptSplit.test_blocked_records_zero_verify -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T02#3

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton tests.test_files_changed_auto_repair -b`
- **oracle:** python3 -m unittest tests.test_dispatch_skeleton tests.test_files_changed_auto_repair -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#1

- **criterion:** `tests.test_gate_timings.TestBaselineAndBroadPhases` fails on HEAD and passes after. It
- **oracle:** python3 -m unittest tests.test_gate_timings.TestBaselineAndBroadPhases -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#2

- **criterion:** `broad_run_result` and `baseline_attribution` payloads are unchanged; the same class asserts
- **oracle:** python3 -m unittest tests.test_gate_timings.TestBaselineAndBroadPhases -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#3

- **criterion:** The narrow tier passes with no existing broad-run or baseline test edited.
- **oracle:** python3 -m unittest tests.test_gate_timings tests.test_dispatch_skeleton tests.test_events_stats -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T04#1

- **criterion:** `tests.test_gate_timings.TestStatsReport` fails on HEAD and passes after: a corpus with
- **oracle:** python3 -m unittest tests.test_gate_timings.TestStatsReport -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py

### T04#2

- **criterion:** `python3 -m unittest tests.test_events_stats -b` passes unchanged.
- **oracle:** python3 -m unittest tests.test_events_stats -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py

### T04#3

- **criterion:** `grep -c "unittest.skip" tests/test_gate_timings.py` prints `0`.
- **oracle:** grep -c "unittest.skip" tests/test_gate_timings.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `158389e952114613487622605f9b1cf5eef49ad1`
- **attempt:** `1`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py
