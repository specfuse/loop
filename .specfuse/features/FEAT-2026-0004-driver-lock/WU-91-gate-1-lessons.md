---
id: FEAT-2026-0004/G1-LESSONS
type: lessons
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.21987
input_tokens: 8
output_tokens: 4754
---

# Gate 1 lessons learned

**Objective.** Promote the generalizable subset of the retrospective into durable
entries appended to `.specfuse/LEARNINGS.md`.

**Context.** Read this feature's `RETROSPECTIVE.md`. Append only; de-duplicate
against existing entries. A likely durable lesson: the driver's git operations
are tree-global, so concurrency control belongs at the working-tree level, and
process-death-safe locking (flock) beats pidfiles for the SIGKILL case.

**Acceptance criteria.** New entries appended to the root `LEARNINGS.md`, each a
reusable rule that would change how a future WU is written or executed, tagged
`FEAT-2026-0004/G1-LESSONS`. Feature-specific noise stays in `RETROSPECTIVE.md`.

**Do not touch.** Source code, existing LEARNINGS.md entries (append only), the
retrospective.

**Verification.** The `doc` gates.

**Escalation triggers.** If nothing generalizes beyond this feature, append
nothing and say why.
</content>
