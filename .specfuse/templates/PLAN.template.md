---
feature_id: FEAT-YYYY-NNNN
title: <short feature title>
slug: <feature-slug>
branch: feat/FEAT-YYYY-NNNN-<feature-slug>
roadmap_goal: <one line copied from the roadmap — the north star this feature serves;
  plan-next anchors every drafted gate to this and flags if a retrospective implies
  it should change>
autonomy_default: review        # auto | review | supervised
status: active                  # active | done | abandoned
---

# Plan: <short feature title>

<One or two paragraphs of human-facing intent. The work units carry the executable
detail; this is the why.>

This file owns the **shape** of the feature: the gate order, which work units belong
to each gate, and the dependency edges between them. It does **not** own status —
each WU file owns its own status, and each GATE file owns its gate's status. Detail
only as far as the next gate; plan-next drafts the gate after that from the
retrospective and lessons.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-YYYY-NNNN/T01
        file: WU-01-<slug>.md
        depends_on: []
      - id: FEAT-YYYY-NNNN/T02
        file: WU-02-<slug>.md
        depends_on: [FEAT-YYYY-NNNN/T01]
      # --- mandatory closing sequence (lint enforces presence + order) ---
      - id: FEAT-YYYY-NNNN/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [FEAT-YYYY-NNNN/T01, FEAT-YYYY-NNNN/T02]
      - id: FEAT-YYYY-NNNN/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-YYYY-NNNN/G1-RETRO]
      - id: FEAT-YYYY-NNNN/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-YYYY-NNNN/G1-LESSONS]
      - id: FEAT-YYYY-NNNN/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-YYYY-NNNN/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units: []     # drafted by gate 1's plan-next; empty is valid (= not yet planned)
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never needs to
  know its own dependencies — they are satisfied by the time the driver hands it the
  file. Deps are scheduling metadata, and scheduling is the driver's job.
- WU file numbers track the correlation sub-ID where it exists (`WU-07` ↔ `/T07`).
  Closing units use a reserved high range (90+) so they sort last.
