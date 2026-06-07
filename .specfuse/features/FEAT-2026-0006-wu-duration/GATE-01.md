---
gate: 1
status: passed
---

# Gate 1 — WU execution-time tracking

## Definition of done

- The driver measures each WU attempt's wall-clock time (`time.monotonic`) and
  records `duration_seconds` per-attempt in `events.jsonl` and cumulative on the
  WU's frontmatter, alongside the existing cost fields.
- Duration is captured even when `cost_tracking` is disabled.
- `WU.template.md` documents the `duration_seconds` frontmatter field.
- Tests cover per-attempt capture, cumulative summing, and the frontmatter write.
- The closing ceremony runs as a **single `close` WU** (this feature's live test
  of FEAT-2026-0005): `RETROSPECTIVE.md`, `LEARNINGS.md`, docs/roadmap
  reconciliation, and the terminal feature-arc verdict all in one session.

## Reflection notes

<Written by the human at review time.>
</content>
