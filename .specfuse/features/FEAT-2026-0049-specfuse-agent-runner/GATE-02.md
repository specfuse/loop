---
gate: 2
status: open
---

# Gate 2 — the agent drains bugs, triage, and findings

## Definition of done

The agent autonomously handles the three cheap action classes and escalates what
it cannot: bug issues through `run_bug_lane`, untriaged issues through
`apply_triage` (honouring `rules.triage.auto`), undiagnosed findings through
`diagnose_cli`, and diagnosed findings through `run_autofix` — plus answered
needs-human issues, parsed and acted on first.

## Status

Substantive work units are drafted by gate 1's `plan-next` (`G1-PLAN`), from
gate 1's retrospective and what the conductor's real shape turns out to be. The
sketch in PLAN.md's gate map is the intent, not the plan.

**Sizing risk to resolve here, not before.** This is the largest gate as
sketched. If drafting it against real code shows it oversized, the split is
findings into their own gate — making the feature four gates. That call belongs
to `G1-PLAN` with evidence in hand.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** No gate-2 WU is expected to
  flip a default or a severity — the providers consume `evaluate_merge_guardrails`
  and `autofix.decide` as they are. `G1-PLAN` must confirm that explicitly rather
  than assume it; if any drafted WU does flip one, it may not be armed on
  "mechanical, nothing design-open" and needs the local runtime probe first.
- **Scope check.** PLAN.md's scope boundary forbids modifying any surface the
  agent drives. A drafted WU that needs to change `run_bug_lane`, `apply_triage`,
  `diagnose_cli`, or `run_autofix` is a plan change to escalate, not a WU to arm.
- **Existing-mechanism check (§1).** Each provider WU names the shipped function
  it composes. Confirm that function still exists and still has the seams the WU
  assumes — these are consumed, not vendored, and they can move.
