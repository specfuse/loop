### T01#1

- **criterion:** `tests/test_failure_signature_names_the_test.py` fails on HEAD before this
- **state:** `unverified`

### T01#2

- **criterion:** That module asserts, for the #3414 pair of Maven reports, two different
- **oracle:** python3 -m unittest tests.test_failure_signature_names_the_test -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T01#3

- **criterion:** It also asserts that a report whose tail carries only the summary yields
- **oracle:** python3 -m unittest tests.test_failure_signature_names_the_test -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T01#4

- **criterion:** `python3 -m unittest tests.test_attempt_outcome_emission tests.test_attempt_outcome_contract tests.test_surefire_run_level_signature tests.test_failure_signature_fail_prefix tests.test_failure_signature_skips_log_noise tests.test_maven_failure_excerpt -v -b`
- **oracle:** python3 -m unittest tests.test_attempt_outcome_emission tests.test_attempt_outcome_contract tests.test_surefire_run_level_signature tests.test_failure_signature_fail_prefix tests.test_failure_signature_skips_log_noise tests.test_maven_failure_excerpt -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T01H#1

- **criterion:** `bandit -r specfuse .specfuse/scripts -ll` exits 0 (it reports one High B324
- **oracle:** bandit -r specfuse .specfuse/scripts -ll
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T01H#2

- **criterion:** `python3 -m unittest tests.test_failure_signature_names_the_test tests.test_spinning_repeat_same_failing_set -v -b`
- **oracle:** python3 -m unittest tests.test_failure_signature_names_the_test tests.test_spinning_repeat_same_failing_set -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_spinning_repeat_same_failing_set.py` fails on HEAD before this
- **state:** `unverified`

### T02#2

- **criterion:** That module asserts, through `loop.run()` with a stubbed `verify` that fails
- **oracle:** python3 -m unittest tests.test_spinning_repeat_same_failing_set -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T02#3

- **criterion:** It also asserts that an exhausted unit's `spinning_detected` escalation
- **oracle:** python3 -m unittest tests.test_spinning_repeat_same_failing_set -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T02#4

- **criterion:** `python3 -m unittest tests.test_attempt_outcome_emission tests.test_spinning_rearm_gate tests.test_deterministic_refusal_repeat tests.test_failure_signature_names_the_test -v -b`
- **oracle:** python3 -m unittest tests.test_attempt_outcome_emission tests.test_spinning_rearm_gate tests.test_deterministic_refusal_repeat tests.test_failure_signature_names_the_test -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_replay_spin_failing_sets.py` fails on HEAD before this unit's
- **state:** `unverified`

### T03#2

- **criterion:** That module asserts, on a synthetic events file with one historical
- **oracle:** python3 -m unittest tests.test_replay_spin_failing_sets -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T03#3

- **criterion:** `grep -c "failing_tests" docs/methodology.md` reports at least 1, and after
- **oracle:** grep -c "failing_tests" docs/methodology.md && python3 -m unittest tests.test_scaffold_data_in_sync -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`

### T03#4

- **criterion:** `python3 -m unittest tests.test_replay_spin -v -b` exits 0 with no edit to
- **oracle:** python3 -m unittest tests.test_replay_spin -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `b43afd5`
- **attempt:** `1`
