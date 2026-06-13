---
id: FEAT-2026-0015/T03
type: implementation
model: claude-sonnet-4-6
effort: low
status: pending
attempts: 0
planned_cost_usd: 0.50
---

# Update templates and `/draft-feature` skill to emit new closing shapes

**Objective.** Make the new closing-shape lexicon (per T01 + T02) the
DEFAULT for newly drafted features. Update PLAN.md and WU.md
templates + the `/draft-feature` skill so operators don't have to
remember to migrate.

**Context.** This is `FEAT-2026-0015/T03`. Depends on T01 (new
type registered in driver) and T02 (lint accepts new shapes).

`/draft-feature` skill currently (per `.specfuse/skills/draft-feature/SKILL.md`)
generates 4-WU closing sequences mechanically per gate. The skill's
§5 says "for the four-WU sequence, generate `G1-RETRO`, `G1-LESSONS`,
`G1-DOCS`, `G1-PLAN` mechanically — IDs, file names, types, and
models follow the template. For a single-gate feature where the
`close` alternative was proposed in step 4, generate a single
`G1-CLOSE` WU instead."

New default per FEAT-2026-0015:
- Non-terminal gate: 2-WU (`close-intermediate → plan-next`).
- Terminal gate (any feature shape): 1-WU (`close`).

`.specfuse/templates/PLAN.template.md`'s gates graph example uses
the legacy 4-WU sequence. `.specfuse/templates/WU.template.md`'s
frontmatter notes enumerate WU types and need `close-intermediate`
added.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. `.specfuse/templates/PLAN.template.md` gates graph example uses
   the new 2-WU intermediate + 1-WU terminal default for a 2-gate
   feature:
   - Gate 1 (non-terminal): T01, T02, then `G1-CLOSE-INTERMEDIATE`
     (file `WU-90-gate-1-close-intermediate.md`, type
     `close-intermediate`), then `G1-PLAN` (file
     `WU-91-gate-1-plan-next.md`, type `plan-next`).
   - Gate 2 (terminal): `work_units: []` (drafted by G1-PLAN).
   - Comment near the gates graph explains the closing shape choice
     and points at FEAT-2026-0015 retrospective for context.
2. `.specfuse/templates/WU.template.md` frontmatter notes list
   `close-intermediate` alongside other valid WU types in the
   `type` field documentation. Explanation: "for non-terminal
   gates, folds RETRO+LESSONS+DOCS into one session; `plan-next`
   stays separate. For terminal gates use `close`."
3. `.specfuse/skills/draft-feature/SKILL.md` §5 rewritten:
   - For non-terminal gate: generate 2-WU (close-intermediate +
     plan-next) by default. Closing WU IDs use
     `G<n>-CLOSE-INTERMEDIATE` and `G<n>-PLAN`.
   - For terminal gate (or single-gate feature): generate single
     `close` WU. ID `G<n>-CLOSE`.
   - The legacy 4-WU generation pattern is removed from the default
     path. A "Legacy: 4-WU sequence" subsection at the end of §5
     documents the OLD pattern for operators migrating in-flight
     features; lint warns when used.
4. New tests in `tests/test_template_closing_shapes.py`:
   - `test_plan_template_uses_2wu_intermediate_for_gate_1`
   - `test_plan_template_uses_1wu_close_for_terminal_gate`
   - `test_wu_template_lists_close_intermediate_in_frontmatter_notes`
5. `.specfuse/scripts/lint_plan.py` (run from this WU's
   verification) accepts the updated `PLAN.template.md` example
   without warnings (template MUST exemplify the new contract, not
   the legacy one).
6. Symbol/string existence checks:
   - `grep -c "close-intermediate" .specfuse/templates/PLAN.template.md`
     ≥ 1.
   - `grep -c "close-intermediate" .specfuse/templates/WU.template.md`
     ≥ 1.
   - `grep -c "close-intermediate" .specfuse/skills/draft-feature/SKILL.md`
     ≥ 2 (at least one in §5 and one in the legacy-pattern
     subsection).

**Do not touch.** Exactly 4 files change:
- `.specfuse/templates/PLAN.template.md`
- `.specfuse/templates/WU.template.md`
- `.specfuse/skills/draft-feature/SKILL.md`
- `tests/test_template_closing_shapes.py` (new file)

No edits to: `loop.py` (T01 owns), `lint_plan.py` (T02 owns), other
skills (T06 in Gate 2 will touch `/wrap-feature`), production WUs
under `.specfuse/features/`, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
must pass. Plus AC5 — `lint_plan.py` against the updated PLAN
template (run on a synthesized feature folder that uses the template
verbatim). Plus AC6 grep checks.

**Escalation triggers.**

1. **Template self-consistency.** If `PLAN.template.md`'s example
   gates graph contradicts the WU types `WU.template.md`
   documents, emit `status: blocked` — the templates must agree.
2. **Lint divergence.** If the updated `PLAN.template.md` example
   fires a lint warning or error after T02's changes are present,
   emit `status: blocked` — the templates must exemplify the
   accepted-without-warning path.
3. **Helper-duplication.** Per authoring-work-units §10: before
   editing `/draft-feature` skill, run
   `grep -rn "G1-RETRO\|G1-LESSONS\|G1-DOCS\|G1-PLAN\|G1-CLOSE" .specfuse/`
   to find every other skill / rule / template that mentions
   closing-WU IDs. If any other skill (especially
   `/authoring-work-units` or `/arm-gate`) needs corresponding
   updates, list them in the WU's RESULT block as out-of-scope
   for this WU and recommend a follow-on hygiene WU. Do NOT silently
   edit them — different WU.
