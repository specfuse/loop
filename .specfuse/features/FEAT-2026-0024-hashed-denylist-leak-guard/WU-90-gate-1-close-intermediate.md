---
id: FEAT-2026-0024/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 0
generated_surfaces: []
oracle_env: macos_local
planned_cost_usd: 2.00
verdict: partially_met
auto_close: true
auto_close_reasons: []
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the mandatory
`## Cost analysis` and `## What the loop did NOT verify` sections), appending
durable lessons to `.specfuse/LEARNINGS.md`, and reconciling any docs state
implied by gate 1. Does NOT flip gate or feature status, and does NOT draft gate
2 — that is `G1-PLAN`'s job.

**Context.** This is `FEAT-2026-0024/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped the
hashed-denylist core (T01) and the CI wiring + generator + committed `.hashes`
(T02), closing issue #45. Read this feature's `events.jsonl`, the gate's commits
(`git diff main..HEAD --stat`), the root `.specfuse/LEARNINGS.md`, and PLAN.md's
`roadmap_goal`.

`close-intermediate` WU (FEAT-2026-0015 contract): folds retrospective + lessons
+ docs into one session for gate 1 (non-terminal). The companion `plan-next` WU
(`G1-PLAN`) drafts gate 2's substantive WUs afterward.

The `verdict: partially_met` frontmatter is deliberate and honest: this is a
GATE verdict, not the terminal feature-arc verdict (which is G2-CLOSE's). The
feature's roadmap_goal spans BOTH surfaces (tracked files AND issue/PR bodies);
gate 1 delivers only the tracked-files surface (#45). The driver has no
`close-intermediate` terminal-flip branch, so the value triggers no flips.

Binding rules: `.specfuse/rules/{result-contract,never-touch,security-boundaries,
correlation-ids}.md`. Verification: `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` exists** at this feature's folder. Non-empty. Contains:
   - One `## Gate 1` section.
   - One sub-section per substantive WU (T01, T02): attempts, blockers if any,
     surprises (especially: did the sliding-window matcher pass the
     mid-atom-substring fidelity test, or did it regress to atom-n-grams?).
   - The required `## Cost analysis` and `## What the loop did NOT verify`
     sections (see AC2, AC3).

2. **`## Cost analysis` section** reconciles `planned_cost_usd` (PLAN.md + per-WU
   frontmatter: T01 $2.50, T02 $2.50, this WU $2.00) against actual spend (from
   `events.jsonl`). Per WU: planned, actual, delta %. Aggregate to gate total.
   Variance > 50% on any WU requires a one-paragraph rationale. Note per WU
   whether each would pass the auto-close predicate's per-WU ratio check (≤ 1.5×).

3. **`## What the loop did NOT verify` section** enumerates each acceptance
   criterion whose verification was deferred. For each row: the criterion, why
   deferred, where verification actually happens. Write `(nothing — every
   acceptance criterion was verified in-loop)` if empty, so the count is visible.
   Likely candidate: T02's committed-`.hashes`-clean-in-real-CI is exercised by
   the `--all` gate locally; the real GitHub-Actions CI run confirms it
   post-merge. If the section has > 2 entries OR > 30% of the gate's criteria,
   flag the gate's sizing under `## What I'd change`.

4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson, OR an explicit
   `[FEAT-2026-0024/G1-CLOSE-INTERMEDIATE] nothing generalizes` note. A strong
   candidate: the substring-fidelity-vs-leak tradeoff (char-sliding-window at a
   committed length-set beats atom-n-grams for a leak guard; cross-link
   `[FEAT-2026-0020/G2/leak-guard-surface-asymmetry]`). Phrase each as a rule
   that would change how a future WU is written.

5. **Docs reconciliation.** No docs/roadmap diff is expected from gate 1 alone
   (the roadmap row stays `active` until the terminal close — do NOT flip it
   here). If a gate-1 finding requires a doc edit (e.g. documenting the `.hashes`
   format in a leak-scan README), include it in this WU's squash; otherwise the
   docs-diff assertion is satisfied by the `RETROSPECTIVE.md` write alone.

6. **NO terminal verdict.** This is intermediate close. The terminal feature-arc
   verdict belongs to G2-CLOSE. Do NOT flip `PLAN.md status` or the roadmap row.

7. **Existence check** before declaring complete:
   ```bash
   FEAT=.specfuse/features/FEAT-2026-0024-hashed-denylist-leak-guard
   test -s "$FEAT/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FEAT/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FEAT/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0024' || \
     grep -q 'nothing generalizes' "$FEAT/RETROSPECTIVE.md"
   git diff --name-only HEAD | grep -qx "$FEAT/RETROSPECTIVE.md"
   ```
   If any check fails, emit `status: blocked`.

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (new file in this feature's folder).
- `.specfuse/LEARNINGS.md` (append-only).
- Docs files iff a gate-1 WU surfaced something requiring doc reconciliation.

No edits to: gate-1 substantive WU files (T01/T02 own them), `leak_scan.py`,
`leak_denylist.hashes`, other features, secrets, `.git/`. Driver owns all git.
See `.specfuse/rules/never-touch.md`.

**Verification.** `doc` gate set in `.specfuse/verification.yml` (this WU is
`close-intermediate` → doc gates). Plus AC7 existence checks. Plus the
[FEAT-2026-0015/T07] closing-deliverable guards
(`assert_retrospective_exists`, `assert_learnings_appended_or_noop`,
`assert_doc_or_roadmap_diff`, `assert_cost_analysis_section_when_met`).

**Escalation triggers.**
1. **Cost-analysis ambiguity.** If a WU's `cost_usd` / `planned_cost_usd`
   disagrees with `events.jsonl` summed over its attempts, emit `status: blocked`
   naming the discrepancy.
2. **No-op vs nothing-generalizes ambiguity.** Prefer the explicit "nothing
   generalizes" note over an invented lesson.
3. **Compound scope.** If you find yourself wanting to draft gate 2 inside this
   WU — STOP. That is G1-PLAN's job.
4. **Fidelity regression surfaced.** If the retrospective review reveals T01/T02
   shipped an atom-n-gram matcher that fails the mid-atom-substring case (a
   silent leak-guard false-negative), do NOT paper over it — flag it loudly and
   emit `status: blocked` so the operator decides reland vs follow-up.
