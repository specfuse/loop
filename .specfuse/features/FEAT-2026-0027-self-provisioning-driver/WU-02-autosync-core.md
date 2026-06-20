---
id: FEAT-2026-0027/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_autosync.py
produces_driver_helper:
  - auto_sync
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Auto-sync decision-tree core (replaces fail-loud check)

**Objective.** Replace `check_scaffold_version()` in `loop.py`'s `main()` with an
`auto_sync()` that version-syncs the project's `.specfuse/` to the installed scaffold on
every run — create / overlay / no-op / never-downgrade — using the manifest (T01) to
detect modified files.

**Context.** This is `FEAT-2026-0027/T02`, depends on T01 (`detect_modified` + manifest).
Today `main()` calls `check_scaffold_version()` which `sys.exit`s on a missing/older
scaffold (`loop.py` ~line 3461 + the `main()` call). This WU swaps that for `auto_sync`.
The non-interactive defaults live here; the TTY prompt + toggles are T03. Calls
`scaffold.init` / `scaffold.upgrade_specfuse` / `scaffold.scaffold_version` (FEAT-2026-0026)
and `scaffold.detect_modified` (T01). Ground in `.specfuse/rules/result-contract.md`.

**Red-test (§12):** `tests/test_autosync.py::test_autosync_creates_when_missing` and
`::test_autosync_refuses_newer` fail on HEAD (`auto_sync` absent) and pass after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_autosync.py::test_autosync_creates_when_missing` exists
   and fails on HEAD before this WU's edits.
2. `auto_sync(...)` (in `loop.py`) implements the decision tree comparing installed
   `scaffold.scaffold_version()` to `.specfuse/VERSION`:
   - **missing `.specfuse/`** → `scaffold.init(repo)` (create);
   - **older, no modified files** (`detect_modified` empty) → `scaffold.upgrade_specfuse`
     (overlay) + restamp;
   - **older, with modified files** → overlay the unmodified versioned files, **skip the
     modified ones + warn** (the interactive prompt is T03); never lose user edits;
   - **equal** → no-op (no writes, no diff noise);
   - **newer than installed** → warn + refuse (do not downgrade; reuse
     `upgrade_specfuse`'s downgrade-refusal direction).
3. `main()` calls `auto_sync` instead of `check_scaffold_version`; the old fail-loud
   `check_scaffold_version` is removed (or reduced to a helper `auto_sync` uses) — no
   path still `sys.exit`s on a merely-older scaffold.
4. **`--dry-run` → read-only**: `auto_sync` writes nothing on dry-run; it prints the
   decision + planned writes. (The existing `--dry-run` flag.)
5. **Never auto-commits.** `auto_sync` only touches the working tree; no `git` calls.
6. One `auto_sync` unit test per branch (missing/older-clean/older-modified/equal/newer)
   with the scaffold + manifest mocked or driven via `tmp_path`; AC1 red tests pass;
   `code` gates green (coverage ≥ 90).

**Do not touch.** `scaffold.py` (T01 owns the manifest/detect; this WU only calls it);
the consent prompt + toggles (T03); the per-WU dispatch/verify loop; secrets; `.git/`.

**Verification.** `code` gates incl. `tests/test_autosync.py`; the red→green proof (AC1,
AC6); a no-op-on-equal assertion (AC2) and a writes-nothing-on-dry-run assertion (AC4).
Symbol check: `python3 -c "from specfuse.loop.loop import auto_sync"`. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If removing `check_scaffold_version` breaks an existing
caller/test that depends on its fail-loud behavior (e.g. a TestMainArgparse mock), update
the caller to the auto-sync contract — but if a test asserts a *behavior* auto-sync
deliberately changes (older scaffold now self-heals instead of exiting), surface it; do
not silently keep both paths.
