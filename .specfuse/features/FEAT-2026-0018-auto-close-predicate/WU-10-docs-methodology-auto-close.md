---
id: FEAT-2026-0018/T10
type: implementation
effort: low
status: done
attempts: 1
planned_cost_usd: 0.30
generated_surfaces: []
duration_seconds: 161.743
cost_usd: 0.286601
input_tokens: 11
output_tokens: 4653
---

# docs/methodology.md auto-close section + /draft-feature template tweak

**Objective.** Document the deterministic close path in
`docs/methodology.md` (the canonical methodology reference) so future
operators read about the predicate, the override surfaces, the
auto-close skip semantics, and the recursive-dogfood property in one
place. Lightly nudge the `/draft-feature` skill template wording so
new features author their cost tables with predicate evaluation in
mind (per PLAN.md: "already mostly in place per FEAT-2026-0015's
planned-cost-capture work").

**Context.** This is `FEAT-2026-0018/T10`. Gate 3 docs WU. The auto-
close behavior is operationally invisible from the methodology doc
otherwise — a new operator reading the methodology would not know the
predicate exists.

Read first:
- `docs/methodology.md` lines 60–135 (the existing `close` /
  `close-intermediate` / `plan-next` documentation that T10 will
  splice an auto-close note into).
- `PLAN.md` § "Predicate v1" — the seven-check predicate. Quote the
  list verbatim into methodology.md.
- `.specfuse/skills/draft-feature/SKILL.md` — the template the
  skill uses to scaffold a new feature's PLAN.md. Light tweak:
  ensure cost-table guidance mentions the predicate.
- `.specfuse/rules/never-touch.md`, `.specfuse/rules/result-contract.md`.

**Acceptance criteria.**

1. **`docs/methodology.md` extended** with a new section after the
   existing `close` / `close-intermediate` documentation
   (around line 80) titled `### Deterministic auto-close path
   (FEAT-2026-0018)`. The section MUST contain:
   - One paragraph: what the predicate is + why it exists (cycle-
     time + brittleness-surface-area reduction; reference PLAN.md).
   - The seven-check list quoted from PLAN.md § "Predicate v1"
     verbatim (criteria 1–7).
   - One paragraph: on auto-close terminal — stub RETROSPECTIVE.md
     + skipped close WU + invariant guard still fires.
   - One paragraph: on auto-close intermediate (option A) —
     skipped close-intermediate WU but plan-next still dispatches.
   - One paragraph: override surfaces — `--force-full-close
     <feature-id>` CLI flag + `auto_close_disabled: true` PLAN.md
     frontmatter.
   - One paragraph: predicate-version transparency — every
     `auto_close_decision` event carries `predicate_version`;
     future v2+ revisions remain auditable retroactively.

2. **No edits to other methodology sections.** Specifically: existing
   `close` / `close-intermediate` / `plan-next` definitions stay
   intact. The new section is purely additive.

3. **`.specfuse/LEARNINGS.md` appended** with one gate-3 lesson
   describing what graduated to authoring-work-units (if anything
   from this feature does) OR an explicit "nothing generalizes —
   gate 3 ran on-plan" note. The close-ceremony's lessons sub-
   step typically owns this; this AC asks T10 to confirm the
   appended entry exists in HEAD before declaring complete —
   not to author one if `G3-CLOSE` already did.

   Note: per the loop's two-WU intermediate contract,
   `close-intermediate` owns lessons appending on intermediate
   gates and `close` owns it on terminal gates. T10 is a docs WU
   running INSIDE gate 3 (before `G3-CLOSE`), so this AC is
   coordination-only — T10 verifies the LEARNINGS file is
   well-formed and (if `G3-CLOSE` runs after T10) is the right
   place to add `[FEAT-2026-0018/G3-CLOSE]` tag. T10 itself
   does not append.

4. **`/draft-feature` template tweak.** In
   `.specfuse/skills/draft-feature/SKILL.md`, locate the
   cost-table-authoring guidance (search for `planned_cost_usd`).
   Add a single short paragraph nudging authors to size the
   cost table with predicate evaluation in mind:

   > Cost tables feed `evaluate_auto_close` at gate close. A WU's
   > `planned_cost_usd` is the threshold the predicate's per-WU
   > ratio check measures against (criteria 3 + 4 in PLAN.md's
   > Predicate v1). Honest planning makes auto-close behave; over-
   > generous estimates make every gate auto-close even when it
   > shouldn't.

   No other edits to `draft-feature/SKILL.md`.

5. **Roadmap unchanged.** The `.specfuse/roadmap.md` row for
   `FEAT-2026-0018` is NOT edited by T10 — driver-side
   `fire_terminal_flips` from `G3-CLOSE` owns the row's terminal
   flip. If you find yourself editing roadmap.md, STOP and re-read
   this AC.

6. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. methodology.md has new heading
   grep -qE '^### Deterministic auto-close path \(FEAT-2026-0018\)' docs/methodology.md

   # b. methodology.md mentions predicate=v1 + override surfaces + criteria
   grep -q 'predicate=v1' docs/methodology.md
   grep -q -- '--force-full-close' docs/methodology.md
   grep -q 'auto_close_disabled' docs/methodology.md
   grep -qE 'No blocked_human in attempt chain|No replan' docs/methodology.md

   # c. /draft-feature template tweak present
   grep -q 'evaluate_auto_close' .specfuse/skills/draft-feature/SKILL.md

   # d. roadmap NOT touched
   ! git diff --name-only HEAD | grep -qx '.specfuse/roadmap.md'

   # e. Working-tree diff actually touches the named files
   git diff --name-only HEAD | grep -qx 'docs/methodology.md'
   git diff --name-only HEAD | grep -qx '.specfuse/skills/draft-feature/SKILL.md'
   ```

   If any check fails, emit `status: blocked`. Do NOT flip this WU's
   `status` field as a substitute.

**Do not touch.** Files this WU may edit:
- `docs/methodology.md` (additive — new section only)
- `.specfuse/skills/draft-feature/SKILL.md` (one paragraph in the
  cost-table guidance area only)

No edits to: `.specfuse/roadmap.md` (driver-side flip on G3-CLOSE),
`LEARNINGS.md` (close ceremony owns), `loop.py` / `gate_eval.py` /
`lint_plan.py` (code), other skills (`wrap-feature` is T08, new
`migrate-to-auto-close` is T09), other features, secrets, `.git/`.
Driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(this WU edits markdown). Plus AC6 existence checks. No tests.

**Escalation triggers.**

1. **Completeness.** AC6 commands (a)–(e) any failing → emit
   `status: blocked`. Do NOT flip frontmatter as substitute.
2. **methodology.md drift.** If `docs/methodology.md` has been
   significantly restructured since T10 was drafted (the close /
   close-intermediate section moved or merged), update the
   insertion location but keep the section additive. If the
   restructure removed the close-section anchor, emit
   `status: blocked` — operator decides on placement.
3. **draft-feature template restructure.** If the
   cost-table-authoring guidance area no longer exists in
   `draft-feature/SKILL.md`, surface as an open question and emit
   `status: blocked` — operator decides whether to add new area
   or skip the tweak.
4. **LEARNINGS coordination.** If T10 runs AFTER `G3-CLOSE` (which
   would be unusual; the gate's substantive WUs run first), AC3
   is moot. Surface the ordering in RESULT block summary;
   `G3-CLOSE` owns the appended lesson.
