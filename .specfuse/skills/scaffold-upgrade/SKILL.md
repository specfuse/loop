---
name: scaffold-upgrade
description: "Dry-run-reports or end-to-end upgrades a target project's Specfuse scaffold via `specfuse upgrade [--dry-run] <target>`, wrapping the git choreography (branch/commit/push/PR/CI/merge-gate) around it. Supports `--dry-run` for a report-only pass with no branch/commit/push/PR."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Scaffold upgrade (dry-run report or full ceremony)

Wraps `specfuse upgrade [--dry-run] <target>` in the git choreography a human
would otherwise repeat by hand: branch, run the upgrade, commit, push, open a
PR, watch CI, then decide merge-vs-halt via the merge-safety gate helper from
`.specfuse/scripts/upgrade_merge_gate.py`. Modeled on
[`../wrap-feature/SKILL.md`](../wrap-feature/SKILL.md) — same single-confirm
posture on outward-facing steps, same graceful degradation when `gh` is
absent.

**Run interactively.** Confirmation prompts are the whole point; `claude -p`
with redirected stdin falls back to a degraded "report plan and stop" mode.

## When to invoke

When a target project's `.specfuse/` scaffold is behind the version this
Specfuse install ships (its `init.sh --upgrade` or `specfuse upgrade
--dry-run` reports a stale `VERSION`), and the operator wants either a
report of what would change, or the change carried through to a merged PR.

## Target

Path-arg to the project whose scaffold is being upgraded, mirroring
`specfuse upgrade <target>`. Defaults to the current working directory when
omitted.

## Hard rules

- **Never force-merge past branch protection.** If `gh pr merge` is rejected
  by branch protection, stop and report the rejection — do not retry with
  `--admin` or any override flag.
- **Never merge on any health FAIL.** The merge-safety gate (step (h) below)
  is the sole merge/halt decision; a `halt` verdict is final for this run.
- **Never edit feature folders.** Bringing a non-conformant feature folder
  into conformance is `/feature-conversion`'s job, not this skill's — this
  skill only names the offending features and hands off.
- **Does not change `specfuse upgrade`'s own behavior.** This skill is
  choreography around the CLI, not a reimplementation of it.

## Dry-run

Report-only pass. No branch, no commit, no push, no PR.

1. Run `specfuse upgrade --dry-run <target>`.
2. Print its would-change summary verbatim to the operator.
3. State plainly: **an upgrade would be performed** — list the files that
   would be written/pruned per the summary — and stop. No git action of any
   kind is taken on a dry-run.

## Live flow

Runs the upgrade end-to-end and hands off to the merge-safety gate.

### (a) Refuse conditions

Check before anything else; refuse and stop (report which check failed) if
any hold:

- `git status --short` in `<target>` is non-empty (dirty working tree).
- `gh auth status` fails or `gh` is not installed.
- `specfuse` CLI is not on `PATH` (or importable, if invoked via module).

### (b) Branch off a fresh remote base

- `git fetch origin` in `<target>` — never branch off a possibly-stale local
  `main`.
- `git checkout -b chore/scaffold-upgrade-<date-or-slug> origin/main`.

### (c) Run the upgrade

- `specfuse upgrade <target>` (no `--dry-run`).

### (d) Commit

- Stage the written/pruned paths the CLI reports and commit, e.g.
  `chore: upgrade Specfuse scaffold to <version>`.

### (e) Push

- `git push --no-verify -u origin chore/scaffold-upgrade-<date-or-slug>`.
  `--no-verify` here is deliberate: local hooks tuned for feature-branch
  content are not calibrated for a scaffold-only commit.

### (f) Open PR

- `gh pr create --fill` (or an explicit `--title`/`--body` describing the
  scaffold version bump). Capture and report the PR URL.

### (g) Watch CI

- `gh run watch --branch chore/scaffold-upgrade-<date-or-slug>`. Do not block
  forever — bail with a hint after a reasonable timeout (~10 min) and print
  the watch command for resume.

### (h) Merge-safety gate

- Call `.specfuse/scripts/upgrade_merge_gate.py`:
  - `collect_reports(<target>)` — runs `lint_plan.py`'s structural-conformance
    check once per feature folder under `<target>/.specfuse/features/`,
    returning `[{"feature": ..., "ok": ..., "detail": ...}, ...]`.
  - `decide(ci_all_green, reports)` — returns `(verdict, reason)` where
    `verdict` is `"merge"` or `"halt"`. Pass the actual CI outcome from step
    (g) as `ci_all_green`; pass the real `collect_reports` output — never an
    invented report shape.

### (i) Act on the verdict

- **`merge`** — squash-merge: `gh pr merge --squash`.
- **`halt`** — STOP. Do not merge. Report the `reason` from `decide(...)`,
  naming every feature in `reports` with `"ok": false`, and point the
  operator at `/feature-conversion` to bring each one into conformance
  before retrying the merge.

## What this skill does NOT do

- **Does not change `specfuse upgrade`'s own upgrade logic.** Purely git
  choreography around an existing CLI command.
- **Does not edit feature folders.** `/feature-conversion` owns bringing a
  non-conformant feature into structural compliance; this skill only detects
  and names the failures via the merge-safety gate.
- **Does not force-merge or override branch protection.** A rejected merge
  is reported, not retried with elevated privileges.
- **Does not merge on a `halt` verdict, ever**, regardless of how minor the
  reported conformance failure looks.
