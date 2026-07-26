---
gate: 2
status: open
cost_budget_usd: 22.0
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

**Substantive work units were drafted by gate 1's `plan-next`** (`FEAT-2026-0069/G1-PLAN`),
not authored here. Four of them, all `status: draft` until the human arms them:

| WU | what it does | planned |
|---|---|---|
| `T05` | decides `invariant`'s `targets` position (reject) and corrects the stale `_check_targets` docstring | $2.00 |
| `T06` | re-keys `discover_components` onto deployment evidence; migrates the Stack A/B pattern tables | $4.00 |
| `T07` | the N-trigger fixture + per-schedule `heartbeat` targets — this gate's falsifiable core | $3.50 |
| `T08` | the `derive-monitoring` skill's Step 1 / Seams prose, canonical copy then synced | $2.50 |

`GATE-02-REVIEW.md` is the arming document: what gate 1 shipped, what changed from the
sketch and why, the §10 symbol enumeration, the runtime-probe failure list, and the open
questions to decide before flipping any WU to `pending`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate carries a `cost_budget_usd` deliberately, so a re-key that turns out to cascade
through fixtures halts to `awaiting_review` between WUs rather than spending the feature's
remaining budget unattended. The brake applies to closing WUs too — if it fires after the
last substantive WU, the close halts and the reviewer either flips this gate back to `open`
and pays the remainder, or writes the retrospective manually.

**Revised $18.00 → $22.00 at `G1-PLAN`, now that gate 1's actual spend is known.** The
drafted WUs sum to $17.00 ($12.00 substantive + $5.00 for `G2-CLOSE`), so an $18.00 ceiling
is 6% of headroom over the plan — a brake that fires by construction on the terminal close,
which is exactly the failure `planning-discipline.md` §5 names for a budget set to the sum
of its own estimates. Gate 1's evidence: its substantive WUs came in at $11.94 against
$11.00, and its `close-intermediate` alone cost $10.01 against a $5.00 estimate across two
attempts. $22.00 carries the $17.00 plan plus roughly one full re-attempt of the largest
WU, and still stops a runaway well short of the feature's remaining budget.

## Reflection notes

<Written by the human at review time.>
