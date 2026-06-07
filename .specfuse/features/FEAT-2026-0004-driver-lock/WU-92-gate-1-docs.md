---
id: FEAT-2026-0004/G1-DOCS
type: docs
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Gate 1 documentation update

**Objective.** Reconcile docs and roadmap status with what gate 1 delivered (the
working-tree lock + gitignore handling).

**Context.** Read the gate's commits and `RETROSPECTIVE.md`. Update this feature's
row/section in `.specfuse/roadmap.md` to reflect completion. If any user/dev doc
describes running the driver, note the single-driver-per-working-tree constraint
and that parallel features use separate git worktrees.

**Acceptance criteria.** Docs describe the delivered behaviour (lock + gitignore);
the roadmap reflects gate 1's completion.

**Do not touch.** Source behaviour — this unit documents, it does not change code.
`loop.py`, `init.sh` (owned by T01), generated directories, secrets, `.git/`.

**Verification.** The `doc` gates.

**Escalation triggers.** If a doc change implies a code change is needed, raise it
in the RESULT block rather than changing code here.
</content>
