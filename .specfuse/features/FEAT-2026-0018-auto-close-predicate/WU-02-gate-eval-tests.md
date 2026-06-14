---
id: FEAT-2026-0018/T02
type: implementation
effort: high
status: draft
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
produces_driver_helper: []
---

# Unit tests for `gate_eval.py` — fixture per criterion, ≥ 90% coverage

**Objective.** Land `tests/test_gate_eval.py` with one test class
per predicate criterion plus combined-scenario tests, driving
fixture feature directories under `tests/fixtures/gate_eval/`.
Coverage on `.specfuse/scripts/gate_eval.py` ≥ 90% per-file.

**Context.** This is `FEAT-2026-0018/T02`. Tests for the module
T01 lands. The predicate's v1 constants and algorithm are
specified in `PLAN.md` § "Predicate v1". This WU does NOT modify
the predicate; if a test surfaces a predicate edge case that T01
mishandled, emit `status: blocked` rather than patching
`gate_eval.py` from this WU — predicate changes are out of scope
for the test WU and must be re-armed against T01.

The fixture directories live under `tests/fixtures/gate_eval/`
and are synthetic: minimal PLAN.md + WU frontmatter + events.jsonl
crafted to exercise each criterion in isolation. Real feature
backtest is T03's job (CLI calibration); T02 stays unit-scope.

Reference: `tests/test_closing_deliverable_guard.py` for fixture
layout + tempdir patterns. `tests/_workspace.py` if a tempdir
git repo is needed (it isn't, for these tests — `evaluate_auto_close`
reads files only, no git operations).

**Acceptance criteria.**

1. **Test file created:** `tests/test_gate_eval.py` exists. Uses
   `unittest` (this repo's testing convention) or `pytest` — match
   whichever pattern dominates in `tests/`. Verify with `python3
   -m pytest tests/test_gate_eval.py -v` (exit 0, all tests pass).

2. **Fixture directory:** `tests/fixtures/gate_eval/` exists. Each
   sub-directory is a synthetic feature folder with at minimum
   `PLAN.md` and 0+ WU files. Optional `events.jsonl`. Each
   fixture's PLAN.md MUST lint clean (`python3
   .specfuse/scripts/lint_plan.py tests/fixtures/gate_eval/<name>/`
   exits 0) — fixtures are valid features even if they exist
   only for predicate testing.

3. **Per-criterion test classes** (one class per predicate
   criterion in PLAN.md § "Predicate v1"). Each class has tests
   for the boundary cases:

   - `TestAutoCloseHappyPath` — fixture `happy_1wu_terminal/`:
     1-WU terminal gate, cost matches plan, no events.
     `evaluate_auto_close` returns `auto=True`, `reasons=[]`.
   - `TestBlockedHumanInChain` — fixture `blocked_in_chain/`:
     WU has a `human_escalation` event in events.jsonl.
     `auto=False`, reason starts with `blocked_human_in_chain`.
   - `TestReplanEvent` — fixture `replan_event/`: events.jsonl
     contains a `replan` event for the gate.
     `auto=False`, reason starts with `replan_event`.
   - `TestPerWuCostOverrun15x` — fixture `cost_overrun_15x/`:
     a WU has `cost_usd: 1.60` vs `planned_cost_usd: 1.00`
     (1.6× — over 1.5× ceiling). `auto=False`, reason starts
     with `per_wu_cost_overrun`.
   - `TestPerWuCostHardOverrun2x` — fixture `cost_overrun_2x/`:
     WU has 2.5× overrun. `auto=False`, reason includes
     `per_wu_hard_overrun`.
   - `TestPlanNextOverrun` — fixture `plan_next_overrun/`: a
     `plan-next` type WU has 2× cost. `auto=False`, reason
     starts with `plan_next_overrun`.
   - `TestGateBudgetBust` — fixture `budget_bust/`: gate
     `cost_budget_usd: 5.0`, sum of WU costs = $6.50.
     `auto=False`, reason starts with `gate_budget_exceeded`.
   - `TestFinalOutcomeFailure` — fixture `final_failure/`: WU's
     final `attempt_outcome` is `tests_failed` (not `passed`).
     `auto=False`, reason mentions `final_outcome_not_passed`.
     (Note: this is a defensive check — by the time `evaluate_auto_close`
     runs the WU is `done`, so a non-passed final outcome would
     be unusual. Tested to enforce predicate-side check 7.)

4. **Graceful-degrade test classes:**

   - `TestMissingPlannedCostUsd` — fixture
     `missing_planned_cost/`: WU has `cost_usd: 1.50` but no
     `planned_cost_usd`. Predicate skips ratio checks for that
     WU; `metrics["warnings"]` contains
     `planned_cost_missing: <wu_id>`. If no OTHER criterion
     fails, `auto=True`.
   - `TestMissingGateBudget` — fixture `missing_budget/`: GATE
     file has no `cost_budget_usd`. Check 6 skipped silently.
   - `TestMissingEventsJsonl` — fixture `no_events/`: no
     `events.jsonl` in `.specfuse/`. Predicate treats events as
     empty; `metrics["warnings"]` contains `events_jsonl_missing`.
     If frontmatter is clean, `auto=True`.
   - `TestMissingWuFile` — fixture `missing_wu_file/`: PLAN.md
     names a WU file that doesn't exist on disk. `auto=False`,
     reason starts with `wu_file_missing`.

5. **Override test:**

   - `TestAutoCloseDisabledPerPlan` — fixture `disabled_per_plan/`:
     PLAN.md frontmatter contains `auto_close_disabled: true`.
     `auto=False`, reason equals `auto_close_disabled_per_plan`.
     Predicate returns this BEFORE inspecting WU evidence (test
     by also setting WU costs that would otherwise produce
     `auto=True` and confirming the override-only reason wins).

6. **Multi-criterion combined test:**

   - `TestMultipleFailures` — fixture `multiple_failures/`:
     blocked_human + cost overrun + plan-next overrun all
     present. `reasons` list has length ≥ 3, all relevant
     reasons present. Confirms predicate collects reasons
     rather than short-circuiting.

7. **Closing-WU exclusion test:**

   - `TestClosingWusSkippedInCostChecks` — fixture
     `closing_high_cost/`: gate's `close-intermediate` WU has
     `cost_usd: $5` (would trip per-WU ratio if checked); no
     other criterion fails. Predicate must IGNORE the close-
     intermediate WU in cost-ratio checks → `auto=True`.
     Validates AC7 of T01.

8. **Coverage gate:**

   ```bash
   coverage run -m pytest tests/test_gate_eval.py
   coverage report --include=.specfuse/scripts/gate_eval.py --fail-under=90
   ```

   Both must exit 0. The `--include` filter scopes the floor to
   this feature's own surface (per
   `[FEAT-2026-0002/G1-CLOSE]` rule on per-file coverage). If
   coverage falls short, name the uncovered branches in the
   RESULT block before adding tests — coverage padding to hit
   the floor without exercising real behavior is hollow-pass
   bait.

9. **Symbol-existence check** before declaring complete:

   ```bash
   # a. Test file exists and references all required test classes
   test "$(grep -cE '^class TestAutoCloseHappyPath|^class TestBlockedHumanInChain|^class TestReplanEvent|^class TestPerWuCostOverrun15x|^class TestPerWuCostHardOverrun2x|^class TestPlanNextOverrun|^class TestGateBudgetBust|^class TestFinalOutcomeFailure|^class TestMissingPlannedCostUsd|^class TestMissingGateBudget|^class TestMissingEventsJsonl|^class TestMissingWuFile|^class TestAutoCloseDisabledPerPlan|^class TestMultipleFailures|^class TestClosingWusSkippedInCostChecks' tests/test_gate_eval.py)" = "15"

   # b. All tests pass
   python3 -m pytest tests/test_gate_eval.py -v

   # c. Coverage ≥ 90% on gate_eval.py
   coverage run -m pytest tests/test_gate_eval.py && coverage report --include=.specfuse/scripts/gate_eval.py --fail-under=90

   # d. Each fixture directory has a PLAN.md that lints clean
   for d in tests/fixtures/gate_eval/*/; do python3 .specfuse/scripts/lint_plan.py "$d" || exit 1; done

   # e. Working-tree diff touches the test file (prior-hollow-pass guard)
   git diff --name-only HEAD | grep -qx 'tests/test_gate_eval.py'
   ```

   If any command exits non-zero, emit `status: blocked` naming
   the failing command. Do NOT flip the WU `status` field as a
   substitute for the tests.

10. **Tempdir-git setup pattern (precautionary).** If any test
    DOES end up needing a tempdir-git repo (it shouldn't, but
    if a test fixture is generated dynamically rather than
    checked in), it MUST run `git config commit.gpgSign false`
    immediately after `git init`, BEFORE the first `git
    commit`. The operator's global git config has SSH commit-
    signing enabled; signing fails inside subprocesses that
    can't reach ssh-agent → tests fail with
    `subprocess.CalledProcessError` exit 128 on commit.
    Pattern reference: `tests/_workspace.py:36`,
    `tests/test_closing_deliverable_guard.py:76`. See
    `[FEAT-2026-0013/G1-CLOSE]` and `[FEAT-2026-0017/T01
    prior_attempts entry 2]` for the failure-mode trace.

**Do not touch.** Files this WU may create or edit:
- `tests/test_gate_eval.py` (new file).
- `tests/fixtures/gate_eval/**/*` (new fixture directories +
  files — PLAN.md, GATE-NN.md, WU-*.md, events.jsonl as needed).

No edits to: `.specfuse/scripts/gate_eval.py` (T01 owns; predicate
changes are out of scope for this WU — emit `status: blocked` if
a test surfaces an edge case requiring a predicate fix),
`.specfuse/scripts/loop.py`, `lint_plan.py` (except as needed to
make fixture PLAN.md files lint clean — if fixture PLAN.md needs
a real-feature-incompatible shape, emit `status: blocked` and
discuss), skills, other features, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set
(`.specfuse/verification.yml`): tests, lint, security, coverage.
Plus AC8 coverage gate (scoped to `gate_eval.py`). Plus AC9
existence checks.

**Escalation triggers.**

1. **Completeness.** AC9 (a) returns anything other than `15` →
   `status: blocked`. The test file is missing test classes.
2. **Coverage shortfall.** If `coverage report --include=
   .specfuse/scripts/gate_eval.py --fail-under=90` exits non-zero,
   do NOT add coverage-padding tests that don't exercise real
   predicate behavior. Name the uncovered lines/branches in the
   RESULT block and emit `status: blocked` if real coverage of
   those branches requires a predicate change. Hollow-coverage
   = hollow-pass.
3. **Predicate-bug surface.** If a test discovers `gate_eval.py`
   misimplements a criterion (e.g., reason string format
   mismatch, ratio calculation off-by-one), emit `status:
   blocked` naming the bug in `gate_eval.py` rather than
   editing it from this WU. T01 owns the module; the operator
   re-arms T01.
4. **Fixture-format incompatibility.** If a fixture PLAN.md
   fails `lint_plan.py` because the linter assumes feature-
   level invariants the fixture violates (e.g., requires a
   real `.specfuse/roadmap.md` row for the fixture's
   feature_id), emit `status: blocked` proposing whether to
   (a) make the fixtures look like real features registered
   in a fixture-only roadmap, or (b) widen `lint_plan.py` to
   accept a `--fixture` flag. Do NOT silently disable lint
   on fixtures — the fixtures must lint clean per AC2.
