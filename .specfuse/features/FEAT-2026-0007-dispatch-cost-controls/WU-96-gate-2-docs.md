---
id: FEAT-2026-0007/G2-DOCS
type: docs
model: claude-sonnet-4-6
effort: low
status: pending
attempts: 0
---

# Gate 2 documentation update

**Objective.** Reconcile project documentation and roadmap status with what
Gate 2 actually delivered.

**Context.** Read the Gate 2 commits and `RETROSPECTIVE.md`'s Gate 2
section. Update the repo's user/dev docs and this feature's row in
`.specfuse/roadmap.md`. Surfaces likely needing updates:

- `WU.template.md` — `model:` and `effort:` field notes (now optional with
  type-keyed defaults per T06).
- `GATE.template.md` — `cost_budget_usd:` documentation per T07.
- `.specfuse/skills/authoring-work-units/SKILL.md` — Haiku policy section
  added by T06 may need cross-references.
- `.specfuse/skills/gate-status/SKILL.md` — the new `cache_hit_rate`,
  `resolved_model`, and budget fields it can now surface.
- `README.md` — only if any user-facing CLI surface changed.

**Acceptance criteria.**
1. Docs describe the delivered behavior (not the planned behavior where
   they diverged — T08H is the obvious place this matters: docs should
   describe the retry ladder *as it actually exists in code after T08H*,
   not as T04 described it).
2. The roadmap reflects Gate 2's completion.
3. If T07's budget brake landed but its halt-during-closing semantics
   ended up different from the spec (Escalation trigger 3 in WU-07
   anticipated this), docs explain the actual behavior, not the
   prescribed behavior.

**Do not touch.** Source behavior — this unit documents, it does not
change code. Generated directories, secrets, `.git/`.

**Verification.** The `doc` gates.

**Escalation triggers.** If a doc change implies a code change is needed,
raise it in the RESULT block rather than changing code here. Defer the
code fix to Gate 3 (if planned) or to a follow-up feature.
