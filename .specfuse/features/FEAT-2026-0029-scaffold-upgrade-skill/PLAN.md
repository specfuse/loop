---
feature_id: FEAT-2026-0029
title: One-command Specfuse scaffold upgrade skill
slug: scaffold-upgrade-skill
branch: feat/FEAT-2026-0029-scaffold-upgrade-skill
roadmap_goal: A Claude Code skill that upgrades a target project's Specfuse scaffold end-to-end — dry-run reports what would change; live mode branches off origin/main, runs specfuse upgrade, commits, pushes, opens a PR, and merges on green (gated on a clean post-upgrade health report, else halts and hands off to feature-conversion).
autonomy_default: review
status: active
planned_cost_usd: 6.00
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: One-command Specfuse scaffold upgrade skill

`specfuse upgrade [--dry-run] <target>` already overlays a newer scaffold in
place. What it does NOT do is the git choreography a human repeats every time:
branch off the latest `origin/main`, run the upgrade, commit, push, open a PR,
watch CI, and merge. Today that is hand-run and error-prone — upgrading a dirty
tree, branching off a stale local `main`, forgetting the post-upgrade health
report that tells you whether existing feature folders still conform.

This feature ships a Claude Code skill, `scaffold-upgrade`, that wraps the
existing CLI in that choreography. It is **orchestration only** — it adds no new
upgrade logic. The one piece of real decision logic — "given CI status and the
post-upgrade health report, is it safe to merge?" — is extracted into a small,
unit-tested helper so the load-bearing call is verified rather than trusted to
prose.

**Decisions (set at draft time):**
- **Target = path arg, defaults cwd.** Mirrors `specfuse upgrade <target>` and
  the roadmap wording "on a given project". The skill can upgrade a repo the
  operator is not sitting in.
- **Dry-run reports, never writes.** `scaffold-upgrade --dry-run <target>` runs
  `specfuse upgrade --dry-run`, prints the would-change diff, and states plainly
  that an upgrade would be performed. No branch, no commit.
- **Merge is gated, and halts on FAIL.** The live flow merges only when CI is
  green AND the post-upgrade health report is clean. On any conformance FAIL the
  skill stops before merge and points at `/feature-conversion` — it never lands a
  scaffold that breaks existing feature folders.
- **Watch-then-merge, graceful fallback.** The skill polls checks to green then
  squash-merges. If the target repo has GitHub auto-merge available it may use
  it; if branch protection blocks the merge (branch behind base, required
  up-to-date), the skill reports and stops rather than forcing.
- **Pure-markdown skill + one tested helper.** The SKILL.md carries the flow
  (like `wrap-feature`); only the merge-safety predicate is code, under
  `.specfuse/scripts/` with pytest coverage.
- **Out of scope:** changing `specfuse upgrade`'s own behavior; performing the
  `feature-conversion` edits (the skill hands off, it does not convert);
  supporting non-`gh` / non-GitHub remotes beyond a graceful "can't automate,
  here's the manual command" degradation.

This file owns the **shape**. Each WU owns its status; each GATE owns its gate
status. Single gate → single terminal `close` (≤ 4 substantive WUs, per
`docs/methodology.md` §6 ceremony proportionality).

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0029/T01
        file: WU-01-merge-gate-helper.md
        depends_on: []
      - id: FEAT-2026-0029/T02
        file: WU-02-author-skill.md
        depends_on: [FEAT-2026-0029/T01]
      - id: FEAT-2026-0029/T03
        file: WU-03-wire-register.md
        depends_on: [FEAT-2026-0029/T02]
      - id: FEAT-2026-0029/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0029/T01
          - FEAT-2026-0029/T02
          - FEAT-2026-0029/T03
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- T02 (the SKILL.md) is pure markdown and carries an explicit `Red-test exempt`
  line; the red→green proof lives in T01 (the helper) and T03 (the deploy bats).
- The close WU records what the loop could not verify in-sandbox: the real
  `git push` / `gh pr create` / merge against a live target repo runs
  post-merge / operator-side, not inside the loop run.
