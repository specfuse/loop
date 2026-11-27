### T01#1

- **criterion:** `tests.test_run_progress.TestPhaseEvents` fails on HEAD and passes after. Through
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T01#2

- **criterion:** `TestStatusFile` passes: during the session the stub reads `STATUS.json` with every field
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T01#3

- **criterion:** `TestDriverLines` passes: captured driver output has one line per phase change and contains
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T01#4

- **criterion:** `python3 -m unittest tests.test_judge_path_registry tests.test_driver_event_registry_covers_emitters tests.test_validate_event_driver_types tests.test_gate_timings tests.test_dispatch_skeleton -b`
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_run_progress.py, tests/test_judge_path_registry.py
- **invalidated_by:** specfuse/loop/progress.py

### T02#1

- **criterion:** `tests.test_run_progress.TestHeartbeat` fails on HEAD and passes after (remove its skip).
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T02#2

- **criterion:** After `run()` returns, and after an attempt whose stubbed session raises, no thread started
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T02#3

- **criterion:** `resolve_heartbeat_seconds` returns 30 for a missing key, `"x"`, `0` and `-5`, and 7 for `7`.
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T02#4

- **criterion:** `python3 -m unittest tests.test_fail_fast_deliverables tests.test_dispatch_skeleton -b`
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_run_progress.py, tests/test_fail_fast_deliverables.py
- **invalidated_by:** specfuse/loop/progress.py

### T03#1

- **criterion:** `tests.test_run_progress.TestWatch` fails on HEAD and passes after (remove its skip). Given
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T03#2

- **criterion:** An `updated_at` older than three heartbeat intervals prints `no update for Ns`.
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T03#3

- **criterion:** `phase: stopped` ends the watch with exit 0; no status file exits 1 with a message naming
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T03#4

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton -b` passes.
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, tests/test_run_progress.py, tests/test_dispatch_skeleton.py
- **invalidated_by:** specfuse/loop/progress.py

### T04#1

- **criterion:** `tests.test_run_progress.TestStopNotification` fails on HEAD and passes after (remove its
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/agent_policy.py, .specfuse/agent-policy.yml.example, docs/getting-started.md, specfuse/loop/data/docs/getting-started.md, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T04#2

- **criterion:** A command that exits 1, one that sleeps past the timeout (patched to 1 s in the test) and
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/agent_policy.py, .specfuse/agent-policy.yml.example, docs/getting-started.md, specfuse/loop/data/docs/getting-started.md, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T04#3

- **criterion:** A message containing `; touch pwned` does not create `pwned`.
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/agent_policy.py, .specfuse/agent-policy.yml.example, docs/getting-started.md, specfuse/loop/data/docs/getting-started.md, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py

### T04#4

- **criterion:** `python3 -m unittest tests.test_agent_policy_schema tests.test_notify tests.test_notify_escalation -b`
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/agent_policy.py, .specfuse/agent-policy.yml.example, docs/getting-started.md, specfuse/loop/data/docs/getting-started.md, tests/test_run_progress.py, tests/test_agent_policy_schema.py
- **invalidated_by:** specfuse/loop/progress.py

### T04#5

- **criterion:** `tests.test_run_progress` has no `unittest.skip` left.
- **state:** `unverified`
- **covers:** specfuse/loop/progress.py, specfuse/loop/loop.py, specfuse/loop/agent_policy.py, .specfuse/agent-policy.yml.example, docs/getting-started.md, specfuse/loop/data/docs/getting-started.md, tests/test_run_progress.py
- **invalidated_by:** specfuse/loop/progress.py
