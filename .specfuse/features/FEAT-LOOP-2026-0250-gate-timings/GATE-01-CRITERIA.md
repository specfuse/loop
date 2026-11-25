### T01#1

- **criterion:** `tests.test_gate_timings.TestAttemptGateEvents` fails on HEAD and passes after. It drives one
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T01#2

- **criterion:** `TestNothingExistingChanges` asserts `gate_result` is in the schema's `event_types`.
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton tests.test_loop_worklist_injection -b`
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_gate_timings.py

### T02#1

- **criterion:** `tests.test_gate_timings.TestAttemptSplit` fails on HEAD and passes after. With a stubbed
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T02#2

- **criterion:** The same class asserts an attempt whose agent reports `blocked` records `verify_seconds: 0`.
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T02#3

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton tests.test_files_changed_auto_repair -b`
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#1

- **criterion:** `tests.test_gate_timings.TestBaselineAndBroadPhases` fails on HEAD and passes after. It
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#2

- **criterion:** `broad_run_result` and `baseline_attribution` payloads are unchanged; the same class asserts
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T03#3

- **criterion:** The narrow tier passes with no existing broad-run or baseline test edited.
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_gate_timings.py

### T04#1

- **criterion:** `tests.test_gate_timings.TestStatsReport` fails on HEAD and passes after: a corpus with
- **state:** `unverified`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py

### T04#2

- **criterion:** `python3 -m unittest tests.test_events_stats -b` passes unchanged.
- **state:** `unverified`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py

### T04#3

- **criterion:** `grep -c "unittest.skip" tests/test_gate_timings.py` prints `0`.
- **state:** `unverified`
- **covers:** specfuse/loop/events_stats.py, docs/methodology.md, tests/test_gate_timings.py
