# Gate 3 — per-criterion state

Written by `FEAT-2026-0109/G3-CLOSE`, attempt 1, per `close-discipline.md` §5.
Every `kind:` and `state:` below was set by this close from an oracle it ran in
its own session; none is inferred, and none is carried forward from an earlier
attempt (there is no earlier attempt).

`kind: narrow` = the oracle has a knowable scope (a named test module, a scoped
probe, a structural assert). `kind: broad` = no knowable scope (the full suite,
the whole smoke-test gate list, a sweep over every feature folder) — re-run
unconditionally on every close attempt.

Entries `T08#1`–`T08#7` are `GATE-03.md`'s definition-of-done bullets, in order.
Entries `G3-CLOSE#1`–`G3-CLOSE#4` are this close's own fresh-oracle criteria.

### T08#1
- **criterion:** The driver executes a pinned build, and records which one — materialized outside the working tree, keyed on `HEAD^{tree}`, with the tree hash and path recorded on the run.
- **oracle:** `python3 -m unittest tests.test_installed_copy_driver_e2e -q` (Ran 9 tests, `OK`, exit 0) + `event_type == "driver_build_pinned"` count over `events.jsonl` → 2, trees `021342f2…` / `134a81f0…`, each with its pin path
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#2
- **criterion:** A unit editing `specfuse/loop/*.py` does not halt the run — no `driver_staleness_detected` with `halted: true` and no `EXIT_DRIVER_RESTART_REQUIRED` when the run is pinned; the edit is still recorded, non-halting, naming the build it will take effect in.
- **oracle:** `python3 -m unittest tests.test_installed_copy_driver_e2e -q` (`test_a_driver_edit_does_not_halt_the_run`, `test_the_driver_edit_is_still_recorded`, `test_a_moving_working_tree_does_not_move_the_running_build`), exit 0; production cross-check — `halted: true` events after the first pin at 2026-09-08T20:30:25Z → 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#3
- **criterion:** The pin is transparent to the operator's command — `specfuse run --feature X` and `python3 -m specfuse.loop.loop --feature X` both still work and both reach the pinned execution, and `resume_command_for` returns a command that reproduces the same pinned execution rather than one that silently escapes it.
- **oracle:** `python3 -c "from specfuse.loop.loop import resume_command_for; print(resume_command_for('FEAT-2026-0109'))"` → `python3 -m specfuse.loop.loop --feature FEAT-2026-0109`, exit 0; reaped-pin probe — with `specfuse/loop/__init__.py` removed from a materialized pin and the `.specfuse-pin-tree` marker intact, a launcher-shaped `sys.path.insert(0, pin)` import of `specfuse.loop.loop` resolved to `<REPO_ROOT>/specfuse/loop/loop.py` (the working tree) while `pinned_build_info` still returned a valid pin, exit 0
- **kind:** `narrow`
- **state:** `fail`
- **attempt:** `1`

### T08#4
- **criterion:** #1040's guarantee survives the migration — `build_provenance` gains a third state, pinned at a recorded tree, reporting both hashes without the "confidently wrong" text; only an unidentified out-of-tree build keeps that warning.
- **oracle:** `python3 -m unittest tests.test_installed_copy_driver_e2e -q` (`BuildProvenanceThreeStates`, 2 tests), exit 0; both branches observed live this session — a pinned driver subprocess printed `running a recorded pin of specfuse from … (tree 8353a86c…); the working tree at … is now at tree 8353a86c…` on stderr, and the installed console script (`specfuse lint … --closing`, an unidentified out-of-tree build) printed the "confidently wrong" text verbatim
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#5
- **criterion:** The cost is stated at the moment it is incurred — a driver change landed by a unit takes effect at the next run, and the driver says so, in words, at the point where it declines to halt; an operator must never have to infer from silence which build verified their gate.
- **oracle:** pinned-run stdout probe — drove `tests.test_installed_copy_driver_e2e.PinnedRunRecordsAndSurvivesDriverEdits`'s real pinned driver subprocess (returncode 0) and read `proc.stdout` directly. At the decline point it prints the pre-T08 text: `STALE DRIVER PROCESS: … A fresh driver process is required before any close can verify this change: stop this driver now and start a new one before dispatching the next work unit.`, and the gate summary repeats `each executed the pre-edit module(s) … A fresh driver process is required before any of these can be trusted`. Case-insensitive `pin` occurrences in that stdout → 2, both the feature slug. No pin-aware sentence is printed at the seam
- **kind:** `narrow`
- **state:** `fail`
- **attempt:** `1`

### T08#6
- **criterion:** A project that never installed the driver is unaffected — no `specfuse/loop/` in the working tree means no pin, no re-exec, no new event, no changed behaviour.
- **oracle:** `python3 -m unittest tests.test_installed_copy_driver_e2e -q` (`ProjectWithoutDriverSourceIsUnaffected.test_no_pin_materialized_no_new_event`), exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#7
- **criterion:** Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.
- **oracle:** this artifact, written by this close; `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing` (requirement `close-l`, `check_criteria_state_well_formed`)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#1
- **criterion:** `python3 -m unittest discover -s tests -q` reports `OK`.
- **oracle:** `python3 -m unittest discover -s tests -q` → `Ran 3819 tests in 158.908s`, `OK (skipped=3)`, exit 0
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#2
- **criterion:** `bash scripts/smoke-test.sh` exits 0.
- **oracle:** `bash scripts/smoke-test.sh` → `smoke test: OK`, exit 0
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#3
- **criterion:** `specfuse lint` over every feature folder reports zero ERROR.
- **oracle:** `python3 .specfuse/scripts/lint_plan.py <dir>` over all 77 `.specfuse/features/*/` folders → 77 linted, 0 with an ERROR finding
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#4
- **criterion:** The three gates' `feature_oracle` commands each report `OK`.
- **oracle:** `python3 -m unittest tests.test_lazy_baseline_e2e -q` (8 tests, `OK`, exit 0); `python3 -m unittest tests.test_tiered_verification_e2e -q` (5 tests, `OK`, exit 0); `python3 -m unittest tests.test_installed_copy_driver_e2e -q` (9 tests, `OK`, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
