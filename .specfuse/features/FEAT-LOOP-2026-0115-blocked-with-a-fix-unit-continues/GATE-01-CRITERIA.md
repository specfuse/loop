### T01#1

- **criterion:** `tests/test_fix_unit_insertion_e2e.py` fails on HEAD before this unit's
- **state:** `unverified`

### T01#2

- **criterion:** That module asserts, end to end through `loop.run()`: the dispatch order is
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b (test_blocked_with_valid_blocked_next_inserts_and_continues)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T01#3

- **criterion:** Two more cases: a blocked RESULT without `blocked_next:` ends
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b (test_blocked_without_blocked_next_escalates_unchanged, test_blocked_with_blocked_next_under_review_autonomy_escalates)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T01#4

- **criterion:** `python3 .specfuse/scripts/event_type_gate.py` exits 0, and
- **oracle:** python3 .specfuse/scripts/event_type_gate.py && python3 -m unittest tests.test_spinout_brief_end_to_end tests.test_replan_end_to_end tests.test_attempt_outcome_contract -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_fix_unit_insertion_refused.py` fails on HEAD before this unit's
- **state:** `unverified`

### T02#2

- **criterion:** That module asserts, through `loop.run()`, one refusal per class: a draft
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_refused -v -b (test_cost_budget_refuses, test_judge_editing_refuses, test_max_fix_units_per_unit_refuses_third_insertion, test_missing_provenance_refuses)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T02#3

- **criterion:** A fifth case asserts a clean draft still inserts and the gate continues
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_refused -v -b (test_clean_draft_still_inserts_and_continues)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T02#4

- **criterion:** `python3 -m unittest tests.test_fix_unit_insertion_e2e tests.test_arm_eval tests.test_lint_plan_next_draft -v -b`
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_e2e tests.test_arm_eval tests.test_lint_plan_next_draft -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_fix_unit_insertion_bookkeeping.py` fails on HEAD before this
- **state:** `unverified`

### T03#2

- **criterion:** That module asserts `evaluate_auto_close` returns `auto: False` with a
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_bookkeeping -v -b (FixUnitInsertedDisablesAutoClose)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T03#3

- **criterion:** It also asserts the escalation brief for a refused insertion contains the
- **oracle:** python3 -m unittest tests.test_fix_unit_insertion_bookkeeping -v -b (EscalationBriefNamesRefusedInsertion)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T03#4

- **criterion:** `python3 -m unittest tests.test_gate_eval tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option -v -b`
- **oracle:** python3 -m unittest tests.test_gate_eval tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T04#1

- **criterion:** `grep -c "blocked_next" .specfuse/rules/result-contract.md docs/methodology.md plugins/specfuse/skills/authoring-work-units/SKILL.md .specfuse/skills/authoring-work-units/SKILL.md`
- **oracle:** grep -c "blocked_next" .specfuse/rules/result-contract.md docs/methodology.md plugins/specfuse/skills/authoring-work-units/SKILL.md .specfuse/skills/authoring-work-units/SKILL.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T04#2

- **criterion:** `grep -n "fix_unit_insertion\|max_fix_units_per_unit" .specfuse/verification.yml.example docs/methodology.md`
- **oracle:** grep -n "fix_unit_insertion\|max_fix_units_per_unit" .specfuse/verification.yml.example docs/methodology.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T04#3

- **criterion:** After running `scripts/sync-scaffold.sh`,
- **oracle:** bash scripts/sync-scaffold.sh && python3 -m unittest tests.test_scaffold_data_in_sync -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`

### T04#4

- **criterion:** `python3 .specfuse/scripts/leak_scan.py --all` exits 0.
- **oracle:** python3 .specfuse/scripts/leak_scan.py --all
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `1c96fee`
- **attempt:** `1`
