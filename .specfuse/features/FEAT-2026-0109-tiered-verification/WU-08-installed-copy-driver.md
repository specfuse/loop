---
id: FEAT-2026-0109/T08
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.50
oracle_env: macos_local
produces_driver_helper: pin_driver_build
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/build_provenance.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_installed_copy_driver_e2e.py
---

# The driver runs from a pinned build, and a driver edit stops halting the run

**Objective.** Make the driver execute a build of `specfuse/` materialized
outside the working tree and keyed on `HEAD^{tree}`, and retire the
`driver_restart_required` halt for runs that are pinned. After this unit a work
unit editing `specfuse/loop/*.py` leaves the run going instead of stopping it
for a human.

**Context.** FEAT-2026-0109/T08; read `PLAN.md`, `GATE-03.md`, and gate 2's
`## Gate 2` section of `RETROSPECTIVE.md`. This is gate 3's only substantive
unit and the feature's last. `[FEAT-2026-0019/G1]` is why it is one unit:
a feature migrating the harness the driver itself runs cannot be split into
separately-gated units, because each piece's exit oracle is the surface being
migrated. Do not decompose it into a helper unit and a wiring unit — that is the
$5.63/49-minute thrash that record names.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file in gate
1; T04, T05 and T06 added tier resolution, selection and the broad run in gate
2. This unit adds startup pinning, changes one halt predicate, and changes what
`resume_command_for` returns. It does not touch what any of those earlier
mechanisms decide.

## What is already true, so you do not rediscover it by failing

Four facts established by a runtime probe in the `G2-PLAN` session that drafted
this unit. They are recorded here because each one would otherwise cost an
attempt.

1. **The driver needs no path rewriting to run from a copy.** `SPECFUSE_DIR =
   Path(".specfuse")` (`loop.py:118`) is **cwd-relative**, not
   `__file__`-relative, so a driver imported from anywhere still resolves
   `.specfuse/`, `REPO_ROOT` and the feature folders against the working
   directory. Probed: importing `specfuse.loop.loop` from a copy under `$TMPDIR`
   reported `module file: <tmp>/specfuse/loop/loop.py` and `REPO_ROOT:
   <the real repo>`. That split is the whole migration.
2. **`PYTHONPATH` is not sufficient; the invocation form is what decides.** For
   `python3 -m …` and `python3 -c …` the cwd is `sys.path[0]`, so the working
   tree's `specfuse/` shadows any copy. For a **script** invocation `sys.path[0]`
   is the script's own directory. Probed both ways: the `-c` form loaded the
   working tree despite `PYTHONPATH`; a script that inserted the copy at
   `sys.path[0]` loaded the copy. Whatever launch mechanism you choose has to
   put the pin ahead of the cwd, and merely exporting `PYTHONPATH` does not.
3. **`main()` runs unmodified from a copy.** Probed: a script importing
   `specfuse.loop.loop:main` from a `$TMPDIR` copy and executing it against this
   repository parsed arguments and printed usage normally. `specfuse/loop/data/`
   lives inside the package and travels with the copy.
4. **`build_provenance` fires on a pinned run today, calling it "confidently
   wrong".** The same probe printed `warning: running specfuse from
   <tmp>/snap/specfuse/loop, but the working tree ... carries its own
   source. This command is measuring the INSTALLED build, not your checkout —
   results can be confidently wrong rather than failing.` Reconciling that is a
   deliverable of this unit, not a nuisance to silence — see below.

## `build_provenance` is the mechanism you are extending, not one you are working around

`specfuse/loop/build_provenance.py` exists (#1040) because an out-of-tree build
"does not error, it returns a plausible number" — a gate-1 arming probe that
measured a stale wheel, and a terminal close that produced 14 spurious red
results. That failure is real and this unit must not reintroduce it.

The distinction the module does not yet draw is between an **unidentified**
out-of-tree build (an arbitrary installed wheel — still exactly as dangerous)
and a **pin whose provenance is recorded** (materialized by this driver, from a
named tree hash, this run). Give it a third state. Only the unidentified case
keeps the "confidently wrong" wording. A pinned run whose working tree has since
moved must report **both** hashes and say which one it executed: neither silent
nor alarmed.

Suppressing or deleting the warning to make a pinned run quiet is the
`never-touch.md` "weakening a failing gate to make a unit pass" failure in a
different costume. Do not.

## Flag-scope table (`planning-discipline.md` §3)

T08 introduces no user-facing flag; the scoping question is which code paths the
pinned/unpinned distinction reaches.

| Code path | Changed when pinned? | Why |
|---|---|---|
| driver startup (`main`) | **yes** | materializes the pin and re-enters execution from it; the one new seam |
| the `driver_edits` halt at the pre-dispatch seam (`loop.py:8343`) | **yes** | the halt's premise — "this process will execute code it cannot observe" — is false when the build is pinned and recorded |
| `changed_paths_for_commit` / `driver_paths_in` (`driver_edit.py`) | **no** | detection is still correct and still wanted; only the *response* to it moves |
| `format_driver_staleness_warning` / `format_driver_staleness_summary` | **no** | the gate-completion summary still names every driver edit the gate made |
| `resume_command_for` | **yes** | must return a command that reproduces the pinned execution, not one that silently escapes it |
| `build_provenance.out_of_tree_warning` | **yes** | gains the third state above |
| `probe_baseline`, `gate_baseline_check`, `attribute_failure_to_baseline` (gate 1) | **no** | attribution is orthogonal; it must not learn about builds |
| `resolve_gate_tiers`, `resolve_narrow_test_selection`, `gate_broad_run_check` (gate 2) | **no** | tiering is orthogonal; it must not learn about builds |
| a working tree with no `specfuse/loop/` (a downstream project) | **no** | no pin, no re-entry, no event — the silence-by-construction posture `build_provenance` already takes |

**Put the pinned build outside the working tree.** Every repo-sweeping surface
would otherwise have to learn about it: `git add -A` in the squash path,
`leak-scan`, `ruff`, the deliverable-presence guard, and the `HEAD^{tree}` hash
the pin is keyed on — which would change because the pin is inside the tree it
names. A platform cache directory keyed by tree hash avoids all six; a
`.gitignore` entry avoids only the first.

## The one restart this unit itself will pay

The driver running gate 3 is the pre-T08 driver, and this unit's squash touches
`specfuse/loop/loop.py` while `G3-CLOSE` is still pending — so the **old** halt
fires exactly once, after this unit lands, and the operator restarts. That is
expected and correct: the restarted driver is the first one to pin, and the
terminal close is therefore the first close in this repository to run from a
pinned build. Do not try to prevent that halt from inside this unit; a process
cannot retire a halt it has already been scheduled to take.

**Acceptance criteria.**

- `tests/test_installed_copy_driver_e2e.py` exists, fails on HEAD, and passes after — and it drives the driver as a **subprocess** launched from a materialized pin, over a temporary scaffold repository, with a stub `claude` on `PATH` (`CLAUDE_CMD`, `loop.py:288`, resolves `argv[0]` through `PATH`). It asserts only on that subprocess's exit code and the `events.jsonl` it writes; it does not import `specfuse.loop.loop` into the test process and assert on the result. `grep -n "import specfuse.loop.loop\|load_loop" tests/test_installed_copy_driver_e2e.py` returns nothing.
- `::test_the_run_records_the_build_it_executed`: the run writes the pin's identity — tree hash and path — and the recorded path is the pin, not the working tree's `specfuse/loop/`.
- `::test_a_driver_edit_does_not_halt_the_run`: a unit whose squash really touches `specfuse/loop/loop.py` is followed by the next unit's dispatch in the same process; no `driver_staleness_detected` event carries `halted: true`, and the process does not exit `EXIT_DRIVER_RESTART_REQUIRED` (3).
- `::test_the_driver_edit_is_still_recorded`: the same run emits a non-halting record of the edit naming the build the edit will take effect in — the edit is not silently dropped.
- `::test_a_moving_working_tree_does_not_move_the_running_build`: mutating `specfuse/loop/loop.py` in the workspace mid-run leaves the pinned process's behaviour unchanged, and the run reports both tree hashes.
- `::test_an_unpinned_run_still_halts`: with pinning unavailable or declined, the halt, its event and exit code 3 are byte-identical to today — the unpinned path is untouched.
- `::test_a_project_without_driver_source_is_unaffected`: a workspace with no `specfuse/loop/` materializes no pin, emits no new event, and behaves as it does today.
- `specfuse/loop/build_provenance.py` distinguishes three states, and each is covered: an in-tree run says nothing; an **unidentified** out-of-tree build keeps the existing "confidently wrong" text verbatim; a **recorded pin** reports both hashes without that text. Assert on `out_of_tree_warning`'s return value, which the module separates from printing for exactly this purpose.
- Any new driver event type is present in `specfuse/loop/data/schemas/driver-event.schema.json` — with a `$comment` provenance line following T01's `baseline_attribution` and T06's `broad_run_result` entries — **before** it is emitted, and `python3 .specfuse/scripts/event_type_gate.py` exits 0. A non-halting `driver_staleness_detected` needs no schema addition; the registry constrains the type list, not the payload.
- `python3 -m unittest tests.test_installed_copy_driver_e2e -q` reports `OK` — this gate's `feature_oracle`.
- `python3 -m unittest tests.test_lazy_baseline_e2e tests.test_tiered_verification_e2e -q` reports `OK`: gates 1 and 2 are not disturbed.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** Gate 1's attribution mechanism — `probe_baseline`,
`gate_baseline_check`, `attribute_failure_to_baseline` — and gate 2's tiering —
`resolve_gate_tiers`, `resolve_narrow_test_selection`, `gate_broad_run_check`,
`run_gate_broad_set`: this unit changes which build runs them, never what they
decide. `specfuse/loop/driver_edit.py`, whose detection is correct and stays.
What any existing gate in `.specfuse/verification.yml` asserts. Gate 1's and
gate 2's work units, `GATE-01.md`, `GATE-02.md`, and `RETROSPECTIVE.md`'s
`## Gate 1` and `## Gate 2` sections. `.specfuse/rules/`, `.specfuse/templates/`,
`.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the pinned build cannot be
reached without changing the command an operator types — a migration that only
works when someone remembers a new invocation is the
`a-rule-a-human-must-execute-is-not-a-control` shape `build_provenance`'s own
docstring names as the thing that does not hold, and choosing to ship it anyway
is an operator decision. Also block if retiring the halt cannot be done without
also changing what `driver_edit.py` detects: the detection is gate 1-era
correctness that this unit has no mandate over, and folding the two would make a
future driver edit invisible rather than merely non-halting. Also block if
re-entering execution from the pin at startup cannot be made to terminate
provably — an exec that can re-enter itself is worse than the restart it
replaces.
