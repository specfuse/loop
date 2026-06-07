---
feature_id: INIT-2026-0001/F06
title: Conform publishRoster to validated spec
slug: conform-publishroster-to-validated-spec
branch: feat/INIT-2026-0001-F06-conform-publishroster-to-validated-spec
roadmap_goal: Conform publishRoster to validated spec
autonomy_default: review
status: planned
source_issue_url: https://github.com/RestoManagerApp/Backend/issues/287
initiative: INIT-2026-0001
---

# Plan: Conform publishRoster to validated spec

Adopted from GitHub issue: https://github.com/RestoManagerApp/Backend/issues/287

This file owns the **shape** of the feature: gate order, work units, dependency edges.
WU files own their own status; GATE files own gate status.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: INIT-2026-0001/F06/T01
        file: WU-01-conform-publishroster-to-validated-spec.md
        depends_on: []
      - id: INIT-2026-0001/F06/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [INIT-2026-0001/F06/T01]
      - id: INIT-2026-0001/F06/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [INIT-2026-0001/F06/G1-RETRO]
      - id: INIT-2026-0001/F06/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [INIT-2026-0001/F06/G1-LESSONS]
      - id: INIT-2026-0001/F06/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [INIT-2026-0001/F06/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units: []
  - gate: 3
    file: GATE-03.md
    work_units: []
```
