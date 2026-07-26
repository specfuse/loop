---
gate: 2
status: passed
cost_budget_usd: 26.0
baseline:
  sha: 6f9ff547fb77ba372a83e7e2feaca7c138f273b3
  probed_at: 2026-07-26T20:00:44.036037+00:00
  failing: []
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
not authored here. All four were reviewed and **armed unmodified on 2026-07-26**; the
terminal close was armed in the same pass. See `GATE-01.md`'s *Reflection notes* for what
was checked and what was corrected before arming.

| WU | what it does | planned |
|---|---|---|
| `T05` | decides `invariant`'s `targets` position (reject) and corrects the stale `_check_targets` docstring | $2.00 |
| `T06` | re-keys `discover_components` onto deployment evidence; migrates the Stack A/B pattern tables | $4.00 |
| `T07` | the N-trigger fixture + per-schedule `heartbeat` targets — this gate's falsifiable core | $3.50 |
| `T08` | the `derive-monitoring` skill's Step 1 / Seams prose, canonical copy then synced | $2.50 |
| `G2-CLOSE` | terminal close; carries the mandatory `## Planning-floor revision` section (AC3) | $8.00 |

`GATE-02-REVIEW.md` is the arming document: what gate 1 shipped, what changed from the
sketch and why, the §10 symbol enumeration, the runtime-probe failure list, and the open
questions to decide before flipping any WU to `pending`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate carries a `cost_budget_usd` deliberately, so a re-key that turns out to cascade
through fixtures halts to `awaiting_review` between WUs rather than spending the feature's
remaining budget unattended. The brake applies to closing WUs too — if it fires after the
last substantive WU, the close halts and the reviewer either flips this gate back to `open`
and pays the remainder, or writes the retrospective manually.

**Revised again at arming: $22.00 → $26.00, and `G2-CLOSE`'s estimate $5.00 → $8.00.**
`G1-PLAN` set $22.00 against a $17.00 plan whose close carried the §5 flat $5.00 floor.
That floor is the thing gate 1 disproved — its own `close-intermediate` cost **$10.01**
and its `plan-next` **$16.44**, both against $5.00 — so a budget built on it inherits the
error. `[FEAT-2026-0069/GATE-1-ARM]` in `.specfuse/LEARNINGS.md` (and issue #260) set the
corrected drafting floors at **$8.00** for `close` / `close-intermediate`; `G2-CLOSE` now
carries that figure.

The ceiling follows the rule that entry states — **sum of estimates plus one re-attempt of
the gate's largest WU**: $20.00 planned ($12.00 substantive + $8.00 close) + $6.00 ≈
**$26.00**. At the old $22.00 against a corrected $20.00 plan there was $2.00 of headroom,
less than one re-attempt of `T06` ($4.00, and the WU `G1-PLAN` judged most likely to need
a second pass) — a brake that fires on ordinary variance rather than on a runaway. $26.00
still halts well short of the feature's remaining budget.

This is a **prospective** correction to a WU that has not run, not a re-baseline of a plan
onto its own overrun — `PLAN.md`'s $34.00 stays untouched, and the widened lint cost-delta
WARN is the signal, not something to silence.

## Reflection notes

<Written by the human at review time.>
