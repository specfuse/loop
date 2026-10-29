### T01#1

- **criterion:** The oracle's clause-1 and clause-2 classes fail on HEAD and pass after. Clause 2 has a
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause1PolicyResolvesOldIds tests.test_migrate_all_repo_stays_valid.Clause2ApplyValidatesResult -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T01#2

- **criterion:** `python3 -m unittest tests.test_agent_policy_queue tests.test_agent_policy_schema tests.test_ids_migrate tests.test_ids_migrate_all -b`
- **oracle:** python3 -m unittest tests.test_agent_policy_queue tests.test_agent_policy_schema tests.test_ids_migrate tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T02#1

- **criterion:** The clause-3 class: in a fixture repository with a real folder `FEAT-LOOP-2026-0005-real`,
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause3RewriteClassification -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_migrate_all_repo_stays_valid.py

### T02#2

- **criterion:** `tests/test_ids_migrate_all.py` passes, with any case whose expectation encoded the old
- **oracle:** python3 -m unittest tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_migrate_all_repo_stays_valid.py

### T03#1

- **criterion:** The clause-4 class: `--include-prose docs` rewrites a mention in `docs/` and not one in
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause4ProseScoping -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T03#2

- **criterion:** `tests/test_ids_migrate_all.py` and `tests/test_ids_migrate.py` pass.
- **oracle:** python3 -m unittest tests.test_ids_migrate_all tests.test_ids_migrate -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T04#1

- **criterion:** The clause-5 class: rehearse exits zero with a passing command and non-zero with a
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause5Rehearse -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md

### T04#2

- **criterion:** `python3 -m unittest tests.test_ids_migrate_all tests.test_caller_check_ratchet tests.test_judge_path_registry -b`
- **oracle:** python3 -m unittest tests.test_ids_migrate_all tests.test_caller_check_ratchet tests.test_judge_path_registry -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md

### T06#1

- **criterion:** A new oracle test in `tests/test_migrate_all_repo_stays_valid.py`: in a fixture
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause6ValidatesWithOwnCode -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all tests.test_caller_check_ratchet -b`
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all tests.test_caller_check_ratchet -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T07#1

- **criterion:** New oracle tests: with an uncommitted edit to a tracked file and a new untracked file
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause5Rehearse.test_dirty_tree_is_rehearsed_not_refused -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T07#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all -b`
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T08#1

- **criterion:** New oracle test: a fixture repository with a planned, folderless row queued in
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid.Clause7AliasFollowsRoadmapRow -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T08#2

- **criterion:** `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_aliases tests.test_agent_policy_queue -b`
- **oracle:** python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_aliases tests.test_agent_policy_queue -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_migrate_all_repo_stays_valid.py

### T05#1

- **criterion:** The command above exits zero, and its output (validation result plus the test
- **oracle:** python3 -m specfuse.loop.ids migrate --all --include-prose '.specfuse/features/**' '.specfuse/roadmap.md' '.specfuse/roadmap-archive.md' '.specfuse/LEARNINGS*.md' --rehearse
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`

### T05#2

- **criterion:** `python3 -m unittest discover -s tests -b` passes on the real, unrenamed tree.
- **oracle:** python3 -m unittest discover -s tests -b (the driver's broad run, `broad_run_result` ok true at 19:42:39 UTC; not re-run in this session)
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `ce07fdb6a731e50b520ff9fcc8c9cb7fcabf3a84`
- **attempt:** `1`

### T05#3

- **criterion:** No assertion is deleted or loosened to pass; every edited test still fails if the
- **kind:** `broad`
- **state:** `unverified`
- **note:** needs the gate diff of the edited test modules; this session may not run git and the unit's RESULT notes are not retained in events.jsonl
