---
id: FEAT-2026-0056/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
model: sonnet
effort: medium
produces_driver_helper:
  - specfuse.loop.loop._clean_attempt_untracked
  - specfuse.loop.criteria_state.criteria_filename
produces:
  - tests/test_loop_criteria_survival.py
generated_surfaces: []
---

# Keep the criteria artifact alive across a failed close attempt

**Objective.** Give `GATE-NN-CRITERIA.md` an explicit carve-out in the driver's
per-attempt untracked-file cleanup, so recorded per-criterion state survives a failed
close attempt instead of being unlinked and re-seeded blank.

**Context.** This is `FEAT-2026-0056/T05`, the first work unit of gate 2. Read
`PLAN.md`, `GATE-02.md`, and `RETROSPECTIVE.md` § *The re-arm property, observed
rather than asserted* in this folder before editing.

Gate 1 shipped the artifact and a test that it survives `fold_cumulative_on_rearm`.
Gate 1's close then observed that the property is true and is not the one that
protects the artifact — the fold rewrites work-unit *frontmatter*, and the artifact
is a separate file, so no fold could ever have touched it. The path that actually
destroys it is the per-attempt reset:

- `untracked_before = untracked_paths()` is snapshotted **once per work unit**, in
  `run()`, before the attempt loop (`specfuse/loop/loop.py:5890`).
- `precreate_dispatch_skeleton` — and with it `_precreate_criteria_state_stub` —
  runs **inside each attempt**, in `execute_unit_attempt`
  (`specfuse/loop/loop.py:3357`).
- So on attempt 1 the artifact is created *after* the snapshot, and a failing
  attempt's `reset_preserving_events(head_before, events_path, untracked_before)`
  hands it to `_clean_attempt_untracked` (`specfuse/loop/loop.py:2028`) as a file
  that appeared since the snapshot. It is unlinked.

Gate 1's close executed that function's real decision rule against a real
filesystem and recorded:

```
criteria artifact still present after attempt reset: False
events.jsonl still present after attempt reset:      True
```

`events.jsonl` survives only because `_clean_attempt_untracked` carries an explicit
hand-written carve-out for it. The criteria artifact has none, and it is untracked
for its whole useful life — until the close's own *passing* attempt commits it. So
through every failed attempt of a close, which is the entire scenario this feature
exists to make cheaper, the recorded state is wiped.

`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]` in
`.specfuse/LEARNINGS.md` is this finding promoted to a rule; its rule (b) — be
suspicious of a survival test that passes with no scaffolding — is why criterion 1
below is mandatory and not a formality.

**Shape of the fix.** Key the carve-out on the artifact's **filename**, not on
widening the `untracked_before` snapshot. Moving the snapshot inside the attempt
loop would also protect every file the *agent* left behind on a failed attempt,
which is the pollution `_clean_attempt_untracked` exists to remove — a far wider
blast radius than this feature needs. `events.jsonl` sets the precedent: a
driver-managed file gets a named exception, and nothing else does.

The filename is currently an f-string literal in three places —
`specfuse/loop/loop.py:2438`, `specfuse/loop/lint_closing.py:334`, and
`specfuse/loop/lint_closing.py:479`. A carve-out keyed on a fourth copy is a
divergence waiting to happen (`/authoring-work-units` §10), so this unit gives the
name one home in `specfuse/loop/criteria_state.py` first and routes all four
readers through it.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_loop_criteria_survival.py::test_criteria_artifact_survives_attempt_reset`
   exists and **fails on HEAD before this WU's edits**. Record the failing output in
   the RESULT block before editing production code.
2. `specfuse/loop/criteria_state.py` exports `criteria_filename(gate_n: int) -> str`
   returning `GATE-01-CRITERIA.md` for `1` and `GATE-12-CRITERIA.md` for `12`, and
   `CRITERIA_FILENAME_RE`, a compiled pattern matching those basenames and not
   matching `GATE-01.md`, `GATE-01-REVIEW.md`, or `RETROSPECTIVE.md`.
3. `grep -nE 'GATE-\{[a-z_]+[^}]*\}-CRITERIA\.md' specfuse/` returns matches only
   inside `specfuse/loop/criteria_state.py` — the three call sites named in the
   Context now call `criteria_filename`.
4. `_clean_attempt_untracked` does not unlink a file whose basename matches
   `CRITERIA_FILENAME_RE`. Asserted by a test that drives the **real**
   `_clean_attempt_untracked` (not a re-implementation of its decision rule) against
   a real temporary git working tree with an `untracked_before` snapshot taken
   before the artifact is created.
5. In that same tree and the same call, an unrelated untracked file created after
   the snapshot in the same feature folder **is** still unlinked. This bounds the
   blast radius: a carve-out that also preserves agent leftovers is too wide and
   fails this criterion.
6. `_clean_attempt_untracked` still never unlinks `events_path` — the existing
   carve-out is intact, asserted in the same test module.
7. The `untracked_before = untracked_paths()` assignment in `run()` remains **outside**
   the attempt `for` loop: `grep -n 'untracked_before = untracked_paths()' specfuse/loop/loop.py`
   returns exactly one line, and its indentation is unchanged from HEAD.
8. `python3 -c "from specfuse.loop.criteria_state import criteria_filename, CRITERIA_FILENAME_RE"`
   exits 0.
9. The test named in criterion 1 **passes** after this WU's edits.
10. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `precreate_dispatch_skeleton` and `_precreate_criteria_state_stub`
in `specfuse/loop/loop.py` — T02 shipped their additive seeding semantics and this
unit only reads the filename from them; changing what they write is out of scope.
`check_criteria_state_well_formed` in `specfuse/loop/lint_closing.py` (T06's scope —
this unit may change only that file's two filename literals, nothing else).
`parse_criteria_state` / `render_criteria_state` / `criterion_id_for` signatures in
`specfuse/loop/criteria_state.py` (T01's; extend the module, do not alter them).
`build_reverification_worklist` (T07's scope — it does not exist yet; do not
pre-build it). `.specfuse/verification.yml`. `.specfuse/rules/` and
`.specfuse/templates/`. `GATE-01.md` and gate 1's work units. Any other feature's
folder under `.specfuse/features/`. Generated directories, secrets, `.git/`. The
driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run criterion 8's
symbol-existence check verbatim and criterion 3's grep verbatim, and paste both
outputs. Criterion 1's red observation must be recorded **before** production edits;
a green-only report cannot distinguish a real fix from a test that could never fail.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
carve-out cannot be expressed without adding a parameter to `reset_preserving_events`
and editing all of its ~15 call sites in `run()` — that is a driver-wide signature
change and an operator decision, not this unit's; making the artifact survive would
require a failing attempt to commit it, which changes the driver's commit semantics
and is out of scope; criterion 5's negative observation cannot be made to hold,
meaning the carve-out preserves agent leftovers too; or criterion 1's test passes on
HEAD before any edit, which means it is a tautology and the destroying path is still
untested — re-read `RETROSPECTIVE.md` § *The re-arm property* and report what the
test is actually asserting rather than reporting `complete`.
