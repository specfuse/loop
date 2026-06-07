---
feature_id: FEAT-2026-0004
title: Single-driver working-tree lock
slug: driver-lock
branch: feat/FEAT-2026-0004-driver-lock
roadmap_goal: A second loop driver launched against the same working tree exits cleanly instead of racing the first and corrupting state.
autonomy_default: review
status: done
---

# Plan: Single-driver working-tree lock

Prevent two `loop.py` drivers from running concurrently in one working tree.
The driver's per-WU `git reset --hard` / soft-reset and `git checkout -B` are
tree-global, so two drivers sharing a checkout clobber each other regardless of
feature (observed during the FEAT-2026-0003 dogfood: competing resets produced
commits mixing multiple WUs' work + contradictory WU statuses). The fix is an
auto-released advisory lock on the working tree, plus making the lock file
gitignored here and in every repo `init.sh` sets up.

Single gate — the change is small and self-contained. Source spec:
[`docs/wu-draft-loop-concurrency-lock.md`](../../../docs/wu-draft-loop-concurrency-lock.md).

This file owns the **shape**. WU files own their own status; GATE files own gate
status.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0004/T01
        file: WU-01-driver-lock.md
        depends_on: []
      - id: FEAT-2026-0004/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [FEAT-2026-0004/T01]
      - id: FEAT-2026-0004/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-2026-0004/G1-RETRO]
      - id: FEAT-2026-0004/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-2026-0004/G1-LESSONS]
      - id: FEAT-2026-0004/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-2026-0004/G1-DOCS]
```

## Notes

- Single gate: `G1-PLAN` is terminal (no next gate to draft) — it writes the
  feature-arc verdict and marks the feature ready for closure.
- Dependencies live here, not in WU frontmatter.
</content>
