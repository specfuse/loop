---
feature_id: FEAT-2026-9907
title: Test fixture budget bust
branch: feat/FEAT-2026-9907-test-fixture
roadmap_goal: Synthetic fixture for gate_eval predicate unit tests
status: active
planned_cost_usd: 7.5
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9907/T01
        file: WU-01-impl.md
        depends_on: []
      - id: FEAT-2026-9907/T02
        file: WU-02-impl.md
        depends_on: [FEAT-2026-9907/T01]
      - id: FEAT-2026-9907/G1-CLOSE
        file: WU-90-close.md
        depends_on: [FEAT-2026-9907/T02]
```
