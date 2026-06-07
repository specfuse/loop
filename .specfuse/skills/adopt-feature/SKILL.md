---
name: adopt-feature
description: List a GitHub repo's open `specfuse:feature` issues as a numbered pick list, accept the human's explicit choice, and scaffold a dispatchable loop-feature folder via adopt_feature.py — the "pick a GitHub issue and grind it" entrypoint for any Specfuse-integrated project.
---

# Adopt a GitHub feature (interactive)

This skill turns a GitHub `specfuse:feature` issue into a dispatchable loop-feature
folder. It enumerates open `specfuse:feature` issues in a target repo, presents them
as a numbered pick list, and on your explicit choice invokes `adopt_feature.py` to
scaffold the folder. The scaffolding behavior lives in `adopt_feature.py` (T03); this
skill is the interactive wrapper humans invoke.

**Run interactively.** The skill presents a pick list and waits for your choice.
`claude -p` with stdin redirected cannot accept a pick; start `claude` in the target
project's working directory.

## Hard rules

- **Recommend, never decide.** The output is a pick list; the human chooses by row
  number or `feature_id`. A skill that picks for you hides the trade-off that matters.
- **Honor active features.** If `.specfuse/roadmap.md` shows any feature with
  `status: active`, surface it first and recommend finishing it before adopting
  another. Only proceed to the pick list on explicit user override.
- **Modify only the new feature folder via the T03 script.** `adopt_feature.py`
  creates exactly one new folder under `.specfuse/features/`. No other file is touched
  by this skill or the script it invokes.
- **Infer first, ask last.** A question is legitimate only when no file the skill could
  read would answer it. Asking "what repo?" when a CLI argument was supplied is a skill
  bug.
- **The issue body IS the WU contract.** `adopt_feature.py` seeds `WU-01` with the
  raw issue body verbatim. Do not rewrite, summarize, or paraphrase it during
  adoption — that is `/draft-feature`'s job.

## Method

### 1. Resolve the target repo

If the skill was invoked with a `<owner/repo>` argument (e.g.
`/adopt-feature myorg/myrepo`), use it directly. Otherwise ask once:

> Which GitHub repo? (format: `owner/repo`)

Do not ask if the value is already present in the invocation.

### 2. Detect active work and respect it

Read `.specfuse/roadmap.md`. If any row has `status: active`, surface it before
continuing:

> You have FEAT-XXXX-NNNN ("title") active. The methodology default is to finish an
> active feature before adopting another. Override intent (parallel track, active is
> blocked, etc.) — or finish it and re-run?

Only proceed to step 3 on explicit user override.

### 3. Enumerate candidates

Call `list_features('<repo>')` from `.specfuse/scripts/gh_features.py`
programmatically (preferred — returns the full candidate dict including `title`,
`initiative`, `number`, and `body`):

```python
import sys; sys.path.insert(0, '.specfuse/scripts')
from gh_features import list_features
candidates = list_features('<repo>')
```

Alternatively run:

```
python3 .specfuse/scripts/gh_features.py <repo>
```

Issues whose titles lack a parseable `[<id>]` tag are skipped by the script with a
warning on stderr — surface those warnings. If `gh` is not authenticated, print the
error verbatim and stop.

### 4. Present the pick list

Sort candidates descending by GitHub issue `number` (highest = most recent). Take the
top 5; if fewer than 2 exist, present whatever is available.

Render a markdown table:

```
| # | feature_id     | title   | initiative | type   | autonomy | url   |
|---|----------------|---------|------------|--------|----------|-------|
| 1 | FEAT-YYYY-NNNN | <title> | <init>     | <type> | <auto>   | <url> |
...
```

Then prompt:

```
Which one? (pick by # or feature_id, or "skip — I'll decide later")
```

### 5. Accept the pick

Accept the human's choice by row number (`1`–`5`) or by `feature_id` string. Any
other input is not a pick — confirm once, then stop if still unclear. Record the
picked candidate's GitHub issue `number` for step 6.

### 6. Invoke adopt_feature.py

Run:

```
python3 .specfuse/scripts/adopt_feature.py <repo> <issue-number>
```

where `<issue-number>` is the GitHub issue `number` from the picked candidate row
(not the display index `#`). Print the script's stdout verbatim — one line: the
created folder path.

If the script exits non-zero (folder already exists, issue not found, network error),
print stderr verbatim and stop without further writes.

### 7. Print the next command

```
Run /draft-feature on the new folder to refine gate 1, or
python3 .specfuse/scripts/loop.py --feature <folder> to dispatch as-seeded.
```

where `<folder>` is the path printed in step 6.

---

End with the RESULT block defined in
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the human picked, `adopt_feature.py` ran without error, the
folder path printed, and the next-command line printed. `status: blocked` if
`adopt_feature.py` exited non-zero, `gh` is unauthenticated, or the active-feature
warning was not overridden.

## What this skill does NOT do

- **Does not flip status to `active`.** The new feature's `PLAN.md` is seeded with
  `status: planned`; the human arms it via `/pick-feature` or by editing the roadmap
  directly.
- **Does not edit other features, binding rules, or templates.** The only write is the
  new folder created by `adopt_feature.py`. No other file is touched.
- **Does not run git.** No commits, no branches, no staging. The driver owns all git.
- **Does not refine the seeded WU-01.** `adopt_feature.py` seeds `WU-01` with the raw
  issue body; refinement is `/draft-feature` or the gate 1 grind.
- **Does not loop or auto-dispatch.** After printing the next command, the skill exits.
  The human runs `loop.py` when ready.

## Version

**v0.1.** Seven steps; the `list_features` call and the active-feature guard are the
entire interaction shape today. Expected to grow once real GitHub repos are adopted
with it — which columns the pick table needs, whether the active-feature warning
fires too aggressively, where the folder path needs surfacing in a different format.
