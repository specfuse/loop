---
id: FEAT-2026-0002/T03
type: implementation
effort: medium
status: done
attempts: 1
duration_seconds: 378.795
cost_usd: 0.727147
input_tokens: 16
output_tokens: 22232
---

# Cover lint_plan.py error arms

**Objective.** Raise `.specfuse/scripts/lint_plan.py` per-file coverage
from 79% to ≥ 90% by adding error-arm tests for the 11 uncovered branches
plus a regression on an existing valid fixture. Tests only; no production
code changes.

**Context.** This is `FEAT-2026-0002/T03`. Measured uncovered lines
(via `coverage report -m --include=.specfuse/scripts/lint_plan.py`):

- `71` — `read_frontmatter` no-frontmatter return.
- `82` — PLAN.md missing.
- `87` — required frontmatter keys missing.
- `91` — yaml fence missing in PLAN body.
- `126-127` — WU graph entry missing `id` or `file`.
- `136-137` — WU file referenced by graph not found on disk.
- `148` — invalid WU `type`.
- `163` — invalid WU `status`.
- `166` — invalid WU `effort`.
- `189` — closing sequence != `CLOSING_SEQUENCE` and != single `close`.
- `199-209, 213` — `main()` print + argparse arms.

Apply the two-case linter-guard pattern (LEARNINGS
[FEAT-2026-0003/G2-LESSONS]) and add the regression case on an existing
valid fixture (LEARNINGS [FEAT-2026-0005/G1-LESSONS]). The bundled
worked example `.specfuse/features/FEAT-2026-0001-health-endpoint` is the
canonical valid fixture in this repo.

Reference the binding rules under `.specfuse/rules/`. Edit files only.

**Acceptance criteria.**

1. New file `tests/test_lint_plan_errors.py` exists with at least two
   test classes: `TestLintErrorArms` (one method per arm above) and
   `TestLintValidRegression`.
2. Each error arm (lines 71, 82, 87, 91, 126-127, 136-137, 148, 163,
   166, 189) has a method that constructs a minimal malformed fixture
   in a `tempfile.TemporaryDirectory()`, runs `lint(Path(tmp))`, and
   asserts the returned errs list contains exactly one error whose
   text names the offending key, file, or condition.
3. `main()` arms: a method invokes `lint_plan.main()` with patched
   `sys.argv` covering (a) usage error (zero args), (b) PASS path
   against a valid fixture (asserts exit 0 and "OK" in stdout), (c)
   FAIL path against a malformed fixture (asserts exit 1 and "FAIL"
   in stdout).
4. **Regression on existing valid fixture.** A method runs
   `lint(Path(".specfuse/features/FEAT-2026-0001-health-endpoint"))`
   and asserts the returned errs list is empty. Protects against
   strictness regressions.
5. **Per-file coverage AC.** `coverage run --source=.specfuse/scripts
   -m unittest discover -s tests && coverage report
   --include=.specfuse/scripts/lint_plan.py --fail-under=90` exits 0.
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from tests.test_lint_plan_errors import
   TestLintErrorArms, TestLintValidRegression"` succeeds.

**Do not touch.** Exactly 1 new file: `tests/test_lint_plan_errors.py`.
No edits to: `.specfuse/scripts/lint_plan.py` (production code stays
untouched), other test files (`tests/test_lint_*.py` are owned by their
original WUs — extend them only if a duplication would result; the
default is a new dedicated file), `.specfuse/scripts/loop.py`,
`.specfuse/scripts/_miniyaml.py` (T04 owns it), `.specfuse/rules/`,
`.specfuse/verification.yml`, the FEAT-2026-0001 fixture
(read-only — modifying it would invalidate the regression test),
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

If a test reveals a real bug in `lint_plan.py` that cannot be
unit-tested without a fix, **emit `status: blocked`** with the bug
evidence rather than touching production code in this WU.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
PLUS the per-file coverage AC 5, PLUS the existence check AC 6. Declare
`files_changed: [tests/test_lint_plan_errors.py]` in the RESULT block.

**Escalation triggers.**

1. **Completeness.** If `tests/test_lint_plan_errors.py` is absent from
   the files you edited, emit `status: blocked`.
2. **Per-file floor not met.** If `coverage report
   --include=.specfuse/scripts/lint_plan.py --fail-under=90` exits
   non-zero, emit `status: blocked` naming the lines still uncovered.
3. **Existing fixture invalidated.** If running
   `lint(Path(".specfuse/features/FEAT-2026-0001-health-endpoint"))`
   ever returns non-empty errs, do not modify the fixture. Emit
   `status: blocked` — this is a pre-existing bug for a separate WU.

**Pre-flight lint discipline.** Before emitting `status: complete`,
run `ruff check tests/test_lint_plan_errors.py` and remove every
finding. The `lint` gate runs `ruff check .specfuse/scripts tests
scripts` — a single unused import (`F401`) in your new file fails the
whole gate and counts as a failed attempt. Remove unused imports
(`import sys`, `import io`, etc.) before declaring complete. A prior
dispatch of this WU spun three attempts on exactly this: `import sys`
was unused and `F401` failed every attempt. Do not repeat.
