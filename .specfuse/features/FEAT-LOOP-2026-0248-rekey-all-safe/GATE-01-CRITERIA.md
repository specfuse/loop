### T01#1

- **criterion:** The oracle's clause-1 and clause-2 classes fail on HEAD and pass after. Clause 2 has a
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T01#2

- **criterion:** `python3 -m unittest tests.test_agent_policy_queue tests.test_agent_policy_schema tests.test_ids_migrate tests.test_ids_migrate_all -b`
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T02#1

- **criterion:** The clause-3 class: in a fixture repository with a real folder `FEAT-2026-0005-real`,
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_migrate_all_repo_stays_valid.py

### T02#2

- **criterion:** `tests/test_ids_migrate_all.py` passes, with any case whose expectation encoded the old
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_migrate_all_repo_stays_valid.py

### T03#1

- **criterion:** The clause-4 class: `--include-prose docs` rewrites a mention in `docs/` and not one in
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T03#2

- **criterion:** `tests/test_ids_migrate_all.py` and `tests/test_ids_migrate.py` pass.
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T04#1

- **criterion:** The clause-5 class: rehearse exits zero with a passing command and non-zero with a
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md

### T04#2

- **criterion:** `python3 -m unittest tests.test_ids_migrate_all tests.test_caller_check_ratchet tests.test_judge_path_registry -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md

### T06#1

- **criterion:** A new oracle test in `tests/test_migrate_all_repo_stays_valid.py`: in a fixture
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all tests.test_caller_check_ratchet -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T07#1

- **criterion:** New oracle tests: with an uncommitted edit to a tracked file and a new untracked file
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T07#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T08#1

- **criterion:** New oracle test: a fixture repository with a planned, folderless row queued in
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T08#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_aliases tests.test_agent_policy_queue -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T05#1

- **criterion:** The command above exits zero, and its output (validation result plus the test
- **state:** `unverified`

### T05#2

- **criterion:** `python3 -m unittest discover -s tests -b` passes on the real, unrenamed tree.
- **state:** `unverified`

### T05#3

- **criterion:** No assertion is deleted or loosened to pass; every edited test still fails if the
- **state:** `unverified`
