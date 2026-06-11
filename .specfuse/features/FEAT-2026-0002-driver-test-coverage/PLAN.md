---
feature_id: FEAT-2026-0002
title: Driver run-loop test coverage
slug: driver-test-coverage
branch: feat/FEAT-2026-0002-driver-test-coverage
roadmap_goal: Cover the driver's remaining orchestration paths and the scaffold modules (loop.py, validate-event.py, lint_plan.py, _miniyaml.py) so this repo's coverage --fail-under floor climbs from 70 to the methodology default of 90.
autonomy_default: review
status: active
---

# Plan: Driver run-loop test coverage

Close the deviation between this repo's own `code` coverage gate
(`--fail-under=70`) and the methodology default (`≥ 90%`). At feature start the
TOTAL is 78% and `loop.py` is already 87% (raised by FEAT-2026-0008's run-loop
integration tests). The remaining gap is concentrated in error arms across four
modules:

- `loop.py` (87%) — `squash_commit` soft-reset, `find_feature` 0/1/many,
  `require_git_ready`, `log_event`, `dispatch` subprocess error paths,
  `gate-budget` halt arm, `BlockingIOError` print arm, argparse `main()`.
- `validate-event.py` (0%) — no test file exists.
- `lint_plan.py` (79%) — 11 error arms (missing PLAN, missing FM keys,
  invalid type/status/effort, closing-sequence mismatch, `main()` print/argparse).
- `_miniyaml.py` (87%) — flow-list double-quote escape arms,
  `_decode_double_quoted` escape decode + error paths, scattered indent arms.

This file owns the **shape**. WU files own their own status; GATE files own
gate status.

## Scope OUT

- New driver behavior or features. Test/coverage feature only.
- Refactor of covered code, unless minimally needed to make an arm testable
  (each such case is flagged per WU as a precondition, not a license).
- Modules already at high coverage (`gh_*`, `adopt_feature.py` ≥ 90%).
- Raising `--fail-under` above 90 — the methodology default is the ceiling
  for this feature.
- Re-landing deferred FEAT-2026-0007 work (T04 retry ladder, T08 telemetry).
  That belongs in a successor feature.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0002/T01
        file: WU-01-loop-orchestration-coverage.md
        depends_on: []
      - id: FEAT-2026-0002/T02
        file: WU-02-validate-event-coverage.md
        depends_on: []
      - id: FEAT-2026-0002/T03
        file: WU-03-lint-plan-error-arms.md
        depends_on: []
      - id: FEAT-2026-0002/T04
        file: WU-04-miniyaml-error-arms.md
        depends_on: []
      - id: FEAT-2026-0002/T05
        file: WU-05-floor-flip.md
        depends_on:
          - FEAT-2026-0002/T01
          - FEAT-2026-0002/T02
          - FEAT-2026-0002/T03
          - FEAT-2026-0002/T04
      - id: FEAT-2026-0002/G1-CLOSE
        file: WU-90-close.md
        depends_on:
          - FEAT-2026-0002/T05
```

## Notes

- Single gate, five substantive WUs (one per module + floor flip), one
  `close` ceremony (valid for single-gate features per FEAT-2026-0005).
- Dependencies live here, not in WU frontmatter.
- T01-T04 are independent and can land in any order. T05 (`--fail-under`
  flip) depends on all four because per-module coverage thresholds must be
  measurably met before the floor rises.
- Each substantive WU declares an explicit per-module coverage AC
  (e.g. `coverage report --include=<file> --fail-under=N`) — a per-file
  threshold survives reorganization of overall coverage and is the right
  falsifiable claim per LEARNINGS [FEAT-2026-0007/G1-LESSONS].
- Each substantive WU includes (a) an existence check per
  LEARNINGS [FEAT-2026-0007/G1-LESSONS] confirming the new test
  class/file is importable, (b) a completeness escalation trigger
  per the same entry, and (c) explicit `files_changed` declaration
  per the driver's T02 files-changed guard (FEAT-2026-0008).
- Per LEARNINGS [FEAT-2026-0007/G2-LESSONS] the new `--fail-under=90`
  floor is intentionally set in T05 and exercised against this gate's
  own work (T01-T04 must land coverage that satisfies it before the
  flip commits). The first independent exercise belongs to the next
  feature.
