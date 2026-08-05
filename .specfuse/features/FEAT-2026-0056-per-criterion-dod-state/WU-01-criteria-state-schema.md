---
id: FEAT-2026-0056/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - specfuse/loop/criteria_state.py
  - tests/test_criteria_state.py
generated_surfaces: []
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-05T23:44:16.612217+00:00
duration_seconds: 285.082
cost_usd: 0.599546
input_tokens: 14
output_tokens: 5024
---

# Add the per-criterion state schema and its parser/renderer

**Objective.** Create `specfuse/loop/criteria_state.py` — the one module that defines
what a criterion-state entry is, parses the per-gate artifact into entries, and
renders entries back into the artifact.

**Context.** This is `FEAT-2026-0056/T01`, the first work unit of gate 1. The feature
gives a close a memory: each close attempt records, per acceptance criterion, which
oracle proved it, that oracle's exit code, and the tree state it ran against, so a
re-dispatched close does not re-verify from scratch. Read `PLAN.md` in this folder —
especially § *Scope decision: what invalidates a cached green*, which is the design
this module encodes — and `GATE-01.md` for the gate's definition of done.

This module is **data and parsing only**. It does not write files, does not decide
what a close may skip, and is not wired into the driver — T02 does the wiring, T03
does the lint, and the skip policy is gate 2. Keeping it side-effect-free is what
makes it testable without a driver run.

Follow the shape of the existing hedged-verdict follow-up record rather than
inventing a new one: `specfuse/loop/closing_requirements.py` holds
`FOLLOW_UP_KIND_MEANINGS`, `FOLLOW_UP_KINDS`, `KIND_FIELD_RE`, and
`verdict_ceiling_for_kinds` — a per-entry classified record living inside a markdown
artifact, regex-parsed, with the classification written by the close and never
inferred by a reader. Read that module before writing this one. The same posture
applies here: `kind` and `state` are written by the close that ran the oracle,
because it is the only party that knows.

The artifact this module parses is `GATE-NN-CRITERIA.md`, one per gate. Its entry
shape, as a `### `-titled block per criterion:

```markdown
### T03#2

- **criterion:** `specfuse-lint --closing` exits 0 on a legacy close with no artifact
- **oracle:** `python3 -m unittest tests.test_lint_closing_criteria -v`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `85c36e8803932c7e358780b8524cff22eaf62846`
- **attempt:** `2`
```

The criterion identity is `<WU sub-id>#<ordinal>` — the producing work unit's
sub-ID (`T03`, not the full correlation ID) and the 1-based ordinal of the criterion
within that WU's `## Acceptance criteria` section. Ordinal, not a hash of the text:
a criterion whose wording is edited between attempts is the same criterion, and a
hash would silently orphan its state.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`, and the
verification skill. Do not restate them.

**Acceptance criteria.**

1. `tests/test_criteria_state.py::test_parse_round_trips_render` exists and **fails
   on HEAD before this WU's edits** (the module does not exist yet, so the import
   raises `ModuleNotFoundError`). Record the failing output before editing.
2. `specfuse/loop/criteria_state.py` defines `ORACLE_KINDS` as a `frozenset`
   containing exactly `narrow` and `broad`, and `CRITERION_STATES` as a `frozenset`
   containing exactly `pass`, `fail`, and `unverified`.
3. The module defines a per-entry record type carrying the fields `criterion_id`,
   `criterion`, `oracle`, `kind`, `state`, `proved_at_sha`, and `attempt`.
4. `parse_criteria_state(text)` returns a list of entry records, one per `### `
   block, in document order; a block missing a field yields that field as `None`
   rather than raising.
5. `render_criteria_state(entries)` returns markdown that `parse_criteria_state`
   parses back into an equal list of entries — asserted by the test in criterion 1
   over a fixture containing at least one `narrow` entry, one `broad` entry, and one
   entry with a missing `kind:`.
6. `criterion_id_for(wu_sub_id, ordinal)` returns `f"{wu_sub_id}#{ordinal}"`, and a
   test asserts `criterion_id_for("T03", 2) == "T03#2"`.
7. The module imports cleanly with no side effects:
   `python3 -c "from specfuse.loop.criteria_state import ORACLE_KINDS, CRITERION_STATES, parse_criteria_state, render_criteria_state, criterion_id_for"`
   exits 0.
8. The test named in criterion 1 **passes** after this WU's edits.
9. No file outside `specfuse/loop/criteria_state.py` and `tests/test_criteria_state.py`
   is modified by this work unit.

**Do not touch.** The driver dispatch module under `specfuse/loop/`, plus
`closing_requirements.py`, `lint_closing.py`, and `lint_plan.py` — T02, T03, and gate
2 own those edits, and a change here would collide. This unit adds no driver wiring
and declares no `produces_driver_helper`; if you find yourself needing one, that is
T02's scope. Any `.specfuse/rules/` or `.specfuse/templates/` file
(T04's scope). Any other feature's folder under `.specfuse/features/`. Generated
directories, secrets, `.git/`. The driver owns all git operations — edit files only.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`
(`ruff check specfuse .specfuse/scripts tests scripts`), `security`
(`bandit -r specfuse .specfuse/scripts -ll`), `coverage`
(`coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90`),
`leak-scan`, and `event-type-gate`. In addition, run the symbol-existence check in
acceptance criterion 7 verbatim — the test suite passes whether or not a symbol is
importable under its intended name, and this check fills that gap. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
round-trip property in criterion 5 cannot be satisfied without changing the entry
shape documented above (that is a design question for the operator, not a
free choice — say which field breaks it and why); the existing
`closing_requirements.py` record shape turns out to conflict with this schema in a
way that would require editing that module (out of scope here — T03 owns it);
`ORACLE_KINDS` or `CRITERION_STATES` is absent from the module you edited, or the
import in criterion 7 fails — do not claim complete; or coverage drops below 90% and
raising it would require touching a module outside this WU's two files.
