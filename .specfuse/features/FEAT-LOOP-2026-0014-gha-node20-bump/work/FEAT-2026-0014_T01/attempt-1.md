### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
AssertionError: ValueError not raised

======================================================================
FAIL: test_unsandboxed_true_without_rationale_raises (test_loop_unsandboxed.TestLoadWURefusesUnjustified.test_unsandboxed_true_without_rationale_raises)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_loop_unsandboxed.py", line 87, in test_unsandboxed_true_without_rationale_raises
    with self.assertRaises(ValueError) as cx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 361 tests in 9.791s

FAILED (failures=2, errors=4)
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
$ coverage run --source=.specfuse/scripts -m unittest discover -s tests && coverage report --fail-under=90
AssertionError: ValueError not raised

======================================================================
FAIL: test_unsandboxed_true_without_rationale_raises (test_loop_unsandboxed.TestLoadWURefusesUnjustified.test_unsandboxed_true_without_rationale_raises)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_loop_unsandboxed.py", line 87, in test_unsandboxed_true_without_rationale_raises
    with self.assertRaises(ValueError) as cx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 361 tests in 10.174s

FAILED (failures=2, errors=4)
```