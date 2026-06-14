---
feature_id: FEAT-2026-9913
title: Test fixture auto close disabled per plan
branch: feat/FEAT-2026-9913-test-fixture
roadmap_goal: Synthetic fixture for gate_eval predicate unit tests
status: active
planned_cost_usd: 1.0
auto_close_disabled: true
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9913/G1-CLOSE
        file: WU-90-close.md
        depends_on: []
```
