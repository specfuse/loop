### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
    subprocess.run(
    ~~~~~~~~~~~~~~^
        ["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/subprocess.py", line 577, in run
    raise CalledProcessError(retcode, process.args,
                             output=stdout, stderr=stderr)
subprocess.CalledProcessError: Command '['git', '-C', '/tmp/claude-501/tmp8a61vxcy', 'commit', '-q', '-m', 'init']' returned non-zero exit status 128.

----------------------------------------------------------------------
Ran 505 tests in 11.643s

FAILED (errors=20)
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
		Low: 33
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 33
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
    subprocess.run(
    ~~~~~~~~~~~~~~^
        ["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/subprocess.py", line 577, in run
    raise CalledProcessError(retcode, process.args,
                             output=stdout, stderr=stderr)
subprocess.CalledProcessError: Command '['git', '-C', '/tmp/claude-501/tmpiik9wum8', 'commit', '-q', '-m', 'init']' returned non-zero exit status 128.

----------------------------------------------------------------------
Ran 505 tests in 11.679s

FAILED (errors=20)
```