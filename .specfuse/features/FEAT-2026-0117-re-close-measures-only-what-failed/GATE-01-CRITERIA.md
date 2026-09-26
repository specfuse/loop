### T01#1

- **criterion:** `tests/test_reclose_carries_narrow_greens_e2e.py` fails on HEAD before this
- **oracle:** python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T01#2

- **criterion:** That module asserts, over two `loop.run()` passes with a re-arm between
- **oracle:** python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T01#3

- **criterion:** A second case sets `defaults: carry_forward_narrow_greens: false` and
- **oracle:** python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T01#4

- **criterion:** `python3 -m unittest tests.test_criteria_state tests.test_criteria_worklist tests.test_loop_criteria_skeleton tests.test_loop_criteria_survival tests.test_lint_closing_criteria -v -b`
- **oracle:** python3 -m unittest tests.test_criteria_state tests.test_criteria_worklist tests.test_loop_criteria_skeleton tests.test_loop_criteria_survival tests.test_lint_closing_criteria -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T02#1

- **criterion:** `tests/test_carried_green_invalidated_by_diff.py` fails on HEAD before this
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_carried_green_invalidated_by_diff.py

### T02#2

- **criterion:** That module asserts, over two `loop.run()` passes with a commit between
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_carried_green_invalidated_by_diff.py

### T02#3

- **criterion:** It also asserts `derive_criterion_covers` for a unittest oracle and a Maven
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_carried_green_invalidated_by_diff.py

### T02#4

- **criterion:** `python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e tests.test_criteria_state tests.test_criteria_worklist tests.test_lint_closing_criteria -v -b`
- **oracle:** python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e tests.test_criteria_state tests.test_criteria_worklist tests.test_lint_closing_criteria -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, specfuse/loop/criteria_state.py, tests/test_carried_green_invalidated_by_diff.py

### T02H#1

- **criterion:** `python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_changed_file_test_selection -v -b`
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_changed_file_test_selection -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** tests/test_carried_green_invalidated_by_diff.py

### T02H#2

- **criterion:** `python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b`
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** tests/test_carried_green_invalidated_by_diff.py

### T02H2#1

- **criterion:** The reproduction command above exits 0 (errors on HEAD before this
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_reclose_carries_narrow_greens_e2e tests.test_claude_resolution tests.test_dispatch_skills_index -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** tests/test_carried_green_invalidated_by_diff.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T02H2#2

- **criterion:** `python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_reclose_carries_narrow_greens_e2e -v -b`
- **oracle:** python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_reclose_carries_narrow_greens_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** tests/test_carried_green_invalidated_by_diff.py, tests/test_reclose_carries_narrow_greens_e2e.py

### T03#1

- **criterion:** `tests/test_carry_accounting_close_and_judge.py` fails on HEAD before this
- **oracle:** python3 -m unittest tests.test_carry_accounting_close_and_judge -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/judge.py, specfuse/loop/closing_requirements.py, tests/test_carry_accounting_close_and_judge.py

### T03#2

- **criterion:** That module asserts the judge bundle text for a criteria file with one
- **oracle:** python3 -m unittest tests.test_carry_accounting_close_and_judge -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/judge.py, specfuse/loop/closing_requirements.py, tests/test_carry_accounting_close_and_judge.py

### T03#3

- **criterion:** `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_lint_closing_criteria tests.test_lint_closing_criteria_pristine -v -b`
- **oracle:** python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_lint_closing_criteria tests.test_lint_closing_criteria_pristine -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** specfuse/loop/judge.py, specfuse/loop/closing_requirements.py, tests/test_carry_accounting_close_and_judge.py

### T04#1

- **criterion:** `grep -c "carried_from_attempt" .specfuse/rules/close-discipline.md docs/methodology.md`
- **oracle:** grep -c "carried_from_attempt" .specfuse/rules/close-discipline.md docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example

### T04#2

- **criterion:** `grep -n "carry_forward_narrow_greens" .specfuse/verification.yml.example docs/methodology.md`
- **oracle:** grep -n "carry_forward_narrow_greens" .specfuse/verification.yml.example docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example

### T04#3

- **criterion:** After running `scripts/sync-scaffold.sh`,
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example

### T04#4

- **criterion:** `python3 .specfuse/scripts/leak_scan.py --all` exits 0.
- **oracle:** python3 .specfuse/scripts/leak_scan.py --all
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `731177cf7cbb133aab87d9e7d70fc3403eaa7553`
- **attempt:** `1`
- **covers:** .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example
