### T01#1

- **criterion:** `tests/test_produces_amendment_e2e.py` fails on HEAD before this unit's edits
- **oracle:** `python3 -m unittest tests.test_produces_amendment_e2e -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T01#2

- **criterion:** That module asserts, end to end through `loop.run()`: a unit declaring
- **oracle:** `python3 -m unittest tests.test_produces_amendment_e2e -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T01#3

- **criterion:** Two more cases in the same module: an amendment that would drop every
- **oracle:** `python3 -m unittest tests.test_produces_amendment_e2e -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T01#4

- **criterion:** `python3 -m unittest tests.test_produces_justification tests.test_guard_repair_e2e tests.test_deliverable_presence_gate tests.test_attempt_outcome_contract -v -b`
- **oracle:** `python3 -m unittest tests.test_produces_justification tests.test_guard_repair_e2e tests.test_deliverable_presence_gate tests.test_attempt_outcome_contract -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_produces_repair_note.py` fails on HEAD before this unit's edits
- **oracle:** `python3 -m unittest tests.test_produces_repair_note -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02#2

- **criterion:** That module asserts, through `loop.run()` with a stubbed dispatch that
- **oracle:** `python3 -m unittest tests.test_produces_repair_note -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02#3

- **criterion:** `python3 -m unittest tests.test_deterministic_refusal_repeat tests.test_guard_repair_e2e tests.test_guard_refusal_failure_excerpt -v -b`
- **oracle:** `python3 -m unittest tests.test_deterministic_refusal_repeat tests.test_guard_repair_e2e tests.test_guard_refusal_failure_excerpt -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02H#1

- **criterion:** `python3 -m unittest tests.test_produces_justification -v -b` exits 0 with
- **oracle:** `python3 -m unittest tests.test_produces_justification -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02H#2

- **criterion:** `tests/test_produces_repair_note.py` gains one test asserting that the
- **oracle:** `python3 -m unittest tests.test_produces_repair_note -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T02H#3

- **criterion:** `python3 -m unittest tests.test_produces_amendment_e2e tests.test_guard_repair_e2e tests.test_produces_repair_note -v -b`
- **oracle:** `python3 -m unittest tests.test_produces_amendment_e2e tests.test_guard_repair_e2e tests.test_produces_repair_note -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_judge_sees_dropped_produces.py` fails on HEAD before this unit's
- **oracle:** `python3 -m unittest tests.test_judge_sees_dropped_produces -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T03#2

- **criterion:** That module asserts on a temp feature dir with one unit carrying
- **oracle:** `python3 -m unittest tests.test_judge_sees_dropped_produces -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T03#3

- **criterion:** `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_judge_path_registry -v -b`
- **oracle:** `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_judge_path_registry -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T04#1

- **criterion:** `grep -c "produces_amended" .specfuse/rules/result-contract.md docs/methodology.md .specfuse/skills/authoring-work-units/SKILL.md`
- **oracle:** `grep -c "produces_amended" .specfuse/rules/result-contract.md docs/methodology.md .specfuse/skills/authoring-work-units/SKILL.md`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T04#2

- **criterion:** `grep -n "produces_amendable" .specfuse/verification.yml.example docs/methodology.md`
- **oracle:** `grep -n "produces_amendable" .specfuse/verification.yml.example docs/methodology.md`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T04#3

- **criterion:** After running `scripts/sync-scaffold.sh`,
- **oracle:** `scripts/sync-scaffold.sh && python3 -m unittest tests.test_scaffold_data_in_sync -v -b`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`

### T04#4

- **criterion:** `python3 .specfuse/scripts/leak_scan.py --all` exits 0.
- **oracle:** `python3 .specfuse/scripts/leak_scan.py --all`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `23d5023d4b3748ebb9c42107f476a4becbd07683`
- **attempt:** `1`
