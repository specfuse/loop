---
name: attention
description: "Local inbox sweeping .specfuse/ repo state and the needs-human GitHub issue queue into one priority-ordered list of everything needing a human. Read-only view over the same state gate-status and the issue queue already hold; never a second source of truth. Degrades gracefully when gh is unavailable."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Attention (interactive, read-only inbox)

This skill answers "what needs me right now, across everything?" It sweeps repo
state under `.specfuse/` and the `needs-human` labelled GitHub issue queue into a
single priority-ordered list, so the operator's check-in ritual is "open
`/attention`, work top-down" instead of a manual, feature-by-feature memory sweep.

## Hard rules

- **Read-only.** The skill produces text; it does not write. It does not flip a
  work unit's status, does not flip a gate's status, does not close or comment on
  a GitHub issue, and does not touch any file under `.specfuse/`. Every surface it
  reads stays exactly as it found it.
- **Never a second source of truth.** The `needs-human` issue queue is
  authoritative for escalations. This skill presents that queue plus a repo-state
  sweep; it does not maintain its own record of what needs attention, and it does
  not duplicate the issue contract's data anywhere on disk.
- **Delegate per-feature diagnosis, don't reimplement it.** For any blocked work
  unit or `awaiting_review` gate this skill surfaces, the deep diagnosis (what's
  blocked, likely root cause, options, recommended action) is `gate-status`'s job.
  This skill names the feature and points at `gate-status`; it does not carry its
  own copy of that diagnosis logic.
- **Degrade, don't fail.** If `gh` is unavailable or unauthenticated, the stale-PR
  sweep is skipped and reported as skipped — the rest of the sweep (everything
  under `.specfuse/`) still runs and is still reported in full.

## When to invoke

Any time the operator returns to the repo and wants one place to see everything
parked for a human, across every feature at once — not just the active one.

## Method

### 1. Sweep local repository state

Read `.specfuse/roadmap.md` and every `.specfuse/features/FEAT-*/` folder. Collect
four classes of state, purely from files on disk:

1. **`blocked_human` work units** — any WU file whose frontmatter `status` is
   `blocked_human`, in any feature folder, not just the active feature.
2. **`awaiting_review` gates** — any `GATE-NN.md` whose frontmatter `status` is
   `awaiting_review`.
3. **`blocked` features** — any roadmap row whose `Status` is `blocked`; read the
   feature's `**Blocked by.**` detail block to name what it's waiting on.
4. **`stale` pull requests** — open PRs with no activity past a reasonable
   staleness window. This is the one class that cannot be read from
   `.specfuse/` files.

### 2. Check for silence

Call `specfuse.loop.heartbeat.silence_check` on open and print the staleness
line among this sweep's sections. Do **not** fire the webhook from here — a
human is already reading this output, so the notification the scheduled path
exists for would be redundant.

### 3. Sweep the needs-human issue queue

Query GitHub for open issues carrying the `needs-human` label (the label defined
by `specfuse/loop/escalation.py`'s `NEEDS_HUMAN_LABEL`). For each, read its
category label (one of `CATEGORY_LABELS`: `gate-review`, `blocked-wu`,
`triage-question`, `drafting-needed`, `merge-approval`) and its assignee.

**Graceful `gh` degradation.** Probe `gh auth status` once. If `gh` is
unavailable or unauthenticated, skip both the issue-queue sweep and the stale-PR
sweep, report plainly that they were skipped and why, and continue — the local
`.specfuse/` sweep from step 1 still runs and is still reported in full. Do not
fail the whole sweep because one input is unreachable.

### 4. Delegate per-feature depth to gate-status

For any `blocked_human` work unit or `awaiting_review` gate this sweep surfaces,
do not re-derive root cause, options, or a recommendation here — name the feature
and point at `gate-status`, which already synthesizes that diagnosis for a single
feature. Running `gate-status` against each flagged feature is how depth is added
without duplicating its logic.

### 5. Present in priority order, top-down

Render one combined list, most urgent first, so the operator can work strictly
top-down without re-sorting mentally.

## Priority order

1. `blocked_human` work units — an agent already tried and gave up; the loop is
   stalled until a human acts.
2. `awaiting_review` gates — a gate boundary is waiting on the human
   accept/revise/reject checkpoint.
3. `blocked` features — a named dependency (an ADR or an upstream feature) is
   unmet; resumable once a human clears it.
4. `stale` pull requests — green and ready, or silently rotting, either way
   waiting on a human to look.

Needs-human issues from the GitHub queue are interleaved into this same ordering
by their category label, since each category maps onto one of the four classes
above (e.g. `blocked-wu` alongside `blocked_human` work units, `gate-review`
alongside `awaiting_review` gates).

## What this skill is not

Not a second source of truth: the issue queue and `.specfuse/` state remain
authoritative; this skill only presents what it reads. Not a diagnosis engine:
depth on any blocked item comes from `gate-status`, not from logic duplicated
here. Not a dispatcher: it never runs the loop, never re-arms a work unit, and
never answers an escalation on the operator's behalf.
