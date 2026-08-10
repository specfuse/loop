---
gate: 1
status: open
cost_budget_usd: 23.00
baseline:
  sha: e9a252d115df9dd8682577884d9b0aa0450766de
  probed_at: 2026-08-10T04:14:56.975854+00:00
  failing: []
---

# Gate 1 — the operator's priorities have one auditable file, and one waiting dial reads it

## Definition of done

- `.specfuse/agent-policy.yml` has a documented schema, a shipped example, a
  structural validator, and a CI gate that runs the validator against this
  repo's own live policy file.
- A reader API exists, and queue entries are validated against the roadmap with
  the WARN/ERROR split PLAN.md § *Escalation-predicate satisfiability* fixes.
- `apply_triage`'s `auto=` parameter — shipped by FEAT-2026-0045 reading no
  configuration of any kind, deliberately, because this file did not exist — is
  supplied from the policy file.
- `/groom-backlog` exists and proposes a queue from real repo state, writing
  only on explicit accept.
- Every implementation work unit in this gate is `done`.
- The terminal close has run: retrospective, lessons, docs, and verdict.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is a **single-gate feature** (four substantive WUs, at the
ceremony-proportionality threshold in `docs/methodology.md` §6). There is no
`plan-next` and no next gate to arm — the closing sequence is one terminal
`close` WU.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Recorded for the reviewer, since this gate is armed at draft time:

- **Runtime probe (§4).** No WU in this gate flips a default value or a
  severity. T01 introduces a validator that is new — nothing to probe against,
  because no prior severity exists to change. The probe requirement does not
  bind here; if T02's queue check were later raised from WARN to ERROR, it would.
- **Flag-scope table (§3).** T03 wires an existing behavior flag
  (`apply_triage(..., auto=)`) to a configuration source. It carries a
  flag-scope table naming every path that flag reaches.
- **Escalation-predicate satisfiability (§2).** Answered in PLAN.md: zero on a
  correct input, under the WARN/ERROR split. The split is the answer, not a
  caveat to it.

## Reflection notes

<Written by the human at review time. This gate was drafted and armed without an
operator interview, on operator instruction (2026-08-09). PLAN.md §
*Assumed decisions* lists the seven decisions taken solo — the review checkpoint
for them is this feature's PR, not a gate boundary.>
