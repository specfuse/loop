---
id: FEAT-2026-0003/G1-DOCS
type: docs
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Gate 1 documentation update

**Objective.** Reconcile project documentation and roadmap status with what gate 1
actually delivered.

**Context.** Read the gate's commits and `RETROSPECTIVE.md`. Update the repo's
user/dev docs to describe the new orchestrated-ID grammar and the discovery script,
and update this feature's row in `.specfuse/roadmap.md` to reflect gate 1's
completion. The correlation-ID rule itself is owned by T01 — do not re-edit it here;
this unit reconciles surrounding docs (README/handoff cross-references, roadmap).

**Acceptance criteria.** Docs describe the delivered behavior (not the planned
behavior where they diverged); the roadmap reflects gate 1's completion.

**Do not touch.** Source behavior — this unit documents, it does not change code.
`lint_plan.py`, `gh_features.py`, `correlation-ids.md` (owned by gate-1
implementation WUs), generated directories, secrets, `.git/`.

**Verification.** The `doc` gates.

**Escalation triggers.** If a doc change implies a code change is needed, raise it in
the RESULT block rather than changing code here.
</content>
