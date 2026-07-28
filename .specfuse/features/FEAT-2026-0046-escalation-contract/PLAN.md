---
feature_id: FEAT-2026-0046
title: Escalation contract — needs-human issues + /attention inbox
slug: escalation-contract
branch: feat/FEAT-2026-0046-escalation-contract
roadmap_goal: Give everything that needs a human one queue with an audit trail and one place to see it, so nothing the loop parks goes silent — a `needs-human` GitHub issue per escalation in a format a later agent can parse, and an `/attention` skill that sweeps repo state and that queue into one priority-ordered view.
autonomy_default: review
status: done
planned_cost_usd: 17.00
---

# Plan: Escalation contract — needs-human issues + /attention inbox

Today the loop halts and prints. A blocked work unit, a gate sitting at
`awaiting_review`, a feature blocked on an unmet dependency — each is visible only
to whoever happens to re-run the driver and read the terminal. There is no queue, no
audit trail, and no way to see across features at once. The operator's own check-in
ritual is a manual sweep, performed from memory.

This feature builds the queue and the view. An escalation becomes a `needs-human`
labelled GitHub issue, assigned, with a body in the six-part plain-English shape
`.specfuse/rules/operator-escalation.md` already makes binding, plus numbered answers
so a reply is unambiguous to parse. `/attention` is the local counterpart: it sweeps
`.specfuse/` state and that issue queue into one priority-ordered list.

**The queue is the source of truth; the skill is a view.** That split is the whole
design. `/attention` never writes state — a rule this feature proves with a test
rather than asserting in prose.

## Scope boundary

**IN.** The issue format as a machine-checkable contract (labels, assignment, the
six-part body, numbered answers) with a validator; a driver-side emission primitive
that is idempotent per correlation ID; the `/attention` skill; and a guard proving
the skill cannot write state.

**OUT, and each has a home.** Outbound webhook notification is
[FEAT-2026-0047](../../roadmap.md#feat-2026-0047). Parsing an answered issue and
acting on it is [FEAT-2026-0049](../../roadmap.md#feat-2026-0049) — the roadmap puts
that verb in the agent's mouth ("closed by the next agent run"), and 0049 lists this
feature as its blocker rather than the reverse, so the contract is the dependency and
not the consumer. Categorising inbound third-party issues is
[FEAT-2026-0045](../../roadmap.md#feat-2026-0045). The policy queue is
[FEAT-2026-0044](../../roadmap.md#feat-2026-0044).

**OUT by deliberate design: automatic emission from the dispatch loop.** The
primitive is invoked, never fired. `[FEAT-2026-0003/G3-LESSONS]` established that a
work unit mutating live GitHub issues is irreversible at execution time and must not
be delegated to the driver's subprocess loop; auto-emitting on every `blocked_human`
would put exactly that mutation inside the automatic path, and would file an issue
every time a work unit blocks during ordinary development. T02 asserts the absence of
such a call site.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rln "awaiting_review\|blocked_human" .specfuse/skills/*/SKILL.md` and
  `grep -rn "repo-wide\|repo state sweep\|inbox" .specfuse/skills/*/SKILL.md`
- **Verdict:** `no existing mechanism, building new` — with one reuse.

Eleven skills read `awaiting_review` / `blocked_human` (`gate-status`, `arm-gate`,
`unblock-wu`, `wrap-feature`, `abandon-feature`, `block-feature`, `pick-feature`,
`accept-hedged-close`, `draft-feature`, `feature-conversion`, `authoring-work-units`),
and the second grep returns nothing: **none performs a repo-wide sweep or presents an
inbox.** Every one of them is scoped to a single feature — usually the active one.

**Reusing `gate-status`.** Its description reads *"Report where the loop stands on
the active feature… synthesizes a structured diagnosis — what's blocked, likely root
cause, options, and a recommended next action. Read-only."* That is precisely the
per-feature diagnosis `/attention` needs, so `/attention` generalises it across
features and delegates the per-feature read rather than reimplementing it. Building a
second diagnosis engine is the duplication §1 exists to prevent.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero.

Two checks in this feature are predicate-shaped. `validate_escalation_body` (T01)
returns an empty findings list for a body rendered by `render_escalation_body`, which
is asserted directly — the renderer and the validator are held to each other, so a
conforming input reports nothing. The T04 non-writing guard greps `/attention`'s
SKILL.md for write-verb patterns and expects zero hits on the real skill; its positive
control proves the pattern is capable of firing, so a zero is evidence of cleanliness
rather than evidence of a dead regex.

## Task graph

```yaml
# Single terminal gate: 4 substantive WUs is at the ceiling of the ceremony
# proportionality rule (docs/methodology.md §6), so this feature uses one gate
# with a single terminal `close` — no close-intermediate, no plan-next.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0046/T01
        file: WU-01-escalation-issue-contract.md
        depends_on: []
      - id: FEAT-2026-0046/T02
        file: WU-02-emission-primitive.md
        depends_on: [FEAT-2026-0046/T01]
      - id: FEAT-2026-0046/T03
        file: WU-03-attention-skill.md
        depends_on: [FEAT-2026-0046/T01]
      - id: FEAT-2026-0046/T04
        file: WU-04-attention-nonwriting-guard.md
        depends_on: [FEAT-2026-0046/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0046/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0046/T01
          - FEAT-2026-0046/T02
          - FEAT-2026-0046/T03
          - FEAT-2026-0046/T04
```

T02 and T03 both depend on T01 and on nothing else, so they are independent of each
other: the contract module is the shared vocabulary, and the emitter and the viewer
consume it separately.

## Notes

- Skills are canonical in `plugins/specfuse/skills/` and vendored byte-for-byte into
  `.specfuse/skills/` by `scripts/sync-scaffold.sh`, guarded by
  `tests/test_skills_vendored_in_sync.py`. T03 writes both copies; editing only one
  fails the suite.
- No work unit in this gate touches a real GitHub issue. Every `gh` interaction runs
  through an injected runner, mirroring `gh_backend.GitHubBackend`'s existing
  `_runner` seam. The cost of that choice is that nothing here proves the real `gh`
  invocation works end to end; the close records it under
  `## What the loop did NOT verify` as an operator post-merge step rather than
  leaving it implied.
