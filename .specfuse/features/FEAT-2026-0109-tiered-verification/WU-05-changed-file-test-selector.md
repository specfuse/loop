---
id: FEAT-2026-0109/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: select_tests_for_changed_files
produces:
  - specfuse/loop/loop.py
  - pyproject.toml
  - tests/test_changed_file_test_selection.py
model: sonnet
effort: high
gate_set: code
---

# "Tests touching changed files" — a measured map, not a guessed one

**Objective.** Give the per-attempt tier its second selector: the tests that
actually execute the lines an attempt changed, derived from coverage data the
broad run already produces, with a fail-safe fallback to the full command.

**Context.** FEAT-2026-0109/T05; read `PLAN.md`, `GATE-02.md`, T04, and
`GATE-02-REVIEW.md` § "Tests touching changed files", which records the four
rules considered and why this one was chosen. Depends on T04, which ships the
tier mechanism and the declared-test half of the selection.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file in
gate 1 and T04 added the tier resolution. This unit adds one selector called
from the point T04 already computes the per-attempt selection, and changes
nothing else in the driver.

**Why this is not a speed unit.** T04's declared-test rule already takes the
per-attempt test run from 146.1s to 3.9s on a gate-1 unit's own modules; this
unit adds almost nothing to that. What it adds is **attribution precision**. A
unit that edits `specfuse/loop/loop.py` and breaks a test it never declared is
caught today only by the broad run — which, under gate 2, happens once, after
every unit in the gate has landed, at which point "which unit broke it" is a
question nobody can answer cheaply. That is the same question gate 1's lazy
attribution exists to answer, one tier up. Catching it on the attempt that
caused it is the value; the fail-safe and the broad run bound the cost of
getting it wrong.

**The rule, and the two it beats.** Measured on this tree and recorded in
`GATE-02.md`'s table:

- **Import graph** — the test modules that import the changed module — narrows
  the suite only 146.1s → 61.8s here, because `loop.py` is one ~9k-line module
  that 153 of 393 test modules import. Its precision is capped by module
  granularity, and this repo's granularity is wrong for it.
- **Path convention** (`specfuse/loop/loop.py` → `tests/test_loop*.py`) is
  free and useless here: the modules covering `loop.py` are named
  `test_baseline_provenance.py`, `test_lazy_baseline_e2e.py` and so on. It
  would select almost nothing, which is the fail-open direction.
- **Line-granularity coverage contexts** are the only option whose precision is
  not capped by module size: a change to `write_gate_baseline` selects the
  tests that executed *those lines*, not the 1704 tests that import the file.

**The mechanism.** `coverage` is already a dependency (7.x, C extension) and
the `tests` gate already runs under `coverage run --source=specfuse`. Turn on
per-test dynamic contexts in `pyproject.toml` (`[tool.coverage.run]`,
`dynamic_context = "test_function"`), and the broad run's coverage data
becomes a measured file/line → test map for free. `pyproject.toml` is the
right home: there is no `.coveragerc` today and the `tests` gate passes
`--source` on the command line, so adding a second config surface would split
the configuration in two.

**Staleness is the whole risk, so make it explicit rather than implicit.** The
map is only as fresh as the last broad run, and the broad run happens *before
the close* — so the map available during an attempt describes an earlier tree.
Record the tree hash the map was built at (T02's `HEAD^{tree}` primitive
already exists) and treat every one of these as "unresolvable":

- no map on disk at all — including the first gate ever run in a project,
  where the changed-file half simply does not narrow until one broad run has
  happened;
- a changed path with no entry in the map — a **new** source file is exactly
  this case, and it is the one that must not fail open;
- a map whose recorded tree is not an ancestor of the current one, or that
  cannot be parsed.

Every unresolvable case falls back to the gate's **full** command, per T04. The
selector may run more tests than necessary; it may never run fewer than the
declared set.

**Where the map lives.** Not in the committed tree — it is derived data, and
`.coverage` is already gitignored. It must also survive the per-attempt
`git reset --hard`: `reset_preserving_events` sweeps untracked paths that were
not present before the attempt, so the map must be written by the broad run
(before any attempt in the next gate) and not by an attempt. If no location
satisfies both constraints, that is an escalation, not a reason to commit
derived data.

**Cost this unit accepts, stated plainly.** `dynamic_context = "test_function"`
makes the coverage run slower and the data file larger. Measure both on this
tree and record the numbers in the RESULT block: if the broad run's `tests`
gate grows by more than roughly half, say so — the trade is then the operator's
to weigh, and the fallback path means the feature still works with the map
disabled.

**Acceptance criteria.**

- `tests/test_changed_file_test_selection.py::test_a_changed_line_selects_the_tests_that_executed_it` fails on HEAD and passes after: given a map built from a real coverage run with dynamic contexts, changing a specific function selects the test modules whose contexts touched those lines, and does not select modules that did not.
- `::test_an_unmapped_new_source_file_falls_back_to_the_full_command`: a changed path absent from the map runs the full gate command — asserted on the recorded command, the fail-safe direction.
- `::test_a_missing_map_falls_back_to_the_full_command`: with no map on disk, the per-attempt run uses the full command and does not error.
- `::test_a_stale_map_is_refused_rather_than_trusted`: a map whose recorded tree does not correspond to an ancestor of the current tree is treated as unresolvable, not consulted.
- `::test_selection_is_the_union_with_the_declared_paths`: the final selection contains every test path from the unit's `produces:` plus everything the map resolved — the map may add, never subtract.
- `python3 -m unittest tests.test_tiered_verification_e2e -q` reports `OK` — T04's per-attempt assertions still hold with the selector wired in.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `coverage report --fail-under=90` still passes with dynamic contexts enabled.
- The RESULT block records the measured wall clock and `.coverage` size of the `tests` gate with and without `dynamic_context`, each from a command run in that session.

**Do not touch.** T04's tier declaration and its absent-key default; T06's
broad-run bookkeeping; T07's attribution bound; gate 1's units, `GATE-01.md`'s
`baseline:` block, and `RETROSPECTIVE.md`; what any existing gate in
`.specfuse/verification.yml` asserts — the `--fail-under=90` threshold in
particular is not this unit's to move; `.specfuse/rules/`, `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if no map location satisfies
both constraints above — gitignored *and* surviving `reset_preserving_events` —
rather than committing derived data or weakening the reset. Also block if
enabling `dynamic_context` cannot be done without breaking the `needs: [tests]`
edge the `coverage` gate depends on, or if it pushes `coverage report
--fail-under=90` red for reasons that are not a real coverage regression: a
measurement artefact silencing a live gate is an operator decision.
