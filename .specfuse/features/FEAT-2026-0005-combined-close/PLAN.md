---
feature_id: FEAT-2026-0005
title: Combined close for single-gate features
slug: combined-close
branch: feat/FEAT-2026-0005-combined-close
roadmap_goal: A single-gate feature may close with one `close` work unit instead of the four-WU retrospective→lessons→docs→plan-next sequence.
autonomy_default: review
status: active
---

# Plan: Combined close for single-gate features

The four closing ceremonies (retrospective → lessons → docs → plan-next) cost
four dispatches — including an Opus plan-next — even on a one-substantive-WU
feature, where `plan-next` is terminal boilerplate (no next gate to forward-
design). This feature adds a single `close` work-unit type that does all four
ceremonies' jobs in one session, **permitted only for single-gate features**
(multi-gate keeps the four-WU sequence, where forward-design plan-next earns its
cost). The LEARNINGS pump (`lessons`) and doc/roadmap reconciliation survive —
folded into the one `close` WU, not dropped.

Itself a single-gate feature — but it closes with the **old** four-WU sequence,
because the `close` type it introduces does not exist when this feature's driver
loads `loop.py`. FEAT-2026-0006 is the first feature to use the new `close` WU.

This file owns the **shape**. WU files own their own status; GATE files own gate
status.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0005/T01
        file: WU-01-combined-close.md
        depends_on: []
      - id: FEAT-2026-0005/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [FEAT-2026-0005/T01]
      - id: FEAT-2026-0005/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-2026-0005/G1-RETRO]
      - id: FEAT-2026-0005/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-2026-0005/G1-LESSONS]
      - id: FEAT-2026-0005/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-2026-0005/G1-DOCS]
```

## Notes

- Single gate: `G1-PLAN` is terminal. (This feature predates its own output, so
  it uses the four-WU closing; FEAT-2026-0006 dogfoods the `close` WU.)
- Dependencies live here, not in WU frontmatter.
</content>
