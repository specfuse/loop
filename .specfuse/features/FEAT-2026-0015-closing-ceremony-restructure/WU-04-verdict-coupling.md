---
id: FEAT-2026-0015/T04
type: implementation
model: claude-sonnet-4-6
effort: medium
status: draft
attempts: 0
planned_cost_usd: 1.20
---

# Couple verdict frontmatter to driver-side terminal flips

**Objective.** Add a required `verdict:` frontmatter field on
`close` and `close-intermediate` WUs, and gate the driver's
terminal flips (PLAN.md → `done`, gate → `passed`, roadmap row →
`done`, `auto_archive_feature`) on `verdict: met`. Lint validates
the verdict lexicon.

**Context.** This is `FEAT-2026-0015/T04`. Per PLAN.md roadmap
detail § "Verdict-state ↔ PLAN.md coupling" and the
[FEAT-2026-0013/G1-CLOSE/oracle-environment] LEARNINGS rule:
hedged verdicts must not flip PLAN.md to `done`. Today the close
ceremony unconditionally writes `status: done`; FEAT-2026-0013
v1 emitted "Met locally; field-pending" AND flipped PLAN.md, then
CI failed and the operator reverse-flipped four surfaces to re-arm.

Allowed verdict values (lexicon — these strings are load-bearing,
referenced by T07's hollow-pass guard and G2-CLOSE):

- `met` — goal fully achieved, oracle confirmed in target env.
- `met_locally` — goal achieved on developer environment, target-env
  oracle pending operator action.
- `partially_met` — some ACs achieved, others deferred or descoped.
- `not_met` — goal not achieved; close emits `status: blocked`.

Driver state machine after this WU:

- `verdict: met` → close MAY flip PLAN.md `done`, gate `passed`,
  roadmap row `done`, fire `auto_archive_feature`.
- `verdict: met_locally | partially_met` → close DOES NOT flip
  PLAN.md status. PLAN.md stays `active`. Terminal gate stays
  `awaiting_review`. RETROSPECTIVE records the hedge and the
  operator-side oracle.
- `verdict: not_met` → close emits `status: blocked` per
  result-contract; no flips.

State-flip mechanics themselves are T06's scope (move from
`/wrap-feature` into driver). T04 ships only the gating predicate
and the frontmatter contract; T06 consumes the predicate.

Reference binding rules under `.specfuse/rules/`. Driver owns git.

**Acceptance criteria.**

1. `loop.py` defines a module-level constant
   `VERDICT_VALUES = frozenset({"met", "met_locally", "partially_met", "not_met"})`
   at top-of-module, near `MODEL_BY_TYPE`.
2. `loop.py` defines a pure helper
   `def verdict_permits_terminal_flips(verdict: str | None) -> bool`
   returning `True` iff `verdict == "met"`; `False` for every
   other value including `None`. Pure function, no side effects.
3. `WorkUnit.load_wu` (or its frontmatter reader — whichever
   reads WU frontmatter today) parses `verdict` for WUs whose
   `type` is `close` or `close-intermediate`. The parsed value
   is exposed on the `WorkUnit` dataclass as attribute
   `verdict: str | None`. For other WU types `verdict` is
   `None`.
4. `lint_plan.py` validates `verdict`:
   - WUs of type `close` or `close-intermediate` MUST have
     `verdict` in `VERDICT_VALUES` — missing or out-of-set
     value emits a hard ERROR with text
     `ERROR: <wu_file>: close-type WU missing or invalid 'verdict' frontmatter (must be one of: met, met_locally, partially_met, not_met).`
     `lint_plan.py` exits non-zero.
   - WUs of any other type that DECLARE a `verdict` field emit
     a hard ERROR (verdict only meaningful for closing types).
   - DRAFT-status closing WUs are exempt — verdict is written
     at execution time, not draft time. Skip the check when
     `status: draft`.
5. New unit tests in `tests/test_verdict_coupling.py`:
   - `test_verdict_permits_terminal_flips_only_for_met` — all
     four enum values plus `None`, `""`, and a junk string.
   - `test_load_wu_parses_verdict_for_close_type` — temp WU
     file with `type: close`, `verdict: met_locally`, assert
     `wu.verdict == "met_locally"`.
   - `test_load_wu_verdict_is_none_for_implementation_type` —
     temp WU file with `type: implementation`, assert
     `wu.verdict is None` regardless of any frontmatter.
   - `test_lint_close_missing_verdict_errors` — temp feature
     with a `close` WU (`status: ready`) missing `verdict`;
     assert `lint_plan.py` exits non-zero with the named text.
   - `test_lint_close_invalid_verdict_errors` — `verdict:
     beautifully_done`; same expected error.
   - `test_lint_close_draft_status_skips_verdict_check` — same
     `close` WU but `status: draft`; assert lint passes (this
     is the state plan-next writes).
   - `test_lint_verdict_on_non_close_type_errors` — temp
     `implementation` WU with `verdict: met`; assert
     non-zero exit naming "only meaningful for closing types".
6. Symbol-existence checks (authoring-work-units §9):
   - `python3 -c "from loop import VERDICT_VALUES, verdict_permits_terminal_flips; assert verdict_permits_terminal_flips('met'); assert not verdict_permits_terminal_flips('met_locally'); assert not verdict_permits_terminal_flips(None)"` exits 0.
   - `python3 -c "from lint_plan import VERDICT_VALUES"` exits 0
     (lint_plan imports the constant — single source of truth).
7. Existing test suite stays green:
   `python3 -m unittest discover tests` exits 0.

**Do not touch.** Exactly 3 files change:
- `.specfuse/scripts/loop.py` (add constant + helper + parse
  `verdict` in `load_wu`).
- `.specfuse/scripts/lint_plan.py` (import `VERDICT_VALUES`
  from `loop`; add closing-type verdict check).
- `tests/test_verdict_coupling.py` (new file).

T06 (state-flip consolidation) will wire `verdict_permits_
terminal_flips` into the post-verify flow; T04 does NOT add the
call site. Defining a callable but not calling it from
production is intentional separation — T06 owns the wiring.

No edits to: `loop.py::run()` post-verify flow (T06 owns),
templates (T03 owned, frozen), `/wrap-feature` skill (T06 owns),
other features' WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage). Plus AC6 symbol-existence
checks. Plus `python3 .specfuse/scripts/lint_plan.py
.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure`
exits 0 (this feature's drafts must still pass).

**Escalation triggers.**

1. **Completeness.** If `VERDICT_VALUES` or
   `verdict_permits_terminal_flips` is absent from the files
   you edited, emit `status: blocked` — do not claim complete.
2. **Cross-surface drift.** Per `[FEAT-2026-0005/G1-LESSONS]`
   and `[FEAT-2026-0015/G1]`: before declaring complete, run
   `grep -n "VERDICT_VALUES\|verdict_permits_terminal_flips" .specfuse/scripts/ tests/`
   and confirm exactly one definition site each in `loop.py`,
   exactly one import site in `lint_plan.py`. If either is
   defined twice, name the duplicate and emit `status: blocked`.
3. **§10 helper-duplication pre-flight.** Before editing
   `load_wu`, run
   `grep -rn "def load_wu\|load_wu(" .specfuse/scripts/ tests/`
   and confirm exactly one production definition. If tests
   define their own `load_wu` shim, name them — they need the
   `verdict` parsing too or the test surface diverges from prod.
4. **T07 coupling concern.** T07 (next WU) will read
   `VERDICT_VALUES` to decide whether a close-WU's verdict
   field is well-formed before the hollow-pass guard fires. If
   you find yourself tempted to add verdict-related guard
   logic into `loop.py::run()`, STOP — that belongs to T06+T07,
   not T04. Emit `status: blocked` if the WU as specified
   cannot be implemented without touching `run()`.
