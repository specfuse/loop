### tests: PASS
```
$ python3 -m unittest discover -s tests -v
task_started with branch: null is valid (nullable per Phase 1 Finding 5). ... ok
test_template_coverage_checked (test_validate_event.TestValidateEventValid.test_template_coverage_checked) ... ok
test_test_plan_authored (test_validate_event.TestValidateEventValid.test_test_plan_authored) ... ok
test_completely_empty_cfg_fails (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_completely_empty_cfg_fails) ... ok
test_doc_set_missing_for_retrospective_fails (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_doc_set_missing_for_retrospective_fails) ... ok
test_empty_list_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_empty_list_for_type_fails_with_config_message) ... ok
test_failing_gate_failure_message_is_distinguishable_from_config_error (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_failing_gate_failure_message_is_distinguishable_from_config_error) ... ok
test_missing_set_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_missing_set_for_type_fails_with_config_message) ... ok
test_null_value_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_null_value_for_type_fails_with_config_message) ... ok
test_passing_gate_with_real_command_still_works (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_passing_gate_with_real_command_still_works) ... ok

----------------------------------------------------------------------
Ran 337 tests in 9.119s

OK
```

### lint: PASS
```
$ ruff check .specfuse/scripts tests scripts
All checks passed!
```

### security: PASS
```
$ bandit -r .specfuse/scripts -ll
		Undefined: 0
		Low: 27
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 27
Files skipped (0):
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.14.3
```

### coverage: FAIL
```
$ coverage run --source=.specfuse/scripts -m unittest discover -s tests && coverage report --fail-under=70
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "tests/test_validate_event.py", line 46, in <module>
    _spec.loader.exec_module(ve)  # type: ignore[union-attr]
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File ".specfuse/scripts/validate-event.py", line 51, in <module>
    sys.exit(2)
    ~~~~~~~~^^^
SystemExit: 2


----------------------------------------------------------------------
Ran 280 tests in 9.277s

FAILED (errors=1)
```