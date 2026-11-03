### T01#1

- **criterion:** The oracle's clause-1 class fails on HEAD and passes after, including its `single`-mode
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause1ConcurrentPrsDoNotConflict -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T01#2

- **criterion:** Clause 5's writer test passes: with no `changelog.mode` key, `add` leaves no `changelog.d/`
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause5NoModeKeyBehavesAsBefore.test_add_without_mode_edits_changelog_md -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_judge_path_registry tests.test_changelog_release_wiring -b` passes.
- **oracle:** python3 -m unittest tests.test_judge_path_registry tests.test_changelog_release_wiring -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T02#1

- **criterion:** The oracle's clause-2 class is unskipped, fails on HEAD and passes after, for all three guards.
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause2GuardsReadFragments -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/closing_requirements.py, specfuse/loop/lint_closing.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T02#2

- **criterion:** `grep -c "parse_changelog" specfuse/loop/lint_closing.py` is 0: the check goes through the helper.
- **oracle:** grep -c parse_changelog specfuse/loop/lint_closing.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/closing_requirements.py, specfuse/loop/lint_closing.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T02#3

- **criterion:** `python3 -m unittest tests.test_terminal_auto_close_changelog tests.test_load_bearing_close_lint tests.test_judge_path_registry -b` passes.
- **oracle:** python3 -m unittest tests.test_terminal_auto_close_changelog tests.test_load_bearing_close_lint tests.test_judge_path_registry -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/closing_requirements.py, specfuse/loop/lint_closing.py, specfuse/loop/loop.py, specfuse/loop/arm_eval.py, tests/test_changelog_fragments.py

### T03#1

- **criterion:** The oracle's clause-3 class is unskipped, fails on HEAD and passes after, driving `release()`
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause3CollateAtRelease -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, scripts/bump_version.py, tests/test_changelog_fragments.py

### T03#2

- **criterion:** Clause 5's release test passes: with no fragments, `release()` output is byte-identical to
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause5NoModeKeyBehavesAsBefore.test_release_without_fragments_unchanged -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, scripts/bump_version.py, tests/test_changelog_fragments.py

### T03#3

- **criterion:** `python3 -m unittest tests.test_changelog_release_wiring tests.test_changelog_append_only -b` passes.
- **oracle:** python3 -m unittest tests.test_changelog_release_wiring tests.test_changelog_append_only -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, scripts/bump_version.py, tests/test_changelog_fragments.py

### T04#1

- **criterion:** The oracle's clause-4 class is unskipped, fails on HEAD and passes after: wrong class, bad
- **oracle:** python3 -m unittest tests.test_changelog_fragments.TestClause4CheckGate -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, .specfuse/verification.yml, tests/test_changelog_fragments.py

### T04#2

- **criterion:** `python3 -m specfuse.loop.changelog_fragments check` exits zero on this repository.
- **oracle:** python3 -m specfuse.loop.changelog_fragments check
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/changelog_fragments.py, .specfuse/verification.yml, tests/test_changelog_fragments.py

### T05#1

- **criterion:** A test in `tests/test_ids_migrate_all.py` fails on HEAD and passes after: an unkeyed
- **oracle:** python3 -m unittest tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py

### T05#2

- **criterion:** `python3 -m unittest tests.test_ids_migrate tests.test_ids_migrate_all -b` passes.
- **oracle:** python3 -m unittest tests.test_ids_migrate tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py

### T06#1

- **criterion:** `grep -c "changelog_fragments add" plugins/specfuse/skills/fix-bug/SKILL.md` is at least 1.
- **oracle:** grep -c 'changelog_fragments add' plugins/specfuse/skills/fix-bug/SKILL.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/fix-bug/SKILL.md, .specfuse/skills/fix-bug/SKILL.md, .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/lifecycles.md, specfuse/loop/data/docs/lifecycles.md

### T06#2

- **criterion:** `grep -c "changelog_fragments add" .specfuse/rules/close-discipline.md` is at least 1.
- **oracle:** grep -c 'changelog_fragments add' .specfuse/rules/close-discipline.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/fix-bug/SKILL.md, .specfuse/skills/fix-bug/SKILL.md, .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/lifecycles.md, specfuse/loop/data/docs/lifecycles.md

### T06#3

- **criterion:** `diff .specfuse/rules/close-discipline.md specfuse/loop/data/rules/close-discipline.md` is empty.
- **oracle:** diff .specfuse/rules/close-discipline.md specfuse/loop/data/rules/close-discipline.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/fix-bug/SKILL.md, .specfuse/skills/fix-bug/SKILL.md, .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/lifecycles.md, specfuse/loop/data/docs/lifecycles.md

### T06#4

- **criterion:** `python3 -m unittest tests.test_plugin_prose_cross_refs -b` passes.
- **oracle:** python3 -m unittest tests.test_plugin_prose_cross_refs -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/fix-bug/SKILL.md, .specfuse/skills/fix-bug/SKILL.md, .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/lifecycles.md, specfuse/loop/data/docs/lifecycles.md

### T07#1

- **criterion:** A test fails on HEAD and passes after: on this repository `python3 -m specfuse.loop.layout get
- **oracle:** python3 -m unittest tests.test_changelog_fragments.RepoOptInTests -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** .specfuse/layout.yml, tests/test_changelog_fragments.py

### T07#2

- **criterion:** `python3 -m unittest tests.test_changelog_schema tests.test_terminal_auto_close_changelog tests.test_changelog_fragments -b` passes.
- **oracle:** python3 -m unittest tests.test_changelog_schema tests.test_terminal_auto_close_changelog tests.test_changelog_fragments -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `c51318c37302fe6c6ff925b2fe34a8cc6dbce69e`
- **attempt:** `1`
- **covers:** .specfuse/layout.yml, tests/test_changelog_fragments.py
