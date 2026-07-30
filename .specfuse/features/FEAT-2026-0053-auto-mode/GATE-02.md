---
gate: 2
status: open
cost_budget_usd: 31.50
# Sum of G1-PLAN's seven drafted units ($25.50 — T05 $3.50, T06 $3.50, T07
# $3.00, T08 $2.50, T09 $2.50, G2-CLOSE-INTERMEDIATE $4.50, G2-PLAN $6.00) plus
# one re-attempt of the largest ($6.00, G2-PLAN) — the defensive-padding shape
# planning-discipline §5 recommends.
baseline:
  sha: b4d707a1c70bfee810f9b06c3dea5960f7c35809
  probed_at: 2026-07-30T22:10:33.041316+00:00
  failing: []
---

# Gate 2 — Live arming behind the dial

## Definition of done

Each criterion below names where it is verified, because gate 1's retrospective
found that 40% of its own definition-of-done asserted driver runtime behavior
the close could not observe.

- **An `auto` feature arms its next gate without a human when the predicate
  says `would_arm`, in exactly one bookkeeping commit** containing the
  draft→pending flips, the gate `awaiting_review → passed` flip, the appended
  events, and the accumulated `FEATURE-REVIEW.md`. *Verified by* T06 AC#2 and
  T08 AC#5 (single-commit changed-path assertions) — **in tests only on this
  feature**, which runs `review`; the first live arm belongs to a successor
  feature after this branch merges.
- **A revert point exists before every arm** — the tag
  `pre-arm/<feature-id>/gate-<N>` at the pre-arm HEAD, with a documented
  recovery procedure. *Verified by* T05 AC#3, T06 AC#2 and AC#7.
- **Every stop class parks at `awaiting_review` with the reason in the event,
  and escalation always overrides autonomy.** *Verified by* T06 AC#4 and AC#5.
- **The plan-next contract fields block an arm under `auto` only**, as a
  veto-only eighth predicate class, with the CLI lint and every non-`auto`
  feature unchanged. *Verified by* T07 AC#2–AC#6, and by the §4 runtime probe
  the human runs before arming this gate.
- **Every auto-armed gate's doubt reaches the PR read** via append-only
  `FEATURE-REVIEW.md` accumulation, with the doubt prose never becoming a
  predicate input. *Verified by* T08 AC#3, AC#4 and its Do-not-touch clause.
- **An unread gate cannot write a durable cross-feature rule** — under `auto`,
  lessons stage to `LEARNINGS-pending.md` and a closing WU touching
  `.specfuse/LEARNINGS.md` does not pass. *Verified by* T09 AC#2–AC#4. Inert on
  this feature, which runs `review`; that must be stated in the close, not
  glossed.
- **A retrospective exists; lessons promoted; docs and roadmap updated; gate 3's
  work units drafted and `GATE-03-REVIEW.md` written.** *Verified by*
  `G2-CLOSE-INTERMEDIATE` and `G2-PLAN`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`. The full detail, including the
census `G1-PLAN` already ran and what it does and does not substitute for, is
in `GATE-02-REVIEW.md`.

- **Runtime probe for a severity flip (§4) — mandatory, and not yet run.** T07
  flips the contract-field lint to blocking under `auto`. Apply the change
  locally, run the exact lint command over every feature folder in this repo,
  and paste the resulting finding list into `GATE-02-REVIEW.md`. The pre-flip
  census in that file is drafting evidence, not the probe: it was taken before
  the change existed, which is precisely the condition §4 refuses.
- **Escalation-predicate satisfiability (§2) — answered.** `WU-07`'s body
  answers it: zero on an input in its intended final state. Read the answer
  against the check set before accepting it.
- **Budget brake.** `cost_budget_usd: 31.50` is set in this file's frontmatter.
  Gate 2 is where gate 1's newly built mechanism gets exercised
  (`[FEAT-2026-0007/G2-LESSONS]`), so the brake interplay is live here.
- **First-firing check, carried forward from gate 1.** Confirm `events.jsonl`
  carries an `arm_predicate_evaluated` event for gate 1 and read its per-class
  verdicts. **Read `RETROSPECTIVE.md` Findings §1 before treating an absent
  event as a false claim** — the driver process that closed gate 1 predates
  T04's commit, so an absent event means re-run the driver, not escalate.
- **Do not cite this feature's own baseline as evidence.** Per
  `RETROSPECTIVE.md` Findings §2, `PLAN.baseline.json` for FEAT-2026-0053 is
  captured after its own gate-2 drafting and therefore already contains gate 2.
  A clean `drift_caps` verdict here measures nothing.

## Reflection notes

<Written by the human at review time.>
