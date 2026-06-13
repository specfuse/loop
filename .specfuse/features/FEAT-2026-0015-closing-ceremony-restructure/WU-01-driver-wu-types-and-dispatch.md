---
id: FEAT-2026-0015/T01
type: implementation
model: claude-sonnet-4-6
effort: medium
status: done
attempts: 1
planned_cost_usd: 1.00
duration_seconds: 159.391
cost_usd: 0.418768
input_tokens: 19
output_tokens: 4958
---

# Add `close-intermediate` WU type and extend `close` to any terminal gate

**Objective.** Wire the driver to know about two new closing-ceremony
shapes: the per-WU constants land in `loop.py`. The lint changes
(WU T02) and template/skill updates (T03) build on this foundation.

**Context.** This is `FEAT-2026-0015/T01`. Today's closing taxonomy
(`loop.py` lines 78-105):

- `MODEL_BY_TYPE` / `EFFORT_BY_TYPE` / `GATES_FOR_TYPE` cover:
  `implementation`, `retrospective`, `lessons`, `docs`, `plan-next`,
  `close`.
- `GATES_FOR_TYPE["close"]` routes to `"plannext"` (lint_plan.py on
  the feature folder).
- Comment on the `close` mapping currently reads: "`close` collapses
  the four closing ceremonies into one session (single-gate only)".

The restructure introduces `close-intermediate` as a new type AND
extends `close` to any-terminal-gate (not single-gate-only).
Mapping intent:

- `close-intermediate`: folds RETRO+LESSONS+DOCS for non-terminal
  gates (plan-next stays separate, dispatched after).
  Model: `opus` (high-stakes synthesis). Effort: `high`.
  Routes to `"plannext"` gate set (lint_plan.py — structural).
- `close` (extended): folds RETRO+LESSONS+DOCS+verdict for ANY
  terminal gate. Model unchanged: `opus`. Effort unchanged: `high`.
  Routes unchanged: `"plannext"`.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. `loop.py::MODEL_BY_TYPE` includes key `"close-intermediate"` with
   value `"opus"`. Existing entries unchanged.
2. `loop.py::EFFORT_BY_TYPE` includes key `"close-intermediate"` with
   value `"high"`. Existing entries unchanged.
3. `loop.py::GATES_FOR_TYPE` includes key `"close-intermediate"` with
   value `"plannext"`. Existing entries unchanged.
4. The comment on the `close` mapping (currently lines ~102-104) is
   updated to say: "`close` collapses the four closing ceremonies
   into one session for any terminal gate (single- or multi-gate);
   `close-intermediate` is the equivalent for non-terminal gates,
   leaving `plan-next` as a separate dispatch." Old comment about
   "single-gate only" removed.
5. Symbol-existence check (per authoring-work-units §9):
   `python3 -c "from loop import MODEL_BY_TYPE, EFFORT_BY_TYPE, GATES_FOR_TYPE; assert MODEL_BY_TYPE['close-intermediate'] == 'opus'; assert EFFORT_BY_TYPE['close-intermediate'] == 'high'; assert GATES_FOR_TYPE['close-intermediate'] == 'plannext'"` exits 0.
6. New unit tests in `tests/test_loop_close_intermediate.py`:
   - `test_close_intermediate_in_model_by_type`
   - `test_close_intermediate_in_effort_by_type`
   - `test_close_intermediate_in_gates_for_type`
   - `test_load_wu_accepts_close_intermediate_type` (calls `load_wu`
     against a temp WU file with `type: close-intermediate`; asserts
     `wu.type == "close-intermediate"`, `wu.model == "claude-opus-4-7"`
     or family alias `"opus"`, `wu.effort == "high"`).
7. Existing test suite stays green: `python3 -m unittest discover
   tests` exits 0. No existing test asserts a count/list that
   excludes the new type — verify by running the suite.

**Do not touch.** Exactly 2 files change:
- `.specfuse/scripts/loop.py` (additions only — no signature changes,
  no behavior changes for existing types).
- `tests/test_loop_close_intermediate.py` (new file).

No edits to: `lint_plan.py` (T02 owns), templates (T03 owns),
`/draft-feature` skill (T03 owns), other test files, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) must pass. Plus AC5's symbol-
existence check.

**Escalation triggers.**

1. **Completeness.** If `MODEL_BY_TYPE`, `EFFORT_BY_TYPE`, or
   `GATES_FOR_TYPE` does not show the new `close-intermediate` key
   after your edits, emit `status: blocked`.
2. **Behavior drift.** If your edit changes any existing entry's
   value (not just adding `close-intermediate`), emit
   `status: blocked` — this WU adds, never modifies.
3. **Pre-existing helper-duplication trigger.** Per authoring-work-
   units §10: before editing `loop.py`, run
   `grep -n "MODEL_BY_TYPE\|EFFORT_BY_TYPE\|GATES_FOR_TYPE" .specfuse/scripts/loop.py`
   and confirm exactly one definition site per dict. If there are
   duplicates anywhere in the codebase (test fixtures inlining the
   dicts, etc.), name them and emit `status: blocked` rather than
   editing only one site.
