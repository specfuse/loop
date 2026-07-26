---
gate: 2
status: open
cost_budget_usd: 18.0
---

# Gate 2 — discovery emits one component with N targets, not N components

## Definition of done

- `/derive-monitoring`, run against a repo whose single deployable carries N triggers,
  emits **1 component with N targets** — not N components.
- `discover_components` keys on *deployment* evidence (Helm chart, compose service,
  Dockerfile); trigger registrations are evidence of a component's `type`, never
  components themselves.
- A fixture exists whose one deployable contains N triggers — the shape 0039's Stack A
  fixture structurally could not express, and the reason this bug survived a passing
  gate.
- Target lists are generated mechanically from trigger evidence, with no operator
  question added.
- The `derive-monitoring` skill's method prose matches what the reference
  implementation actually does, canonical copy first and propagated by
  `scripts/sync-scaffold.sh`.
- Every implementation work unit in this gate is `done`, and the terminal close has run.

**Substantive work units are drafted by gate 1's `plan-next`**, not authored here. The
`G2-CLOSE` entry in `PLAN.md`'s graph is scaffolded so the linter reads this gate as
non-empty and gate 1 as non-terminal; `plan-next` inserts the real WUs above it and sets
its `depends_on`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate carries a `cost_budget_usd` deliberately. Gate 1 sketches gate 2 at ~$13; the
ceiling is set at $18 so a re-key that turns out to cascade through fixtures halts to
`awaiting_review` between WUs rather than spending the feature's remaining budget
unattended. The brake applies to closing WUs too — if it fires after the last
substantive WU, the close halts and the reviewer either flips this gate back to `open`
and pays the remainder, or writes the retrospective manually.

## Reflection notes

<Written by the human at review time.>
</content>
