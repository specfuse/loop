---
gate: 3
status: open
cost_budget_usd: 22.00
# Sum of G2-PLAN's five drafted units ($17.00 — T10 $3.00, T11 $3.00, T12
# $3.00, T13 $3.00, G3-CLOSE $5.00) plus one re-attempt of the largest ($5.00,
# G3-CLOSE) — the defensive-padding shape planning-discipline §5 recommends.
# Note the brake is evaluated BEFORE each WU dispatch, so an overrun inside the
# last WU is structurally invisible to it; gate 2 landed ~$2.3 over its declared
# budget without the brake firing.
---

# Gate 3 — Terminal: docs, methodology, and the honest close

## Definition of done

Each criterion names where it is verified. Gate 1's retrospective found 40% of
its own definition-of-done asserting driver runtime behavior its close could not
observe; gate 3's exposure is different but real — three of its four substantive
units deliver **prose**, and a green test suite proves the mirrored copies match
and nothing regressed, not that the prose is correct.

- **`docs/methodology.md` §9 describes the autonomy dial the run loop actually
  implements**, including the two claims in the old §9 that were never built
  (the per-gate tightening-only override; `supervised` as a level distinct from
  `review`), recorded as unbuilt rather than deleted. *Verified by* T10 AC#1–#4
  mechanically, and by **the human at PR review** for correctness of the prose.
- **An auto-arm is described once, in the methodology, and its recovery
  procedure stays in `docs/dev/auto-arm-recovery.md`** — concept and procedure
  in one home each. *Verified by* T10 AC#5 and AC#7.
- **A parked `auto` feature is diagnosable from documentation alone**: all eight
  stop classes, their three statuses, the v1 constants, the clearing action per
  class, and how to read an `arm_predicate_evaluated` event without
  misattributing an escalation-site emission. *Verified by* T11 AC#1–#5. **The
  clearing actions are the load-bearing part** — a reference that describes the
  classes without saying what to do is the failure mode this gate exists to
  avoid.
- **An operator can adopt `auto` without reading source**: the artifact
  inventory, the three consumer-breakage items gate 2 flagged for
  acknowledgment, the mid-life baseline hazard, and an executable opt-in
  procedure with both back-out paths. *Verified by* T12 AC#1–#5.
- **Both new pages ship to downstream projects.** *Verified by* T11 AC#7 and
  T12 AC#7 — registration in `DOCS_TRACKED` is part of the deliverable, not a
  follow-up; an unregistered page is invisible to the scaffold drift guard.
- **`FEATURE-REVIEW.md` and `LEARNINGS-pending.md` reach the human at PR
  review.** *Verified by* T13 AC#1–#5 in the skill text, and **only in prose** —
  the real oracle is the first `auto` feature's PR. Stated here rather than
  hidden behind a green suite. Inert if T13 is rejected at arming.
- **A terminal close re-runs every oracle fresh, enumerates consumer-visible
  contract changes across all three gates, enumerates what the loop did not
  verify, and states a feature-arc verdict that is honest about no feature
  having ridden `auto` in production.** *Verified by* `G3-CLOSE`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 3's WUs to `pending`. Full detail in `GATE-03-REVIEW.md`.

- **No §4 runtime probe is required, and that is a finding, not an omission.**
  §4 binds a gate whose WUs flip a **default value** or a **severity**. Gate 3
  flips neither: T10–T12 are documentation and T13 changes a skill's prose. The
  §4 precondition that blocked gate 2's arming does not apply here. Confirm that
  reading before accepting it — if any drafted WU turns out to change a default
  or a severity, the probe becomes mandatory and this line is wrong.
- **Escalation-predicate satisfiability (§2) — not applicable.** Gate 3
  introduces no severity flip and asserts no "zero issues" close predicate.
  Gate 1's PLAN.md answered this for gate 1 and required gate 2 to answer it
  again; gate 3's answer is that there is nothing to answer, which is a
  different statement from silence.
- **Flag-scope table (§3) — not applicable.** No gate-3 WU introduces, gates on,
  or flips a behavior flag. T13 changes behavior unconditionally on the presence
  of a file, not behind a dial.
- **Budget brake.** `cost_budget_usd: 22.00` is set in this file's frontmatter.
  Gate 2 consumed 75.4% of its brake before its closing pair ran and landed
  roughly $2.3 over; the brake did not fire because it is evaluated before each
  dispatch. Read gate 2's actuals before trusting this number.
- **T13 is `human_only: true` and is the one scope decision on this gate.** It
  widens PLAN.md's gate-3 scope boundary from documentation-only. Accept it,
  reject it, or defer it with a named home — but decide it explicitly. It
  strands nothing: T10, T11 and T12 do not depend on it.
- **The `judge_editing` class will fire on this gate's own drafted WUs, and the
  reason is a v1 path-prefix approximation, not a real hazard.** T10, T11 and
  T12 each `produce` a mirrored scaffold copy under
  `specfuse/loop/data/docs/`, which the predicate's `JUDGE_PATHS` prefix
  `specfuse/loop/` cannot distinguish from driver source. Detail and evidence in
  `GATE-03-REVIEW.md`; it costs nothing on this feature, which runs `review`,
  and it would park a successor feature running `auto` that ships any
  documentation.
- **Do not cite this feature's own baseline as evidence.** Carried forward from
  gate 2 and still true: `PLAN.baseline.json` for FEAT-2026-0053 was captured
  after its own gate-2 drafting, so it already contains gate 2. A clean
  `drift_caps` verdict here measures nothing.

## Reflection notes

<Written by the human at review time.>
