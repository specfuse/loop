---
id: FEAT-2026-0079/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.50
produces_driver_helper:
  - specfuse.loop.roadmap_archive.main
produces:
  - specfuse/loop/roadmap_archive.py
  - .specfuse/scripts/roadmap_archive.py
  - tests/test_roadmap_archive_cli.py
---

# T01 — Expose the archiver as a command line

## Context

`auto_archive_feature` (`specfuse/loop/loop.py:3928`) is the complete single-feature
archiving algorithm, including `_reconcile_moved_section` (`loop.py:3884`) which #1169
added to fix cross-reference and `**Status:**` reconciliation. It is called from exactly
one place — `fire_terminal_flips` (`loop.py:4290`) — and **is not reachable from any
command line**. That unreachability is why the `/roadmap-archive` skill restates the
algorithm rather than calling it, which is the divergence this feature exists to close.

This unit adds reachability only. **The archiving behaviour is held constant**: no edit to
`auto_archive_feature` or `_reconcile_moved_section` beyond what an import requires.

Two constraints fixed at drafting, not open for re-litigation here:

- **No `pyproject.toml` console script.** That file is both a judge path and a dependency
  manifest, so an entry point fires `judge_editing` and `decision_class_paths` for no gain.
  The invocation is `python3 -m specfuse.loop.roadmap_archive <FEAT-ID>` and the shim.
- **A new module, not a `main()` added to `loop.py`.** `loop.py` is ~7,700 lines and a judge
  module; a thin wrapper keeps the diff off it. Follow `.specfuse/scripts/gate_eval.py`
  (26 lines) as the shim's shape verbatim — it path-inserts the repo root so `specfuse.loop`
  resolves from source even when the package is not pip-installed, which is the property
  that makes delegation safe in a tree with no installed driver.

`specfuse/loop/roadmap_archive.py` is a **new module under `specfuse/loop/`**, so
`tests/test_judge_path_registry.py` will fail until it is classified. It belongs in
`JUDGE_MODULES` (`specfuse/loop/arm_eval.py`): archiving is what the terminal-close
post-pass invariant `assert_terminal_flips_fired` depends on, so an edit to it can change
whether a close is judged complete.

## Acceptance criteria

1. `tests/test_roadmap_archive_cli.py::TestArchiveCLI::test_archives_a_done_feature` fails
   on HEAD before this unit runs (the module does not exist) and passes after. It builds a
   temp repo with a `done` roadmap row plus its inline detail section, invokes `main()`, and
   asserts the section moved to `roadmap-archive.md` with its `<a id>` anchor and the row's
   Detail cell rewritten to `[→ archive](roadmap-archive.md#feat-…)`.
2. A second test asserts the CLI reports the three documented outcomes distinctly —
   `archived`, `already archived`, and `refused: <reason>` — since the skill will branch on
   them in T02. A non-zero exit accompanies `refused`.
3. `.specfuse/scripts/roadmap_archive.py` re-exports the module and resolves `specfuse.loop`
   from source with no pip install, verified by a test invoking it as a subprocess with the
   package absent from `sys.path`.
4. `specfuse/loop/roadmap_archive.py` appears in `JUDGE_MODULES` and
   `tests/test_judge_path_registry.py` passes.
5. `auto_archive_feature` and `_reconcile_moved_section` are unchanged — asserted by the
   diff carrying no edit to either function body.
6. `pyproject.toml` is not modified.

## Verification

- `python3 -m unittest discover -s tests -v -b`
- `ruff check specfuse .specfuse/scripts tests scripts`
- `bandit -r specfuse .specfuse/scripts -ll`
- `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90`

## Escalation triggers

Stop and escalate rather than guessing:

- `auto_archive_feature` cannot be imported from a new module without a circular import.
  That would mean the wrapper has to live in `loop.py` after all, which reverses a drafting
  decision and belongs with the operator, not an inline workaround.
- The shim cannot resolve `specfuse.loop` from source without a pip install. That property is
  what makes T02's delegation safe in a driverless tree; losing it changes this feature's
  premise.
- Classifying the new module as a judge surface turns out to be wrong on inspection — say so
  rather than filing it under `NON_JUDGE_MODULES` to make the registry test pass.

## Do not touch

- `auto_archive_feature` / `_reconcile_moved_section` bodies — behaviour is held constant.
- `pyproject.toml`.
- The `/roadmap-archive` skill — that is T02's surface.
