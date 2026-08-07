### T01#1

- **criterion:** `tests/test_driver_edit_detection.py::test_loop_py_edit_is_detected` exists and
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#2

- **criterion:** `specfuse/loop/driver_edit.py` defines `DRIVER_MODULE_PREFIXES` as a tuple of
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v (TestDiffEditsDriver.test_driver_module_prefixes_contains_loop_dir) + python3 -c "from specfuse.loop.driver_edit import DRIVER_MODULE_PREFIXES, diff_edits_driver, driver_paths_in, changed_paths_for_commit"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#3

- **criterion:** `diff_edits_driver(paths)` returns `True` for any iterable containing a path under
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#4

- **criterion:** `driver_paths_in(paths)` returns only the matching paths, in input order, so a
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v (TestDriverPathsIn.test_returns_only_matches_in_input_order)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#5

- **criterion:** `changed_paths_for_commit(sha, repo_root)` returns the list of paths a commit
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v (TestChangedPathsForCommit)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#6

- **criterion:** `diff_edits_driver` and `driver_paths_in` are pure — a grep for
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v (TestPurity.test_no_filesystem_or_subprocess_calls_in_predicate_sources) + grep -nE 'subprocess|open\(|os\.environ|Path\(' specfuse/loop/driver_edit.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#7

- **criterion:** The module does not import `specfuse.loop.loop`:
- **oracle:** grep -n 'specfuse.loop.loop' specfuse/loop/driver_edit.py (only hit is line 17, a docstring sentence; no import statement)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#8

- **criterion:** `python3 -c "from specfuse.loop.driver_edit import DRIVER_MODULE_PREFIXES, diff_edits_driver, driver_paths_in, changed_paths_for_commit"`
- **oracle:** python3 -c "from specfuse.loop.driver_edit import DRIVER_MODULE_PREFIXES, diff_edits_driver, driver_paths_in, changed_paths_for_commit"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#9

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest discover -s tests -p test_driver_edit_detection.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T01#10

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** code gate set (12 gates: tests, lint, security, coverage, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate, monitoring-example-lint, 3x bats)
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#1

- **criterion:** `tests/test_driver_staleness_warning.py::test_driver_edit_warns_at_squash` exists
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#2

- **criterion:** `specfuse/loop/loop.py` exports
- **oracle:** python3 -c "from specfuse.loop.loop import format_driver_staleness_warning"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#3

- **criterion:** The returned message names the work unit's ID, every path in `driver_paths`, and
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v (TestFormatDriverStalenessWarningUnit.test_names_wu_id_and_paths_and_restart_requirement)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#4

- **criterion:** The warning is emitted from the outcome path immediately after the `squash_commit`
- **oracle:** grep -n 'format_driver_staleness_warning' specfuse/loop/loop.py -> call site at loop.py:6287 in the outcome path, plus python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v (TestDriverStalenessWarningSeam.test_driver_edit_warns_at_squash)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#5

- **criterion:** **Seam test, not formatter test.** A test drives the real outcome path with a stub
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v (TestDriverStalenessWarningSeam.test_driver_edit_warns_at_squash)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#6

- **criterion:** A unit whose squash diff touches no driver path produces **no** warning — asserted
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v (TestDriverStalenessWarningSeam.test_no_driver_edit_no_warning)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#7

- **criterion:** `python3 -c "from specfuse.loop.loop import format_driver_staleness_warning"`
- **oracle:** python3 -c "from specfuse.loop.loop import format_driver_staleness_warning"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#8

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_warning.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T02#9

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** code gate set (12 gates: tests, lint, security, coverage, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate, monitoring-example-lint, 3x bats)
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#1

- **criterion:** `tests/test_driver_staleness_gate_summary.py::test_summary_names_units_dispatched_after`
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#2

- **criterion:** `specfuse/loop/loop.py` exports
- **oracle:** python3 -c "from specfuse.loop.loop import format_driver_staleness_summary"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#3

- **criterion:** For a gate in which unit A edited the driver and units B and C were dispatched
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v (TestFormatDriverStalenessSummaryUnit.test_names_editor_paths_and_dispatched_after)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#4

- **criterion:** A unit dispatched **before** the driver-editing unit is not named as affected —
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v (TestDriverStalenessGateSummarySeam.test_summary_names_units_dispatched_after; T00 precedes the edit and is not named)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#5

- **criterion:** The summary is emitted at gate completion, before the gate flips to
- **oracle:** grep -n 'format_driver_staleness_summary' specfuse/loop/loop.py -> gate-completion call site at loop.py:6824-6828, before the gate flip, plus python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#6

- **criterion:** A gate containing no driver-editing unit produces **no** summary and **no** event,
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v (TestDriverStalenessGateSummarySeam.test_no_driver_edit_no_summary_no_event)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#7

- **criterion:** A `driver_staleness_detected` event is appended to the feature's `events.jsonl`,
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v (seam asserts the driver_staleness_detected event append at loop.py:6832)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#8

- **criterion:** `driver_staleness_detected` is added to the `event_types` list in
- **oracle:** grep -n 'driver_staleness_detected' specfuse/loop/data/schemas/driver-event.schema.json -> present in event_types at line 17
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#9

- **criterion:** The `event-type-gate` gate passes over every feature's `events.jsonl`:
- **oracle:** python3 .specfuse/scripts/event_type_gate.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#10

- **criterion:** `python3 -c "from specfuse.loop.loop import format_driver_staleness_summary"`
- **oracle:** python3 -c "from specfuse.loop.loop import format_driver_staleness_summary"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#11

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest discover -s tests -p test_driver_staleness_gate_summary.py -v
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

### T03#12

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** code gate set (12 gates: tests, lint, security, coverage, leak-scan, event-type-gate, roadmap-link-gate, arm-sweep-gate, monitoring-example-lint, 3x bats)
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`
- **attempt:** `2`

