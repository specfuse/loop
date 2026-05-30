---
id: FEAT-YYYY-NNNN/T01
type: implementation        # implementation | retrospective | lessons | docs | plan-next
model: claude-opus-4-7      # opus for foundational/forward-design; sonnet for mechanical/synthesis
status: pending             # draft | pending | ready | in_progress | in_review | done | blocked_human
attempts: 0
---

# <imperative title, e.g. "Add health-check endpoint">

This whole body below the frontmatter is what a fresh `claude -p` session receives.
Write it so a session with no memory can execute it from this file alone. The five
sections are mandatory — the linter rejects a dispatchable WU that is missing any.

**Objective.** One sentence: what this unit produces.

**Context.** What this is part of, the correlation ID, and the specs/files that
ground it. Enough for a cold session to orient. Reference the binding rules in
`.specfuse/rules/` and the verification skill rather than restating them.

**Acceptance criteria.** Explicit, testable statements of done. Write them so the
verification gates — and a reviewer — can judge them objectively.

**Do not touch.** Generated directories (`_generated/`, `gen-src/`), files owned by
other work units, secrets, branch protection, `.git/`. The driver owns all git
operations — you edit files only.

**Verification.** The gates that must pass. For `implementation` units these are the
`code` gates in `.specfuse/verification.yml` (tests, coverage ≥ 90%, zero warnings,
lint, security scan). Name anything unit-specific.

**Escalation triggers.** Conditions under which you stop and emit `status: blocked`
in the RESULT block rather than pushing through (spec ambiguity, a required override
of generated code, a missing dependency). Blocked is a respectable outcome.
