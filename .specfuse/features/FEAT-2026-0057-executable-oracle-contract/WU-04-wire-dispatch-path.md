---
id: FEAT-2026-0057/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
oracle_env: macos_local
generated_surfaces: []
provenance: "FEAT-2026-0057/G1-CLOSE RETROSPECTIVE.md follow-ups FU-1 and FU-2 — the close measured that no dispatch path reads `prep:`/`oracles:` or calls `format_oracle_capture`, so the gate's definition of done was unmet on a feature whose three units all passed."
produces:
  - specfuse/loop/loop.py
  - tests/test_prerun_wiring.py
produces_driver_helper:
  - WorkUnit.prep
  - WorkUnit.oracles
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-05T13:35:25.427248+00:00
duration_seconds: 1413.382
cost_usd: 5.136799
input_tokens: 4138
output_tokens: 31669
---

# Wire the pre-dispatch runner into the driver's dispatch path

**Objective.** Make `prep:` and `oracles:` real: parsed off a work unit, run
before its session starts, with captured oracle output appended to the body the
session receives.

**Context.** Correlation ID `FEAT-2026-0057/T04`. This unit exists because gate 1
closed `partially_met`: T01, T02, and T03 each passed their own oracles and
together built a mechanism that **nothing calls**. Read
`RETROSPECTIVE.md` in this folder — sections *What was not built, measured rather
than assumed* and *Hedged-verdict follow-up record* (FU-1, FU-2) — before writing
any code. Its measurements are your starting state, not background reading.

What the close established by probe, not inference:

- `WorkUnit`'s field list carries `extra_gates` but neither `prep` nor `oracles`,
  and `load_wu` has no parse branch for either key.
- `resolve_prerun_sets` reads both through `getattr(wu, "prep", None)`, which on a
  real `WorkUnit` is unconditionally `None` — so `run_pre_dispatch` returns the
  empty "no pre-dispatch work" outcome for a unit that declared both keys, and
  nothing reports that the declaration was ignored.
- A repo-wide grep for the five symbols the earlier units produced returns 28
  hits, every one inside those modules or their own tests. Zero in
  `specfuse/loop/loop.py`.

The pieces you are connecting already exist and are tested:

- `specfuse/loop/prerun.py` — `run_pre_dispatch(wu, feature_dir, cfg)`,
  `resolve_prerun_sets`, `PREP_HALT_CLASS`. Returns a dict with `halted`,
  `halt_class`, `message`, `prep_results`, `oracle_results`.
- `specfuse/loop/prerun_capture.py` — `format_oracle_capture(results)` and
  `ORACLE_CAPTURE_BUDGET_BYTES`. Returns a bounded section with a
  `## Captured oracle output (pre-dispatch)` header and one
  `### oracle: <name> (OK|FAIL)` block per entry.
- `specfuse/loop/loop.py:612-622` — how `load_wu` parses `extra_gates` with
  string-or-list handling. `prep` and `oracles` parse identically; mirror it
  rather than inventing a second shape.
- `specfuse/loop/loop.py:212` — the `extra_gates` field declaration on the
  `WorkUnit` dataclass, and the comment style used for an optional field.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/correlation-ids.md`. See
`.specfuse/skills/verification/SKILL.md` for running and interpreting gates.

**Acceptance criteria.**

1. `tests/test_prerun_wiring.py::TestWiring::test_declared_prep_and_oracles_reach_the_runner`
   exists and **fails on HEAD before this work unit runs** — the file does not yet
   exist, which counts as red. Scoped run:
   `python3 -m unittest tests.test_prerun_wiring.TestWiring.test_declared_prep_and_oracles_reach_the_runner`.
2. `WorkUnit` carries `prep: list[str]` and `oracles: list[str]`, and `load_wu`
   parses both keys with the same string-or-list handling `extra_gates` receives
   at `loop.py:612-622` — absent yields `[]`, a bare string yields a one-element
   list, a list yields the list, and a wrong type raises the same class of error.
3. A work unit file declaring `prep: [<set>]` and `oracles: [<set>]`, loaded
   through `load_wu` and passed to `run_pre_dispatch` with a
   `verification.yml`-shaped cfg containing both sets, returns **non-empty**
   `prep_results` and `oracle_results`. This is the exact probe the close ran to
   prove the defect; it must now return the opposite result.
4. The dispatch path calls `run_pre_dispatch(wu, feature_dir, cfg)` **before** the
   session is started, and a work unit whose prep entry exits non-zero halts
   before dispatch with `halt_class == PREP_HALT_CLASS`, with no later prep entry
   executed and no session spawned.
5. `run_pre_dispatch`'s `oracle_results` are passed through
   `format_oracle_capture` and the returned section is appended to the work-unit
   body the session receives, so a dispatched session's prompt contains the
   `## Captured oracle output (pre-dispatch)` header with one
   `### oracle: <name> (OK|FAIL)` block per declared entry.
6. A work unit declaring no `oracles` receives neither that header nor a
   truncation marker, and a work unit declaring neither key causes no
   pre-dispatch work — the no-op path stays a no-op.
7. The test named in criterion 1 **passes after this work unit's edits**
   (`python3 -m unittest tests.test_prerun_wiring.TestWiring.test_declared_prep_and_oracles_reach_the_runner`
   exits zero).

**Do not touch.**

- **The exit-time verification symbols**, by name: `verify()`, `_run_gate_set`,
  `select_gate_report_lines`, and the existing `extra_gates` parsing branch. Do
  not change their signatures or their behaviour. Exit-time verification semantics
  remain out of scope for this feature — this unit adds a pre-dispatch call site
  and changes nothing about what happens when a work unit finishes, and
  `extra_gates` keeps working exactly as it does today alongside the new keys.

  The boundary here is those symbols, **not** the module that holds them: this
  unit's `produces` list names the driver module deliberately, because every
  earlier unit in this gate was forbidden from touching it and that is exactly why
  the feature shipped unwired. Add the new dataclass fields, the new parse branch,
  and the new call site freely; leave the four named symbols alone.
- `specfuse/loop/prerun.py` and `specfuse/loop/prerun_capture.py`. Both are
  `done`, tested, and behave to spec. If one of them cannot serve the wiring,
  that is an escalation, not an edit.
- `.specfuse/verification.yml` and its `oracles` set — T03's, already landed.
- Other features' folders under `.specfuse/features/`.
- Generated directories, secrets (`.env`, `*.pem`, `*.key`, `credentials.json`),
  and `.git/` internals. See `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set as declared in `.specfuse/verification.yml`: `tests`,
  `lint`, `security`, `coverage` (≥ 90%), `leak-scan`, `event-type-gate`,
  `roadmap-link-gate`, `arm-sweep-gate`.
- The scoped red→green run named in criteria 1 and 7.
- `python3 -c "from specfuse.loop.loop import WorkUnit; assert hasattr(WorkUnit('x',__import__('pathlib').Path('.'),[],'implementation','m','pending',0,'t','b'), 'prep')"`
  or an equivalent field-presence check — the `code` gate cannot detect an absent
  dataclass field on its own.
- **You are editing the driver that runs your own gates.** Run the full `code` set
  after your edits and read the result: a wiring defect here can make every
  subsequent work unit fail for reasons unrelated to its own code.

**Escalation triggers.**

- If the dispatch path cannot call `run_pre_dispatch` without changing `verify()`
  or `_run_gate_set`, emit `status: blocked` with the specific coupling. That
  boundary is what keeps this change additive.
- If wiring the call site makes any existing test fail for a reason you cannot
  attribute to your own edit, block with the failure rather than adjusting the
  test. A pre-dispatch hook that breaks the driver's existing behaviour is a
  design problem, not a test problem.
- If `prep` and `oracles` cannot both be parsed the way `extra_gates` is because
  the two differ in a way this spec did not anticipate, block with the divergence
  rather than inventing a second parsing vocabulary.
- If `WorkUnit` still lacks a `prep` or `oracles` attribute after your edits, or
  if `format_oracle_capture` still has no caller in `specfuse/loop/loop.py`, emit
  `status: blocked` — do not claim complete. Those two absences are the exact
  defect this unit exists to remove, and the close will grep for them again.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
