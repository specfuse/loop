### T01#1

- **criterion:** `tests.test_gate_parallel_cache.TestParallel` fails on HEAD and passes after: with
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestParallel)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T01#2

- **criterion:** `TestDefaultUnchanged` passes: for a set of a passing gate, a failing gate and a gate that
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestDefaultUnchanged)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T01#3

- **criterion:** `TestResultOrder` passes: when a later-declared gate finishes first, results, the joined
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestResultOrder)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T01#4

- **criterion:** `python3 -m unittest tests.test_gate_timings tests.test_run_progress tests.test_dispatch_skeleton -b`
- **oracle:** HOME=$TMPDIR/home python3 -m unittest tests.test_gate_timings tests.test_run_progress tests.test_dispatch_skeleton -b
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T02#1

- **criterion:** `tests.test_gate_parallel_cache.TestParallelSafety` fails on HEAD and passes after (remove its
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestParallelSafety)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/progress.py, tests/test_gate_parallel_cache.py

### T02#2

- **criterion:** With four parallel gates, `events.jsonl` has exactly one `gate_started` and one
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestParallelSafety)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/progress.py, tests/test_gate_parallel_cache.py

### T02#3

- **criterion:** A stub gate reading `STATUS.json` while another gate runs sees `phase: gate` and both names
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestParallelSafety)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/progress.py, tests/test_gate_parallel_cache.py

### T02#4

- **criterion:** `python3 -m unittest tests.test_run_progress tests.test_gate_timings -b` passes.
- **oracle:** HOME=$TMPDIR/home python3 -m unittest tests.test_run_progress tests.test_gate_timings -b
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/progress.py, tests/test_gate_parallel_cache.py

### T03#1

- **criterion:** `tests.test_gate_parallel_cache.TestCacheHit` fails on HEAD and passes after (remove its
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestCacheHit)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T03#2

- **criterion:** `TestCacheMiss` passes: each of editing, adding and deleting a matching file, `chmod +x` on
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestCacheMiss)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T03#3

- **criterion:** `TestNeverForAVerdict` passes: with a stored PASS, `run_gate_broad_set`, `probe_baseline`,
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestNeverForAVerdict)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T03#4

- **criterion:** Show the hit test fails with the cache argument removed from `verify()`'s call (state it in
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestCacheHit) on a temporary copy with the cache argument removed from verify()
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T03#5

- **criterion:** `python3 -m unittest tests.test_gate_timings tests.test_dispatch_skeleton -b` passes.
- **oracle:** HOME=$TMPDIR/home python3 -m unittest tests.test_gate_timings tests.test_dispatch_skeleton -b
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_gate_parallel_cache.py

### T04#1

- **criterion:** `tests.test_gate_parallel_cache.TestConfigurationErrors` fails on HEAD and passes after
- **oracle:** python3 -m unittest tests.test_gate_parallel_cache -v -b (class TestConfigurationErrors)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_gate_parallel_cache.py

### T04#2

- **criterion:** `tests.test_gate_parallel_cache` has no `unittest.skip` left.
- **oracle:** grep -nE "skip(Test)?\(" tests/test_gate_parallel_cache.py (only two win32 skipIf guards)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_gate_parallel_cache.py

### T04#3

- **criterion:** `python3 -m unittest tests.test_gate_timings tests.test_run_progress -b` passes, and
- **oracle:** HOME=$TMPDIR/home python3 -m unittest tests.test_gate_timings tests.test_run_progress -b; cmp docs/methodology.md specfuse/loop/data/docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_gate_parallel_cache.py
