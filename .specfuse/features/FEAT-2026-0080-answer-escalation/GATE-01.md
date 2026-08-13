---
gate: 1
status: awaiting_review
cost_budget_usd: 24.0
# Sum of this gate's WU estimates ($16.00) plus one re-attempt of its largest WU
# ($8.00, T01) — the defensive padding `.specfuse/rules/planning-discipline.md` §5
# prescribes while first-attempt success runs 51–74%.
baseline:
  sha: ee7c24962ee8bf6386c838a0b5d8c6331598b86b
  probed_at: 2026-08-13T12:08:30.268485+00:00
  failing: []
---

# Gate 1 — an operator can answer a parked escalation, and the next agent run is better for it

## Definition of done

An operator runs one skill against one `needs-human` issue, understands what
stopped the agent, chooses a disposition, and — for every disposition except
`skip` — leaves the issue unparked with a durable record of the decision. A
subsequent `/fix-bug` dispatch against that issue receives the operator's guidance
as part of its context rather than re-reading the original report alone.

Concretely:

- Every work unit in this gate is `done`.
- `/answer-escalation` exists in both the canonical and vendored skill trees,
  byte-identical, and refuses to run non-interactively.
- `/fix-bug`'s Step 1 names a command that actually returns comment bodies.
- The close ceremony has run: retrospective, lessons, docs and terminal verdict
  folded into the single `close` WU, with the two deferred verifications named in
  `## What the loop did NOT verify`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This gate is terminal, so its closing sequence is one `close` WU rather than
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** Not applicable — neither WU
  flips a default value or a severity. T02 changes a documented command in skill
  prose; the behaviour change is what an operator's session reads, not a
  configuration default.
- **Flag-scope table (§3).** Not applicable — neither WU introduces or gates on a
  behaviour flag.
- **Escalation-predicate satisfiability (§2).** Not applicable — no check is
  raised to `ERROR` and no "zero issues" predicate is asserted. PLAN.md records
  this as `n/a`.

One arming check that *does* apply, specific to this gate: confirm before arming
that T01's acceptance criteria assert on `SKILL.md` prose and require no live `gh`
call. If a criterion drifts toward exercising the real API, the WU needs
`unsandboxed: true` — the command sandbox breaks `gh` with an invalid-token or TLS
failure, per `[FEAT-2026-0014/T01/gh-claudeP-broken]` as corrected by
`[FEAT-2026-0041/G1-CLOSE]`. As drafted, neither WU needs it.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and
why, anything the close got wrong. This is your record, not the agent's — keep it
honest.>
