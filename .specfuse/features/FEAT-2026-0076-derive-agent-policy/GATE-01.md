---
gate: 1
status: open
cost_budget_usd: 29.00
baseline:
  sha: 0caf94a5186cc9c9dd74bda71aa523eb23367ba8
  probed_at: 2026-08-10T14:45:41.423035+00:00
  failing: []
---

# Gate 1 — a greenfield repository can be interviewed into a valid policy file

## Definition of done

Written as what **this gate can decide**, per `[FEAT-2026-0069/G2-CLOSE]`. The
wording deliberately does not say "the skill produces X" — that claim needs an
agent executing prose against an unseen tree, which no test here performs.

- `propose_policy_defaults` computes, from fixture repositories, a proposal per
  derivable value carrying the evidence it came from, and proposes **nothing**
  where the evidence is absent.
- Every value it proposes validates clean against `validate_agent_policy`.
- The `derive-agent-policy` skill exists canonically in `plugins/`, is vendored
  and discovery-linked, and its prose describes that algorithm — asserted by a
  structural test naming the real API as exact literals.
- The disjoint-key boundary is stated in **both** `derive-agent-policy` and
  `/groom-backlog`, and a test fails if either widens into the other's keys.
- Every implementation work unit in this gate is `done`.
- The closing sequence has run: `close-intermediate`, then `plan-next` drafting
  gate 2 against what gate 1 actually learned.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## What this gate explicitly does NOT prove

**That an agent following the skill's prose reproduces the algorithm's output on
a repository it has not seen.** That is the deferral fixed in `PLAN.md` §
*The oracle problem*, and its re-run condition is one operator invocation against
this repository's own `.specfuse/agent-policy.yml`.

Stated here, not only in the close, because a gate whose definition of done is
read six weeks later should carry its own limits.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe (§4).** No work unit flips a default value or a severity. T01
  adds a new module and T02/T03 add prose; nothing changes an existing
  threshold, so there is no default to probe against.
- **Flag-scope table (§3).** No behavior flag is introduced or gated on.
- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`: no new
  rule. The inverse property — every proposal validates clean — is T01's, and
  T01 asserts it directly.

## The gate-2 arming checkpoint

This feature runs `autonomy_default: review` (operator decision 4) **because of
this checkpoint**. When gate 1 completes, read `GATE-02-REVIEW.md` before
arming: gate 1's retrospective is meant to answer the open question `PLAN.md`
leaves for gate 2 — how review distinguishes an agent-chosen default from a
deliberate operator choice — and that answer should come from how many values
gate 1 found derivable, not from a guess made before the evidence existed.

Arming gate 2 without that read would skip the checkpoint the two-gate staging
exists to create.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in
the drafted gate 2 and why, anything the retrospective got wrong. This is your
record, not the agent's — keep it honest.>
