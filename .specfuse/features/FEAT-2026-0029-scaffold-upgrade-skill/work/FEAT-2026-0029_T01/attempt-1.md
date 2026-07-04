### tests: PASS
```
$ python3 -m unittest discover -s tests -v

[21:26:45] -- FEAT-2026-9301/G1-LESSONS [lessons] model=claude-haiku-4-5-20251001 effort=low
   [21:26:45] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed fa075e3de7533ac5f5ccdffa49557ffb8de84ddc

[21:26:45] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   [21:26:45] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 94bee351f33c2a2c7a4b650b4cea8131a8e44833

[21:26:46] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   [21:26:46] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed f304d1b2d71462a32c24b562b754366db0bfad02

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
```

### security: PASS
```
$ bandit -r specfuse .specfuse/scripts -ll
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 7

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 53
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 53
Files skipped (0):
```

### coverage: PASS
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
Name                              Stmts   Miss  Cover
-----------------------------------------------------
specfuse/loop/__init__.py             0      0   100%
specfuse/loop/_miniyaml.py          235      0   100%
specfuse/loop/adopt_feature.py       70      2    97%
specfuse/loop/gate_eval.py          285     10    96%
specfuse/loop/gh_backend.py          24      1    96%
specfuse/loop/gh_features.py         40      4    90%
specfuse/loop/lint_plan.py          303     21    93%
specfuse/loop/loop.py              1613    159    90%
specfuse/loop/scaffold.py           331     12    96%
specfuse/loop/validate_event.py     127      4    97%
-----------------------------------------------------
TOTAL                              3028    213    93%
```

### leak-scan: PASS
```
$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: clean
```

### leak-scan-hook: FAIL
```
$ bats tests/leak_scan_hook.bats
1..3
not ok 1 hook exits 0 when the scanner is clean
# (from function `setup' in test file tests/leak_scan_hook.bats, line 11)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.PQyFtH6Jvg: Operation not permitted
not ok 2 hook exits 1 when the scanner reports a leak
# (from function `setup' in test file tests/leak_scan_hook.bats, line 11)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.VdBmeftBwh: Operation not permitted
not ok 3 hook exits 1 when the scanner is missing
# (from function `setup' in test file tests/leak_scan_hook.bats, line 11)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.BEQnkNk3q7: Operation not permitted
```

### sync-scaffold-bats: FAIL
```
$ bats tests/sync_scaffold.bats
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.32FagQg28g: Operation not permitted
not ok 3 sync is idempotent (second run exits 0 and reports unchanged)
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.1qbFMoInLd: Operation not permitted
not ok 4 sync updates a stale file and reports it
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.3xKh3BZHFk: Operation not permitted
not ok 5 sync exits non-zero if canonical source dir is missing
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.v8oAZhwA0F: Operation not permitted
```

### init-sh-shim-bats: FAIL
```
$ bats tests/init_sh_shim.bats
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.dlp7AaPJJ0: Operation not permitted
not ok 3 upgrade --dry-run: forwards --dry-run flag to specfuse upgrade
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.yuzPbOYOG8: Operation not permitted
not ok 4 specfuse absent: exits non-zero with pip install hint
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.cb7Dg6d88z: Operation not permitted
not ok 5 no target: exits non-zero with usage
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.xTSU7aqYcY: Operation not permitted
```