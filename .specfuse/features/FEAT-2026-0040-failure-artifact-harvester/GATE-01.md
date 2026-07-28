---
gate: 1
status: open
cost_budget_usd: 26.00
---

# Gate 1 — a failure artifact can be modelled, fingerprinted, and redacted

## Definition of done

- A neutral `FailureArtifact` exists that core logic reasons about, and adapter
  protocols that produce one — with **no provider type reachable from the core**.
- Telemetry is resolved per component through a seam, so a later per-component
  binding extends the interface rather than changing it.
- A finding derived from a target fingerprints on that target's coordinates, so two
  targets on one component never collapse into one fingerprint.
- No artifact text can leave the process unredacted.
- `RETROSPECTIVE.md` exists with a `## Gate 1` section; lessons are promoted; gate
  2 is drafted and `GATE-02-REVIEW.md` written.

Every clause is decidable by this gate — no provider, no GitHub, no downstream
feature. That is deliberate, per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** Not applicable to gate 1 — no
  work unit flips a default or raises a check's severity, and every assertion is
  over modules this gate creates. **Gate 2 is a different matter:** its
  cron-dialect validator change *is* a severity flip, and arming it without the
  probe is what makes an implementation WU spin on a defect one local run would
  have shown. `G1-PLAN` must carry that forward.
- **Flag-scope table (§3).** Not applicable — no behaviour flag is introduced.
- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it must
  be answered **again** for gate 2, where tightening heartbeat-target validation
  makes it live.

## Reflection notes

<Written by the human at review time.>
