---
name: pick-feature
description: Read the project's Specfuse roadmap and surface 2-3 next-feature candidates with hat-based trade-offs, so the human can decide faster. Does NOT pick — feature selection is a strategy call. Lean v0.1; useful once the roadmap has enough planned items that "skim and pick" stops being instant.
---

# Pick a feature (interactive, surfacing — never deciding)

This skill helps you decide which planned feature to pull next on a
Specfuse-integrated project's roadmap. It reads the roadmap, the
durable lessons, and the planned features' framings, then proposes
**2–3 candidates with trade-offs surfaced** — never one answer, never
a written change. You pick.

**Run interactively.** The skill may ask one batched round of
clarifying questions (capacity, deadline, recent context). `claude -p`
with stdin redirected won't have that channel; degraded mode produces
a less-tailored comparison.

## Hard rules

- **Surface, don't decide.** The skill's output is a comparison plus
  a recommendation; the human picks. A skill that hands you a single
  answer hides the trade-offs that matter.
- **Don't modify anything.** No edits to roadmap, no status flips, no
  new files. The skill only reads.
- **Honor active features.** If a feature is already `active`, the
  default recommendation is "finish that one first." Only override on
  explicit user direction.
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
  (`planned` / `active` / `done` / `abandoned`) and one-line goal are
  the primary input.
- **`.specfuse/LEARNINGS.md`** — durable rules from past gates that
  would change the shape of feature to pull next (e.g. "after a
  refactor-heavy gate, pull a feature with clear acceptance criteria
  to recover trust").
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

### 5. Present 2–3 candidates with a recommendation

Output format — a compact comparison the user can act on in seconds:

```
Candidates (active: FEAT-XXXX or none)

| ID             | Title           | Why pull now                              | Cost  | Risk |
|----------------|-----------------|-------------------------------------------|-------|------|
| FEAT-YYYY-NNNN | <title>         | <one-line hat-anchored reason>            | S/M/L | L/M/H|
| FEAT-YYYY-NNNN | <title>         | <one-line hat-anchored reason>            | ...   | ...  |
| FEAT-YYYY-NNNN | <title>         | <one-line hat-anchored reason>            | ...   | ...  |

Recommendation: FEAT-YYYY-NNNN, because <one sentence anchored in
the hat that mattered most for this comparison>. The runners-up
have <one-line reason each>; if <condition>, prefer them.

Next step (yours): pick one, then run /draft-feature against it.
```

Keep it short. The point is to make the trade-off visible, not write
an essay. Three candidates is the cap — more dilutes attention.

End with the RESULT block defined in
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the comparison was produced and shown.

## What this skill does NOT do

- **Does not pick for you.** It recommends and explains; you decide.
- **Does not modify the roadmap or any feature file.** Read-only.
- **Does not draft the chosen feature.** That handoff is to
  `/draft-feature`. Out of scope here; the recommendation line above
  names it.
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
