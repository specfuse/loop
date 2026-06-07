---
id: FEAT-2026-0003/G4-LESSONS
type: lessons
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.356704
input_tokens: 8
output_tokens: 6902
---

# Gate 4 lessons learned

**Objective.** Promote the generalizable subset of the gate-4 retrospective into
durable entries appended to `.specfuse/LEARNINGS.md`.

**Context.** Read this feature's `RETROSPECTIVE.md` (gate-4 section). The most likely
durable lesson here is cross-surface contract hygiene: a live smoke caught a
format-contract mismatch (ATX vs bold headings) that offline tests could not. Append
only; de-duplicate against existing entries.

**Acceptance criteria.** New entries appended to the root `LEARNINGS.md`, each a
reusable rule that would change how a future WU is written or executed, tagged with
`FEAT-2026-0003/G4-LESSONS`. Feature-specific noise stays in `RETROSPECTIVE.md`.

**Do not touch.** Source code, existing LEARNINGS.md entries (append only), the
retrospective.

**Verification.** The `doc` gates.

**Escalation triggers.** If nothing generalizes beyond this feature, append nothing and
say why. Promoting noise is worse than promoting nothing.
</content>
