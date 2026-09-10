---
id: FEAT-2026-0110/T01
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.00
produces_driver_helper:
  - resolve_narrow_selection_config
  - render_selected_tests
produces:
  - specfuse/loop/loop.py
  - tests/test_language_aware_narrow_selection.py
---

# Read `narrow_selection` from the gate and render the selection through it

**Objective.** Thread an optional `narrow_selection` block from a `code` gate's
config into the narrow-test selection, so a unit whose tests live outside
`tests/` resolves to a narrow command instead of falling back to the full suite.

**Context.** FEAT-2026-0110/T01, issue #3281. This is gate 1's **walking
skeleton**: its job is to wire the thinnest end-to-end path and turn
`GATE-01.md`'s `feature_oracle` green, not to build any one part well. Stubs are
permitted in this unit and nowhere else in this gate
(`/authoring-work-units` tracer-bullet rule).

The selection is built in `specfuse/loop/loop.py` by `select_narrow_test_modules`
(keeps `produces:` entries under `tests/`) and `_test_module_name` (dotted
conversion), unioned by `resolve_narrow_test_selection`, and substituted by
`resolve_narrow_command` — which already receives the gate dict, so the config
is reachable without a new parameter on the public entry point.

`resolve_gate_tiers` is the shape to copy for an optional per-gate key: read it
with `.get`, and make the absent-key default reproduce today's behaviour exactly.
`GATE-01.md` carries the table of the four defaults; it is the contract, not a
suggestion.

Ship `format: class_name` in this unit — it is what the oracle's Maven fixture
needs. `path` and the unknown-value refusal are T02's.

**Acceptance criteria.**

1. `tests/test_language_aware_narrow_selection.py` exists and fails on HEAD
   before this unit's edits (the module is absent today); after this unit,
   `python3 -m unittest tests.test_language_aware_narrow_selection -v` exits 0.
2. That module asserts the Maven shape end to end: a `WorkUnit` whose
   `produces:` names two paths under `src/test/java/`, against a gate declaring
   `narrow_command: "./mvnw test -Dtest={selected_test_modules}"` and
   `narrow_selection` with `test_roots: ["src/test/java/"]`,
   `format: class_name`, `separator: ","`, resolves through
   `resolve_narrow_command` to `./mvnw test -Dtest=FooTest,BarTest`.
3. A gate declaring **no** `narrow_selection` resolves byte-identically to
   today: `python3 -m unittest tests.test_tiered_verification_e2e -v` exits 0
   with no edit to that file.
4. `grep -n "narrow_selection" specfuse/loop/loop.py` shows the key read via
   `.get` with the four documented defaults, and
   `grep -c "narrow_selection" .specfuse/verification.yml` returns 0 — this
   repo's own gate set is not edited.

**Do not touch.** `.specfuse/verification.yml` (PLAN.md's framing explains why
editing it would break every sibling WU's exit oracle);
`CHANGED_FILE_SELECTION_ENABLED` and `select_tests_for_changed_files`
(explicitly out of scope); the sibling WU files
`WU-02-formats-and-refusal.md` and `WU-03-document-the-contract.md`; plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set minus every gate declaring `tier: broad`,
with `tests` through its `narrow_command` over this unit's own `produces:` test
modules. Then the gate's own oracle:
`python3 -m unittest tests.test_language_aware_narrow_selection -v`. Symbol
check for each new symbol: `grep -n "<symbol>" specfuse/loop/loop.py`. The full
suite, coverage and the broad gates are the driver's, once per gate — never run
in-session.

**Escalation triggers.** Stop with `status: blocked` if making the oracle green
appears to require editing `.specfuse/verification.yml` (that is the
`[FEAT-2026-0019/G1]` hazard this feature is shaped to avoid, and it means the
design is wrong, not that the boundary should be crossed); or if
`resolve_narrow_command`'s existing callers cannot reach the gate config without
changing a signature outside `loop.py`.
