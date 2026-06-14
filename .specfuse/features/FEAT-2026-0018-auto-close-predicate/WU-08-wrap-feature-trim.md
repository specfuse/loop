---
id: FEAT-2026-0018/T08
type: implementation
effort: low
status: pending
attempts: 0
planned_cost_usd: 0.40
generated_surfaces: []
---

# /wrap-feature skill trim — push + PR + CI + next-pick only

**Objective.** Strip `/wrap-feature` SKILL.md of the executive-recap +
retrospective-evaluation prose (current Method §§ 2–3). After this feature,
most on-plan features auto-close: their `RETROSPECTIVE.md` is the stub
template, no `# Feature-arc verdict` section, no goal-recap synthesis worth
surfacing. The recap then misleads more than it helps. Keep `wrap-feature`
focused on its irreducible job: push branch + open PR + watch CI + point
at next pick.

**Context.** This is `FEAT-2026-0018/T08`. The auto-close path lands in
gate 2 — wrap-feature must keep working on BOTH paths (auto and full
ceremony) without the operator having to choose a different skill.

Read first:
- `.specfuse/skills/wrap-feature/SKILL.md` — current skill at v0.2
  (FEAT-2026-0015/T06). Method has 9 steps; §§ 2–3 (Executive recap +
  Manual verification step) are what gets cut. Steps 1, 4–9 are kept.
- `PLAN.md` § "Predicate v1" — the auto-close stub RETROSPECTIVE.md
  shape (`## Gate N — auto-closed (predicate=v1)` heading +
  ~5-line YAML-shape metrics body, NO `# Feature-arc verdict`
  section). The recap reads against shapes that auto-close features
  do not produce.
- `.specfuse/rules/never-touch.md`, `.specfuse/rules/result-contract.md`.

**Acceptance criteria.**

1. **Method §2 ("Surface the executive recap") removed** from
   `wrap-feature/SKILL.md`. Replaced with a one-paragraph "Surface
   target feature" step:
   - Read PLAN.md frontmatter (`feature_id`, `slug`, `branch`,
     `roadmap_goal`).
   - Detect auto-close vs full-ceremony via RETROSPECTIVE.md heading
     pattern: `grep -qE '^## Gate [0-9]+ — auto-closed \(predicate=v[0-9]+\)'`.
   - Print one line: `<feature_id> [<slug>] — auto-closed | ceremony`
     and the branch + roadmap_goal in 2 lines.
   - No multi-section recap, no diff-stat synthesis, no LEARNINGS
     enumeration.

2. **Method §3 ("Manual verification step") removed.** Manual
   verification of deferred items is rare (last observed
   FEAT-2026-0014); the few cases where it's needed are best surfaced
   by reading RETROSPECTIVE.md directly. When the auto-close path
   fires, RETROSPECTIVE.md is a stub — there is nothing to scan for
   "deferred verification" anyway.

3. **Numbering re-flowed.** Old steps 4–9 become 2–7. Cross-references
   inside the skill (e.g. "skip to step 6") updated to new numbers.

4. **Hard-rules section retained**, with one addition:
   - "Refuses on non-`done` features." — unchanged.
   - "Read-only on RETROSPECTIVE / LEARNINGS / roadmap content." —
     unchanged.
   - "No file writes before git." — unchanged.
   - "gh-CLI gracefully degraded." — unchanged.
   - "Never auto-merge." — unchanged.
   - **NEW:** "Auto-close and full-ceremony features both supported.
     Skill MUST NOT assume `RETROSPECTIVE.md` carries a feature-arc
     verdict — the auto-close stub does not." Phrase as a hard rule
     so future revisions can't sneak the recap back in.

5. **Version bump to v0.3.** Append version note: "v0.3
   (FEAT-2026-0018/T08). Method §§ 2–3 removed — executive recap +
   manual-verification step are noise on the auto-close path. Wrap is
   now: locate → push → PR → CI watch → next-pick. The deterministic
   close path makes the recap redundant on most features; rare
   off-plan cases surface via RETROSPECTIVE.md directly."

6. **No skill-system changes.** `name:` + `description:`
   frontmatter values unchanged (the slash command and discovery
   string stay stable). Description COPY can be tightened to match
   the trimmed scope but the trigger phrase MUST still match the
   strings agents look for ("wrap-feature", "/wrap-feature", "wrap
   the feature").

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Method §§ 2–3 removed (negative grep — neither heading exists)
   ! grep -qE '^### 2\. Surface the executive recap' .specfuse/skills/wrap-feature/SKILL.md
   ! grep -qE '^### 3\. Manual verification step' .specfuse/skills/wrap-feature/SKILL.md

   # b. New "Surface target feature" header replaces them
   grep -qE '^### 1\. Locate' .specfuse/skills/wrap-feature/SKILL.md

   # c. Auto-close-vs-ceremony detection line present
   grep -qE 'auto-closed \\\(predicate=v' .specfuse/skills/wrap-feature/SKILL.md

   # d. Version bumped to v0.3
   grep -qE '^\*\*v0\.3\*\*' .specfuse/skills/wrap-feature/SKILL.md

   # e. Hard rule on auto-close support present
   grep -qE 'Auto-close and full-ceremony features both supported' .specfuse/skills/wrap-feature/SKILL.md

   # f. Frontmatter unchanged keys
   head -5 .specfuse/skills/wrap-feature/SKILL.md | grep -qE '^name: wrap-feature$'

   # g. Working-tree diff actually edits the skill (hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/skills/wrap-feature/SKILL.md'
   ```

   If any check fails, emit `status: blocked` naming the failing
   check. Do NOT flip this WU's `status` field as a substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/skills/wrap-feature/SKILL.md` (only the file edited)

No edits to: any code (`loop.py`, `gate_eval.py`, `lint_plan.py`),
other skills, RETROSPECTIVE.md, LEARNINGS.md, roadmap, other features,
secrets, `.git/`. Driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(this WU edits a markdown skill, not code). Plus AC7 existence
checks. No new tests required.

**Escalation triggers.**

1. **Completeness.** AC7 commands (a)–(g) any failing → emit
   `status: blocked`. Do NOT flip frontmatter as substitute.
2. **Skill discovery regression.** If the skill `description:` field
   change breaks the trigger phrase agents look for, the slash
   command stops working — verify trigger phrase preservation
   before declaring complete. If unsure, emit `status: blocked` —
   operator decides on final copy.
3. **Cross-skill reference drift.** Other skills (e.g.
   `/pick-feature`, `/draft-feature`) reference `/wrap-feature` by
   name; renumbered step references inside `wrap-feature` SKILL.md
   stay internal. No external skill references the inner-step
   numbering (verified at draft time via `grep -rn 'wrap-feature.*step'
   .specfuse/skills/`). If a hit appears at arm time, surface it.
4. **Recap-was-actually-needed.** If during execution you discover a
   case where the recap is genuinely load-bearing (e.g. a hard
   constraint references a section that the recap surfaces), STOP
   and emit `status: blocked` — operator decides scope. The
   reasonable-but-breaking choice here is to silently retain part of
   the recap; that's the trap.
