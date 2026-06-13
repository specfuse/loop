---
id: FEAT-2026-0015/G1-DOCS
type: docs
effort: low
status: done
attempts: 1
planned_cost_usd: 0.30
duration_seconds: 141.179
cost_usd: 0.491994
input_tokens: 18
output_tokens: 7035
---

# Gate 1 docs

**Objective.** Reconcile docs that mention the closing-WU contract
with the new shapes Gate 1 introduced (`close-intermediate` type,
extended `close`).

**Context.** Correlation ID `FEAT-2026-0015/G1-DOCS`. Gate 1's T03
already updated `.specfuse/templates/*` and the `/draft-feature`
skill — those are PRODUCTION surfaces and out of this WU's scope.
G1-DOCS handles the remaining doc + reference surfaces. Reference
binding rules under `.specfuse/rules/`.

**Acceptance criteria.**

1. Audit and update the following surfaces for the new closing-shape
   lexicon (only edit those that actually mention closing-WU types
   today):
   - `.specfuse/rules/correlation-ids.md` (if it enumerates G<n>-RETRO
     / LESSONS / DOCS / PLAN / CLOSE patterns — add
     `G<n>-CLOSE-INTERMEDIATE` to the documented set).
   - `.claude/CLAUDE.md` / repo README (if either describes the
     closing-WU shape; add a one-paragraph note about the new shapes
     + link to FEAT-2026-0015 retrospective).
   - `docs/methodology.md` if present (likely the canonical
     methodology doc; would mention the 4-WU pattern explicitly).
   - The `.specfuse/skills/authoring-work-units/SKILL.md` §sizing
     guidance — if it currently quotes "the four-WU closing sequence
     plus the substantive WUs," update to reflect the 2-or-1-WU
     closing depending on gate position.
   - The `.specfuse/skills/arm-gate/SKILL.md` — currently expects to
     walk gate-N+1 drafts after gate N's plan-next. The flow stays
     valid (plan-next still drafts the next gate); minor wording
     updates likely needed where it enumerates "the four closing-
     sequence units."
2. NO new docs created — only existing surfaces edited. List every
   modified file in the RESULT block's `files_changed`.
3. If a surface does NOT mention closing-WU types today, leave it
   alone. Don't fabricate doc updates for the sake of "having
   touched docs."

**Do not touch.** Source code (`loop.py`, `lint_plan.py`),
templates (T03 owned), `/draft-feature` skill (T03 owned), other
WU files, generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(file exists / something changed).

**Escalation triggers.**

1. **No doc surface mentions closing-WU types.** If grep across the
   repo for `four-WU\|4-WU\|G1-RETRO\|G1-LESSONS\|G1-DOCS\|G1-PLAN`
   returns ONLY hits in files this WU is "Do not touch" against,
   emit `status: complete` with files_changed: [] and explain in
   the RESULT block that the doc-reconcile surface was empty —
   that's a legitimate outcome.
2. **Helper-duplication.** Per authoring-work-units §10: if the
   audit reveals MULTIPLE files independently describing the
   closing-WU contract with different phrasings, name them all
   in the RESULT block; recommend a follow-on doc-consolidation WU
   if the divergence is large.
