---
id: FEAT-2026-0070/T08
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.25
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_closing_guard_prediction.py
oracle_env: macos_local
produces_driver_helper: check_autoclose_debt_prediction
model: sonnet
effort: medium
---

# Predict T07's refusal at arm time instead of charging a dispatch for it

**Objective.** Add an arm-time `lint_plan` WARN that fires when a feature has an auto-closed
gate carrying a debt marker and its terminal close WU's body never instructs the agent to
reconcile it — so `assert_autoclose_debt_reconciled` costs a lint line, not a re-dispatch.

**Context.** This is `FEAT-2026-0070/T08`. Read `PLAN.md`, `GATE-02.md`, and
`GATE-02-REVIEW.md` first. Depends on `FEAT-2026-0070/T06` (which writes the marker) and
`FEAT-2026-0070/T07` (whose guard this predicts).

**Why this WU exists at all.** `close-discipline.md` §4 measured it: across 158 closing WUs
in 9 repositories, **28% of all closing-WU spend was burned on attempts the driver refused**,
and three guards whose requirements appeared in no authoring surface accounted for **45% of
that waste** — `assert_gate_review_exists` alone at $53.11 over 15 fires. By contrast
`assert_verdict_well_formed` fired 10 times for **$0.00**, because it is checked before the
agent spends anything. `FEAT-2026-0070/T07` ships a brand-new blocking condition on terminal
closes. This WU is the difference between that guard being the $0.00 kind and the $53.11
kind, and it is being written in the same gate rather than after the first refusal.

The mechanism already exists: `check_closing_guard_literals` (`lint_plan.py:407`) and its
`_GUARD_LITERAL_PREDICTIONS` table (`:380`) do exactly this for three guards today, and
`tests/test_closing_guard_prediction.py` is its test file. **This WU extends that mechanism;
it does not build a second one.**

**§10 helper-duplication pre-flight, run at drafting time:**

```
grep -rn "check_closing_guard_literals" --include="*.py" .
    -> specfuse/loop/lint_plan.py:407 (def), :781 (single call site, inside main)
       tests/test_closing_guard_prediction.py (test file)
grep -rn "_GUARD_LITERAL_PREDICTIONS" --include="*.py" .
    -> specfuse/loop/lint_plan.py:380 (def), :424 (single use, inside the function above)
```

**Why the existing table cannot simply gain a fourth row.** Every entry in
`_GUARD_LITERAL_PREDICTIONS` is a static regex over the WU body, keyed on WU type alone.
This prediction is **conditional on feature state** — it should fire only when the feature
actually has a marked auto-closed predecessor gate. A static `close` row would WARN on
every terminal close in every project, which is noise, and noise is how a WARN stops being
read. A sibling function is the honest shape.

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_closing_guard_prediction.py::TestAutoCloseDebtPrediction::test_warns_when_terminal_close_body_ignores_marked_debt`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_closing_guard_prediction.TestAutoCloseDebtPrediction -v`
   exits non-zero. It builds a feature whose `RETROSPECTIVE.md` carries a gate-1 debt marker
   and whose terminal close WU body says nothing about reconciling it, runs the check, and
   asserts a `WARN:` line naming `assert_autoclose_debt_reconciled` is printed.
2. The same test passes after this WU's edits.
3. **Positive control:** the same fixture whose terminal close body *does* instruct the
   agent to reconcile the auto-closed gate emits no WARN. A predictor that warns
   unconditionally is worse than none — it trains the reader to skip the line.
4. **No marker, no WARN.** A feature with an auto-closed gate but no debt marker (every
   feature that closed before `FEAT-2026-0070/T06` shipped) emits nothing. This mirrors
   `FEAT-2026-0070/T07` AC4 and is what keeps the check off 11 features of history.
5. `check_autoclose_debt_prediction(feature_dir, gates)` is a new function in
   `lint_plan.py`, called from the same place `check_closing_guard_literals` is called
   (`lint_plan.py:781`), and like it **prints `WARN:` and never changes the exit code**.
   `check_closing_guard_literals`'s own docstring records why: an ERROR predicate
   unsatisfiable on a populated tree is the failure `[FEAT-2026-0015/G2-CLOSE]` names.
6. It skips a close WU whose `status` is `done` — sealed history, matching
   `check_closing_guard_literals`'s `:427` behavior. One test.
7. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
   exits 0 and emits **no new WARN** for this feature — gate 1 did not auto-close
   (`WU-90-gate-1-close-intermediate.md` carries `auto_close_disabled: true` and ran a real
   session), so there is no marker and nothing to predict. Paste the full output.
8. Run the check across every feature in `.specfuse/features/` and paste the WARN count.
   The expected answer is **zero**; report and stop if it is not.
9. `python3 -c "from specfuse.loop.lint_plan import check_autoclose_debt_prediction"`
   exits 0 (`authoring-work-units` §9 symbol-existence check).
10. `python3 -m unittest discover -s tests -v` exits zero. Coverage stays ≥ 90%.

**Cost-reintroduction trade (`[FEAT-2026-0039/G2-CLOSE]`).** This WU lands on the **keeps
the saving** side and is the clearest case of the three: it is a static check in a linter
that already runs, and its entire purpose is to move a cost from dispatch time (where it is
a full re-attempt) to arm time (where it is a printed line). It cannot reintroduce an agent
dispatch because it runs in a process that has no agent.

**Do not touch.**

- `check_closing_guard_literals` (`lint_plan.py:407`) and `_GUARD_LITERAL_PREDICTIONS`
  (`:380`) — out of scope by design; the reason a fourth row is the wrong shape is in the
  Context above. Both are single-call-site symbols per the §10 enumeration and stay as they
  are.
- `assert_autoclose_debt_reconciled` (`loop.py`) — `FEAT-2026-0070/T07` owns it. This WU
  predicts it; it must not re-implement its logic. Matching the marker and grepping the
  close WU's body is not the same computation as the guard's, and it does not need to be.
- `build_autoclose_debt_enumeration` and the auto-close stub writers —
  `FEAT-2026-0070/T06` owns them.
- `specfuse/loop/_wu_sections.py` — `FEAT-2026-0070/T05` owns it. Import if useful; do not
  edit.
- `REQUIRED_SECTIONS`, `VALID_FEATURE_STATUS`, and every existing `check_*` function in
  `lint_plan.py` — this WU adds one function and one call, and changes no existing finding.
  AC7's "no new WARN for this feature" is the guard against drift into them.
- `.git/`, secrets. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests, ruff, bandit,
coverage ≥ 90%, leak-scan, the four `bats` gates). Scoped red/green proof:
`python3 -m unittest tests.test_closing_guard_prediction -v`. Plan lint per AC7. Symbol
check per AC9.

> Sandbox note: the four `bats` gates call `mktemp -d` in `setup`, which the default session
> sandbox denies before any assertion runs (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
> Report which sandbox each gate ran under.

**Escalation triggers.** Emit `status: blocked` if AC8's repo-wide run produces WARNs on
features that closed correctly — a noisy predictor is the failure mode this check exists to
avoid, and the narrowing decision belongs to the reviewer. Also block if
`FEAT-2026-0070/T07`'s shipped guard turns out to require something this prediction cannot
see from `PLAN.md` plus the WU bodies: a prediction that does not match the guard it
predicts is worse than none, because it certifies a WU that then gets refused. Blocked is a
respectable outcome (`result-contract.md` rule 4).
