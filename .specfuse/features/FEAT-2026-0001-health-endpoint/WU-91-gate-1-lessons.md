---
id: FEAT-2026-0001/G1-LESSONS
type: lessons
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Gate 1 lessons learned

**Objective.** Promote the generalizable subset of the retrospective into durable
entries appended to `.specfuse/LEARNINGS.md` (the root, cross-feature file).

**Context.** Read this feature's `RETROSPECTIVE.md`. `LEARNINGS.md` is read at planning
time for every future feature — this is the pump that turns one feature's experience
into better plans for the next. Append only; de-duplicate against existing entries.

**Acceptance criteria.** New entries appended to the root `LEARNINGS.md`, each phrased
as a reusable rule that would change how a future WU is written or executed (e.g.
"implementation WUs must name the module a route lives in"), tagged with this gate's
ID. Feature-specific observations stay in `RETROSPECTIVE.md` and are NOT promoted.

**Do not touch.** Source code, existing LEARNINGS.md entries (append only), the
retrospective.

**Verification.** The `doc` gates.

**Escalation triggers.** If nothing generalizes beyond this feature, append nothing and
say why in the RESULT block. Promoting noise is worse than promoting nothing.
