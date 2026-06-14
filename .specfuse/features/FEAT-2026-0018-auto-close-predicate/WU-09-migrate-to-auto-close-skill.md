---
id: FEAT-2026-0018/T09
type: implementation
effort: medium
status: done
attempts: 1
planned_cost_usd: 1.20
generated_surfaces: []
duration_seconds: 140.711
cost_usd: 0.349642
input_tokens: 15
output_tokens: 5431
---

# /migrate-to-auto-close skill — surface capability per feature, opt-in

**Objective.** Author a new skill `migrate-to-auto-close` that, run against
a Specfuse project, scans the project's `.specfuse/features/` directory,
identifies features whose PLAN.md predates the auto-close path, and surfaces
per-feature the capability + a recommended action — without auto-rewriting
any PLAN.md files. Opt-in by design: the operator decides per feature
whether to flip `auto_close_disabled` (off, leave default), reshape a
gate's closing sequence, or leave the feature unchanged.

**Context.** This is `FEAT-2026-0018/T09`. The deterministic predicate +
driver wiring landed in gates 1 and 2; this skill is the operator-facing
discoverability surface for projects that have features already in flight
when FEAT-2026-0018 ships.

PLAN.md § "Scope OUT" explicitly forbids auto-rewriting in-flight feature
PLAN.md files — migration is opt-in per feature, surfaced by this skill.

Read first:
- `PLAN.md` § "Predicate v1" and § "Scope OUT" (the auto-close
  semantics + the per-feature override `auto_close_disabled: true`
  shipped in T01 + T06).
- `.specfuse/scripts/gate_eval.py` (the predicate the skill consults
  for read-only feature evaluation).
- `.specfuse/skills/wrap-feature/SKILL.md` and
  `.specfuse/skills/pick-feature/SKILL.md` — shape and tone reference;
  follow their hard-rules-+-method-steps structure.
- `.specfuse/rules/never-touch.md`, `.specfuse/rules/result-contract.md`.

**Acceptance criteria.**

1. **Skill file lands** at
   `.specfuse/skills/migrate-to-auto-close/SKILL.md`. Frontmatter:

   ```yaml
   ---
   name: migrate-to-auto-close
   description: Scan a Specfuse project's `.specfuse/features/` for features whose PLAN.md predates the deterministic auto-close predicate (FEAT-2026-0018). For each feature, surface eligibility for auto-close on its remaining gates, the predicate's verdict on already-passed gates (read-only), and a recommended action — without auto-rewriting any PLAN.md. Opt-in per feature. Triggers: /migrate-to-auto-close, "migrate to auto-close", "audit auto-close eligibility".
   ---
   ```

2. **Hard-rules section** at the top of the body, six rules:
   - **Read-only on PLAN.md content.** This skill DOES NOT rewrite
     in-flight PLAN.md files. The auto-close path takes effect
     automatically on next gate close for any feature whose PLAN.md
     does not declare `auto_close_disabled: true`; no migration
     edit is required for that path.
   - **Surface, do not decide.** For each scanned feature, print
     status + a recommended action; the operator confirms or
     overrides per feature.
   - **Refuse to scan if the project is not Specfuse-shaped.** No
     `.specfuse/` directory → stop with a one-line diagnostic.
   - **Predicate-version transparency.** Every recommendation
     references `predicate=v1` explicitly; future v2+ revisions
     will require re-running this skill.
   - **No git.** This skill is read-only on `.specfuse/features/**`
     content and does not run `git`.
   - **Per-feature confirm before any flip.** When the operator
     opts in to set `auto_close_disabled: true` on a specific
     feature (the only write this skill is allowed to perform),
     ask a single y/n confirm per feature naming the path.

3. **Method section** with six numbered steps:
   - **1. Locate and validate target project.** `pwd` is a
     Specfuse-shaped repo (`.specfuse/` present); else stop.
   - **2. Enumerate features.** `ls .specfuse/features/FEAT-*-*/`;
     for each: read PLAN.md frontmatter (`feature_id`, `status`,
     `auto_close_disabled` (optional)). Bucket into: `done`,
     `active`, `abandoned`.
   - **3. Per-feature eligibility report.** For each `active` and
     `done` feature, build a one-paragraph report:
     - `feature_id` + `slug`.
     - `auto_close_disabled` value (default: absent = false).
     - Run `python3 .specfuse/scripts/gate_eval.py backtest
       <feature_id>` and capture the per-gate auto verdict.
     - Recommended action — see AC4.
   - **4. Recommended action per feature.** Two cases:
     - `active` feature with any future gate predicted on-plan
       (predicate auto=True against current cost/event data
       extrapolated): recommend "leave default" with a one-line
       rationale ("predicate will fire on gate N").
     - `active` feature with predicate refusing on gates 1..N
       and `auto_close_disabled` absent: recommend either
       (a) "leave default — predicate refuses correctly; full
       ceremony will run automatically" OR (b) "flip
       `auto_close_disabled: true` to lock current behavior
       in case of future-gate predicate fires you do not want."
       The skill names BOTH options and asks; does not pick.
     - `done` feature: report "no action — feature is closed."
   - **5. Opt-in flip (one feature at a time).** When the
     operator chooses option (b) on an active feature, ask
     `Flip auto_close_disabled: true on <feature_id>? (y/n)`.
     On y: write the PLAN.md frontmatter field, print the new
     PLAN.md head as confirmation, commit instruction reminder
     ("driver owns git; no commit from this skill"). On n: skip.
   - **6. Final summary.** Print `<scanned N>: <left M unchanged,
     flipped K>` and one-line "next: monitor next gate close
     to see predicate behavior on the live path."

4. **No auto-rewrites of PLAN.md content beyond the single
   frontmatter field.** AC3 step 5 may write ONLY
   `auto_close_disabled: <bool>` to a target feature's PLAN.md
   frontmatter, leaving title / branch / status / roadmap_goal /
   gates graph unchanged.

5. **No methodology drift in tone.** Skill body follows the same
   structure as `wrap-feature/SKILL.md` and `pick-feature/SKILL.md`:
   `## When to invoke`, `## Hard rules`, `## Method`, `## What this
   skill does NOT do`, `## Version` (v0.1).

6. **Discoverability validation.** Verify the new skill's slash
   command is reachable: it appears under
   `.specfuse/skills/migrate-to-auto-close/SKILL.md` (Claude Code
   auto-discovers via the symlink convention; this project's
   `.claude/skills/` symlinks `.specfuse/skills/` — see
   `.claude/CLAUDE.md`). Confirm the symlink resolves:
   `test -L .claude/skills/migrate-to-auto-close || test -d .claude/skills/migrate-to-auto-close || true` — non-blocking (some projects don't keep the symlink), but if absent, T09
   prints a one-line note in the RESULT block.

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Skill file exists with frontmatter
   test -s .specfuse/skills/migrate-to-auto-close/SKILL.md
   grep -qE '^name: migrate-to-auto-close$' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # b. Six hard rules present (count "## Hard rules" then bullet under it)
   grep -qE '^## Hard rules' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # c. Six method steps present
   for i in 1 2 3 4 5 6; do
     grep -qE "^### $i\\. " .specfuse/skills/migrate-to-auto-close/SKILL.md || { echo "missing step $i"; exit 1; }
   done

   # d. References auto_close_disabled + predicate=v1
   grep -q 'auto_close_disabled' .specfuse/skills/migrate-to-auto-close/SKILL.md
   grep -q 'predicate=v1' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # e. References gate_eval.py backtest CLI
   grep -q 'gate_eval.py backtest' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # f. "What this skill does NOT do" section present
   grep -qE '^## What this skill does NOT do' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # g. Version v0.1 noted
   grep -qE '^\*\*v0\.1\*\*' .specfuse/skills/migrate-to-auto-close/SKILL.md

   # h. Working-tree diff actually creates the file (hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/skills/migrate-to-auto-close/SKILL.md'
   ```

   If any check fails, emit `status: blocked` naming the failing
   check + observed output. Do NOT flip this WU's `status` field
   as a substitute.

**Do not touch.** Files this WU may edit / create:
- `.specfuse/skills/migrate-to-auto-close/SKILL.md` (new — only file)

No edits to: `loop.py`, `gate_eval.py`, `lint_plan.py`, other skills
(`wrap-feature` is T08's), other features, secrets, `.git/`. Driver
owns all git; edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(this WU adds a markdown skill, not code). Plus AC7 existence
checks. The skill itself does not need unit-test coverage (it's
prose instructions consumed by a slash command).

**Escalation triggers.**

1. **Completeness.** AC7 commands (a)–(h) any failing → emit
   `status: blocked`. Do NOT flip frontmatter as substitute.
2. **PLAN.md mutation scope.** If during authoring you find a
   case where surfacing the recommendation requires multi-field
   PLAN.md mutation (not just `auto_close_disabled`), STOP and
   emit `status: blocked` — multi-field migration is OUT of scope
   per PLAN.md and would silently grow the skill's authority.
3. **Cross-version migration.** If `predicate=v2` lands before
   this skill ships, the v1-only assumption becomes brittle.
   Surface in RESULT block summary; do NOT add a version-switch
   branch unilaterally.
4. **Skill-discovery symlink missing.** AC6 — if `.claude/skills/`
   does not symlink `.specfuse/skills/`, note in RESULT block;
   the skill still WORKS, the slash command auto-discovery
   route is the only thing affected.
