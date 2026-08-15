### T04#1

- **criterion:** `tests/test_driver_module_surface.py::test_data_path_is_not_a_driver_module`
- **oracle:** `python3 -m unittest tests.test_driver_module_surface.TestDataPathIsNotADriverModule.test_data_path_is_not_a_driver_module -v  # ok, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#2

- **criterion:** `specfuse/loop/driver_edit.py` exports `is_driver_module_path(path) -> bool`
- **oracle:** `python3 -c "from specfuse.loop.driver_edit import is_driver_module_path, DRIVER_DATA_PREFIXES"  # ok ('specfuse/loop/data/',), exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#3

- **criterion:** `diff_edits_driver` and `driver_paths_in` both delegate to
- **oracle:** `grep -n 'startswith' specfuse/loop/driver_edit.py  # 2 hits, both inside is_driver_module_path (lines 38, 40), exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#4

- **criterion:** Positive cases still detected, each asserted separately:
- **oracle:** `python3 -m unittest tests.test_driver_module_surface.TestIsDriverModulePathPositive -v  # 3 tests OK; loop.py/driver_edit.py/arm_eval.py all True, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#5

- **criterion:** Negative cases now silent, each asserted separately:
- **oracle:** `python3 -m unittest tests.test_driver_module_surface.TestIsDriverModulePathNegative -v  # 5 tests OK; schema.json/methodology.md/WU.template.md/monitoring.yml.example/data-scaffold_payload.py all False, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#6

- **criterion:** `driver_edit.py` stays pure apart from `changed_paths_for_commit`: `is_driver_module_path`
- **oracle:** `grep -nE '^import|^from|open\(|Path\(|os\.|subprocess' specfuse/loop/driver_edit.py  # only `import subprocess` (23) and its single use at 60 inside changed_paths_for_commit, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#7

- **criterion:** The module remains free of a `specfuse.loop.loop` import (T01's no-cycle property):
- **oracle:** `grep -n 'specfuse.loop.loop' specfuse/loop/driver_edit.py  # 1 hit, line 17, inside the module docstring — no import statement, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#8

- **criterion:** `python3 -c "from specfuse.loop.driver_edit import is_driver_module_path, DRIVER_DATA_PREFIXES"`
- **oracle:** `python3 -c "from specfuse.loop.driver_edit import is_driver_module_path, DRIVER_DATA_PREFIXES"  # exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#9

- **criterion:** **The sweep is re-run against the real narrowed code**, not against `G1-PLAN`'s
- **oracle:** `90-gate sweep re-run against the shipped is_driver_module_path over all 57 feature folders  # features=57 gates=90 broad=42 narrow=39 broad-only=3 no-driver=48; +1 vs G1-PLAN's 41/38/49 is FEAT-2026-0075's own gate 2, drafted after that sweep ran, exit 0`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#10

- **criterion:** Any gate-1 test that asserts the old broad behaviour is updated rather than
- **oracle:** `python3 -m unittest tests.test_driver_edit_detection tests.test_driver_staleness_warning tests.test_driver_staleness_gate_summary  # Ran 22 tests, OK — gate 1's suites still green under the narrowed predicate, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T04#11

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** `full `code` gate set, all 15 gates  # every gate exit 0; tests Ran 2481 OK (skipped=3); coverage TOTAL 7860 505 94%`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#1

- **criterion:** `tests/test_driver_restart_hold.py::test_halt_leaves_gate_open_and_units_pending`
- **oracle:** `python3 -m unittest tests.test_driver_restart_hold.TestHaltForDriverRestart.test_halt_leaves_gate_open_and_units_pending -v  # ok, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#2

- **criterion:** `specfuse/loop/loop.py` defines a module-level constant
- **oracle:** `python3 -c "from specfuse.loop.loop import HALT_REASON_DRIVER_RESTART as H, EXIT_DRIVER_RESTART_REQUIRED as E; print(repr(H), E, E not in (0,1,2))"  # 'driver_restart_required' 3 True, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#3

- **criterion:** `specfuse/loop/loop.py` exports
- **oracle:** `python3 -c "from specfuse.loop.loop import format_driver_restart_halt as f; print(repr(f('X',[],[],'c'))); print(bool(f('X',['specfuse/loop/loop.py'],['Y'],'cmd')))"  # '' then True, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#4

- **criterion:** The rendered message names, each asserted separately against the string: the work
- **oracle:** `python3 -m unittest tests.test_driver_restart_hold.TestFormatDriverRestartHaltUnit -v  # 6 tests OK — wu_id, every driver path, every remaining WU id, 'cannot execute', literal resume command each asserted separately, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#5

- **criterion:** **The halt is a brake at the `for wu in pending` seam**, alongside
- **oracle:** `grep -n 'HALT_REASON_DRIVER_RESTART' specfuse/loop/loop.py  # 2 hits: 1961 (definition) and 1995 (event payload inside _halt_for_driver_restart) — none inside squash_commit or an attempt loop, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#6

- **criterion:** On halt, asserted separately: the gate file's `status` is still `open`; **no** WU's
- **oracle:** `python3 -m unittest tests.test_driver_restart_hold.TestHaltForDriverRestart.test_halt_leaves_gate_open_and_units_pending  # asserts rc == EXIT_DRIVER_RESTART_REQUIRED, gate status still 'open', T01 still 'pending', close still 'pending', exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#7

- **criterion:** A `driver_staleness_detected` event is appended to the feature's `events.jsonl`
- **oracle:** `python3 -m unittest tests.test_driver_restart_hold.TestHaltForDriverRestart.test_halt_leaves_gate_open_and_units_pending  # asserts exactly 1 driver_staleness_detected line in the written events.jsonl with halted is True, remaining_wu_ids == [close_id], and the resume command, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#8

- **criterion:** The bookkeeping commit for the halt is made through the existing
- **oracle:** `python3 -m unittest tests.test_driver_restart_hold.TestHaltForDriverRestart.test_halt_leaves_gate_open_and_units_pending  # asserts events_after_reset == events — the commit_bookkeeping path makes the halt event survive, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#9

- **criterion:** `python3 -c "from specfuse.loop.loop import format_driver_restart_halt, HALT_REASON_DRIVER_RESTART, EXIT_DRIVER_RESTART_REQUIRED"`
- **oracle:** `python3 -c "from specfuse.loop.loop import format_driver_restart_halt, HALT_REASON_DRIVER_RESTART, EXIT_DRIVER_RESTART_REQUIRED"  # ok, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#10

- **criterion:** `python3 .specfuse/scripts/event_type_gate.py` exits 0 — confirming the reused
- **oracle:** `python3 .specfuse/scripts/event_type_gate.py  # ok: no validation errors across 54 events.jsonl file(s), 1310 event(s) checked, exit 0`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#11

- **criterion:** No new entry is added to `VALID_STATUS`, `VALID_TYPES`, `MODEL_BY_TYPE`,
- **oracle:** `python3 -c "import specfuse.loop.loop as L; [print(n, sorted(getattr(L,n))) for n in (...)]" plus grep -n 'VALID_STATUS\s*=\|VALID_TYPES\s*=' specfuse/loop/lint_plan.py  # MODEL_BY_TYPE/EFFORT_BY_TYPE/GATES_FOR_TYPE = the 7 pre-existing WU types; CLOSING_ASSERTIONS_BY_TYPE = [close, close-intermediate, plan-next]; POST_PASS_INVARIANTS_BY_TYPE = [close, close-intermediate]; VALID_TYPES/VALID_STATUS carry no halt or restart vocabulary. Observed values, not a diff — see RETROSPECTIVE.md gate 2 §6, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T05#12

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** `full `code` gate set, all 15 gates  # every gate exit 0`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#1

- **criterion:** `tests/test_driver_restart_halt_wiring.py::test_driver_edit_halts_before_next_dispatch`
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_driver_edit_halts_before_next_dispatch -v  # ok, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#2

- **criterion:** **Seam test, not formatter test.** The test drives the real outcome path with a stub
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_driver_edit_halts_before_next_dispatch  # drives the real run loop: asserts rc == EXIT_DRIVER_RESTART_REQUIRED, dispatched == [t01_id] (the next unit was never dispatched), and 'DRIVER RESTART REQUIRED' in captured driver output, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#3

- **criterion:** The halt fires from the `for wu in pending` brake, not from inside the squash block
- **oracle:** `grep -n 'format_driver_restart_halt\|_halt_for_driver_restart' specfuse/loop/loop.py  # 4 hits: 1965 def, 1987 call inside the helper, 2273 def of the formatter, 5976 the `for wu in pending` brake — none inside squash_commit (2288+), exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#4

- **criterion:** The unit whose squash set the flag reaches its terminal outcome first: its status is
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_driver_edit_halts_before_next_dispatch  # asserts t01_fm['status'] == 'done' and exactly one task_completed event after the halt, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#5

- **criterion:** **A driver edit by the gate's final unit does not halt.** With no further unit
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_final_unit_driver_edit_does_not_halt  # asserts rc != EXIT_DRIVER_RESTART_REQUIRED, no 'DRIVER RESTART REQUIRED', 'STALE DRIVER PROCESS (gate summary):' IS in output, gate flips to awaiting_review, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#6

- **criterion:** **`--dry-run` never halts.** Asserted through the same harness.
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_dry_run_never_halts  # asserts rc != EXIT_DRIVER_RESTART_REQUIRED and no halt message, through the same harness, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#7

- **criterion:** **The negative case, through the same harness:** a unit whose squash diff touches no
- **oracle:** `python3 -m unittest tests.test_driver_restart_halt_wiring.TestDriverRestartHaltWiring.test_no_driver_edit_run_uninterrupted  # asserts dispatched == [t01, t02, t03] and gate awaiting_review, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#8

- **criterion:** `T02`'s existing immediate warning still prints at the squash site. The halt is
- **oracle:** `grep -n 'format_driver_staleness_warning' specfuse/loop/loop.py  # call site still present at 6395, in the post-squash outcome path, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#9

- **criterion:** `changed_paths_for_commit` is called exactly once per squash:
- **oracle:** `grep -n 'changed_paths_for_commit' specfuse/loop/loop.py  # 2 hits: the import at 103 and exactly one call site at 6393, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#10

- **criterion:** **Runtime probe (`planning-discipline.md` §4), pasted in full.** Re-run
- **oracle:** `90-gate sweep re-run against the shipped predicate  # 48 of 90 gates carry no driver-module edit and report ZERO halts; 39 carry one and report exactly one halt at the first driver-editing unit; 3 broad-only gates are silent after T04. No halt on any gate without a driver-module edit, exit 0`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`

### T06#11

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** `full `code` gate set, all 15 gates  # every gate exit 0`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `89b42cb`
- **attempt:** `1`
