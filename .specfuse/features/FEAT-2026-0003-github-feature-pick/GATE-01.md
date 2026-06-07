---
gate: 1
status: awaiting_review
---

# Gate 1 — The read path: orchestrated ID grammar + GitHub feature discovery

## Definition of done

- The loop's correlation-ID grammar admits orchestrated `INIT-YYYY-NNNN/FNN`
  feature-level IDs and `INIT-YYYY-NNNN/FNN/(TNN[H…]|G<n>-…)` task-level IDs,
  alongside the existing `FEAT-…` grammar — in both the rule
  (`.specfuse/rules/correlation-ids.md`) and the linter (`lint_plan.py`), with
  tests proving admission and rejection (`FEAT-2026-0003/T01`).
- A discovery script (`.specfuse/scripts/gh_features.py`) lists a target repo's
  open `specfuse:feature` issues as feature candidates — id, initiative, type,
  autonomy, url — with an injectable runner so it is unit-tested without a live
  `gh` call (`FEAT-2026-0003/T02`).
- A retrospective exists; generalizable lessons are promoted to
  `.specfuse/LEARNINGS.md`; docs and roadmap reflect what shipped; gate 2's WUs
  are drafted and `GATE-02-REVIEW.md` is written.

The closing sequence (retrospective → lessons → docs → plan-next) is part of
every gate and is enforced by the linter. The driver runs the gate unattended,
then stops here for human review-and-arm: read `GATE-02-REVIEW.md`, accept or
edit the drafted gate-2 work units, flip the accepted ones to `pending`, set
this gate's status to `passed`, and re-run.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in
the drafted gate 2 and why, anything the retrospective got wrong.>
</content>
