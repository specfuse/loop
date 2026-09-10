### T01#1

- **criterion:** `tests/test_guard_repair_e2e.py` fails on HEAD before this unit's edits (the
- **oracle:** python3 -m unittest tests.test_guard_repair_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T01#2

- **criterion:** That module asserts, end to end through `loop.run()`: attempt 1's
- **oracle:** python3 -m unittest tests.test_guard_repair_e2e.TestGuardRefusalRetainsTree.test_retained_tree_lets_attempt_2_finish_the_job -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T01#3

- **criterion:** A second case in the same module sets `defaults: retain_on_guard_refusal:
- **oracle:** python3 -m unittest tests.test_guard_repair_e2e.TestGuardRefusalRetainsTree.test_retain_disabled_falls_back_to_todays_reset -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T01#4

- **criterion:** `python3 -m unittest tests.test_loop_files_changed_guard tests.test_deliverable_presence_gate tests.test_empty_files_escalation tests.test_produces_justification -v` exits 0 with no edit to those modules; if one of them asserts the tree was reset after a refusal, stop with `status: blocked` naming the test (that is an arming finding, not a test to rewrite).
- **oracle:** python3 -m unittest tests.test_loop_files_changed_guard tests.test_deliverable_presence_gate tests.test_empty_files_escalation tests.test_produces_justification -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T01#5

- **criterion:** `python3 -m unittest tests.test_attempt_outcome_contract -v` exits 0: no new
- **oracle:** python3 -m unittest tests.test_attempt_outcome_contract -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_guard_repair_prompt.py::test_retained_guard_note_leads_with_the_complaint`
- **oracle:** python3 -m unittest tests.test_guard_repair_prompt.RetainedGuardNoteTest.test_retained_guard_note_leads_with_the_complaint -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T02#2

- **criterion:** `::test_unretained_guard_note_is_unchanged`: with the kill switch off the
- **oracle:** python3 -m unittest tests.test_guard_repair_prompt.RetainedGuardNoteTest.test_unretained_guard_note_is_unchanged -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T02#3

- **criterion:** `python3 -m unittest tests.test_attempt_outcome_emission tests.test_convergent_iteration -v`
- **oracle:** python3 -m unittest tests.test_attempt_outcome_emission tests.test_convergent_iteration -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T02#4

- **criterion:** `python3 -m unittest tests.test_guard_repair_e2e -v` still exits 0.
- **oracle:** python3 -m unittest tests.test_guard_repair_e2e -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_files_changed_auto_repair.py::test_untouched_non_deliverable_is_dropped_and_the_attempt_passes`
- **oracle:** python3 -m unittest tests.test_files_changed_auto_repair.TestAutoRepairFilesChangedUnit.test_untouched_non_deliverable_is_dropped_and_the_attempt_passes tests.test_files_changed_auto_repair.TestExecuteUnitAttemptAutoRepair.test_untouched_non_deliverable_is_dropped_and_the_attempt_passes -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T03#2

- **criterion:** `::test_untouched_deliverable_still_refuses`: the same RESULT with the
- **oracle:** python3 -m unittest tests.test_files_changed_auto_repair.TestAutoRepairFilesChangedUnit.test_untouched_deliverable_still_refuses tests.test_files_changed_auto_repair.TestExecuteUnitAttemptAutoRepair.test_untouched_deliverable_still_refuses -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T03#3

- **criterion:** `::test_nothing_to_repair_is_a_plain_pass`: a RESULT with no mismatch emits
- **oracle:** python3 -m unittest tests.test_files_changed_auto_repair.TestExecuteUnitAttemptAutoRepair.test_nothing_to_repair_is_a_plain_pass -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T03#4

- **criterion:** `python3 -m unittest tests.test_files_changed_guard tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v` exits 0.
- **oracle:** python3 -m unittest tests.test_loop_files_changed_guard tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v -b  (SUBSTITUTED: the criterion names `tests.test_files_changed_guard`, a module that exists nowhere in the tree; see RETROSPECTIVE.md § Measurements)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04#1

- **criterion:** `tests/test_retain_on_guard_refusal_docs.py` asserts the example file
- **oracle:** python3 -m unittest tests.test_retain_on_guard_refusal_docs -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04#2

- **criterion:** `python3 -m unittest tests.test_attempt_outcome_contract -v` exits 0 after
- **oracle:** python3 -m unittest tests.test_attempt_outcome_contract -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04#3

- **criterion:** `grep -n "retain_on_guard_refusal" specfuse/loop/data/verification.yml.example docs/methodology.md` returns at least one hit in each.
- **oracle:** grep -n "retain_on_guard_refusal" specfuse/loop/data/verification.yml.example docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04H#1

- **criterion:** `python3 -m unittest tests.test_scaffold_data_in_sync -v` fails on HEAD
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04H#2

- **criterion:** `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`
- **oracle:** diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example && diff docs/methodology.md specfuse/loop/data/docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04H#3

- **criterion:** `git diff --stat` for this unit touches exactly `.specfuse/verification.yml.example`
- **oracle:** events.jsonl attempt_outcome (FEAT-2026-0103/T04H, 2026-09-10T10:48:11Z, outcome=passed) files_touched  (SUBSTITUTED: a close session runs no git; see RETROSPECTIVE.md § Measurements)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`

### T04H#4

- **criterion:** `python3 -m unittest tests.test_retain_on_guard_refusal_docs -v` still exits 0.
- **oracle:** python3 -m unittest tests.test_retain_on_guard_refusal_docs -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `126e7c661a036ea9039a96cb4e6ff7f03966fab8`
- **attempt:** `1`
