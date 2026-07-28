---
gate: 2
status: open
---

# Gate 2 — drafted by the previous gate's plan-next

## Definition of done

<Written by gate 1's `plan-next` work unit, from that gate's
retrospective and lessons. The methodology's forward-design move: a gate is
detailed only once the gate before it has actually run.>

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Written by `G1-PLAN` when it drafts this gate. Three requirements are already
known and are recorded here at drafting time so they cannot be forgotten:

- **Runtime probe for a default/severity flip (§4) — MANDATORY here.** The
  cron-dialect change tightens heartbeat-target validation, which is a severity
  flip: a tree that lints clean today can lint dirty after it. Before arming, apply
  the change locally, run the exact command the WU's tests gate will run over every
  shipped YAML surface, and paste the finding list into `GATE-02-REVIEW.md`. That
  list is the enumerated migration surface.
- **Escalation-predicate satisfiability (§2) — must be answered again.** `PLAN.md`
  answers it for gate 1, where every assertion is over new modules. Gate 2 asserts
  over existing shipped configuration, so "what does the rule report on a correct
  input" is a live question with a different answer.
- **Migrate before contract, and the migrate criterion must be a sweep.**
  `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` lost $5.26 to a criterion scoped to a
  sample where the flip needed "no non-conforming instance remains anywhere."
  Flip-first is unsatisfiable under the preflight baseline probe.

## Reflection notes

<Written by the human at review time.>
