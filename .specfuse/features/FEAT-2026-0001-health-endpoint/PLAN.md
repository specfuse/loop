---
feature_id: FEAT-2026-0001
title: Health-check endpoint
slug: health-endpoint
branch: feat/FEAT-2026-0001-health-endpoint
roadmap_goal: Operators can verify a running instance is healthy without inspecting logs.
autonomy_default: review
status: active
---

# Plan: Health-check endpoint

Add a `GET /health` endpoint that reports liveness and the build version, with tests.
A deliberately small feature: enough to exercise the loop end-to-end (two
implementation units with a dependency) without the work itself getting in the way.

This file owns the shape. WU files own their own status; GATE files own gate status.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0001/T01
        file: WU-01-health-endpoint.md
        depends_on: []
      - id: FEAT-2026-0001/T02
        file: WU-02-endpoint-tests.md
        depends_on: [FEAT-2026-0001/T01]
      - id: FEAT-2026-0001/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [FEAT-2026-0001/T01, FEAT-2026-0001/T02]
      - id: FEAT-2026-0001/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-2026-0001/G1-RETRO]
      - id: FEAT-2026-0001/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-2026-0001/G1-LESSONS]
      - id: FEAT-2026-0001/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-2026-0001/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units: []     # drafted by gate 1's plan-next
```
