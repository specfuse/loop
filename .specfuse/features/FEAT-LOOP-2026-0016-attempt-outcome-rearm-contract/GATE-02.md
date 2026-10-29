---
gate: 2
status: passed
cost_budget_usd: 12.00  # raised at arm time from 9.50 — gate-1 ratio 1.62× × $7.40 plan ≈ $12; T04 spec revised with no_gate_marker defense per GATE-02-REVIEW open-verification #5
---

# Gate 2 — Consumers: spinning-detector hook + /gate-status + /unblock-wu (drafted by G1-PLAN)

## Definition of done

Drafted by G1-PLAN from gate 1's retrospective + lessons. Expected
shape:

- Spinning-detector active driver hook (T04): after attempt N with
  `failure_signature == ` prior attempt's signature, halt the WU
  to `blocked_human` before attempt N+1 dispatches. Emit
  `human_escalation` event with reason `spinning_signature_repeat`.
  Eliminates the operator's manual Monitor-and-kill pattern.
- `/gate-status` (T05) surfaces per-attempt `failure_class` +
  `failure_signature` + `re_arm_count` for blocked WUs. Today it
  greps stdout via the operator.
- `/unblock-wu` (T06) prompts for mandatory re-arm rationale,
  writes new `re_arm_history` entry, increments `re_arm_count`,
  triggers driver cumulative-fold on next dispatch.

## Reflection notes

<Written by the human at gate-2 review time.>
