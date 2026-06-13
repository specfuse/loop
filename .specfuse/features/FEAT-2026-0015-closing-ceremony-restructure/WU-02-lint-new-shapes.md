---
id: FEAT-2026-0015/T02
type: implementation
model: claude-sonnet-4-6
effort: medium
status: pending
attempts: 0
planned_cost_usd: 1.00
---

# Update `lint_plan.py` to accept new closing-WU shapes

**Objective.** Teach `lint_plan.py` about the new closing-WU
taxonomy: `close-intermediate → plan-next` for non-terminal gates,
`close` for any terminal gate. Grandfather the old 4-WU
(`retrospective → lessons → docs → plan-next`) sequence with a
WARNING (not an error). Reject mixed-shape closings within a single
feature as ERROR.

**Context.** This is `FEAT-2026-0015/T02`. Depends on T01 (the new
`close-intermediate` type must already be in `VALID_TYPES` via
`MODEL_BY_TYPE`/`EFFORT_BY_TYPE`/`GATES_FOR_TYPE`).

`lint_plan.py` currently defines:
- `CLOSING_SEQUENCE = ["retrospective", "lessons", "docs", "plan-next"]`
- `_CLOSING_TYPES = frozenset(CLOSING_SEQUENCE) | {"close"}`
- A check that closes a gate as either the four-WU sequence in
  exact order OR a single `close` WU (single-gate features only).

The new closing-shape lexicon:

| Gate type | Allowed closes |
|-----------|----------------|
| Non-terminal gate (any feature, any size) | 2-WU: `close-intermediate → plan-next` (NEW) OR 4-WU: `retrospective → lessons → docs → plan-next` (LEGACY, warns) |
| Terminal gate (any feature, single- or multi-gate) | 1-WU: `close` (NEW for multi-gate; existed for single-gate) OR 4-WU: `retrospective → lessons → docs → plan-next` (LEGACY, warns) |

Mixed shapes within a single feature (e.g. gate 1 uses new
2-WU, gate 2 uses legacy 4-WU): hard ERROR. Operators pick one
contract per feature.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. `lint_plan.py` defines a new constant
   `NEW_INTERMEDIATE_SEQUENCE = ["close-intermediate", "plan-next"]`
   and updates `_CLOSING_TYPES` to include `"close-intermediate"`.
2. The per-gate closing-shape check accepts the new shapes:
   - On a non-terminal gate: 2-WU `close-intermediate → plan-next`
     (in this exact order) passes silently.
   - On a terminal gate: single `close` WU passes silently for ANY
     feature (single- or multi-gate). The previous restriction to
     single-gate is REMOVED.
3. The legacy 4-WU sequence
   (`retrospective → lessons → docs → plan-next`) still passes lint
   but emits a WARNING on stdout of the form:
   `WARN: <feature_dir>/GATE-NN.md uses legacy 4-WU closing sequence; new contract is 2-WU (close-intermediate + plan-next) for intermediate or 1-WU (close) for terminal. See FEAT-2026-0015.`
4. Mixed shapes within a single feature emit a hard ERROR:
   `ERROR: <feature_dir>: mixed closing-shape contracts across gates (gate N uses NEW, gate M uses LEGACY). Pick one contract per feature.`
   `lint_plan.py` exits non-zero.
5. New unit tests in `tests/test_lint_close_intermediate.py`:
   - `test_new_2wu_intermediate_passes_silently`
   - `test_new_1wu_terminal_passes_for_multigate_feature`
   - `test_legacy_4wu_sequence_emits_warn_but_exits_zero`
   - `test_mixed_shapes_emit_error_and_exits_nonzero`
   - `test_close_intermediate_followed_by_non_plan_next_emits_error`
     (close-intermediate MUST be followed by plan-next on a
     non-terminal gate)
6. Existing tests stay green. Pay special attention to
   `tests/test_lint_close_wu.py` — its assertions about single-gate
   restrictions on `close` must be updated to reflect the new
   any-terminal-gate semantics. If those tests EXIST and assert
   "close requires single-gate", update them; document the change
   in the WU's RESULT block.

**Do not touch.** Exactly 2 files change:
- `.specfuse/scripts/lint_plan.py`
- `tests/test_lint_close_intermediate.py` (new file)

Plus 1 file MAY change (only if its assertions break under the new
semantics):
- `tests/test_lint_close_wu.py` — update single-gate restriction
  assertions to reflect any-terminal-gate semantics.

No edits to: `loop.py` (T01 owns), templates (T03 owns),
`/draft-feature` skill (T03 owns), production WUs / features,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
must pass. Plus the symbol-existence check:
`python3 -c "from lint_plan import NEW_INTERMEDIATE_SEQUENCE; assert NEW_INTERMEDIATE_SEQUENCE == ['close-intermediate', 'plan-next']"`
exits 0.

**Escalation triggers.**

1. **Test breakage outside scope.** If running the full suite shows
   failures in tests NOT named in this WU's scope (e.g.
   `test_loop_orchestration.py`), emit `status: blocked` — root
   cause likely a regression in T01 or an unanticipated coupling.
2. **Helper-duplication.** Per authoring-work-units §10: before
   editing `lint_plan.py`, run
   `grep -rn "CLOSING_SEQUENCE\|_CLOSING_TYPES" .specfuse/`
   to enumerate every site that mentions the closing-shape lexicon.
   If any production code outside `lint_plan.py` and tests carries
   its own copy of the sequence, name it and emit `status: blocked`
   rather than editing only one site.
3. **Completeness.** If `lint_plan.py` does not show
   `NEW_INTERMEDIATE_SEQUENCE` after your edits, emit
   `status: blocked`.
