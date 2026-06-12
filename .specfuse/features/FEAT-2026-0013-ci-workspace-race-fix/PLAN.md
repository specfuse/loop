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
- **Belt-and-suspenders `ignore_cleanup_errors=True`** — explicitly
  rejected. Symptom suppression hides future leaks and erodes the
  verification-as-oracle property. Revisit only if root-cause audit
  cannot converge on a deterministic fix.

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
