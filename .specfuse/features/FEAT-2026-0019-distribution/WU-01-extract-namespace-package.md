---
id: FEAT-2026-0019/T01
type: implementation
status: done
attempts: 2
planned_cost_usd: 2.50
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/__init__.py
  - pyproject.toml
duration_seconds: 712.413
cost_usd: 4.648368
input_tokens: 10717
output_tokens: 28291
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Extract the `specfuse.loop` namespace package

**Objective.** Move the deployable driver code from `.specfuse/scripts/` into a
`specfuse/loop/` PEP 420 namespace package and make it pip-installable, so the package
becomes the single source of driver code.

**Context.** This is `FEAT-2026-0019/T01`, gate 1 of the distribution feature. Today
the driver and its helpers live only in `.specfuse/scripts/` and ship by `init.sh`
copying them into consumer repos (see `PLAN.md` and the roadmap detail for
FEAT-2026-0019). This WU creates the package; T02 makes `.specfuse/scripts/` thin
shims over it; T03 migrates the test harness. Naming is decided in `PLAN.md`: the
distribution is `specfuse-loop`, imported as `specfuse.loop`; the bare `specfuse`
name is reserved for a future umbrella package — **do not** create a top-level
`specfuse` module or claim that name here. `specfuse/` is a PEP 420 namespace (NO
`specfuse/__init__.py`); `specfuse/loop/` is a regular subpackage (HAS
`specfuse/loop/__init__.py`). Ground in `.specfuse/rules/never-touch.md` and
`correlation-ids.md`.

**Red-test exempt:** refactor/migration — this WU moves code and changes import style
without adding behavior; the existing suite (migrated in T03) is the safety net.

**Acceptance criteria.**

1. The eight deployable modules are moved from `.specfuse/scripts/` to
   `specfuse/loop/`: `loop.py`, `lint_plan.py`, `_miniyaml.py`, `gate_eval.py`,
   `gh_backend.py`, `gh_features.py`, `adopt_feature.py`, and `validate-event.py`
   renamed to `validate_event.py` (hyphen removed so it is importable).
2. `specfuse/loop/__init__.py` exists; `specfuse/__init__.py` does NOT exist (PEP 420
   namespace), verified by `test ! -e specfuse/__init__.py`.
3. Every intra-package import is package-relative: no bare `import _miniyaml`,
   `from gate_eval import …`, `import gh_features`, or `import gh_features as …`
   remains under `specfuse/loop/` — `grep -rnE '^(import|from) (_miniyaml|gate_eval|gh_backend|gh_features|adopt_feature|lint_plan|validate_event)\b' specfuse/loop/` returns nothing.
4. `pyproject.toml`: distribution `name` stays `specfuse-loop`; a `[project.scripts]`
   table declares `specfuse-loop = "specfuse.loop.loop:main"` and
   `specfuse-lint = "specfuse.loop.lint_plan:main"`; setuptools is configured to find
   the `specfuse.loop` package (namespace-package discovery).
5. `pip install -e .` exits 0 in a clean environment.
6. `python -c "from specfuse.loop import loop, lint_plan, gate_eval, _miniyaml, gh_backend, gh_features, adopt_feature, validate_event"` exits 0.
7. `specfuse-loop --help` and `specfuse-lint --help` both exit 0.

**Do not touch.** `.specfuse/features/`, `.specfuse/LEARNINGS.md`,
`.specfuse/roadmap.md`, `.specfuse/verification.yml`, `.specfuse/templates/`,
`.specfuse/rules/`; the internal leak-guard files (`leak_scan.py`,
`leak_scan_content.py`, `leak_denylist.*`) stay in `.specfuse/scripts/`; `tests/`
(T03's job); `init.sh` (T02/later); secrets; `.git/` (the driver owns all git ops).

**Verification.** `pip install -e .` (AC5); the import + `--help` checks (AC6, AC7);
the namespace + bare-import greps (AC2, AC3); `ruff check specfuse`. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `loop.py` or `lint_plan.py` has no `main()` entrypoint to
bind the console scripts to, emit `status: blocked` — the entrypoint shape is a design
decision, not a guess. If any moved module imports a sibling in a way that cannot be
made package-relative without a behavior change, stop and report rather than
restructuring logic. If `from specfuse.loop import …` cannot resolve after
`pip install -e .` (namespace mis-config), emit `status: blocked` with the setuptools
error.
