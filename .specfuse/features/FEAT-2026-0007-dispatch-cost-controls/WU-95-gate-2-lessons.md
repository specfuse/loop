---
id: FEAT-2026-0007/G2-LESSONS
type: lessons
model: claude-sonnet-4-6
effort: low
status: pending
attempts: 0
---

# Gate 2 lessons learned

**Objective.** Promote the generalizable subset of Gate 2's retrospective
into durable entries appended to `.specfuse/LEARNINGS.md` (the root,
cross-feature file).

**Context.** Read this feature's `RETROSPECTIVE.md` Gate 2 section.
`LEARNINGS.md` is read at planning time for every future feature — this
is the pump that turns one feature's experience into better plans for the
next. Append only; de-duplicate against existing entries. Tag each entry
with `[FEAT-2026-0007/G2-LESSONS]`.

**Acceptance criteria.**
1. New entries appended to the root `LEARNINGS.md`, each phrased as a
   reusable rule that would change how a future WU is written or executed
   (e.g. "defaults-by-type should be authored as a single tuple per type;
   splitting model and effort across tables invites drift").
2. Feature-specific observations stay in `RETROSPECTIVE.md` and are
   **not** promoted.
3. Specific candidates the retrospective likely surfaces (only promote
   what actually emerged):
   - Whether `T08H`'s presence (the corrective hygiene WU for a prior
     gate's silent failure) generalizes — i.e. should the methodology
     formalize "if a `status: done` WU's symbols don't import, the next
     gate's plan-next must insert a hygiene WU"?
   - Whether the budget brake's halt-between-WU semantics survived
     contact with the closing sequence cleanly.
   - Whether the cache_hit_rate denominator chosen in T08 matched
     observable reality once telemetry was real.

**Do not touch.** Source code, existing `LEARNINGS.md` entries (append
only), the retrospective.

**Verification.** The `doc` gates.

**Escalation triggers.** If nothing generalizes beyond this feature,
append nothing and say why in the RESULT block. Promoting noise is worse
than promoting nothing.
