---
gate: 1
status: open
---

# Gate 1 — Dispatch mechanics

## Definition of done

- `claude -p` is dispatched per WU with: model family alias (T01), effort tier
  flag (T02), tier-gated caveman preamble (T03).
- Retry attempts escalate effort by one tier and loosen the terseness directive
  per attempt (T04).
- Failure note piped between attempts is bounded in lines and characters with
  head+tail truncation (T05).
- Every Gate 1 substantive WU is `done`.
- `RETROSPECTIVE.md` exists; durable lessons are promoted to
  `.specfuse/LEARNINGS.md`; docs and roadmap status reflect what shipped.
- Gate 2's substantive WUs are drafted (defaults-by-WU-type policy, per-gate
  cost budget, telemetry extension) and `GATE-02-REVIEW.md` is written.

## Reflection notes

<Written by the human at review time.>
