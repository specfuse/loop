---
name: wrap-feature
description: Finalize a feature after its close ceremony — push the feature branch, open a PR, optionally watch CI, and point at the next feature pick. Supports both auto-close and full-ceremony features. Refuses to run on features whose PLAN.md is not yet `done`. Single-confirm for the push and PR steps; gracefully degrades when `gh` is unavailable.
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Wrap feature (interactive, post-close finalization)

> **As of FEAT-2026-0015/T06, terminal flips are driver-side; /wrap-feature
> no longer touches `GATE-NN.md` status or the roadmap row.** The driver's
> `fire_terminal_flips` helper fires automatically when a `close`-type WU
> passes with `verdict: met`, flipping the terminal gate to `passed`, the
> roadmap row to `done`, and triggering auto-archive.

After the close ceremony runs (`/G1-CLOSE` for single-gate features, or
the four-WU `retrospective → lessons → docs → plan-next` sequence for
the terminal gate of multi-gate features), the methodology has done its
job: `PLAN.md status: done`, `GATE-NN.md status: passed`, the roadmap
row reflects `done`, `RETROSPECTIVE.md` exists, and durable lessons are
appended. What remains is the **plumbing handoff**: push the branch,
open the PR, watch CI, merge advisory, then point at the next pick.

This skill is the per-feature human checkpoint **after** the loop has
finished doing methodology work but before the change is shipped to
the world (or to `main`). Before this skill existed, those steps were
freelance and inconsistent — see the earlier dogfood runs in
`.specfuse/LEARNINGS.md` for examples of feature folders that closed
methodologically but stalled on push/PR for days.

Posture: **single-confirm for irreversible-ish actions** (push, PR
open). Everything before that is read-only inspection. Stop at any
step if the operator decides to take the rest manually.

**Run interactively.** Confirmation prompts are the whole point;
`claude -p` with redirected stdin falls back to a degraded "report
plan and stop" mode.

## Hard rules

- **Refuse on non-`done` features.** PLAN.md `status` MUST be `done`
  before this skill will touch anything. If `active`: stop, point at
  `/gate-status` (if a WU is blocked) or wait for the close ceremony.
  If `abandoned`: stop, this skill is the wrong path. If `active` and
  the gate is `awaiting_review` with closing-sequence WUs pending,
  point at re-running `loop.py` (drafted closing WUs need dispatch
  before wrap).
- **Read-only on RETROSPECTIVE / LEARNINGS / roadmap content.** The
  close ceremony OWNS those edits. This skill only confirms they
  exist + reads their tail. Do not amend retrospectives here.
- **No file writes before git.** All state flips (gate status, roadmap
  row) are now performed driver-side by `fire_terminal_flips`. This
  skill is read-only on all `.specfuse/` files; git actions happen
  after operator confirmation.
- **gh-CLI gracefully degraded.** Per LEARNINGS
  `[FEAT-2026-0014/T01/gh-claudeP-broken]`, `gh` is unreliable inside
  agent dispatch and may be similarly unreliable inside whatever
  context invokes this skill. Probe with `gh auth status` once
  before any `gh` step. If it fails: print the exact `gh` command(s)
  the operator should run, do not attempt them.
- **Never auto-merge.** PR opening is fine after confirm; the merge
  itself is an operator-owned decision (after CI green + review).
- **Auto-close and full-ceremony features both supported.** Skill MUST
  NOT assume `RETROSPECTIVE.md` carries a `# Feature-arc verdict`
  section — the auto-close stub does not. Detection via
  `grep -qE '^## Gate [0-9]+ — auto-closed \(predicate=v[0-9]+\)'`
  in RETROSPECTIVE.md; if that matches, treat the feature as
  auto-closed. Never synthesize recap sections from a stub.

## When to invoke

When the loop driver has printed something like:

```
Gate N complete (combined close ceremony ran).
Terminal gate of this feature.
```

— or any time the active feature's PLAN.md is `status: done` and you
have not yet pushed the branch + opened the PR. The loop driver
points at this skill in that printout (see `loop.py`'s terminal-gate
branch).

If the feature is mid-flight (`active`, not `done`), the skill stops
and points elsewhere. It does NOT run a final verification gate or a
retrospective check — those are the close ceremony's job, run before
this.

## Method

### 1. Locate and surface the target feature

- Find the most recently `done` feature whose PLAN.md is `done` (or
  the one named explicitly via `--feature`). Read its frontmatter
  (`feature_id`, `slug`, `branch`, `roadmap_goal`).
- Refuse if PLAN.md `status` is not `done`:
  - `active` → `/gate-status` (if blocked) or wait for close.
  - `abandoned` → wrong skill.
- Confirm the terminal gate is `passed` and the roadmap row is `done`.
  These are set driver-side by `fire_terminal_flips` when the close WU
  passes with `verdict: met`. If either is still `awaiting_review` /
  `active`, the close WU likely ran with a hedged verdict — surface
  this and stop; do not attempt manual reconciliation here.
- Detect close path: run
  `grep -qE '^## Gate [0-9]+ — auto-closed \(predicate=v[0-9]+\)'`
  on RETROSPECTIVE.md. Match → auto-closed; no match → full ceremony.
- Print one line: `<feature_id> [<slug>] — auto-closed | ceremony`
  then two lines: `branch: <branch>` and `goal: <roadmap_goal>`.
  No recap synthesis, no diff-stat walk, no LEARNINGS enumeration.

### 2. Push the branch

- Read PLAN.md's `branch` field (e.g. `feat/FEAT-2026-0014-gha-node20-bump`).
- Confirm `git branch --show-current` matches.
- Confirm `git status --short` is clean (no uncommitted changes;
  the close ceremony's writes should already be committed by the
  driver as `chore(loop): gate N awaiting_review` and
  `chore(loop): {wu_id} terminal flips`).
- Show diff stat: `git diff main...HEAD --stat`.
- Ask: "Push to origin/<branch>? (y / n)" — n exits with the
  push command for the operator.
- On y: `git push -u origin <branch>`. Report the upstream
  tracking confirmation or the error.

### 3. Open the PR

- Probe `gh auth status` once. If ✗: per LEARNINGS, print the
  exact `gh pr create --fill` command for the operator and skip
  to step 4.
- If ✓: ask "Open PR via `gh pr create --fill`? (y / n)"
- On y: run it. Capture the PR URL from output; report it.
- On n: print the command for the operator.

### 4. Watch CI (optional, gh-only)

- If `gh` works and PR was opened: offer "Watch CI? (y / n)"
- On y: `gh run watch --branch <branch>`. Stream summary to
  operator. Do NOT block on completion forever — bail with a
  hint after a reasonable timeout (~10 min) and print the
  watch command for resume.
- On n / gh broken: skip.

### 5. Merge advisory (do NOT merge)

- Do not auto-merge. State: "PR is open at <url>. Wait for CI
  green + review, then merge via `gh pr merge` or the GitHub UI."
- If branch protection / required reviews are configured, name
  them (best-effort via `gh pr view --json mergeable,mergeStateStatus`).

### 6. Point at the next pick

- After merge advisory, suggest `/pick-feature` for the next
  roadmap row.
- If the operator says they want to keep working: also mention
  `/draft-feature` (new initiative) and `/abandon-feature` (if
  the next pick is wrong).

### 7. RESULT

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means every step ran or was skipped by operator
choice and the operator has a clear path to merge. `status: blocked`
is reserved for the case where the canonical files contradict each
other (e.g. PLAN.md `done` but terminal gate still `awaiting_review`)
AND the operator declined to investigate.

## What this skill does NOT do

- **Does not run verification gates.** Close ceremony did that.
- **Does not write to RETROSPECTIVE.md, LEARNINGS.md, or roadmap.md
  content.** Read-only on those surfaces.
- **Does not flip GATE-NN.md status or the roadmap row.** These are
  now driver-side (FEAT-2026-0015/T06). See `fire_terminal_flips` in
  `loop.py`.
- **Does not auto-merge the PR.** Operator-owned decision.
- **Does not archive the roadmap detail section.** `/roadmap-archive`
  skill's job.
- **Does not flip PLAN.md status.** The close ceremony already did.
  If PLAN.md is not `done`, this skill stops.

## Version

**v0.3** (FEAT-2026-0018/T08). Method §§ 2–3 removed — executive
recap + manual-verification step are noise on the auto-close path.
Wrap is now: locate → push → PR → CI watch → next-pick. The
deterministic close path makes the recap redundant on most features;
rare off-plan cases surface via RETROSPECTIVE.md directly.

**v0.2** (FEAT-2026-0015/T06). Nine steps reduced to eight; terminal
state flips (gate status, roadmap row, auto-archive) moved to the
driver's `fire_terminal_flips` helper. Single-confirm posture for
push + PR is the safety discipline.
