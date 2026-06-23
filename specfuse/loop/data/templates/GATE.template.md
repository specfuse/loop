---
gate: 1
status: open        # open | awaiting_review | passed
# cost_budget_usd: 5.0   # optional cumulative-cost ceiling (USD).
# When the sum of `cost_usd` across this gate's done WUs reaches the ceiling,
# the loop halts to `awaiting_review` between WUs — the current WU always runs
# to a terminal outcome first; the brake fires before the next WU's dispatch.
# Applies to ALL WU types including closing-sequence WUs (retrospective, lessons,
# docs, plan-next): if the budget is exceeded after the last substantive WU, the
# closing sequence halts and the gate ends without a retrospective. The reviewer
# can flip the gate back to `open` and pay the remaining cost, or write the
# retrospective manually. Mirrors MAX_ATTEMPTS' shape, per-gate instead of
# per-WU. The implementing gate's own GATE.md intentionally omits this field;
# set it in the successor gate to exercise the brake for the first time.
---

# Gate 1 — <name of the milestone this gate proves>

## Definition of done

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- The next gate's work units are drafted, and `GATE-NN-REVIEW.md` is written.

The closing sequence (retrospective → lessons → docs → plan-next) is part of every
gate and is enforced by the linter. The driver runs the gate unattended, then stops
here for human review-and-arm: read the review artifact, accept or edit the drafted
next-gate work units, flip the accepted ones to `pending`, set this gate's status to
`passed`, and re-run.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
