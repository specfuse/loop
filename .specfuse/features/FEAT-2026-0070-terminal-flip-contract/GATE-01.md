---
gate: 1
status: awaiting_review
baseline:
  sha: aa20e4ad16572f8f8c71c5e56f802b2a2479663f
  probed_at: 2026-07-27T03:00:23.399212+00:00
  failing: []
---

# Gate 1 — a correctly-closed feature reaches `done` through the driver, from any legitimate starting state

## Definition of done

- A feature whose roadmap row is `planned` at terminal close reaches `done` — the
  `autonomy: auto` self-dispatch path no longer escalates `roadmap_row_not_done` on a
  correct close (#226).
- A completed close WU whose verdict has since been upgraded to `met` can have its
  terminal flips fired **by the driver**, without re-dispatching the WU.
- An operator can accept a standing `met_locally` verdict through
  `/accept-hedged-close`, leaving an auditable record of the reason and the accepted
  follow-up list — instead of hand-editing three surfaces with no trace (#243).
- `lint_plan` no longer fails a mid-dispatch close WU with a message about the wrong
  thing.
- **Terminal state still has exactly one driver-side writer.** Every path above routes
  through the same helper.
- Every implementation work unit is `done`; retrospective written, durable lessons
  promoted, gate 2 drafted, `GATE-02-REVIEW.md` written.

**What this gate deliberately does NOT do.** It does not stop a feature from *reaching*
`met_locally` (that is #243 candidate 3, held as a follow-up), and it does not touch
auto-close's skipped enumeration (#241, gate 2). It makes the dead end exitable; it does
not remove the dead end.

## The constraint that outranks the acceptance criteria

`[FEAT-2026-0023/G1-CLOSE]`: **terminal-state flips have exactly ONE driver-side owner,
called identically by every close path.** Issue #49 existed because two paths diverged.

T03 is a skill. If it writes `PLAN.md status`, the gate status, or the roadmap row
directly — rather than calling T02's primitive — it has rebuilt #49 with a friendlier
name. A WU that does this has failed even with every gate green, and the reviewer should
reject it at close regardless of its RESULT block.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for the severity flip (§4).** Gate 2's likely shape includes a
  post-pass invariant that escalates when a terminal close ignores an auto-closed
  predecessor's deferred-verification debt. That is a new blocking condition: apply it
  locally, run the **full** oracle (`python3 -m unittest discover -s tests -v`), and paste
  the failure list into `GATE-02-REVIEW.md`. Features in this repo that auto-closed a gate
  are the population it will fire on — confirm the count is finite and intended before
  arming, per §2.
- **Escalation-predicate satisfiability (§2).** Confirm what the new invariant reports on
  a tree already in its intended final state. If that answer is not zero, redesign before
  arming.
- **Closing-guard literal prediction.** `lint_plan`'s arm-time check (#269) now warns when
  a closing WU's body omits a literal its guard will demand. Read those warnings before
  arming rather than paying for them at dispatch.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
