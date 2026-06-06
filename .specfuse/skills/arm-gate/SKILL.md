---
name: arm-gate
description: At a gate boundary — driver halted with `awaiting_review` on the just-completed gate and next gate's WUs in `draft` — walk the drafts, accept / revise / reject each, flip statuses, mark the completed gate `passed`, and print the resume command. The human-review-and-arm checkpoint of the methodology, made fast.
---

# Arm gate (interactive, propose-and-confirm)

This skill is the per-gate human checkpoint of the methodology. The
loop driver halts at the end of every gate with the just-completed
gate in `status: awaiting_review` and the next gate's WUs sitting in
`status: draft` (written by the prior gate's `plan-next` closing
unit). This skill walks the drafts one by one, asks accept/revise/
reject per WU, applies the flips, marks the completed gate
`status: passed`, and tells you the command to resume.

Posture mirrors `/draft-feature` and `/feature-conversion`:
propose-and-confirm-per-WU. The skill writes nothing without your
explicit decision on each draft.

**Run interactively.** Per-draft prompts are the whole point;
`claude -p` with redirected stdin cannot ask, falls back to a
degraded "list drafts and stop" mode.

## Hard rules

- **Per-draft decision required.** No batch-accept-all (defeats the
  human checkpoint). Each draft is its own accept/revise/reject.
- **Modify only WU status fields and the gate file.** Two write
  surfaces per accepted/rejected WU (the WU's status), one for the
  completed gate (its status). No body edits, no PLAN graph surgery,
  no roadmap edits. If a draft needs heavy revision, exit the skill
  and edit the WU file directly.
- **Honor the methodology arm-discipline.** Only `draft` → `pending`
  or `draft` → `abandoned`. Never `draft` → `done` (that's the
  driver's flip after a real PASS); never touch substantive WUs
  already in `pending` or `in_progress`.

## When to invoke

When `./scripts/smoke-test.sh` or `python3 .specfuse/scripts/loop.py`
just printed `Gate N complete (retro, lessons, docs, plan-next). The
next gate has been drafted. …`, or any time a gate file sits at
`status: awaiting_review` and the next gate has drafts pending review.

If no gate is in `awaiting_review`, the skill stops with a hint
(probably you wanted `/gate-status` for a blocked WU, or
`/draft-feature` to start a new feature).

## Method

### 1. Detect the state

- Find the active feature (roadmap `status: active`; if multiple,
  ask).
- Walk PLAN.md's gates graph in order. Find the first gate whose
  GATE file has `status: awaiting_review` — that's the **completed**
  gate. The next gate after it in the graph is the **target** gate
  whose drafts you're arming.
- If no `awaiting_review` gate exists, stop and explain.

### 2. Read the review context

- `GATE-NN-REVIEW.md` (the just-completed gate's review summary,
  written by `plan-next`). Quote its "if you check only three things"
  block and its open questions to you up front so they shape your
  thinking about the drafts.
- `.specfuse/LEARNINGS.md` tail — any new rules surfaced by the
  just-completed gate that affect the drafts.
- Briefly summarize: "Gate N drafted M substantive WUs + the four
  closing-sequence units. Reviewing them in order."

### 3. Per-draft accept / revise / reject

For each WU in the target gate whose `status: draft`:

1. **Show**: the WU's ID, title, type, model, the body's five
   sections in compact form (Context one-liner, Acceptance criteria
   bullets, Do-not-touch list, Verification gate set, Escalation
   triggers).
2. **Anchor against the review summary**: if `plan-next` flagged
   uncertainty about this WU specifically, name it now.
3. **Ask**: `Accept (a) / Revise (r) / Reject (j) / Skip (s)`?
   - **Accept** — flip `status: draft` → `status: pending`. WU is
     now armed; loop will dispatch on resume.
   - **Revise** — ask the user what to change. For small edits
     (typo, model swap, one acceptance criterion tweak), apply
     directly and then flip to `pending`. For substantial edits,
     stop and tell the user to open the WU file directly — this
     skill is not a substitute for direct editing on big changes.
   - **Reject** — flip `status: draft` → `status: abandoned`. The
     WU stays in the PLAN graph (don't do graph surgery) but the
     loop will skip it (`abandoned` is not in `DISPATCHABLE`). The
     user can later delete the row from PLAN.md and the WU file
     by hand. Worth pausing to note: an abandoned closing-sequence
     WU breaks the gate's mandatory closing sequence; lint will
     reject it. Reject only substantive WUs unless replacing the
     closing-sequence unit immediately.
   - **Skip** — leave at `draft`, move to next. The gate cannot be
     armed with drafts remaining (per the methodology); the skill
     reminds you at the end and refuses the final mark-passed step.

Defer per-WU craft (what makes a good Acceptance criterion, etc.)
to [`../authoring-work-units/SKILL.md`](../authoring-work-units/SKILL.md) —
don't restate those rules here.

### 4. Mark the completed gate `passed`

Once every draft in the target gate has a non-`draft` status (all
accepted or rejected, none skipped):

- Edit the completed gate's GATE-NN.md frontmatter: `status:
  awaiting_review` → `status: passed`.
- Confirm the change to the user.

If any draft is still `draft` (skipped), DO NOT mark the gate
passed. Tell the user which drafts remain and stop.

### 5. Print the resume command

Tell the user the exact command to resume:

- One active feature: `python3 .specfuse/scripts/loop.py`
- Multiple active features: `python3 .specfuse/scripts/loop.py
  --feature FEAT-YYYY-NNNN-<slug>` (name the chosen feature).

Mention: if you want to confirm before dispatching, run with
`--dry-run` first.

End with the RESULT block per
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means every draft was decided and the gate was
marked passed (or the user accepted that some drafts stay at
`draft` and the gate stays `awaiting_review`).

## What this skill does NOT do

- **Does not heavy-edit WU bodies.** Small inline tweaks during
  Revise are fine; major rewrites belong in a direct file edit.
- **Does not modify the PLAN.md gates graph.** Rejected WUs stay
  in the graph as `abandoned`; the user prunes by hand if they
  want.
- **Does not delete WU files.** Same reasoning — file removal is
  one of those small acts that's easier to do by hand than
  approve-prompt-by-approve-prompt.
- **Does not run the loop.** Prints the command; the user runs it.
- **Does not touch the roadmap.** Roadmap `active` → `done`
  belongs at feature completion (final gate), not per-gate.

## Version

**v0.1.** Five steps; the accept/revise/reject/skip option set is
the entire per-draft decision vocabulary today. Expected to grow
once real multi-gate runs surface drafts that don't fit it —
e.g. "merge two drafts," "split one draft into two," "add a
hygiene WU before this one" — which are real possibilities but
deferred until evidence warrants. Shared methodology craft (loop
is near-term author).
