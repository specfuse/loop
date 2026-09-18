---
id: FEAT-2026-0113/T07H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
produces:
  - specfuse/agent/severity_backfill.py
  - tests/test_build_provenance.py
---

# T07H — the backfill console script calls `warn_if_out_of_tree()`

**Objective.** Make `specfuse-backfill-severity` satisfy the build-provenance
contract every other console script satisfies, and put it under the guard that
enforces it.

**Context.** Hygiene unit. Gate 3 halted at entry with
`preexisting_gate_failure`, two checks red:

```
AssertionError: Items in the first set but not the second:
'specfuse.agent.severity_backfill' : console script(s) declared in
pyproject.toml whose module does not call warn_if_out_of_tree()
```

`tests/test_build_provenance.py:146` holds a six-entry `ENTRY_MODULES` tuple and
`test_the_declared_console_scripts_match_the_wired_set` asserts every
`[project.scripts]` target appears in it. T07 registered
`specfuse-backfill-severity` — correctly, per the Q1 arm-checkpoint decision —
and `specfuse/agent/severity_backfill.py` neither imports nor calls
`warn_if_out_of_tree()`.

The `coverage: no_gate_marker` failure recorded alongside it is downstream: the
coverage gate emits no marker when the tests gate fails first. It needs no
separate fix and should go green with this one.

**Why this is its own unit rather than a two-line hand edit.** The change is
small and the invariant is not: every committed state change traces to a
dispatched-and-verified work unit. This feature has already used the pattern
twice — `T01H` for a `parse_marker` regression and `T02H` for the missing gate
oracle — and doing it differently here because the diff is short is how the
invariant erodes.

**Attribution, stated plainly.** The escalation records `attributed_to:
FEAT-2026-0113/T09`, but T09 was only the unit in flight when the gate-entry
check ran. The guard broke when **T07** landed the console script. T09 is
unmodified by this unit and re-runs behind it.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_build_provenance -v` fails on HEAD before
   this unit runs, on
   `test_the_declared_console_scripts_match_the_wired_set`, and passes after.
2. `specfuse/agent/severity_backfill.py` imports `warn_if_out_of_tree` from
   `specfuse.loop.build_provenance` and calls it in `main()`, in the same
   position the other six entry points call it — first statement of `main()`,
   before argument parsing does any work. Asserted by reading the call site,
   not only by the guard going green.
3. `specfuse/agent/severity_backfill.py` is added to
   `tests/test_build_provenance.py`'s `ENTRY_MODULES` tuple, so
   `test_each_entry_point_calls_the_check` covers it from now on. **Both halves
   are required**: the call alone leaves that second guard blind to this module,
   and the tuple entry alone would fail it.
4. The `ENTRY_MODULES` tuple gains exactly one entry and loses none — asserted
   by its length going from 6 to 7 — so a hygiene unit cannot quietly drop an
   existing entry point from the guard.
5. The full `tests` gate passes, and the `coverage` gate produces its marker
   again, confirming the second failing check was downstream of the first.

**Do not touch.** `pyproject.toml` — T07's `[project.scripts]` registration is
correct and is not what broke; this unit fixes the module it points at.
`specfuse/agent/run.py`, which no unit in this gate edits (the Q1 decision;
T07 criterion 2 asserts an empty diff on it). Every other module named in
`ENTRY_MODULES`. `severity_backfill.py`'s backfill behaviour — selection,
classification, the write path and its ordering are T08/T09/T10's, and this
unit adds a provenance call and nothing else. T09's file.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_build_provenance tests.test_severity_backfill_end_to_end -b`
and `python3 -c "from specfuse.agent.severity_backfill import main"`.

**Escalation triggers.** If satisfying the guard appears to require editing
`pyproject.toml` or any module in `ENTRY_MODULES` other than adding this one
entry, stop — the fix is a provenance call in the module the script already
points at, and anything wider means the diagnosis was wrong. If adding the call
changes any backfill behaviour or any assertion in
`tests/test_severity_backfill_*`, stop: this unit is provenance wiring, and a
behaviour change here belongs to the unit that owns that behaviour.
