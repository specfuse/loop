# Gate 3 — per-criterion close state

Written by `FEAT-2026-0109/G3-CLOSE`, attempt 1 of the re-armed close, per
`.specfuse/rules/close-discipline.md` §5. `kind` and `state` are recorded by
the close that ran the oracle and are never inferred by a reader.

`T08#1`–`T08#7` are `GATE-03.md`'s seven definition-of-done bullets, in
document order; the IDs keep T08's prefix because T08 is the gate's tracer
bullet, but two of them were closed by T09 and each entry says so.
`G3-CLOSE#1`–`G3-CLOSE#6` are this close's own acceptance criteria whose
oracle is a fresh re-run.

### T08#1

- **criterion:** The driver executes a pinned build, and records which one — materialized outside the working tree, keyed on `HEAD^{tree}`, identity recorded on the run.
- **oracle:** python3 -m unittest tests.test_installed_copy_driver_e2e -q (Ran 9 tests, OK, exit 0) + a count of `driver_build_pinned` events in this feature's events.jsonl (6, trees 021342f2/134a81f0/51a3e401/869aed0a/4545ce57/b396c1a6, each carrying its pin path) + `ps -eo pid,ppid,command` showing PID 55697 executing `<pin-cache>/b396c1a62fee67b966aa4e113a57c0be6ea06921/_run_pinned.py --feature FEAT-2026-0109`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#2

- **criterion:** A unit editing `specfuse/loop/*.py` does not halt the run — no `driver_staleness_detected` with `halted: true` and no `EXIT_DRIVER_RESTART_REQUIRED` when pinned; the edit is still recorded, non-halting, naming the build it takes effect in.
- **oracle:** python3 -m unittest tests.test_installed_copy_driver_e2e -q (Ran 9 tests, OK, exit 0) + production events: T09 (2026-09-09T13:30:52Z) and T10 (13:32:22Z) each emitted `driver_staleness_detected` with `halted: false`, `pinned_tree: 4545ce57…`, a `next_pin_tree`, and the same process dispatched the next unit — 0 `halted: true` anywhere after the pin landed
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#3

- **criterion:** The pin is transparent to the operator's command — both invocation forms reach the pinned execution and `resume_command_for` returns a command that reproduces it rather than silently escaping it. (Recorded `not_met` at the previous close attempt as issue #3271; closed by T09.)
- **oracle:** python3 -m unittest tests.test_pin_honesty_and_integrity -q (Ran 5 tests, OK, exit 0) + python3 -c "…resume_command_for('FEAT-2026-0109')" -> `python3 -m specfuse.loop.loop --feature FEAT-2026-0109` (exit 0), observed live in the process table as the parent of the pinned `_run_pinned.py` + a direct probe: the real reaped pin `021342f2…` (40 of 131 files) now fails `_pin_is_complete`, and materialize/delete-2-files/re-materialize returns a rebuilt 131-file pin whose launcher-shaped import resolves `specfuse.loop.loop` to the pin
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#4

- **criterion:** #1040's guarantee survives the migration — `build_provenance` gains a third state, pinned at a recorded tree; only an unidentified out-of-tree build keeps the "confidently wrong" warning.
- **oracle:** python3 -m unittest tests.test_installed_copy_driver_e2e tests.test_pin_honesty_and_integrity -q (OK, exit 0) + python3 -c "…out_of_tree_warning()" over the live pin, which reports both tree hashes and no alarming text, against the installed wheel's unidentified out-of-tree path which prints the original warning verbatim
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#5

- **criterion:** The cost is stated at the moment it is incurred — the driver says, in words, at the point where it declines to halt, that the edit takes effect at the next run. (Recorded `not_met` at the previous close attempt as issue #3270; closed by T09.)
- **oracle:** a direct stdout probe of the real pinned driver subprocess (`PinnedRunRecordsAndSurvivesDriverEdits`, returncode 0), run in this session: the per-unit seam prints `DRIVER EDIT RECORDED (pinned build <tree>)` naming `next_pin_tree` and "continues dispatching against its own pinned snapshot", the gate summary prints `DRIVER EDITS RECORDED (gate summary, pinned build <tree>)` and "No restart was required.", and neither pre-T09 string (`STALE DRIVER PROCESS:` / "stop this driver now and start a new one") appears anywhere on stdout + python3 -m unittest tests.test_pin_honesty_and_integrity -q (OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#6

- **criterion:** A project that never installed the driver is unaffected — no `specfuse/loop/` in the working tree means no pin, no re-exec, no new event, no changed behaviour.
- **oracle:** python3 -m unittest tests.test_installed_copy_driver_e2e -q (Ran 9 tests, OK, exit 0), specifically `ProjectWithoutDriverSourceIsUnaffected.test_no_pin_materialized_no_new_event`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T08#7

- **criterion:** Per-criterion state and the narrow/broad oracle contract — `close-discipline.md` §5.
- **oracle:** this file, written by this close + python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing (exit 0, `close-l` reports no findings)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#1

- **criterion:** `python3 -m unittest discover -s tests -q` reports `OK`.
- **oracle:** python3 -m unittest discover -s tests -q — `Ran 3829 tests in 199.120s`, `OK (skipped=3)`, exit 0
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#2

- **criterion:** `bash scripts/smoke-test.sh` exits 0.
- **oracle:** bash scripts/smoke-test.sh — `smoke test: OK`, exit 0
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#3

- **criterion:** `specfuse lint` over every feature folder reports zero ERROR.
- **oracle:** python3 .specfuse/scripts/lint_plan.py over each of the 77 `.specfuse/features/*/` folders — 77 linted, 0 folders with an ERROR finding, exit 0 on each
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#4

- **criterion:** The three gates' `feature_oracle` commands each report `OK`.
- **oracle:** python3 -m unittest tests.test_lazy_baseline_e2e -q / tests.test_tiered_verification_e2e -q / tests.test_installed_copy_driver_e2e -q — each `OK`, exit 0; counts recorded in RETROSPECTIVE.md § Fresh oracle re-runs
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#5

- **criterion:** `## Consumer-visible contract changes` — the reconciled enumeration across gates 1, 2 and 3, with matching `CHANGELOG.md` `Unreleased` entries carrying `FEAT-2026-0109`.
- **oracle:** python3 -c "…specfuse.loop.changelog.parse_changelog(CHANGELOG.md)" — parses with no errors, 22 Unreleased entries tracing to FEAT-2026-0109 / #3270 / #3271 (exit 0) + `close-k` in `specfuse lint --closing` (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#6

- **criterion:** `specfuse lint --closing` passes before this unit reports `complete`.
- **oracle:** python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing — `CLOSING-READY`, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
