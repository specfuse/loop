---
gate: 1
status: awaiting_review
cost_budget_usd: 50.0
# Raised 2026-08-13 from $24.00 by operator decision, with the reason recorded
# here so the number is not mysterious later.
#
# The original $24.00 was the correct estimate: this gate's WU estimates ($16.00)
# plus one re-attempt of its largest WU ($8.00, T01), the defensive padding
# `.specfuse/rules/planning-discipline.md` §5 prescribes. It was not wrong; it
# was overrun.
#
# The overrun is $40.27 of failed G1-CLOSE attempts, all three refused on
# `assert_learnings_appended_or_noop`, caused by this WU's own criterion 5 naming
# `.specfuse/LEARNINGS.md` as the lesson destination on an `autonomy_default: auto`
# feature — the one path `close-i` forbids. Diagnosed and fixed (the criterion now
# names `LEARNINGS-pending.md`); the authoring gap that allowed it is filed as
# #2173.
#
# `planning-discipline.md` §5 warns against raising a ceiling to absorb a retry,
# because "a closing-WU retry is a defect to diagnose, not a cost to budget for".
# That warning is honoured rather than waived: the defect WAS diagnosed and fixed,
# and the remaining work is one bounded close at ~$5.00. $50.00 covers the sunk
# $43.52 plus that close. It is not headroom for further retries — a second spin
# here is a new defect and should halt again.
baseline:
  sha: 26e6c56e2abcad34f22d862b5c9ccb35adb23ecd
  probed_at: 2026-08-13T12:24:03.449129+00:00
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
