### tests: PASS
```
$ python3 -m unittest discover -s tests -v

[21:32:05] -- FEAT-2026-9301/G1-LESSONS [lessons] model=claude-haiku-4-5-20251001 effort=low
   [21:32:05] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed f23f96b29d2354d59e9d1c0084d50dd21f2c500a

[21:32:05] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   [21:32:05] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 8ea6e4d18e8d21577b8bab7e6730da9940197a67

[21:32:05] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   [21:32:05] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 444f6e519702c8f2b6a869c1092fe7f6c5c0f00a

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
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.qpmJS9lRAa: Operation not permitted
not ok 2 hook exits 1 when the scanner reports a leak
# (from function `setup' in test file tests/leak_scan_hook.bats, line 11)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.G2HanethOy: Operation not permitted
not ok 3 hook exits 1 when the scanner is missing
# (from function `setup' in test file tests/leak_scan_hook.bats, line 11)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.Mf34t1Bd7d: Operation not permitted
```

### sync-scaffold-bats: FAIL
```
$ bats tests/sync_scaffold.bats
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.e0MaA9P3bH: Operation not permitted
not ok 3 sync is idempotent (second run exits 0 and reports unchanged)
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.59AbR9e4Ps: Operation not permitted
not ok 4 sync updates a stale file and reports it
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.winc2haFJr: Operation not permitted
not ok 5 sync exits non-zero if canonical source dir is missing
# (from function `setup' in test file tests/sync_scaffold.bats, line 13)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.N2dT4psAut: Operation not permitted
```

### init-sh-shim-bats: FAIL
```
$ bats tests/init_sh_shim.bats
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.SUxklB09Fr: Operation not permitted
not ok 3 upgrade --dry-run: forwards --dry-run flag to specfuse upgrade
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.4Zsry2dpB2: Operation not permitted
not ok 4 specfuse absent: exits non-zero with pip install hint
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.e137qKPX7Q: Operation not permitted
not ok 5 no target: exits non-zero with usage
# (from function `setup' in test file tests/init_sh_shim.bats, line 17)
#   `TESTDIR="$(mktemp -d)"' failed
# mktemp: mkdtemp failed on /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp.NcnSSuDK6I: Operation not permitted
```