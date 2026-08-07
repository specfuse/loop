---
id: FEAT-2026-0075/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces_driver_helper:
  - specfuse.loop.loop.format_driver_staleness_warning
produces:
  - tests/test_driver_staleness_warning.py
generated_surfaces: []
---

# Warn the moment a driver-editing unit's squash lands

**Objective.** When a work unit's squash commit touches the driver, print immediately
that this process is now stale — before the next unit is dispatched, while the
operator can still restart.

**Objective's whole point, stated once so it is not optimised away.** A warning at
gate completion would be correct and useless: on all three real occurrences the close
was the very next unit dispatched after the driver-editing one, so a gate-end message
would have printed immediately *after* each loss. The window between a unit's squash
landing and the next dispatch is where the money went. This unit puts the warning in
that window. T03 adds the gate-end summary for the close to read; the two are not
substitutes.

**Context.** This is `FEAT-2026-0075/T02`, gate 1. `T01` built
`specfuse/loop/driver_edit.py` (`DRIVER_MODULE_PREFIXES`, `diff_edits_driver`,
`driver_paths_in`, `changed_paths_for_commit`); this unit wires it into the driver's
outcome path. Read `PLAN.md` and `GATE-01.md` in this folder.

**The seam.** `squash_commit` (`specfuse/loop/loop.py:2175`) is called at
`loop.py:6182` and returns the sha of the commit a passing unit produced. That sha's
diff is the ground truth for what the unit changed. Immediately after that call
succeeds, resolve the changed paths through `T01`'s helper and, when they touch the
driver, print the warning. Do **not** put the check inside `squash_commit` — that
function's contract is "make a commit and return its sha", it is called from more than
one place, and widening it would make the warning fire in contexts this unit has not
reasoned about.

**What the warning must say**, because a message that only says "stale" sends the
reader to the source to find out what to do: which unit edited the driver, which files
it touched, that every subsequent dispatch in this process executes the pre-edit
modules, and that a fresh driver process is required before any close can verify the
change. `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` rule (a) is the
content; the message is that rule delivered at the moment it applies instead of in a
file nobody rereads at plan time.

**This unit edits the dispatch path, so nothing in this session can observe its
runtime effect.** Your own tests pass in fresh interpreters and report the new
behaviour correctly — that is precisely why the hazard reads as a mystery. Report what
the tests and a fresh interpreter show; the in-situ observation belongs to
`G1-CLOSE-INTERMEDIATE` after the restart `GATE-01.md` requires.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_driver_staleness_warning.py::test_driver_edit_warns_at_squash` exists
   and **fails on HEAD before this WU's edits**. Record the failing output in the
   RESULT block before editing production code.
2. `specfuse/loop/loop.py` exports
   `format_driver_staleness_warning(wu_id, driver_paths) -> str`, returning exactly
   `""` when `driver_paths` is empty and a non-empty message otherwise.
3. The returned message names the work unit's ID, every path in `driver_paths`, and
   contains an explicit statement that a fresh driver process is required before a
   close can verify the change — each asserted separately against the rendered string.
4. The warning is emitted from the outcome path immediately after the `squash_commit`
   call at `loop.py:6182` succeeds, **not** from inside `squash_commit`:
   `grep -n 'format_driver_staleness_warning' specfuse/loop/loop.py` shows no match
   inside `squash_commit`'s body. Paste the grep.
5. **Seam test, not formatter test.** A test drives the real outcome path with a stub
   that reports a squash diff touching `specfuse/loop/loop.py`, and asserts the
   warning reaches the driver's output. Asserting only on
   `format_driver_staleness_warning` in isolation does not satisfy this criterion —
   the seam is what gate 1 exists to get right, and it is what FEAT-2026-0056's gate 1
   got wrong.
6. A unit whose squash diff touches no driver path produces **no** warning — asserted
   through the same harness, so the negative case exercises the same seam.
7. `python3 -c "from specfuse.loop.loop import format_driver_staleness_warning"`
   exits 0.
8. The test named in criterion 1 **passes** after this WU's edits.
9. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/driver_edit.py` — T01's; import it, do not extend it.
The body of `squash_commit` (criterion 4 asserts it is unchanged in this respect).
The gate-completion path and any event emission — T03's scope; a second warning site
added here would be the drift the two units exist to keep apart.
`specfuse/loop/arm_eval.py` (gate 2's surface). `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. Any other feature's folder under
`.specfuse/features/`. Generated directories, secrets, `.git/`. The driver owns all
git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, `event-type-gate`. In
addition run criterion 7's symbol-existence check and criterion 4's grep verbatim,
pasting both outputs. Do **not** report the running driver's in-situ behaviour as
evidence — this session's process predates your edits by construction.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 5's seam cannot be asserted because the outcome path cannot be driven with a
stub in a test, which would mean the wiring is unverifiable and the whole shape needs
rethinking; emitting the warning at the `loop.py:6182` call site requires changing
`squash_commit`'s signature or return type; `format_driver_staleness_warning` is
absent from the file you edited or criterion 7's import fails — do not claim complete;
or the only way to satisfy criterion 6 is to special-case work-unit types rather than
read the diff, which would reintroduce the declaration-trust `PLAN.md` rejects.
