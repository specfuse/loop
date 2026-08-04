---
id: FEAT-2026-0034/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - .specfuse/scripts/roadmap_link_gate.py
  - .specfuse/verification.yml
  - tests/test_roadmap_link_gate.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-04T03:55:48.893168+00:00
duration_seconds: 721.288
cost_usd: 1.169444
input_tokens: 50
output_tokens: 11123
---

# The gate: fail on rot, green on this tree, loud about the fix

**Objective.** Give T01's linter a command-line entry point, wire it into
`.specfuse/verification.yml`, and leave it exiting 0 on this tree.

**Context.** Correlation ID `FEAT-2026-0034/T02`. Read `PLAN.md` first. T01 owns the
invariants and returns findings; this WU decides exit codes, output shape, and gate
wiring. Do not re-implement a check here.

**Follow the two-feature-deep precedent.** `.specfuse/scripts/event_type_gate.py`
(FEAT-2026-0060/T02) and `.specfuse/scripts/arm_sweep_gate.py` (FEAT-2026-0063/T02) are
the shape: a thin script importing the package module, exit 0/1, offenders on stderr,
and the reason for any deliberate scoping written into the docstring so the next reader
does not "fix" a narrow scope into permanent redness.

**Severity decides the exit code, and the split is the point.** ERROR findings exit 1.
WARN findings print and exit 0. A gate that fails on the non-`blocked` **Blocked by.**
WARN, or on an orphan detail section, would be red on trees that are merely untidy
rather than broken — and a gate that is red for tidiness gets ignored, which is how the
rot survived long enough to need this feature.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_roadmap_link_gate.py::TestRoadmapLinkGate::test_error_finding_exits_1_warn_exits_0`
   exists and **fails on HEAD before this WU runs** (no entry point exists, which
   counts as red).
2. That test drives the entry point over a fixture carrying exactly one ERROR and
   asserts exit 1; then over a fixture carrying only WARNs and asserts exit 0 with the
   warnings printed. It passes after this WU's edits.
3. A test asserts every finding is printed with its file, its line, and the mechanical
   fix — a gate whose output does not say what to change makes the operator re-derive
   what the linter already knew.
4. A test asserts a clean tree exits 0 and still prints a one-line summary naming what
   was checked and the counts. A gate that reports nothing when it passes is a gate
   nobody trusts.
5. `.specfuse/verification.yml` carries the new gate, following the `event_type_gate`
   entry's shape, with a comment recording that WARN severities deliberately do not
   fail it.
6. **The gate exits 0 on this tree.** Run it against the real `.specfuse/roadmap.md`
   and `.specfuse/roadmap-archive.md`; quote the exit code and the summary line in the
   result.
7. The entry point's docstring states which severities fail the gate and why the WARN
   set does not.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/loop/lint_roadmap.py`'s findings contract — T01 owns it; if
the gate needs a field the findings do not carry, that is an escalation, not a quiet
edit to T01's module. The driver package's own modules — this WU adds no driver
symbol and wires no dispatch path; it is a thin entry point plus a `verification.yml`
row. `.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md` — the tree is clean and
this WU must not "fix" it into greenness.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Plus criterion 6: the gate itself must run
green against the real files, with the exit code quoted. A gate wired into
`verification.yml` that has never been run against real input is the failure shape this
project has now shipped twice against.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: making
the gate exit 0 on this tree requires editing the roadmap files (they were verified
clean before this feature was drafted — a violation now means either new rot landed or
T01's checker disagrees with the hand check, and both need reporting rather than
papering over); or the ERROR/WARN split cannot be expressed because T01's findings do
not carry a severity. Do **not** downgrade an ERROR to a WARN to make the gate green.
