---
feature_id: FEAT-2026-9915
title: Test fixture closing wu high cost skipped
branch: feat/FEAT-2026-9915-test-fixture
roadmap_goal: Synthetic fixture for gate_eval predicate unit tests
status: active
planned_cost_usd: 8.0
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9915/T01
        file: WU-01-impl.md
        depends_on: []
      - id: FEAT-2026-9915/G1-CLOSE-INTERMEDIATE
        file: WU-90-close-int.md
        depends_on: [FEAT-2026-9915/T01]
      - id: FEAT-2026-9915/G1-PLAN
        file: WU-91-plan-next.md
        depends_on: [FEAT-2026-9915/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-9915/G2-CLOSE
        file: WU-90-g2-close.md
        depends_on: []
```
