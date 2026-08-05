---
id: FEAT-2026-0057/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
generated_surfaces: []
produces:
  - specfuse/loop/prerun.py
  - tests/test_prerun_oracles.py
produces_driver_helper:
  - run_pre_dispatch
  - resolve_prerun_sets
  - PREP_HALT_CLASS
---

# Add the pre-dispatch runner for `prep` and `oracles` work-unit frontmatter

**Objective.** One runner that resolves a work unit's `prep` and `oracles` sets
against `.specfuse/verification.yml` and executes them before the session starts
— prep fail-fast, oracles capture-all.

**Context.** Correlation ID `FEAT-2026-0057/T01`, the first of three substantive
units in this feature's only gate. Read `PLAN.md` in this folder for the framing
and the scope boundary, and `GATE-01.md` for the gate's definition of done.

The problem this solves is timing, not execution. Everything in this repo that
runs a declared command runs it at work-unit **exit**: `verify()`
(`specfuse/loop/loop.py:2855`) describes itself as *"the exit oracle."* Captured
output therefore reaches an agent only as failure feedback on a retry. An agent
that needs oracle results *before* writing a verdict must hand-drive the commands
itself, and an environment-prep step — whose failure is a setup problem, not a
verdict — has nowhere to live at all.

The grounding files:

- `specfuse/loop/loop.py:2753` — `_run_gate_set(gate_set, feature_dir)`, which
  you **call** rather than modify. It already handles `{feature_dir}`
  substitution, `stdin=DEVNULL`, process-group kill on timeout, and Git-Bash
  routing on Windows. It returns a list of `{"name", "ok", "report"}`.
- `specfuse/loop/loop.py:2875-2891` — how `verify()` resolves `extra_gates`
  against `verification.yml` and how it phrases a CONFIGURATION ERROR for a
  missing set name. Your resolution and error shape mirror this deliberately;
  read it before writing yours.
- `specfuse/loop/loop.py:212` — the `extra_gates` field on `WorkUnit`, and
  `loop.py:612-622` for how `load_wu` parses a string-or-list frontmatter field.
  `prep` and `oracles` parse the same way.
- `tests/test_extra_gates.py` — the closest test precedent, including the fixture
  shape for writing a work unit and a `verification.yml` into a tempdir.

Binding rules apply by reference and are not restated here:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`,
`.specfuse/rules/security-boundaries.md`, `.specfuse/rules/correlation-ids.md`.
For running and interpreting gates, see `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. `tests/test_prerun_oracles.py::TestPreDispatch::test_prep_failure_halts_before_dispatch`
   exists and **fails on HEAD before this work unit runs** — the file does not yet
   exist, which counts as red. Scoped run:
   `python3 -m unittest tests.test_prerun_oracles.TestPreDispatch.test_prep_failure_halts_before_dispatch`.
2. `run_pre_dispatch(wu, feature_dir, cfg)` executes every entry in the work
   unit's `prep` set in declared order and **stops at the first non-zero exit**,
   returning an outcome carrying `PREP_HALT_CLASS`. A later prep entry does not
   run once an earlier one has failed.
3. When prep succeeds, the `oracles` set runs with **every** entry executed
   regardless of any individual failure, and each result is returned carrying its
   name, its ok flag, and its captured output.
4. A `prep` or `oracles` name absent from `verification.yml` returns a named
   CONFIGURATION ERROR whose message names the missing set and the work unit —
   the same class and phrasing shape as `verify()`'s `extra_gates` treatment at
   `loop.py:2882`. It is never a silent pass.
5. A work unit declaring neither `prep` nor `oracles` causes no pre-dispatch work
   and no behavior change: `run_pre_dispatch` returns an empty outcome without
   invoking `_run_gate_set`.
6. The test named in criterion 1 **passes after this work unit's edits**
   (`python3 -m unittest tests.test_prerun_oracles.TestPreDispatch.test_prep_failure_halts_before_dispatch`
   exits zero).
7. `python3 -c "from specfuse.loop.prerun import run_pre_dispatch, resolve_prerun_sets, PREP_HALT_CLASS"`
   exits zero.

**Do not touch.**

- `verify()`, `_run_gate_set`, and the `extra_gates` handling in
  `specfuse/loop/loop.py`. This unit **calls** `_run_gate_set`; it does not change
  its signature or its behaviour. Exit-time verification semantics are out of
  scope for the whole feature (see PLAN.md's scope boundary), and keeping them
  untouched is what keeps sibling work units' oracles green.
- `specfuse/loop/prerun_capture.py` and `tests/test_prerun_capture.py` — owned by
  T02 in this gate.
- `.specfuse/verification.yml` — owned by T03 in this gate. Your tests declare
  their own fixture config in a tempdir; they do not read or edit the repo's.
- Generated directories, secrets (`.env`, `*.pem`, `*.key`, `credentials.json`),
  and `.git/` internals. See `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set as declared in `.specfuse/verification.yml`: `tests`,
  `lint`, `security`, `coverage` (≥ 90%), `leak-scan`, `event-type-gate`,
  `roadmap-link-gate`, `arm-sweep-gate`.
- The scoped red→green run named in criteria 1 and 6.
- The symbol-existence check in criterion 7. The `code` gate passes when no test
  asserts a symbol exists and cannot detect its absence; this check fills that
  gap.

**Escalation triggers.**

- If `run_pre_dispatch` cannot be wired without editing `_run_gate_set`'s
  signature or `verify()`'s behaviour, emit `status: blocked` — that is a
  boundary this feature scoped out deliberately, and widening it is a decision
  for a human, not for this session.
- If the resolution logic cannot mirror `verify()`'s CONFIGURATION ERROR shape
  because the two differ in a way the plan did not anticipate, block with the
  specific divergence rather than inventing a second error vocabulary.
- If any of `run_pre_dispatch`, `resolve_prerun_sets`, or `PREP_HALT_CLASS` is
  absent from the files you edited, emit `status: blocked` — do not claim
  complete.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
  A reasoned block with evidence beats a guessed pass.
