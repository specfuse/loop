---
gate: 1
status: open        # open | awaiting_review | passed
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
