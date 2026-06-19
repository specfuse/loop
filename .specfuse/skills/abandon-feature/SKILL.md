---
name: abandon-feature
description: "Cleanly abandon the active feature when retry isn't worth it. Flips every non-`done` WU to `abandoned`, every non-`passed` gate to `passed`, PLAN.md `status: active` \u2192 `abandoned`, and the roadmap row's status column to `abandoned`. Single up-front confirmation surfaces all four surfaces before any write."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Abandon feature (interactive, single-confirm)

The escape hatch for the loop driver. Use when a feature has hit a
wall that's bigger than a re-arm can fix — the chosen approach was
wrong, the upstream dependency went away, the requirements changed,
the cost is no longer worth the value — and you want to mark the
feature `abandoned` cleanly across all four surfaces it touches
(WUs, gates, PLAN.md, roadmap.md) in one operation.

Posture is **single-confirm**, not per-surface. Abandon is one
decision; the four file edits are mechanical consequences of that
one decision. The skill surfaces every write up front so the user
sees exactly what will move, then applies them after a single `yes`.

**Run interactively.** The up-front confirmation prompt is the
whole point; `claude -p` with redirected stdin falls back to a
degraded "show plan only" mode and refuses to write.

## Hard rules

- **Single up-front confirmation.** Surface every planned write
  (every WU status flip, every gate status flip, PLAN.md flip,
  roadmap row flip), then ask once. Yes → apply all. No → exit
  with no writes.
- **Never touch `done` WUs or `passed` gates.** They reflect work
  that actually shipped (or ceremonies that actually ran). Flipping
  them to `abandoned` would lie about history. Only `pending`,
  `ready`, `in_progress`, `blocked_human`, and `draft` move to
  `abandoned`; only `open` and `awaiting_review` gates move to
  `passed`.
- **No graph surgery, no file deletion.** WU files stay; gate files
  stay; the feature folder stays. The feature is marked abandoned;
  it is not erased. Audit trail intact.
- **Roadmap row: status column only.** Do not edit the row's title,
  ID, or folder column. Do not touch detail sections. (Migration of
  the detail section to a roadmap-archive is a separate skill, not
  this one.)
- **Refuse to abandon a `done` feature.** A feature whose PLAN.md is
  already `done` is closed; abandoning it is meaningless. The skill
  exits with a hint to use direct file edits if the user really
  means to retroactively re-classify.

## When to invoke

When the active feature should be marked dead, e.g.:

- A blocked WU's root cause is structural (the approach is wrong)
  and re-armed retries will keep failing.
- An upstream change made the feature obsolete.
- Cost or time budget is gone and the feature isn't worth the
  remaining work.
- The roadmap was reshuffled and this feature is now lower priority
  than its remaining cost.

If you just want to retry blocked WUs after a fix, use `/unblock-wu`
instead. If you want to switch what's `active` to a different
planned feature, use `/pick-feature` after this skill closes the
current one.

## Method

### 1. Detect the state

- Find the active feature (PLAN.md `status: active`; if multiple,
  ask via `--feature` or pick interactively).
- Read PLAN.md frontmatter and the gates graph.
- For every WU file, read frontmatter (`id`, `status`).
- For every gate file, read frontmatter (`gate`, `status`).
- Read the roadmap row for the feature (find by `FEAT-YYYY-NNNN` ID).
- If the feature is already `done` or `abandoned`, stop and explain.

### 2. Compute the write plan

Build the list of file edits this skill will apply:

- For each WU with `status` in `{pending, ready, in_progress,
  blocked_human, draft}`: planned flip → `abandoned`. WUs already
  `done` or `abandoned` are listed as "untouched" but not flipped.
- For each gate with `status` in `{open, awaiting_review}`:
  planned flip → `passed`. Gates already `passed` are untouched.
- PLAN.md frontmatter: `status: active` → `abandoned`.
- Roadmap row: status column → `abandoned`. (Detail-section
  `**Status: planned.**` / `**Status: active.**` lines under the
  per-feature header are not edited by this skill — those are
  prose; the table row is the source of truth.)

### 3. Surface the write plan and ask once

Display the full plan:

```
About to abandon FEAT-YYYY-NNNN — <title>.

Files that will change:

  PLAN.md
    - status: active  -> abandoned

  GATE-01.md
    - status: open    -> passed
  GATE-02.md
    - status: open    -> passed   (no WUs were ever dispatched)

  WU-01-<slug>.md  (FEAT-YYYY-NNNN/T01)
    - status: blocked_human -> abandoned
  WU-02-<slug>.md  (FEAT-YYYY-NNNN/T02)
    - status: pending       -> abandoned
  WU-90-close.md   (FEAT-YYYY-NNNN/G1-CLOSE)
    - status: pending       -> abandoned

  .specfuse/roadmap.md
    - row status column: active -> abandoned

Untouched (already done / passed):
  - WU-03-<slug>.md  (FEAT-YYYY-NNNN/T03, status: done)

Proceed? (yes / no)
```

If `no`: exit with no writes.

If `yes`: apply every edit. Report the count of files written.

### 4. Print the next step

- If other planned features exist on the roadmap: suggest
  `/pick-feature` to choose the next one.
- If no planned features remain: suggest `/draft-feature` to add
  one, or just say the roadmap is empty.

End with the RESULT block per
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the user confirmed and every planned write
applied. `status: blocked` is used only if a planned write could not
be applied (e.g. the roadmap row isn't in the expected format) —
write whatever did apply, then stop and report.

## What this skill does NOT do

- **Does not delete files.** Feature folder, WU files, gate files,
  events.jsonl — all stay. Abandoned ≠ erased.
- **Does not archive the roadmap detail section.** That's a separate
  skill (`/roadmap-archive`, future). The row's status column flip is
  the audit signal; archival is housekeeping.
- **Does not run git.** The user reviews via `git diff` and commits.
- **Does not flip a `done` feature.** History stays history.
- **Does not touch other features' files.**

## Version

**v0.1.** Four steps; the single-confirm posture is the entire
decision discipline today. Expected to grow once real abandonments
surface needs that don't fit it — e.g. partial-abandon (abandon
remaining gates, keep what's done as a separable subset), or a
"reason" field captured in PLAN.md frontmatter — which are real
possibilities but deferred until evidence warrants. Shared
methodology craft (loop is near-term author).
