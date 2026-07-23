---
name: pick-feature
description: "Read the project's Specfuse roadmap and present 2-3 next-feature candidates as a pick list with hat-based trade-offs. On your explicit pick, flip status from `planned` to `active` (in roadmap.md and PLAN frontmatter if it exists) and print the next command (/draft-feature if no folder yet, loop.py if gate 1 is detailed). The human picks; the skill executes the pick."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Pick a feature (interactive)

This skill helps you decide which planned feature to pull next on a
Specfuse-integrated project's roadmap, then executes the pick. It
reads the roadmap, the durable lessons, and the planned features'
framings; proposes **2–3 candidates with trade-offs surfaced**;
presents them as a pick list; and on your choice flips the chosen
feature's status to `active` and tells you exactly what command to
run next.

The skill recommends but does not decide — the choice is yours. Once
you've chosen, the mechanical work (status flip in roadmap and any
PLAN frontmatter; next-command instruction) is the skill's job.

**Run interactively.** The skill needs the channel to present the
pick list and ask any clarifying question. `claude -p` with stdin
redirected won't have that channel; degraded mode produces the
comparison but cannot accept your pick.

## Hard rules

- **Recommend, never decide.** The output is a comparison with a
  recommendation; the human picks from the list. A skill that picks
  for you hides the trade-offs that matter.
- **Modify only the chosen feature's status, only on explicit pick.**
  Two writes per accepted pick: the roadmap row's status column
  (`planned` → `active`), and the chosen feature's `PLAN.md`
  frontmatter (`status: planned` → `status: active`) if a folder
  already exists. Nothing else.
- **Honor active features.** If a feature is already `active`,
  surface it first and recommend finishing it before pulling a new
  one. Only proceed to the pick list on explicit user override. Do
  NOT auto-demote the existing active — the user owns that
  transition (mark it `done`, `blocked_human`, `abandoned`, or
  leave it parallel).
- **`deferred` and `blocked` are not pick candidates — and not active
  blockers.** A `deferred` feature is parked by choice; a `blocked` feature
  waits on a named unmet dependency (an ADR or upstream feature, linked from
  its detail section's `**Blocked by.**` block). For either: do NOT offer it in
  the pick list (neither is `planned`), and do NOT treat it as the current
  active that must be finished first (neither is `active`, nothing is
  loop-dispatchable). Resuming one is a human flip to `active`, not a pick.
  When a `blocked` feature's blocker is itself a `planned`/`active` roadmap
  feature, note that in the Dependency-hat read — pulling the blocker unblocks
  it.
- **Infer first, ask last.** A question is legitimate only when no
  file the skill could read would answer it. Asking "what's the
  goal?" when `roadmap_goal` is set in PLAN frontmatter is a bug.

## When to invoke

When you have multiple `planned` rows on `.specfuse/roadmap.md` and
want a structured read on which to pull next. For a single-item
roadmap, this skill is solving nothing — just start it.

## Method

### 1. Read the roadmap and the durable lessons

- **`.specfuse/roadmap.md`** — the master index. Each row's status
  (`planned` / `active` / `blocked` / `deferred` / `done` / `abandoned`) and
  one-line goal are the primary input.
- **Durable lessons, sliced, not the whole file.** Run
  `python3 .specfuse/scripts/learnings_query.py "<query>" --top 15`
  rather than reading `.specfuse/LEARNINGS.md` whole. Because this
  skill ranks 2-3 candidate features, not one, there is no single
  feature query — build `<query>` as the **concatenated one-line
  goals and slugs of every `planned` row under comparison** (the
  roadmap rows from step 1 above), and keep `--top` at 15 or higher
  so a lesson relevant to a lower-ranked candidate isn't dropped. If
  the CLI instead prints the sentinel line `LEARNINGS-LOAD-WHOLE`,
  fall back to reading `.specfuse/LEARNINGS.md` in full. Also prefer
  the whole-file read outright when the comparison set is large or
  heterogeneous (many candidates spanning unrelated areas) — a
  diffuse comparison is exactly where slicing risks dropping a needed
  lesson, so don't force a narrow query onto it.
- For each `planned` row that has a feature folder under
  `.specfuse/features/`, read its `PLAN.md` frontmatter (the
  `roadmap_goal`, the framing prose if present, and the gates graph
  to see if a skeleton was drafted ahead). Most planned features
  won't have a folder yet — that's fine; the roadmap row is the
  signal.

### 2. Detect active work and respect it

If a feature has `status: active`, that's the default next thing to
work on. Surface it first:

> You have FEAT-XXXX-NNNN ("title") active. The methodology default
> is to finish an active feature before starting another. Override
> intent (parallel track, dependency on a different planned feature,
> active is blocked, etc.) — or finish it and re-run?

Only proceed to ranking planned features if the user explicitly says
to override.

### 3. Ask, only if evidence is thin

If the roadmap rows are well-described (a real one-line goal each)
and LEARNINGS gives clear orientation, skip this step. Otherwise
batch a short round, choosing the few that matter:

- **Capacity** — single feature next, or parallel? (Default: single.)
- **Constraint** — is there a deadline, a stakeholder ask, or an
  external dependency that pins the choice?
- **Recent context** — anything that happened since the roadmap was
  last edited that should reshuffle? (A bug surfaced, a customer
  ask, a postmortem.)

### 4. Apply the hats to rank candidates

For each planned feature on the roadmap, score it briefly through
3–4 of these hats. Choose hats whose perspective actually differs
across candidates — a hat that scores everything the same is dead
weight here.

- **Dependency hat** — does this unblock other planned features, or
  is it a leaf? Unblockers tend to pay forward.
- **Risk hat** — what's the uncertainty? High-uncertainty features
  surfaced early teach you what you don't know; deferred they
  surprise late.
- **Value hat** — what user-observable outcome does this produce, and
  how soon? Outcomes that ship a real win soonest tend to win ties.
- **Cost hat** — how big does the gate skeleton look? Smaller is
  faster to ship and gives a faster feedback signal into the next
  pick.
- **LEARNINGS hat** — what do durable lessons from past gates say
  about pulling this shape of feature next?

### 5. Present 2–3 candidates as a pick list

Output format — a compact comparison the user can act on in seconds:

```
Candidates (active: FEAT-XXXX or none)

| # | ID             | Title    | Why pull now                       | Cost  | Risk |
|---|----------------|----------|------------------------------------|-------|------|
| 1 | FEAT-YYYY-NNNN | <title>  | <one-line hat-anchored reason>     | S/M/L | L/M/H|
| 2 | FEAT-YYYY-NNNN | <title>  | <one-line hat-anchored reason>     | ...   | ...  |
| 3 | FEAT-YYYY-NNNN | <title>  | <one-line hat-anchored reason>     | ...   | ...  |

Recommendation: #1 (FEAT-YYYY-NNNN), because <one sentence anchored
in the hat that mattered most>. #2 if <condition>; #3 if <other>.

Which one? (1 / 2 / 3, or "none — show me more" / "tell me more
about #X" / "skip — I'll pick later")
```

Keep the table short — three candidates is the cap, more dilutes
attention.

### 6. On explicit pick, flip status and name the next command

When the user picks a candidate by number (or by ID):

- **Roadmap row.** Edit `.specfuse/roadmap.md`: find the chosen
  feature's row by its `FEAT-YYYY-NNNN` ID and change its status
  column from `planned` to `active`. Leave other rows alone.
- **PLAN frontmatter (if folder exists).** If
  `.specfuse/features/FEAT-YYYY-NNNN-<slug>/PLAN.md` exists, change
  its frontmatter `status: planned` to `status: active`. If no
  folder exists yet (just a roadmap row), skip this — the folder
  will be created by the next step.
- **Print the next command:**
  - If no feature folder exists for the pick: `Run /draft-feature
    to author the feature folder.`
  - If a folder exists with gate 1's WUs detailed: `Run python3
    .specfuse/scripts/lint_plan.py .specfuse/features/<folder> &&
    python3 .specfuse/scripts/loop.py --dry-run to verify, then
    python3 .specfuse/scripts/loop.py to start dispatching.`
  - If a folder exists but gate 1 isn't detailed: `Run /draft-feature
    to fill in gate 1's WUs.`
- **If another feature is `active`,** the skill flipped the pick to
  active too — the loop driver requires `--feature` to disambiguate
  when more than one is active. Surface this in the output: `Note: N
  features are now active. Either pass --feature to loop.py, or
  demote one of {list} via roadmap.md and its PLAN frontmatter.`

If the user says "skip — I'll pick later" or "none — show me more,"
exit without modifying anything.

End with the RESULT block defined in
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the user picked, the status flip(s) wrote,
and the next-command instruction printed. `status: blocked` is used
only if the roadmap edit could not be applied (e.g. the roadmap row
isn't in the expected format and the linter would reject the edit).

## What this skill does NOT do

- **Does not pick for you.** It recommends and explains; you choose
  from the list.
- **Does not modify anything beyond the chosen feature's status.**
  Two writes per pick: the roadmap row and (if it exists) the PLAN
  frontmatter. Other features, other rows, other files — untouched.
- **Does not demote the existing active feature.** If one is already
  active and you intentionally start a parallel pick, you decide
  what to do with the old one (mark done / blocked_human /
  abandoned / leave parallel). The skill notes the consequence;
  the transition is yours.
- **Does not draft the chosen feature's contents.** That handoff is
  `/draft-feature`. The next-command line names it when needed.
- **Does not re-prioritize across teams** beyond what the project's
  own roadmap and LEARNINGS encode. If the project has a separate
  prioritization tool (Jira, Linear), this skill complements it; it
  doesn't replace it.

## Version

**v0.1.** Five steps; the hats are the entire ranking move today.
Expected to grow once the loop is used on a project with a roadmap
big enough that selection actually friction-bound the work — which
hat earned a tie-break, which candidate count was wrong, when the
user wanted a different output shape than the comparison table.
Shared methodology craft (loop is near-term author, like the
addendum).
