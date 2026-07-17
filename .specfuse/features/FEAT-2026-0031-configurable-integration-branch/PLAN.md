---
feature_id: FEAT-2026-0031
title: Configurable integration branch
slug: configurable-integration-branch
branch: feat/FEAT-2026-0031-configurable-integration-branch
roadmap_goal: Make a feature's base branch an explicit property declared once in PLAN.md frontmatter and read by every consumer — branch creation, the staleness guard, and PR creation — so teams working off a long-lived integration or release branch can run the loop without wrong-target PRs or spurious halts.
autonomy_default: auto
status: done
planned_cost_usd: 5.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Configurable integration branch

The loop cuts every feature onto its own branch — correct, and the reason
per-feature isolation holds. But it cuts that branch from **whatever HEAD happens
to be**: `ensure_feature_branch` (loop.py:1028) runs a bare `git checkout -B
<branch>` with no base ref (loop.py:1104). Meanwhile the GitHub backend hardcodes
`--base main` when opening the PR (gh_backend.py:73).

A team working off a long-lived integration or release branch therefore cannot use
the loop: the branch is cut correctly only if the operator happened to be standing
in the right place, and the PR targets `main` regardless. Cutting from a non-default
base does work today, but only by accident — nothing validates that HEAD is the
intended base, nothing records what the base was, and the staleness guard's rebase
hint (loop.py:1081) points at the *current* branch, so on a non-default base it
advises a rebase onto the wrong one.

**Decisions (set at draft time):**

- **Frontmatter is the sole input.** An optional `base:` key in PLAN.md, written
  once at draft time and read on every run of that feature. No `--base` CLI flag:
  a flag is per-invocation, and the point is a property that survives across runs
  and operators. Frontmatter is also auditable (`git log` on PLAN.md shows when the
  base changed) and lintable; a flag is neither.
- **One resolver, no threading.** `resolve_base(feat_fm)` → frontmatter `base` if
  set, else `_default_branch()` (loop.py:769, already remote-aware), else the
  current branch. Every consumer calls it. Nothing passes a base through call args.
- **Staleness guard re-anchors to the resolved base.** Both the
  `merge-base --is-ancestor` check and the rebase hint move off HEAD/`current` onto
  the resolved base. On a configured base the current check fires spuriously and its
  hint actively corrupts (it would rebase a `release/2.0` feature onto `main`). The
  error text is rewritten for a non-git-expert reader, and the destructive
  `git branch -D` suggestion is removed — the loop should not suggest a
  work-destroying command to an operator who cannot evaluate it.
- **Missing base is classified, not blanket-halted.** A declared base absent locally
  is either a typo (fetching cannot help) or a real branch this clone never fetched
  (fetching fixes it entirely). `git ls-remote` separates them. Network is touched
  **only** on the miss path — the happy path resolves a local ref and stays
  offline-clean.
- **PR base fixed where frontmatter is readable.** `gh_backend.py` and the
  `wrap-feature` skill both operate on a feature and can read `base`. `fix-bug` and
  `scaffold-upgrade` cut branches with no feature folder at all — no frontmatter to
  read — so making them base-aware needs a repo-level default base this feature has
  not designed and will not invent at the end of a WU.

**Out of scope:** a repo-level default base (`fix-bug`, `scaffold-upgrade` keep
hardcoding `main` — documented gap, not oversight); per-gate base override (base is
a feature property); auto-rebase onto base (the driver never rebases for you);
auto-fetching a base that exists locally but is stale ("your local default branch is
three weeks behind" is real and different); cross-repo / orchestrated
(`INIT-YYYY-NNNN/FNN`) base; a `--base` CLI flag.

This file owns the **shape**. Single gate → single terminal `close` (3 substantive
WUs ≤ 4, per `docs/methodology.md` §6 ceremony proportionality). Autonomy `auto`:
the gate auto-closes if it stays on-plan, else the `gate_eval` predicate disables
auto-close and dispatches the close as a reflective session.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0031/T01
        file: WU-01-resolve-base.md
        depends_on: []
      - id: FEAT-2026-0031/T02
        file: WU-02-ensure-feature-branch.md
        depends_on:
          - FEAT-2026-0031/T01
      - id: FEAT-2026-0031/T03
        file: WU-03-pr-base.md
        depends_on:
          - FEAT-2026-0031/T01
      - id: FEAT-2026-0031/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0031/T02
          - FEAT-2026-0031/T03
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- T02 and T03 are independent of each other; both need T01's resolver.
- **Oracle split.** `resolve_base` / `ensure_base_ref` / `ensure_feature_branch`
  (T01, T02) are fully in-loop-verifiable against **real git** in a tmpdir — git
  works in the loop sandbox, and a local bare repo stands in for `origin`, so even
  the `ls-remote` classification needs no network. The `gh` surfaces (T03) are not:
  `gh` returns auth errors inside `claude -p` (the documented `gh`↔claude-p bug,
  LEARNINGS FEAT-2026-0020/G1-CLOSE-INTERMEDIATE), so T03's oracle is a
  stub-`_runner` assertion on the call shape, with live proof deferred post-merge.
- This feature declares **no `base:` key of its own** — it is based on the default
  branch, so `resolve_base` falls through to `_default_branch()`. The opt-in path is
  what gets dogfooded here; the configured-base path is proven by tests, and by the
  first real integration-branch run after merge.
