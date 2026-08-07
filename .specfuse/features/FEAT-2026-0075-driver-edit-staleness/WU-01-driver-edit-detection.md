---
id: FEAT-2026-0075/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces_driver_helper:
  - specfuse.loop.driver_edit.diff_edits_driver
  - specfuse.loop.driver_edit.driver_paths_in
  - specfuse.loop.driver_edit.changed_paths_for_commit
produces:
  - specfuse/loop/driver_edit.py
  - tests/test_driver_edit_detection.py
generated_surfaces: []
---

# Detect a driver-editing diff from a commit's changed paths

**Objective.** Create `specfuse/loop/driver_edit.py` — the one place that answers
"does this set of changed paths edit the driver", plus the helper that extracts a
commit's changed paths, which does not exist today.

**Context.** This is `FEAT-2026-0075/T01`, the first work unit of gate 1. Read
`PLAN.md` in this folder — especially § *Scope decision*, whose second load-bearing
property is the contract this module implements — and `GATE-01.md`.

The feature makes a hazard visible: a work unit that edits the driver changes nothing
for anything the same process dispatches afterwards, because Python caches modules in
`sys.modules` at first import. T02 and T03 are the consumers; this unit is the
predicate they share.

**Detection keys on the diff, never on declarations — this is the contract, not a
preference.** `produces:` and `produces_driver_helper` are author-supplied, and the
lint on the latter is WARN-only, so a work unit can edit `loop.py` while declaring
nothing at all. A detector that trusts the declaration misses exactly the careless
case it exists to catch. `squash_commit` (`specfuse/loop/loop.py:2175`, called at
`loop.py:6182`) produces the commit whose diff is ground truth; this unit provides the
extraction, and T02 wires it.

**This module is data and a pure predicate.** `changed_paths_for_commit` shells out to
git and is the one impure function here; keep it separate from the predicate so the
predicate itself is trivially testable without a repository. The module must not
import `loop.py` — `loop.py` will import it, and the reverse edge would be a cycle.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_driver_edit_detection.py::test_loop_py_edit_is_detected` exists and
   **fails on HEAD before this WU's edits** (the module does not exist, so the import
   raises `ModuleNotFoundError`). Record the failing output in the RESULT block before
   editing production code.
2. `specfuse/loop/driver_edit.py` defines `DRIVER_MODULE_PREFIXES` as a tuple of
   path prefixes naming the driver's own importable surface, containing at minimum
   `specfuse/loop/`.
3. `diff_edits_driver(paths)` returns `True` for any iterable containing a path under
   a `DRIVER_MODULE_PREFIXES` entry and `False` otherwise, asserted for each of:
   `specfuse/loop/loop.py` → True; `specfuse/loop/arm_eval.py` → True;
   `tests/test_loop.py` → False; `.specfuse/features/X/PLAN.md` → False;
   `docs/methodology.md` → False; the empty iterable → False.
4. `driver_paths_in(paths)` returns only the matching paths, in input order, so a
   caller can name the offending files rather than only report a boolean.
5. `changed_paths_for_commit(sha, repo_root)` returns the list of paths a commit
   touched, asserted against a real temporary git repository with a two-file commit.
   Exactly one function in this module invokes a subprocess; a grep for
   `subprocess` over the module returns matches only inside it.
6. `diff_edits_driver` and `driver_paths_in` are pure — a grep for
   `open(|Path(|subprocess|os\.` over each function's own body returns no match.
   Paste the grep.
7. The module does not import `specfuse.loop.loop`:
   `grep -n 'import' specfuse/loop/driver_edit.py` shows no `loop` import. Paste it.
8. `python3 -c "from specfuse.loop.driver_edit import DRIVER_MODULE_PREFIXES, diff_edits_driver, driver_paths_in, changed_paths_for_commit"`
   exits 0.
9. The test named in criterion 1 **passes** after this WU's edits.
10. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/loop.py` — T02 and T03 own every call site for this
module, and a call site added here would be dead code the gate's own units disagree
about. `specfuse/loop/arm_eval.py` (gate 2's surface; its class-2 detection stays as
shipped). `.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`.
Any other feature's folder under `.specfuse/features/`. Generated directories,
secrets, `.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`
(`ruff check specfuse .specfuse/scripts tests scripts`), `security`
(`bandit -r specfuse .specfuse/scripts -ll`), `coverage`
(`coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90`),
`leak-scan`, and `event-type-gate`. In addition run criterion 8's symbol-existence
check and criteria 6 and 7's greps verbatim, pasting each output.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`changed_paths_for_commit` cannot be written without importing `loop.py` (that is a
cycle and a design question for the operator, not a free choice); the prefix list in
criterion 2 cannot classify the criterion-3 cases without also matching `tests/`,
which would make every test-editing unit look driver-editing and drown the warning
T02 builds; `diff_edits_driver` or `changed_paths_for_commit` is absent from the file
you edited, or criterion 8's import fails — do not claim complete; or coverage drops
below 90% and raising it would require touching a module outside this WU's two files.
