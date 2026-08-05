---
id: FEAT-2026-0056/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper:
  - specfuse.loop.loop._precreate_criteria_state_stub
  - specfuse.loop.loop.extract_wu_criteria
produces:
  - tests/test_loop_criteria_skeleton.py
generated_surfaces: []
---

# Pre-create the criteria-state artifact on every close dispatch

**Objective.** Make `precreate_dispatch_skeleton` scaffold `GATE-NN-CRITERIA.md` for
`close` and `close-intermediate` dispatches, seeded from the gate's substantive work
units' acceptance criteria — and prove the artifact survives a re-arm.

**Context.** This is `FEAT-2026-0056/T02`, gate 1 of this feature. T01 built
`specfuse/loop/criteria_state.py` (the entry schema, `parse_criteria_state`,
`render_criteria_state`, `criterion_id_for`); this unit wires it into the driver's
dispatch path. Read `PLAN.md` in this folder and `GATE-01.md`.

Two existing surfaces matter and both are already in the tree:

- **`precreate_dispatch_skeleton`** (`specfuse/loop/loop.py:2389`) is the hook. Its
  docstring states the principle this unit extends: "guards can only pass, not
  construct format from prose." It dispatches on `wu.type`, calling
  `_precreate_gate_review_stub` for `plan-next` and `_precreate_retrospective_stub`
  for the two close types. Add the criteria-state stub alongside the retrospective
  stub for `close` and `close-intermediate`. It must remain a no-op for `plan-next`
  and every other type.
- **`build_autoclose_debt_enumeration`** (`specfuse/loop/loop.py:3920`) already
  extracts per-criterion acceptance bullets from every substantive WU in a gate: it
  walks the gate's refs from `load_graph`, skips `NON_SUBSTANTIVE_TYPES`, slices the
  body with `_wu_sections.slice_acceptance_criteria`, and matches items with
  `_DEBT_AC_ITEM_RE`. **Hoist that extraction into a shared helper —
  `extract_wu_criteria` — and call it from both sites.** Do not write a second
  parser. Two parsers for "what are this gate's acceptance criteria" will drift, and
  the drift will be invisible until a close reads a criterion list the debt
  enumeration disagrees with.

The seeded artifact records what is *known at dispatch time*, which is the criterion
identity and its text — nothing more. Every seeded entry is `state: unverified` with
`oracle`, `kind`, `proved_at_sha`, and `attempt` absent. The close's session fills
them in as it runs oracles; T03's lint checks the filled-in result. Do not guess a
`kind` at seed time: `close-discipline.md` §2 establishes that the classification is
written by the session that ran the thing and never inferred by a reader, and the
same reasoning applies to oracle kind.

**The re-arm survival property is the load-bearing half of this unit.**
`fold_cumulative_on_rearm` (`specfuse/loop/loop.py:1828`) folds the prior cycle's
cost, duration, and token spend into the `cumulative_*` accumulators and zeroes the
per-cycle fields. `[FEAT-2026-0053/G2-CLOSE]` is the lesson: an aggregate that reads
a per-cycle field silently under-counts every re-armed unit, and the error
concentrates in exactly the work the aggregate exists to catch. Per-criterion state
whose entire purpose is to outlive a re-dispatch must not be zeroed by that fold —
hence a standalone per-gate artifact rather than close-WU frontmatter, and hence an
explicit test rather than an assumption.

Re-seeding on a re-dispatch must be **additive**: a criterion already present in the
artifact keeps its recorded entry, a criterion that has appeared since the last
attempt is appended as `unverified`, and a criterion no longer in any WU is left in
place rather than deleted (the close is the party that can say whether its
disappearance was intended). Silent deletion would destroy the record a reviewer
needs.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_loop_criteria_skeleton.py::test_close_dispatch_precreates_criteria_artifact`
   exists and **fails on HEAD before this WU's edits**. Record the failing output
   before editing.
2. `extract_wu_criteria(feature_dir, gate_number)` exists in `specfuse/loop/loop.py`
   and returns, for each substantive WU in the gate, its sub-ID paired with its
   ordered acceptance-criterion strings — skipping `NON_SUBSTANTIVE_TYPES` exactly
   as `build_autoclose_debt_enumeration` does today.
3. `build_autoclose_debt_enumeration` calls `extract_wu_criteria` instead of
   re-implementing the slice-and-match, and every existing test of that function
   still passes unchanged — `python3 -m unittest discover -s tests -v -b -k debt`
   exits 0.
4. `precreate_dispatch_skeleton` writes `GATE-NN-CRITERIA.md` into the feature
   directory for a WU of type `close` and for a WU of type `close-intermediate`,
   with `NN` zero-padded to two digits matching the gate number.
5. `precreate_dispatch_skeleton` writes no criteria artifact for a WU of type
   `plan-next`, `implementation`, `retrospective`, `lessons`, or `docs` — asserted
   per type by a test.
6. Every seeded entry carries `state: unverified` and omits `oracle`, `kind`,
   `proved_at_sha`, and `attempt`; the file is produced through
   `criteria_state.render_criteria_state`, not by string-formatting in `loop.py`.
7. Re-seeding is additive: a test writes an artifact with one entry whose `state` is
   `pass`, re-runs `precreate_dispatch_skeleton` after adding a criterion to a WU,
   and asserts the `pass` entry is unchanged and the new criterion is appended as
   `unverified`.
8. `tests/test_loop_criteria_skeleton.py::test_criteria_artifact_survives_rearm_fold`
   re-arms a close WU, calls `fold_cumulative_on_rearm`, and asserts every entry in
   `GATE-NN-CRITERIA.md` parses back identical to what was written before the fold.
9. `python3 -c "from specfuse.loop.loop import extract_wu_criteria, _precreate_criteria_state_stub"`
   exits 0.
10. The tests named in criteria 1 and 8 **pass** after this WU's edits.

**Do not touch.** `specfuse/loop/criteria_state.py` (T01 owns it — import it, do not
edit it). `specfuse/loop/closing_requirements.py` and `specfuse/loop/lint_closing.py`
(T03's scope). `.specfuse/rules/` and `.specfuse/templates/` (T04's scope).
`.specfuse/verification.yml`. Any other feature's folder under
`.specfuse/features/`. Generated directories, secrets, `.git/`. The driver owns all
git operations — edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run the
symbol-existence check in acceptance criterion 9 verbatim, and criterion 3's scoped
regression command, since a hoist that changes the debt enumeration's behaviour is
the specific way this unit can break something already shipped.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
hoisting the extraction cannot preserve `build_autoclose_debt_enumeration`'s current
output byte-for-byte (say which case diverges — a behaviour change there is a
contract change this WU is not scoped to make); `fold_cumulative_on_rearm` turns out
to touch the artifact and preventing it would require changing the fold's semantics
(that is a driver-contract question for the operator); `extract_wu_criteria` or
`_precreate_criteria_state_stub` is absent from the files you edited, or the import
in criterion 9 fails — do not claim complete; or the additive re-seed in criterion 7
cannot be made idempotent without deleting entries.
