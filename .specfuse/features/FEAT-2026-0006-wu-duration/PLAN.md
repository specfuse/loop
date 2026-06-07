---
feature_id: FEAT-2026-0006
title: WU execution-time tracking
slug: wu-duration
branch: feat/FEAT-2026-0006-wu-duration
roadmap_goal: The loop records each work unit's wall-clock execution time alongside the cost it already captures.
autonomy_default: review
status: done
---

# Plan: WU execution-time tracking

Capture per-WU wall-clock execution time and record it the same way cost is
recorded today: per-attempt in `events.jsonl` and cumulative on the WU's
frontmatter. The cost plumbing already exists (`attempts_usage`,
`write_cost_to_wu`, `cum_usage` in `run()`); duration rides it via
`time.monotonic()`.

**This feature is the first to use the single `close` work unit** (FEAT-2026-0005)
instead of the four-WU closing sequence — it is a single-gate feature, so the
collapsed close applies. That makes 0006 the live test of the combined-close
ceremony.

This file owns the **shape**. WU files own their own status; GATE files own gate
status.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0006/T01
        file: WU-01-duration-tracking.md
        depends_on: []
      - id: FEAT-2026-0006/G1-CLOSE
        file: WU-90-close.md
        depends_on: [FEAT-2026-0006/T01]
```

## Notes

- Single gate, single substantive WU, **one `close` WU** (not the four-WU
  sequence) — valid because the feature has exactly one gate. This dogfoods
  FEAT-2026-0005's combined close.
- Dependencies live here, not in WU frontmatter.
</content>
