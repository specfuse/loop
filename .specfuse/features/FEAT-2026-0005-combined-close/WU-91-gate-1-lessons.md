---
id: FEAT-2026-0005/G1-LESSONS
type: lessons
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Gate 1 lessons learned

**Objective.** Promote the generalizable subset of the retrospective into durable
entries appended to `.specfuse/LEARNINGS.md`.

**Context.** Read this feature's `RETROSPECTIVE.md`. Append only; de-duplicate against
existing entries. A likely durable lesson: ceremony weight should scale with gate
count — single-gate features warrant the collapsed `close`.

**Acceptance criteria.** New entries appended to the root `LEARNINGS.md`, each a reusable
rule, tagged `FEAT-2026-0005/G1-LESSONS`. Feature-specific noise stays in
`RETROSPECTIVE.md`.

**Do not touch.** Source code, existing LEARNINGS.md entries (append only), the
retrospective.

**Verification.** The `doc` gates.

**Escalation triggers.** If nothing generalizes beyond this feature, append nothing and
say why.
</content>
