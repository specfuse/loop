---
id: FEAT-LOOP-2026-0251/T04
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
produces:
  - specfuse/loop/lint_plan.py
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - tests/test_fail_fast_deliverables.py
model: sonnet
effort: medium
---

# T04 — arm-time warning for an unmentioned `produces:` path, and docs

**Objective.** Turn Definition-of-done clause 5 green and document the new order.

**Context.** `FEAT-LOOP-2026-0251/T04`; decisions 6 and 7 in `PLAN.md`. Sits beside
`check_produces_satisfiability`, `check_produces_shape` and `check_produces_boundary` in
`lint_plan.py`.

- Add a WARN check: for each dispatchable unit (not `done`, not `abandoned`), every `produces:`
  path must appear in the unit's body by full path or by file name. The message names the unit,
  the path, and the post-attempt refusal it pre-empts (`produces_not_in_diff`).
- Measure it on this repository before reporting: count the `done` units across
  `.specfuse/features/` whose `produces:` would fire if they were dispatchable, and put the
  count and the total in the RESULT's notes. If it exceeds 10% of `done` units with `produces:`,
  narrow the match (for example, accept the path's parent directory) and re-measure.
- `docs/methodology.md`: in the outcome table and the guard paragraph that mentions
  `retain_on_guard_refusal`, say the three refusals now run before verification unless
  `defaults.fail_fast_deliverables` is `false`, and that the retry note lists the changed
  paths. Then run `scripts/sync-scaffold.sh`.

**Acceptance criteria.**

1. `tests.test_fail_fast_deliverables.TestArmTimeWarning` fails on HEAD and passes after: a
   `pending` unit whose `produces:` path its body never names gets the WARN; the same unit
   naming the file name gets none; a `done` unit gets none.
2. `specfuse lint` exits 0 on every feature folder under `.specfuse/features/` (WARN only).
3. The RESULT's notes give the measured count and total from the Context bullet.
4. `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` is empty.
5. `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`.

**Do not touch.** The driver module and its guard sites (T01–T03).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_lint_plan -b`.

**Escalation triggers.** If no narrowing brings the measured rate to 10% or below, block with
the measurements instead of shipping a noisy warning.
