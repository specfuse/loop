---
gate: 1
status: passed
---

# Gate 1 — events.jsonl writes are redacted of absolute home paths

## Definition of done

- `flush_events` redacts absolute home-directory paths (`/Users/<x>/…`,
  `/home/<x>/…`) from every string leaf of each event payload before writing —
  driver-local, no import of the repo-internal `leak_scan.py` (T01).
- A note containing a home path lands in `events.jsonl` redacted, the audit signal
  (correlation id, event type, failure class) is preserved, and this repo's staged
  `events.jsonl` passes `leak_scan.py --staged`.
- Retrospective, durable lessons, docs/roadmap reconciliation, and the feature-arc
  verdict are produced by the terminal `close` WU.

Single-gate feature: the terminal `close` WU (G1-CLOSE) collapses
retrospective + lessons + docs + verdict into one session. Autonomy `auto` — the
gate auto-closes on-plan via the `gate_eval` predicate; off-plan falls back to a
dispatched reflective close. Driver-side terminal flips (gate → passed, roadmap row
→ done, auto-archive) fire when the close settles `verdict: met`.

## Reflection notes

<Written by the human at review time.>
