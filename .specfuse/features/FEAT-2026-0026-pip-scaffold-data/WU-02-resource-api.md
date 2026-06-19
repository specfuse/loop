---
id: FEAT-2026-0026/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_resources.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Resource API over the packaged scaffold data

**Objective.** Add `specfuse.loop.scaffold` — a small API that reads the packaged
scaffold seed (T01) via `importlib.resources`, the substrate `specfuse init`/`upgrade`
(gates 2–3) build on.

**Context.** This is `FEAT-2026-0026/T02`, depends on T01 (the `specfuse/loop/data/`
package data). The API must resolve resources from an INSTALLED wheel, not just the
source tree — so it uses `importlib.resources` against the `specfuse.loop.data`
package, never a filesystem path relative to `__file__`. Keep it stdlib-only (no new
deps), consistent with the driver. Ground in `.specfuse/rules/result-contract.md`.

**Red-test (§12):** `tests/test_scaffold_resources.py::test_iter_scaffold_files_lists_all_seed`
fails on HEAD (module/function absent) and passes after this WU.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_resources.py::test_iter_scaffold_files_lists_all_seed`
   exists and fails on HEAD before this WU's edits (import error / missing symbol).
2. `specfuse/loop/scaffold.py` provides:
   - `iter_scaffold_files() -> list[tuple[str, bytes]]` — every seed file as
     `(relative_path, content)` (relpaths like `templates/PLAN.template.md`,
     `rules/never-touch.md`, `verification.yml.example`, `VERSION`,
     `gitignore.snippet`).
   - `scaffold_version() -> str` — the packaged `VERSION` string.
   - `read_scaffold(relpath: str) -> bytes` — one resource by relpath.
3. The API uses `importlib.resources` over `specfuse.loop.data` (verified: no
   `Path(__file__)`-relative filesystem access in `scaffold.py`).
4. Resolves from an installed wheel: after `pip install` of the built wheel into a clean
   venv, `python -c "from specfuse.loop.scaffold import iter_scaffold_files, scaffold_version; assert iter_scaffold_files(); print(scaffold_version())"` exits 0.
5. `scaffold_version()` equals the canonical `.specfuse/VERSION`.
6. The red test (AC1) passes after the edits.

**Do not touch.** `specfuse/loop/data/` content (T01 owns it); the driver modules
(`loop.py`, `lint_plan.py`, etc.); `.specfuse/` state; secrets; `.git/`.

**Verification.** `code` gates (tests incl. the new file, coverage ≥ 90, ruff, bandit);
the red→green proof (AC1, AC6); the installed-wheel resolution check (AC4);
`python -c "from specfuse.loop import scaffold"`. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `importlib.resources` cannot enumerate a nested data
subtree (`templates/`, `rules/`) on the target Python (API differences across 3.10–3.12),
emit `status: blocked` naming the version + API gap rather than falling back to
`__file__` paths (which break in a zipped wheel).
