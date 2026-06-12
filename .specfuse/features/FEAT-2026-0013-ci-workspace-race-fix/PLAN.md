---
feature_id: FEAT-2026-0013
title: CI integration_workspace cleanup race fix
slug: ci-workspace-race-fix
branch: feat/FEAT-2026-0013-ci-workspace-race-fix
roadmap_goal: Eliminate the fd-leak race in `integration_workspace()` so the integration-test path is deterministic on Python 3.12 CI runners (no `OSError: Directory not empty` flakes).
autonomy_default: auto
status: active
---

# Plan: CI integration_workspace cleanup race fix

## Prior attempts

- **v1** (2026-06-12, $2.21 total / 944.97s wall): shipped methodologically
  with root-cause fix only (gc.auto=0 + `git rev-parse HEAD` sync barrier
  in `integration_workspace`). Oracle was 50× macOS-local audit, 50/50 OK.
  PR #9 push CI on Linux runner `27412918877` re-fired the SAME race
  (`test_no_files_changed_in_result_block_runs_squash_as_today` ERROR on
  `tempfile._rmtree`). Root cause: oracle environment mismatch — macOS
  APFS hides a race Linux ext4 surfaces. v1 cost preserved in each WU's
  `historical_*` frontmatter fields. PR #9 NOT merged. T01 + G1-CLOSE
  re-armed (`status: pending`, `attempts: 0`) for v2.
- **v2** (2026-06-12, $2.05 total / 701.7s wall): added belt-and-
  suspenders `ignore_cleanup_errors=True` + source-presence verification
  to v1's root-cause fix. macOS local 50× and Linux Docker 50× both
  PASS=50 OSError=0. Pushed to PR #9. Linux CI **re-failed** in
  `tests/test_loop_files_changed_guard.py::test_agent_creates_new_file_and_declares_it_completes`
  — same OSError race, DIFFERENT integration_workspace. Scope-discovery
  miss: repo has 5 copies of `def integration_workspace` (test_driver_
  integration, test_backend, test_loop_files_changed_guard, test_loop_
  smoke_runner, test_loop_zero_token_guard) AND ~50 bare
  `tempfile.TemporaryDirectory()` call sites. v1+v2 only fixed one of
  five. WU-01 + WU-90 reverse-flipped; v2 cost preserved.
- **v3** (in progress): widened scope. Centralize all 5 copies into
  one shared `tests/_workspace.py::integration_workspace()`. Apply
  `gc.auto=0` + sync barrier + `ignore_cleanup_errors=True` ONCE in the
  central helper. Replace 5 duplicate definitions with import statements.

CI intermittently fails with `OSError: [Errno 39] Directory not empty:
'/tmp/.../.git/objects'` when `integration_workspace()` (in
`tests/test_driver_integration.py`) exits its `TemporaryDirectory`
context. Python 3.12's `shutil.rmtree` races against leftover file
descriptors / git background tasks. Three observed occurrences (one of
which was hit during this very session's push CI for FEAT-2026-0014,
run `27391633691`).

This file owns the **shape**. WU files own their own status; the GATE
file owns gate status.

## Scope OUT

- Bumping Python version or test framework.
- Refactoring `integration_workspace()` API surface beyond what the
  leak fix requires (it must remain a `@contextmanager` yielding a
  `Path`).
- Changing other tests' fixture patterns — only this one fixture is
  at issue today.
- ~~Belt-and-suspenders `ignore_cleanup_errors=True` — explicitly
  rejected.~~ **REVISED 2026-06-12 after v1 ship-and-CI-recur.** PR #9's
  v1 fix (gc.auto=0 + git rev-parse sync barrier) passed 50× locally on
  macOS but the SAME race fired on Linux CI runners
  (run `27412918877`, same `test_..._rmtree` ERROR). The oracle ran in
  the wrong environment. Root-cause fix STAYS in v2 + belt-and-
  suspenders `ignore_cleanup_errors=True` is ADDED to cover the
  Linux-only fs surface not addressed by gc + sync barrier alone.
  This is harm-reduction not symptom-only: root cause still being
  attacked AND the symptom is suppressed if it slips through.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0013/T01
        file: WU-01-audit-and-fix-fd-leaks.md
        depends_on: []
      - id: FEAT-2026-0013/G1-CLOSE
        file: WU-90-close.md
        depends_on:
          - FEAT-2026-0013/T01
```

## Notes

- Single gate, one substantive WU, combined `close` ceremony (valid
  for single-gate features per FEAT-2026-0005). Mirrors FEAT-2026-0014
  and FEAT-2026-0008.
- Recursive audit at close: 50× `tests/test_driver_integration.py`
  loop with zero failures. Locks in the deterministic-CI property.
- Independent of every other planned feature.
