---
id: FEAT-2026-0019/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
oracle_env: macos_local
produces:
  - .specfuse/scripts/loop.py
  - .specfuse/scripts/lint_plan.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Vendored shims over the package (dogfood + back-compat)

**Objective.** Replace the moved `.specfuse/scripts/*.py` with thin shims that
re-export from `specfuse.loop`, so this repo's dogfood invocation
(`python .specfuse/scripts/loop.py`) and the existing back-compat import keep working
now that the real code lives in the package.

**Context.** This is `FEAT-2026-0019/T02`, depends on T01 (which moved the code into
`specfuse/loop/`). This repo runs the loop on itself from `.specfuse/scripts/`, and a
smoke test imports `from loop import …` with cwd at `.specfuse/scripts/`. After T01
those files are gone; this WU recreates them as shims. The package is canonical (the
"package canonical, vendored synced" decision in `PLAN.md`); these shims are the
vendored surface for the editable-install dev case. Ground in
`.specfuse/rules/never-touch.md`.

**Red-test exempt:** refactor/migration — preserving existing behavior through a new
indirection; no new behavior introduced.

**Scope boundary (deferred, NOT this WU).** Rebuilding `init.sh`'s vendored-copy
generation so offline / no-pip targets get real code (not shims that import an
uninstalled package) is **out of scope** for gate 1 and is left for a later gate.
This WU targets the pip-present dogfood + back-compat case only.

**Acceptance criteria.**

1. Each deployable module under `.specfuse/scripts/` exists again as a shim that
   imports its implementation from `specfuse.loop` (e.g. `.specfuse/scripts/loop.py`
   re-exports from `specfuse.loop.loop`), and modules with a CLI entrypoint preserve
   `if __name__ == "__main__": main()` (or equivalent dispatch).
2. `pip install -e .` is in effect, then
   `python .specfuse/scripts/loop.py --dry-run --feature FEAT-2026-0001-health-endpoint`
   exits 0 (dogfood preserved).
3. Back-compat import resolves: with cwd `.specfuse/scripts/`,
   `python -c "from loop import ensure_feature_branch"` exits 0 — OR the back-compat
   smoke test (`test_smoke_import_from_scripts_dir`) is updated to the shim reality
   and passes (T03 may finalize the test edit; the import itself must resolve here).
4. The shims do not duplicate driver logic: each shim file is a re-export, verified by
   it being short (no function/class bodies copied from the package) — `grep -cE 'def |class ' .specfuse/scripts/loop.py` is small (re-exports only, not the full driver).

**Do not touch.** `specfuse/loop/` (T01's canonical code — shims import it, don't edit
it); `.specfuse/features/`, `LEARNINGS.md`, `roadmap.md`, `verification.yml`;
`init.sh` (deferred); the internal leak-guard files; secrets; `.git/`.

**Verification.** AC2 dry-run; AC3 import; `ruff check .specfuse/scripts`. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If a shim cannot preserve back-compat for the offline (no-pip)
case, emit `status: blocked` and name it — that is the deferred `init.sh` problem
surfacing early and is a respectable blocked outcome, not something to paper over by
copying code back into the shim. If `validate-event.py` (hyphenated script name) is
referenced anywhere as an executable path that the rename to `validate_event.py`
breaks, report it rather than silently leaving a dangling reference.
