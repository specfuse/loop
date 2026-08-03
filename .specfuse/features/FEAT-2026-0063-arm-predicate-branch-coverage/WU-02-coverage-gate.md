---
id: FEAT-2026-0063/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - .specfuse/verification.yml
  - tests/test_arm_sweep_gate.py
produces_driver_helper:
  - arm_sweep_gate_main
oracle_env: macos_local
---

# A gate that fails when the sweep goes blind — not when a branch has yet to fire

**Objective.** Give `arm_sweep` a command-line entry point and wire it into
`.specfuse/verification.yml` as a gate that exits non-zero when the sweep becomes
incomplete, and exits zero on this tree today.

**Context.** Correlation ID `FEAT-2026-0063/T02`. Read `PLAN.md` first —
specifically the §2 satisfiability section, which is the load-bearing decision on
this work unit. Do not reopen it.

**The decision this WU must not re-litigate.** A gate asserting that every class has
fired, or that `not_evaluable` has been observed, is **red today and cannot be made
green by any work this feature permits**: five of eight classes have never fired and
no class has ever reported `not_evaluable`. That is an unsatisfiable acceptance
criterion — the shape that cost FEAT-2026-0060 two blocked attempts and $4.48 last
week. This gate asserts the sweep is *complete*, not that the branches are *covered*.

Follow `.specfuse/scripts/event_type_gate.py`'s shape: the scoping reason lives in
the entry point's docstring, stated plainly, so the next reader does not mistake a
deliberate narrow scope for an oversight and "fix" it into permanent redness.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

Exit codes:

- **0** — every evaluable feature was evaluated, and no `not_evaluable` verdict
  appeared among them.
- **1** — at least one evaluable feature landed in `could_not_evaluate`, or at least
  one `not_evaluable` verdict appeared. Offenders on stderr, named.

The branch-observation table prints on stdout on both paths. The never-fired list is
**output, never an assertion** — printing it is the deliverable; failing on it is the
trap.

`not_evaluable` is treated as a failure here because among *evaluable* features it
means a class could not judge an input it was handed — the predicate's fail-closed
path firing for real. That has never happened, so asserting its absence is
satisfiable today and would genuinely fire on a regression. This is the opposite of
asserting it has been *observed*, which is what would be unsatisfiable.

**Acceptance criteria.**

1. `tests/test_arm_sweep_gate.py::TestArmSweepGate::test_unevaluable_feature_fails_the_gate`
   exists and **fails on HEAD before this WU runs** (no entry point exists, which
   counts as red).
2. That test builds a fixture root containing a baselined feature whose `PLAN.md`
   raises, and asserts the gate exits 1 and names that feature on stderr. It passes
   after this WU's edits.
3. A test asserts a fixture where every evaluable feature sweeps cleanly and no
   `not_evaluable` appears exits 0 — **even though several classes have never
   fired**. This is the satisfiability guarantee from `PLAN.md`, held as a test
   rather than a claim.
4. A test asserts a `not_evaluable` verdict among evaluable features exits 1 and
   names the class and feature.
5. A test asserts the branch-observation table is printed on stdout on both the
   exit-0 and exit-1 paths — a gate that reports nothing when it passes is a gate
   nobody reads.
6. A test asserts an empty evaluable set (no baselined feature anywhere) exits 0 with
   an explicit "nothing evaluable" line rather than a vacuous pass — the sweep must
   say when it had nothing to look at.
7. The entry point's docstring states, in plain sentences, that the gate does not
   assert branch coverage, names the five never-fired classes as of authoring, and
   says what would have to change for a coverage assertion to become satisfiable.
8. `.specfuse/verification.yml` carries the new gate with a comment recording the
   same scoping reason, following the `event_type_gate` entry's shape.
9. **The gate exits 0 on this tree.** Run it against the real
   `.specfuse/features/` and quote the exit code and the printed table in the result.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/arm_sweep.py`'s report contract — T01 owns it; if
the gate needs a field the report does not expose, that is an escalation, not a
quiet edit to T01's module. `specfuse/loop/arm_eval.py`.
`docs/concepts/autonomy-stop-classes.md` — T03 owns the record.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus criterion 9: the new gate
itself must exit 0 against the real `.specfuse/features/`, with the exit code and
printed table quoted in the result. A gate wired into `verification.yml` that has
never been run against real input is the failure shape this whole feature is about.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
making the gate exit 0 on this tree requires excluding a feature T01 classified as
evaluable; T01's report does not expose a field the gate needs (that is an
escalation, not a quiet edit to T01's module); or the gate cannot distinguish
"`not_evaluable` among evaluable features" from "feature excluded for no baseline",
since collapsing those two is the original false-blindness. Narrowing the evaluable
set to buy a green gate is forbidden — a non-zero count of genuinely unevaluable
features is a finding to report, not a number to suppress. Do **not** add a
branch-coverage assertion to make the gate feel stronger; `PLAN.md` §2 records why
that is unsatisfiable today.
