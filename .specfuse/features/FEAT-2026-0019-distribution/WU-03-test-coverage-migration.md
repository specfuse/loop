---
id: FEAT-2026-0019/T03
type: implementation
status: done
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - scripts/smoke-test.sh
  - .specfuse/verification.yml
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Migrate the test harness, coverage, and smoke to the package

**Objective.** Point the test suite, coverage source, and smoke check at the
`specfuse.loop` package instead of path-loading `.specfuse/scripts/*.py`, and prove the
full `code` gate set green under `pip install -e .[dev]`.

**Context.** This is `FEAT-2026-0019/T03`, depends on T01 (package) and T02 (shims).
Today `tests/` load modules by file path via a `load_module(".specfuse/scripts/…")`
helper, coverage runs `--source=.specfuse/scripts`, `scripts/smoke-test.sh` invokes
`.specfuse/scripts/*.py`, and `.specfuse/verification.yml` targets the same paths. With
code now in `specfuse/loop/`, these must import the package and measure its coverage.
Ground in `.specfuse/skills/verification/SKILL.md` and `.specfuse/rules/`.

**Red-test exempt:** test migration — the assertions are unchanged; only the import
path and coverage source move. The migrated suite IS the behavior safety net for T01
and T02.

**Acceptance criteria.**

1. Test modules import the package (`from specfuse.loop import loop, lint_plan, …`)
   rather than path-loading from `.specfuse/scripts/` — `grep -rn '\.specfuse/scripts/' tests/`
   returns no remaining module-load references (string fixtures that exercise the
   scaffold-copy path may remain, but no `load_module` of driver code).
2. `scripts/smoke-test.sh` and `.specfuse/verification.yml` measure coverage with
   `--source=specfuse` (was `.specfuse/scripts`) and point ruff/bandit at `specfuse`
   in addition to `tests`/`scripts`.
3. After `pip install -e .[dev]`, the full `code` gate set passes: tests (pytest or
   the existing unittest discovery), coverage `--fail-under=90`, `ruff check`, and
   `bandit` — `./scripts/smoke-test.sh` exits 0 end to end.
4. The back-compat smoke test (`test_smoke_import_from_scripts_dir`) reflects the T02
   shim reality and passes (not skipped).

**Do not touch.** `specfuse/loop/` driver logic (T01) and the shims (T02) — this WU
fixes tests/config to match them, it does not change behavior to make tests pass;
`.specfuse/features/`, `LEARNINGS.md`, `roadmap.md`; secrets; `.git/`.

**Verification.** `pip install -e .[dev] && ./scripts/smoke-test.sh` green (AC3); the
coverage-source + no-path-load greps (AC1, AC2). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If coverage drops below 90% after migration because a module
silently fell out of `--source` (e.g. a renamed file like `validate_event.py` not
picked up), emit `status: blocked` and name the uncovered module rather than lowering
the threshold. If a test asserts behavior that T01/T02 actually changed (not just an
import path), stop and report — fixing the test to hide a real behavior change is a
hollow pass.
