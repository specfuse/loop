---
feature_id: FEAT-2026-9905
title: Test fixture cost overrun 2x
branch: feat/FEAT-2026-9905-test-fixture
roadmap_goal: Synthetic fixture for gate_eval predicate unit tests
status: active
planned_cost_usd: 2.0
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9905/T01
        file: WU-01-impl.md
        depends_on: []
      - id: FEAT-2026-9905/G1-CLOSE
        file: WU-90-close.md
        depends_on: [FEAT-2026-9905/T01]
```
