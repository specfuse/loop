---
id: FEAT-2026-0062/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/loop/arm_eval.py
  - specfuse/loop/loop.py
  - tests/test_arm_eval.py
  - tests/test_gate_budget.py
produces_driver_helper:
  - gate_spent_usd
oracle_env: macos_local
---

# Route both cost consumers through the lifetime reader

**Objective.** Make `budget_projection` (`arm_eval.py:266`) and `gate_spent_usd`
(`loop.py:1782`) both compute spend via `wu_lifetime_cost_usd` from T01, so the two
aggregates can no longer drift apart or acquire different blind spots.

**Context.** Correlation ID `FEAT-2026-0062/T02`. Depends on T01, which ships the
reader. Read `PLAN.md` for the two re-arm shapes and the rejected alternatives.

The two consumers are in different states today and the WU must not treat them as
equivalent:

- **`budget_projection`** sums `wu["cost_usd"]` alone (`arm_eval.py:266`, via
  `_read_wu`). Blind to both the fold path and the history path.
- **`gate_spent_usd`** sums `cost_usd + cumulative_cost_usd` (`loop.py:1782`). Already
  correct for the fold path since #199/#219; blind only to the fold-never-ran shape
  where spend survives in `re_arm_history[].prior_cost_usd`.

So this WU widens one consumer a lot and the other a little. `gate_spent_usd`'s
docstring already claims *"Sum lifetime recorded cost"* — after this change that
claim becomes true, and the docstring must be updated to say how, naming
`events.jsonl` as the source and the frontmatter sum as the fallback.

**`arm_eval` must still not import `loop`.** Both import `cost`. Preserve that
direction.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_arm_eval.py::TestArmPredicate::test_budget_projection_counts_rearmed_lifetime_spend`
   exists and **fails on HEAD before this WU runs** — `budget_projection` reads
   `cost_usd` alone today, so a fixture whose spend sits in `cumulative_cost_usd`
   reads low and the class returns `clean` where it should fire.
2. That test passes after this WU's edits, and `python3 -m unittest tests.test_arm_eval -v`
   exits zero.
3. A test asserts `gate_spent_usd` returns the **full $9.29** on a
   `FEAT-2026-0053/WU-07`-shaped gate fixture, where it returns $4.28 today.
4. A test asserts neither consumer double-counts on the fold-ran shape — a fixture
   where `cumulative_cost_usd` equals its `re_arm_history[].prior_cost_usd` produces
   the events sum, not a value inflated by either frontmatter field. **This is the
   one regression this design can introduce**; a passing test here is the criterion
   that matters most in this WU.
5. A test asserts a never-re-armed work unit produces the identical number before and
   after this change, for both consumers.
6. A test asserts the two consumers agree: over the same gate fixture,
   `gate_spent_usd` and the spend term inside `budget_projection` compute the same
   total. The whole point of a shared reader is that they cannot diverge again.
7. `grep -n "cost_usd" specfuse/loop/arm_eval.py` shows no remaining bare per-cycle
   sum in the class-1 block, and `grep -n "^from\|^import" specfuse/loop/arm_eval.py`
   shows no import of `loop`. Quote both in the result.
8. `gate_spent_usd`'s docstring names `events.jsonl` as the primary source and the
   frontmatter sum as the fallback, replacing the current #199-era description.
9. The pre-existing budget tests still pass unmodified, or each modification is
   justified inline. Name which suites were run.
10. A tree-wide sweep is run and recorded: `evaluate_arm_predicate` over all 44
    feature folders, reporting how many `budget_projection` verdicts change from
    `clean` to `fired` as a result of this WU. A verdict that changes is a feature
    that was over budget and not stopped; a large number is a finding for the close,
    not a problem with this WU.
11. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/cost.py` — T01 owns it; if the reader is wrong,
report it rather than patching it from here. `BUDGET_PROJECTION_MULTIPLIER` and any
`cost_budget_usd` value — this WU changes what the brakes *read*, never their
thresholds. `_should_halt_for_budget`'s call site — T03 owns the evaluation point.
`fold_cumulative_on_rearm` and `detect_rearm_dispatch`. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1–2 and the corpus sweep in criterion 10.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
red test in criterion 1 passes on HEAD, which would mean `budget_projection` already
reads lifetime spend and this WU's premise is wrong; criterion 4 cannot be satisfied
— a double-count on the fold-ran shape means the reader's contract is wrong and the
fix belongs in T01, not here; `gate_spent_usd` cannot reach `events.jsonl` from its
existing signature without a change that ripples into its callers, which is a design
question rather than a wiring one; or criterion 10's sweep cannot run. If neither
`specfuse/loop/arm_eval.py` nor `specfuse/loop/loop.py` is among the files you
edited, emit `status: blocked` — do not claim complete.
