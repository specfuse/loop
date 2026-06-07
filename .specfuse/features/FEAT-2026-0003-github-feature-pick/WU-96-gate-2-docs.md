---
id: FEAT-2026-0003/G2-DOCS
type: docs
model: claude-sonnet-4-6
status: draft
attempts: 0
---

# Gate 2 documentation update

**Objective.** Reconcile project documentation and roadmap status with what
gate 2 actually delivered: the `adopt_feature.py` scaffolding script and the
`adopt-feature` skill.

**Context.** Read the gate-2 commits and the gate-2 section of
`RETROSPECTIVE.md`. Update the repo's user/dev docs to describe the new
adopt-flow (how a human goes from a GitHub `specfuse:feature` issue to a
dispatchable loop feature folder), and update this feature's row in
`.specfuse/roadmap.md` to reflect gate 2's completion. The handoff brief
(`docs/handoff-github-feature-pick.md`) cross-references the discovery and
adopt steps — update its §3 if the as-built shape diverged from the planned
shape. The skill and the script are owned by gate-2 implementation WUs (T03,
T04) — do not re-edit them here; this unit reconciles surrounding docs only.

**Acceptance criteria.**
1. Docs (README sections, `docs/handoff-github-feature-pick.md`, any
   `.claude/CLAUDE.md` cross-reference) describe the delivered adopt-flow as
   shipped (not the planned shape where they diverged).
2. The feature's row in `.specfuse/roadmap.md` reflects gate 2's completion
   (e.g. status note updated to indicate gates 1 and 2 done).
3. Any doc change that implies a code change is needed is raised in the
   RESULT block (an escalation) rather than absorbed into code edits here.

**Do not touch.** Source behavior — `.specfuse/scripts/` (including
adopt_feature.py and gh_features.py), `.specfuse/skills/adopt-feature/SKILL.md`,
binding rules under `.specfuse/rules/`, templates under `.specfuse/templates/`,
generated directories, secrets, `.git/`. This unit documents; it does not
change code or skills.

**Verification.** The `doc` gates in `.specfuse/verification.yml`.

**Escalation triggers.** If a doc change implies a code change is needed
(e.g. the as-built CLI surface mismatches what the handoff brief promised),
raise it in the RESULT block rather than changing code here — a code change
is the next gate's WU or its own follow-up.
