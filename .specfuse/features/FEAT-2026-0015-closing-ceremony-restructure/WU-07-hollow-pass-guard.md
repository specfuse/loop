---
id: FEAT-2026-0015/T07
type: implementation
model: claude-sonnet-4-6
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
---

# Type-keyed hollow-pass guard for the new closing taxonomy

**Objective.** Extend FEAT-2026-0008's hollow-pass guards
(zero-token, files_changed, smoke-import) with a type-keyed
assertion table covering the new closing-WU taxonomy. The driver
fires the table between successful verify+squash and the
status-flip-to-done; a missing assertion rolls back via
`git reset --hard head_before` and records
`closing_deliverable_missing` as an `attempt_outcome` event.

**Context.** This is `FEAT-2026-0015/T07`. Depends on T04
(VERDICT_VALUES) and T05 (`oracle_env` field). T06's
`fire_terminal_flips` runs AFTER T07's guard succeeds.

Per PLAN.md roadmap detail § "Subsumed scope (from
FEAT-2026-0012)" and LEARNINGS `[FEAT-2026-0008/G1-CLOSE]`
(recursive close audit pattern). FEAT-2026-0008's three guards
covered `implementation`; the new closing taxonomy
(`close`, `close-intermediate`, `plan-next`) has its own hollow-
pass surface that's currently open.

Type-keyed assertion table:

| WU type | Required deliverables (assertions) |
|---------|-----------------------------------|
| `close` | (a) `RETROSPECTIVE.md` in feature dir exists + non-empty; (b) `.specfuse/LEARNINGS.md` has ≥1 line added in this WU's squash OR an explicit "nothing generalizes" note in `RETROSPECTIVE.md`; (c) some doc/roadmap file in `git diff` of this WU's squash (`.specfuse/roadmap.md` or a `docs/` file); (d) `verdict` frontmatter field present and in `VERDICT_VALUES`; (e) if `verdict == "met"`, `## Cost analysis` section header present in `RETROSPECTIVE.md`. |
| `close-intermediate` | (a) `RETROSPECTIVE.md` section for THIS gate exists (heading matches `## Gate N` or `### Gate N`); (b) `.specfuse/LEARNINGS.md` appended OR explicit-no-op acknowledged in RETRO; (c) doc surface diff if the WU spec declared one (otherwise skipped). |
| `plan-next` | (a) `GATE-(N+1)-REVIEW.md` exists + non-empty in feature dir; (b) next gate's `work_units` list in PLAN.md has at least one entry (drafted) OR PLAN.md `status: done` (terminal post-plan) OR roadmap row `status: done`. |
| `implementation` | UNCHANGED — FEAT-2026-0008's three guards (zero-token + files_changed + smoke-import) already cover. T07 does NOT modify the implementation guards. |

Driver-side wiring:

- New helper `assert_closing_deliverables(wu: WorkUnit,
  feature_dir: Path, repo_root: Path, head_before: str)
  -> tuple[bool, str]` returns `(True, "")` on success or
  `(False, summary)` naming the failing assertion.
- Called in `loop.py::run()` post-verify flow, AFTER the smoke-
  import block (around L1336–L1353) but BEFORE
  `fire_terminal_flips` (T06's helper). Order: verify → squash
  → smoke-import → THIS GUARD → terminal-flips → task_completed.
- On failure: roll back via `reset_preserving_events(head_
  before, events_path)` (same as smoke-failure path), emit
  `attempt_outcome` event with `outcome:
  "closing_deliverable_missing"`, count as a verification
  failure in the attempt loop (3-in-a-row → `blocked_human`).

Reference binding rules under `.specfuse/rules/`. Driver owns git.

**Acceptance criteria.**

1. `loop.py` defines a module-level constant
   `CLOSING_ASSERTIONS_BY_TYPE` — a `dict[str, list[Callable]]`
   keyed on WU type (`close`, `close-intermediate`, `plan-next`)
   mapping to a list of single-purpose assertion callables. Each
   callable has signature
   `(wu: WorkUnit, feature_dir: Path, repo_root: Path,
   head_before: str) -> tuple[bool, str]` — returns
   `(True, "")` on hold, `(False, named_reason)` on missing.
   Each assertion is a separate top-level function so it's
   independently testable.
2. The assertions listed in this WU's Context table are
   implemented. Per-assertion function names:
   `assert_retrospective_exists`,
   `assert_learnings_appended_or_noop`,
   `assert_doc_or_roadmap_diff`,
   `assert_verdict_well_formed`,
   `assert_cost_analysis_section_when_met`,
   `assert_retrospective_gate_section`,
   `assert_gate_review_exists`,
   `assert_next_gate_drafted_or_terminal`.
   Naming is binding — tests grep for these names; T07 reviewer
   sees a one-to-one map between table rows and code.
3. `loop.py` defines
   `def assert_closing_deliverables(wu, feature_dir, repo_root,
   head_before) -> tuple[bool, str]` that:
   - Looks up `CLOSING_ASSERTIONS_BY_TYPE.get(wu.type, [])`.
   - Returns `(True, "")` if the lookup is empty (the
     implementation case — guards run elsewhere).
   - Iterates each assertion; on the FIRST failure returns
     `(False, summary)` where summary names the failing
     assertion's function name and its reason. Subsequent
     assertions are not run.
4. `loop.py::run()` integrates the guard:
   - Call site: after the smoke-import block, before
     `fire_terminal_flips` (T06's helper).
   - On `(False, summary)`:
     - `reset_preserving_events(head_before, events_path)`
     - Append `attempt_outcome` event with `outcome:
       "closing_deliverable_missing"`, `assertion: <name>`,
       `summary: <text>`.
     - `attempt_notes.append((attempt, summary))`
     - `failure_note = summary`
     - `print(f"   CLOSING DELIVERABLE MISSING attempt
       {attempt}/{MAX_ATTEMPTS} — {summary}")`
     - `continue` (next attempt iteration).
5. Unit tests in `tests/test_closing_deliverable_guard.py`
   covering each assertion (eight separate test classes or
   methods, one per assertion function) plus four integration
   tests:
   - `test_close_passes_when_all_assertions_hold` — fixture
     with RETROSPECTIVE.md, LEARNINGS appended, roadmap diff,
     verdict: met, Cost analysis section. Assert
     `assert_closing_deliverables` returns `(True, "")`.
   - `test_close_fails_when_retrospective_missing` — assert
     summary names `assert_retrospective_exists`.
   - `test_close_intermediate_passes_when_gate_section_added`
     — assert intermediate close passes.
   - `test_plan_next_fails_when_gate_review_missing` — assert
     summary names `assert_gate_review_exists`.
6. Integration test
   `test_run_rolls_back_on_closing_deliverable_missing`:
   stub a `close` WU whose body would "pass" verify and smoke
   but produces no RETROSPECTIVE.md. Drive
   `execute_unit_attempt` + post-verify flow; assert
   `git reset` fired, attempt counted, event written.
7. Symbol-existence:
   `python3 -c "from loop import CLOSING_ASSERTIONS_BY_TYPE, assert_closing_deliverables, assert_retrospective_exists, assert_learnings_appended_or_noop, assert_doc_or_roadmap_diff, assert_verdict_well_formed, assert_cost_analysis_section_when_met, assert_retrospective_gate_section, assert_gate_review_exists, assert_next_gate_drafted_or_terminal"`
   exits 0.
8. Existing test suite stays green:
   `python3 -m unittest discover tests` exits 0. In
   particular, the FEAT-2026-0008 implementation-guard tests
   (`test_loop_zero_token_guard.py`,
   `test_loop_files_changed_guard.py`,
   `test_loop_smoke_runner.py`) must continue to pass
   unmodified — T07's guard runs in addition to, not in place
   of, the implementation guards.

**Do not touch.** Exactly 2 files change:
- `.specfuse/scripts/loop.py` (assertions + table + helper +
  run() integration).
- `tests/test_closing_deliverable_guard.py` (new file).

No edits to: `lint_plan.py` (no lint surface here),
templates (T03 owned), `/draft-feature` skill, the FEAT-
2026-0008 guard files, other features' WU files, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Plus AC7 symbol-existence. Plus `python3
.specfuse/scripts/lint_plan.py
.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure`
exits 0.

**Escalation triggers.**

1. **Completeness.** If any of the ten symbols listed in AC7
   are absent from `loop.py` after your edits, emit
   `status: blocked` — do not claim complete.
2. **§10 helper-duplication pre-flight.** Before adding
   `assert_closing_deliverables` and friends, run
   `grep -rn "def assert_\|CLOSING_ASSERTIONS" .specfuse/scripts/ tests/`
   and confirm no pre-existing definitions. Per
   `[FEAT-2026-0008/G1-CLOSE]` the existing guards (zero_token,
   files_changed, smoke_imports) sit in `loop.py`; ensure your
   new code is additive and does not shadow them.
3. **Guard ordering.** If the call site for
   `assert_closing_deliverables` ends up BEFORE the
   smoke-import block, BEFORE `squash_commit`, or AFTER
   `fire_terminal_flips`, emit `status: blocked` with the
   wrong-ordering named. The order is: verify → squash →
   smoke → CLOSING GUARD → terminal-flips → task_completed.
4. **Self-audit recursive coupling.** This guard MUST fire on
   G2-CLOSE's own deliverables (per
   `[FEAT-2026-0008/G1-CLOSE]` recursive-audit pattern). If
   the implementation has a code path that exempts the
   currently-executing WU from its own guard (e.g. "skip
   check if WU is the close ceremony itself"), emit
   `status: blocked` — the recursive load-bearing test
   requires NO exemption.
5. **VERDICT_VALUES import drift.** Per
   `[FEAT-2026-0015/G1]` §10 coupling rule and
   `[FEAT-2026-0005/G1-LESSONS]`: `assert_verdict_well_formed`
   MUST import `VERDICT_VALUES` from the single definition
   site in `loop.py` (T04). Do not re-define the set; if you
   feel tempted to inline it for "test isolation", emit
   `status: blocked` — the duplicate would diverge silently
   when T04's lexicon is extended.
