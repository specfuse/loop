---
gate: 2
status: awaiting_review
---

# Gate 2 — Defaults, telemetry, and guardrails

## Definition of done

- Sensible model + effort defaults applied by WU type when frontmatter omits
  them (T06), with Haiku policy documented.
- Per-gate cost budget on `GATE.md` halts the loop to `blocked_human` on
  overshoot, mirroring the `MAX_ATTEMPTS` brake (T07).
- `events.jsonl` per-attempt + per-WU outcome records include the new fields
  (`resolved_model`, `effort_used`, `terseness`, cache tokens); gate summary
  surfaces cache hit rate (T08).
- Closing sequence written; LEARNINGS appended; G2-PLAN writes the terminal
  feature-arc verdict if no Gate 3 surfaces.

Substantive WUs to be drafted by Gate 1's plan-next from Gate 1's own
telemetry. Skeleton today; details after Gate 1 runs.

## Reflection notes

<Written by the human at review time.>
