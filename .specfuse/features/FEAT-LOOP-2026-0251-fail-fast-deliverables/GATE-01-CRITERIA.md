### T01#1

- **criterion:** `tests.test_fail_fast_deliverables.TestProducesNotInDiffEarly` fails on HEAD and passes
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_fail_fast_deliverables.py

### T01#2

- **criterion:** The early refusal's `failure_class`, `failure_signature` and `summary` equal what the late
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_fail_fast_deliverables.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` passes; any
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_fail_fast_deliverables.py

### T02#1

- **criterion:** `tests.test_fail_fast_deliverables.TestPresenceEarly` fails on HEAD and passes after: an
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_fail_fast_deliverables.py

### T02#2

- **criterion:** `TestOptOut` fails on HEAD and passes after: with `fail_fast_deliverables: false`, each of
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_fail_fast_deliverables.py

### T02#3

- **criterion:** `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example` is
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example, tests/test_fail_fast_deliverables.py

### T03#1

- **criterion:** `tests.test_fail_fast_deliverables.TestTreeAndNote` fails on HEAD and passes after. It
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_fail_fast_deliverables.py

### T03#2

- **criterion:** The cap holds: a diff of 30 paths lists 20 and the count of the remaining 10.
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_fail_fast_deliverables.py

### T04#1

- **criterion:** `tests.test_fail_fast_deliverables.TestArmTimeWarning` fails on HEAD and passes after: a
- **state:** `unverified`
- **covers:** specfuse/loop/lint_plan.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_fail_fast_deliverables.py

### T04#2

- **criterion:** `specfuse lint` exits 0 on every feature folder under `.specfuse/features/` (WARN only).
- **state:** `unverified`
- **covers:** specfuse/loop/lint_plan.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_fail_fast_deliverables.py

### T04#3

- **criterion:** The RESULT's notes give the measured count and total from the Context bullet.
- **state:** `unverified`
- **covers:** specfuse/loop/lint_plan.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_fail_fast_deliverables.py

### T04#4

- **criterion:** `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` is empty.
- **state:** `unverified`
- **covers:** specfuse/loop/lint_plan.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_fail_fast_deliverables.py

### T04#5

- **criterion:** `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`.
- **state:** `unverified`
- **covers:** specfuse/loop/lint_plan.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_fail_fast_deliverables.py
