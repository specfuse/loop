---
id: FEAT-2026-0018/T03
type: implementation
effort: medium
status: pending
attempts: 0
planned_cost_usd: 0.80
generated_surfaces: []
produces_driver_helper:
  - main
  - _format_decision
  - _resolve_feature_dir
---

# CLI backtest entrypoint + calibration regression

**Objective.** Add a `__main__`-style CLI to `gate_eval.py` so an
operator can run `python3 .specfuse/scripts/gate_eval.py backtest
<feature-id> [--gate N]` against any historical feature and see
the predicate decision + reasons. Plus a calibration regression
test that pins the predicate's behavior against the 4-feature
backtest baseline (0013, 0014, 0015, 0017) — drift flags either
predicate change or feature-data change.

**Context.** This is `FEAT-2026-0018/T03`. Builds on T01 (the
module) and T02 (the test scaffolding). The CLI is read-only: no
file writes, no git commands, no state mutation. Exit 0 always —
this is a diagnostic tool, not a gate.

The calibration regression is the load-bearing piece: it pins
the empirical baseline established during the design backtest
(see PLAN.md § "Predicate v1" rationale). If a future predicate
tweak changes how an existing feature scores, this test fails
LOUDLY — forcing the operator to acknowledge the change before
shipping. Without it, predicate evolution silently rescores
history.

Reference: T01's `evaluate_auto_close` is the only API this WU
should call. No re-implementation of predicate logic in the CLI
layer. The CLI is a render around the module, nothing more.

**Acceptance criteria.**

1. **CLI invocation:**
   `python3 .specfuse/scripts/gate_eval.py backtest <feature-id>`
   - Resolves `<feature-id>` to a feature directory under
     `.specfuse/features/FEAT-YYYY-NNNN-<slug>/` (slug-tolerant:
     a partial ID like `0017` resolves to FEAT-2026-0017 if
     unambiguous; ambiguous matches print options and exit 0).
   - For each gate in the feature's PLAN.md, calls
     `evaluate_auto_close(feature_dir, gate_id)`.
   - Prints a per-gate decision block:
     ```
     FEAT-2026-0017  predicate=v1
       G01  auto=False
         reasons:
           - blocked_human_in_chain: T01 escalated 2026-06-11
           - per_wu_cost_overrun: T01 actual=$26.74 planned=$3.20 ratio=8.36x
         metrics:
           gate_total_cost: $26.74
           gate_budget: <unset>
     ```
   - Exits 0.

2. **`--gate N` flag:** Restricts evaluation to one gate.

3. **Bare invocation help:**
   `python3 .specfuse/scripts/gate_eval.py` (no args) or
   `python3 .specfuse/scripts/gate_eval.py --help` prints a
   one-screen help message naming the `backtest` subcommand,
   its args, and the predicate version. Exits 0.

4. **Unknown subcommand:** Exits 2 with a one-line error +
   help. This is the only non-zero exit path; everything else
   (file missing, no feature matching the ID, etc.) prints a
   diagnostic and exits 0 because the CLI is a read-only
   diagnostic, not a gate that should block CI.

5. **`_format_decision(decision: AutoCloseDecision) -> str`** —
   pure function that renders a `AutoCloseDecision` to the
   block shape shown in AC1. Unit-testable independently.

6. **`_resolve_feature_dir(feature_id: str, repo_root: Path) ->
   Path | None`** — resolves a feature ID (full
   `FEAT-2026-0017`, partial `0017`, or slug-suffix matching)
   to a feature directory. Returns `None` on no match;
   returns the first directory on exact match; raises
   `ValueError` on ambiguous partial match. Unit-testable.

7. **Calibration regression test** — `tests/test_gate_eval_calibration.py`:
   a separate test file (not folded into T02's
   `test_gate_eval.py`) that:
   - For each of `FEAT-2026-0013`, `FEAT-2026-0014`,
     `FEAT-2026-0015`, `FEAT-2026-0017`, calls
     `evaluate_auto_close` against each of its gates.
   - Asserts the (auto, reason-class-set) pair matches a
     pinned baseline:
     ```python
     CALIBRATION = {
         ("FEAT-2026-0013", 1): {"auto": True, "reason_classes": set()},
         ("FEAT-2026-0014", 1): {"auto": True, "reason_classes": set()},
         ("FEAT-2026-0015", 1): {"auto": False, "reason_classes": {"per_wu_cost_overrun", "plan_next_overrun"}},
         ("FEAT-2026-0015", 2): {"auto": False, "reason_classes": {"per_wu_cost_overrun"}},
         ("FEAT-2026-0017", 1): {"auto": False, "reason_classes": {"blocked_human_in_chain", "per_wu_cost_overrun"}},
     }
     ```
     Reason class = first colon-separated segment of each
     reason string (e.g. `"per_wu_cost_overrun: T03 actual=$..."`
     → class `per_wu_cost_overrun`).
   - On mismatch: fails with a diff showing observed vs
     expected for the specific (feature, gate) pair.

   **Drift policy:** if a test fails because the actual
   feature data evolved (e.g., a re-arm of an old WU changed
   cost), the test's baseline IS the source of truth — the
   data drift is the bug. If the test fails because a
   predicate change was intentional, the baseline must be
   updated explicitly in the same commit, and the commit
   message must call out the rationale.

8. **`tests/test_gate_eval_calibration.py` may be skipped
   cleanly** when a feature in the baseline doesn't exist on
   disk (e.g., running on a checkout where 0013 was deleted).
   Use `unittest.skipUnless` (or pytest's `skipif`) keyed on
   `pathlib.Path(...).is_dir()`. Skipping ≠ passing — the
   test message must say `skipped: feature dir absent`.

9. **Symbol-existence check** before declaring complete:

   ```bash
   # a. CLI module has all required symbols
   test "$(grep -cE '^def main|^def _format_decision|^def _resolve_feature_dir|^if __name__' .specfuse/scripts/gate_eval.py)" = "4"

   # b. CLI invocation succeeds against this feature
   python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0018

   # c. Help exits 0
   python3 .specfuse/scripts/gate_eval.py --help

   # d. Unknown subcommand exits 2
   python3 .specfuse/scripts/gate_eval.py garbage; test "$?" = "2"

   # e. Calibration test exists and passes
   test -f tests/test_gate_eval_calibration.py
   python3 -m pytest tests/test_gate_eval_calibration.py -v

   # f. Working-tree diff touches both files
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/gate_eval.py'
   git diff --name-only HEAD | grep -qx 'tests/test_gate_eval_calibration.py'
   ```

   If any command exits non-zero or reports the wrong count,
   emit `status: blocked`. Do NOT flip the WU `status` field
   as a substitute.

**Do not touch.** Files this WU may edit/create:
- `.specfuse/scripts/gate_eval.py` (extend with CLI; do NOT
  modify the predicate or helper functions T01 shipped —
  additions only).
- `tests/test_gate_eval_calibration.py` (new file).

No edits to: `.specfuse/scripts/loop.py`, `lint_plan.py`,
`tests/test_gate_eval.py` (T02 owns), other features, skills,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set. Plus AC9 existence
checks. Plus calibration regression test passes against the
4-feature baseline.

**Escalation triggers.**

1. **Predicate change required.** If running the calibration
   test surfaces that the current predicate scores a baseline
   feature differently from the expected baseline, emit
   `status: blocked` naming the (feature, gate, observed,
   expected) tuple. Do NOT patch T01's predicate from this WU;
   the operator re-arms T01 with a revised spec. Do NOT relax
   the calibration baseline silently; the baseline IS the
   contract.
2. **Backtest feature data drift.** If a baseline feature's
   directory is present but the feature data has evolved
   (e.g., a frontmatter retroactively gained
   `planned_cost_usd` that wasn't there at backtest time),
   emit `status: blocked` naming the changed feature. The
   operator decides whether to update the baseline
   (intentional drift) or restore the feature data (drift
   bug).
3. **CLI flag ambiguity.** If the spec for `--gate N` clashes
   with anything in Python's `argparse` defaults
   (e.g., conflict with `--help`), emit `status: blocked` with
   the conflict and propose a resolution; do not silently
   rename the flag.
4. **Feature-resolution edge case.** If the user passes an ID
   that matches no feature, the CLI must print "no feature
   matches: <id>" and exit 0 (read-only tool). If the spec's
   "exits 0 on missing feature" rule conflicts with anything
   in the linter or CI, emit `status: blocked` rather than
   changing the exit code.
