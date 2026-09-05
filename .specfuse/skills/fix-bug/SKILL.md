---
name: fix-bug
description: "Triage and fix a reported bug \u2014 1 bug = 1 branch = 1 PR, test-first. Use when the user references a GitHub issue number, asks to fix a bug, or pastes a bug report. Refuses if the work is large/complex/risky and proposes promoting to a feature instead. Triggers \u2014 \"/fix-bug\", \"fix issue\", \"fix bug\", \"address issue NN\", \"patch NN\", pasting an issue URL."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Fix a reported bug (interactive)

This skill executes the project's bug-fix workflow on a single GitHub
issue. It is the **lightweight counterpart** to `/draft-feature`: bugs
do NOT go through the Specfuse feature methodology — no PLAN.md, no
gates, no retrospective, no roadmap row. The methodology is for
FEATURES (planned work). Bugs are unplanned, often urgent, and the fix
shape is well-known: write a failing test, fix code until it passes,
verify no regression, ship one PR.

**1 bug = 1 branch = 1 PR.** Hard contract.

## Hard rules

- **Test-first is non-negotiable.** No code edit before a failing test
  exists that replicates the bug. "I'll add the test after" is the
  documented anti-pattern — the test is the falsifiable claim and
  proves the fix actually fixed the right thing.
- **Never skip the gate run.** Full code gate set (tests + lint +
  security + coverage if declared in `.specfuse/verification.yml`)
  must pass after the fix. Claims of "tests pass" without proof are
  not evidence.
- **Never auto-merge.** The PR is opened; the operator decides when to
  merge after CI green + review.
- **Never promote mid-flow.** If scope expands beyond bug-fix size
  during execution (≥3 files touched, new abstractions introduced,
  contract change downstream consumers must observe, irreversible
  state migration), STOP the branch, surface the scope creep, and
  ask the user whether to promote to a feature via `/draft-feature`.
  Do NOT silently expand the branch into a feature's worth of work.
- **Reference the issue in commit + PR.** Commit message body and PR
  body MUST cite `closes #<issue-number>` so the issue auto-closes on
  merge. Audit trail = issue ↔ PR ↔ commit chain. No feature folder.
- **No methodology surfaces.** Do NOT create feature folders, PLAN.md,
  GATE-NN.md, WU-*.md, roadmap rows, or RETROSPECTIVE.md. Do NOT call
  the loop driver. Do NOT touch `.specfuse/features/`.

## When to invoke

- User references a GitHub issue number: "fix #42", "address issue 17",
  "look at bug 23".
- User pastes a bug report / issue URL.
- User asks to fix a misbehavior with a clear repro.
- User invokes `/fix-bug <issue#>` directly.

Do NOT invoke for: unconfirmed misbehavior (ask for repro first),
ambiguous "something seems broken" (triage first), or work that is
clearly feature-scoped (multi-file refactor, new capability, redesign).

## Method (strict order)

### 1. Fetch the issue

- `gh issue view <issue-number> --comments` (or accept the body if user
  pasted it). Plain `gh issue view` truncates at the issue body and
  drops comments — comments matter because a prior run on this same
  issue may have hit a halt and been answered by an operator since;
  reading them is the difference between repeating that refusal and
  resolving it.
- Read: title, labels, body, comments. Capture: symptom, repro steps,
  observed vs expected behavior, root-cause hypothesis (if author
  provided one), proposed fix shape (if author proposed one).
- If the issue has no clear repro: surface "no repro — need
  reproduction steps before I can write a falsifiable test" and stop.

### 2. Triage — bug or feature?

Bug indicators (proceed):

- Observable misbehavior with a concrete repro.
- Fix shape is bounded: ≤ 2 production files + 1 test file.
- No new abstractions, no contract change downstream consumers see,
  no irreversible state migration.
- The fix is "make the code do what the spec / docstring / type
  signature already promises."

Feature indicators (refuse + propose `/draft-feature`):

- ≥ 3 files modified, OR
- New abstractions / new modules / new APIs introduced, OR
- Contract change downstream consumers must observe (event-schema
  change, public API change, frontmatter-field addition), OR
- Irreversible state migration (data shape change, file-format
  evolution), OR
- The work needs coordination across multiple WUs (impl + tests +
  docs + skill update + migration).

If a feature indicator fires: STOP, print "this is feature-scoped, not
bug-scoped — promote to a feature via `/draft-feature`?" Wait for the
user's call.

### 3. Branch

- `git checkout main && git fetch origin && git rebase origin/main` to
  ensure a clean base.
- `git checkout -b fix/issue-<#>-<short-slug>` from main. The slug is
  3–5 hyphen-separated words describing the bug ("roadmap-row-parser",
  "legacy-4wu-terminal-flips"). Branch naming is structured so the
  issue ↔ branch ↔ PR audit trail is greppable.

### 4. Write a failing test

- Locate the test file most relevant to the affected code. If
  multiple call sites are affected, prefer a NEW dedicated test file
  named after the issue ("test_<short-slug>.py") so the regression
  surface stays auditable.
- Author one or more test cases that replicate the bug per the
  issue's repro. Tests must use real fixtures (no excessive mocking
  of the code under test).
- Run the new test(s): they MUST fail with output consistent with
  the issue's observed behavior. If they pass on the unchanged code,
  the test isn't replicating the bug — fix the test before fixing
  the code.

### 5. Fix the code

- Locate the buggy code (the issue's root-cause section is your
  starting point; verify against current source — code evolves).
- Apply the minimum change that makes the failing test pass.
- Do NOT bundle unrelated improvements ("while I'm here…"). Scope
  creep poisons audit. If you spot another bug in the same file,
  file a separate issue and address it on its own branch.

### 6. Run gates

Run the code gate set declared in `.specfuse/verification.yml`. For
this repo (specfuse/loop) that is:

```bash
python3 -m unittest discover -s tests -v          # tests
ruff check .specfuse/scripts tests scripts        # lint
bandit -r .specfuse/scripts -ll                   # security
coverage run --source=.specfuse/scripts -m unittest discover -s tests \
  && coverage report --fail-under=90              # coverage
```

ALL must pass. Coverage on the fixed file must stay above the floor;
if the fix drops it, write additional tests for the new branches.

If any gate fails: fix the underlying cause. Do NOT silence gates.
Do NOT add `# nosec` / `# noqa` to suppress new findings unless the
finding is a documented false positive and the suppression is
narrowly scoped + commented.

### 6.5. Diff self-check (before commit)

Step 2's triage ran against the issue text, before the fix existed. A
feature indicator can be invisible at triage and only become visible in
the diff the fix actually produces — e.g. the fix turns out to need a
new frontmatter field to carry state, which nothing in the issue text
predicted. Re-checking here closes that gap.

- After gates pass, re-apply Step 2's feature indicators to the diff
  itself (`git diff main...HEAD` / `git diff --stat`), not to the
  issue text triage already used.
- Mechanically check for the one indicator that's greppable in a diff:
  a new key added inside a YAML frontmatter block (`---` … `---`) that
  did not exist on the pre-fix side, in any changed file. That is the
  "frontmatter-field addition" indicator from Step 2 firing — treat it
  as fired even though Step 2 itself didn't catch it.
- Also re-read the diff against Step 2's other indicators (file count,
  new abstractions/modules, other contract changes, irreversible state
  migration) — these are harder to grep but still checkable by eye
  against the actual changed files.
- If any Step 2 indicator fires against the diff: STOP. Do not commit,
  push, or open a PR. This is the same situation as "When to break the
  rules" — a feature indicator surfacing mid-flow — handle it
  identically: surface the scope creep, propose `/draft-feature`, leave
  the branch in place as evidence.
- If no indicator fires: proceed to Step 7.

### 7. Commit + push + PR

- One commit, scoped to this fix. Message format:
  ```
  fix(<scope>): <one-line summary>

  Closes #<issue-number>. <One paragraph root cause.>

  <One paragraph fix description.>

  Tests:
  - <file>:<test_class> — <what it asserts>

  Verification:
  - <N> tests pass; <other gates green>

  Co-Authored-By: <as configured>
  ```
- **Before opening the PR**, append one entry to `CHANGELOG.md`'s
  `Unreleased` section (FEAT-2026-0064) via `specfuse/loop/changelog.py`'s
  schema: classified `added` / `changed` / `fixed` / `breaking`, one line
  derived from the same root-cause/fix understanding the commit message
  above already captures, carrying `#<issue-number>` as its trace. This is
  the bug side's collection point — bugs have no close ceremony to collect
  through, so `fix-bug` is where the entry is written or it is dropped.
  Include the `CHANGELOG.md` change in the same commit as the fix.
- `git push -u origin fix/issue-<#>-<short-slug>`.
- `gh pr create --title "fix(<scope>): <summary> (closes #<#>)" --body <markdown-body>`.
  PR body sections: Root cause, Fix, Tests, Verification. Reference
  the issue explicitly so the merge auto-closes it.
- Probe `gh auth status` once before any `gh` step — per LEARNINGS
  `[FEAT-2026-0014/T01/gh-claudeP-broken]`, gh can be unreliable; if
  it fails, print the exact `gh pr create` command for the operator.

### 8. Watch CI + report

- `gh pr checks <PR#> --watch --fail-fast` in background, OR print
  the command and exit.
- When CI completes:
  - **Green** → report PR URL + "merge when ready via `gh pr merge
    <#> --squash --delete-branch`". Do NOT auto-merge.
  - **Red** → fetch the failing job output, diagnose, surface to user.
    Common causes: a test that passes locally but fails on CI's
    container (environment-parity per LEARNINGS
    `[FEAT-2026-0013/G1-CLOSE]`), a flaky test (re-run once before
    re-fixing), a coverage drop from the new test file being
    excluded.

### 9. RESULT

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means: failing test was authored and verified to
fail on unchanged code, fix landed, all gates pass, the diff
self-check (Step 6.5) found no Step 2 indicator against the actual
diff, commit + push + PR opened, PR URL surfaced. `status: blocked` is
reserved for: the issue isn't a bug (feature-scoped — `/draft-feature`
instead), the repro can't be reduced to a failing test (insufficient
information), a gate failure that requires operator decision, or the
diff self-check found a Step 2 indicator against the actual diff.

## What this skill does NOT do

- **Does not auto-merge the PR.** Operator-owned decision.
- **Does not create a feature folder.** Bugs are out-of-methodology.
- **Does not modify roadmap.md.** Bugs don't get roadmap rows.
- **Does not modify LEARNINGS.md.** Unless the fix surfaces a durable
  rule that would change future bug fixes or feature authoring, the
  commit message + PR body carry the full audit.
- **Does not run the loop driver.** No `specfuse run` invocation.
- **Does not close the GitHub issue manually.** The `closes #<#>`
  reference in the merge commit auto-closes the issue. If the issue
  needs manual closure (e.g. user wants to keep it open for tracking
  related work), the operator handles it.
- **Does not handle multiple bugs at once.** One issue per
  invocation. If the user references two issues, ask which to fix
  first.

## When to break the rules

If the bug fix becomes too complex mid-flow — meaning a feature
indicator from Step 2 surfaces only after you've started — STOP the
branch immediately, do not delete it, surface the scope creep to the
user, and propose `/draft-feature`. The half-done branch becomes
evidence the operator can use to inform the feature scope. Never
silently grow a bug fix into a feature.


## Escalation framing (binding — `.specfuse/rules/operator-escalation.md`)

Whenever this skill halts for a human decision — a refusal, a blocked unit, a
review checkpoint, an option that only the operator can pick — present it in the
six parts that rule requires, in plain English, **before** any correlation ID,
guard name, or cost table: what has been done so far; what the issue is about;
what decision is needed and why; why it did not close automatically; the options
with their pros and cons; and a recommendation.

Never author the operator's own justification. Where a field records *why a human
decided something*, that text comes from them.

## Headless mode

Everything above this section describes the **interactive** path and is
unchanged by headless mode: same triage, same test-first discipline, same
`1 bug = 1 branch = 1 PR` contract, same refusal criteria. Headless mode is an
**invocation mode**, not a different workflow — a caller passes `mode:
headless` (vs. the default interactive invocation) and every point above that
would otherwise halt for a human resolves to one of three named, closed
outcomes instead.

**Step 6's gate commands run in the foreground (binding, headless-only).** A
headless session dispatches Step 6's gate commands inline and waits on their
own exit code, in the same turn — never handed off as an unwaited process the
skill expects a later completion signal for. A headless run's turn ends when
the run itself ends; twenty of 72 escalations in the 2026-09-02 unattended run
were finished fixes lost because the session ended mid-wait for a gate that
was, from the runner's point of view, still going. If the runner enforces a
wall-clock limit on the whole invocation, a foreground gate run that exceeds
it surfaces as this skill's own `could_not_proceed` (Step 6's row in the
mapping table below) — never as a silent stop with no recorded outcome.

**The closed outcome set** (no fourth outcome exists; a headless run always
ends in exactly one of these):

- **`refused`** — the skill's existing refusal criteria (Step 2's feature
  indicators, the Step 6.5 diff self-check finding one of those same
  indicators against the actual diff, or the Step 2/"When to break the
  rules" mid-flow scope-creep escalation) say this is not a bug-sized fix.
  The recorded reason names which criterion fired and, for Step 6.5, that
  it fired against the diff rather than the issue text.
- **`could_not_proceed`** — a precondition the workflow needs was missing:
  the issue has no clear repro (Step 1), the repro cannot be reduced to a
  falsifiable failing test (Step 4), a gate failure that would otherwise
  require an operator decision (Step 6/Step 9), or an operational
  precondition such as `gh auth status` failing (Step 7).
- **`completed`** — the fix ran end-to-end: failing test authored and
  verified red on unchanged code, fix applied, all gates green, the Step
  6.5 diff self-check found no Step 2 indicator against the actual diff,
  one commit, branch pushed, PR opened. Same definition of done as the
  interactive `status: complete` in Step 9.

**The rule (binding, explicit — not implied by the method above).** A
headless run never asks a question, never waits for input, and never
silently proceeds past a decision the interactive path would have escalated
to a human. Every point in the Method above that says "stop", "wait for the
user's call", "surface to user", or "ask" is, in headless mode, a fork: take
the branch that the operator's answer would have picked only if the
workflow's own deterministic criteria already picked it (e.g. a bug
indicator with no feature indicator firing); otherwise resolve to the named
outcome that halt maps to and stop. The interactive prompt text itself is
never shown and never answered — the mapping table below is exhaustive.

**Halt → outcome mapping**, enumerated from the current skill body so the
mapping stays honest as the method above evolves:

| Interactive halt (Method step) | What it decides | Headless outcome |
| --- | --- | --- |
| Step 1 — issue has no clear repro | precondition missing | `could_not_proceed` |
| Step 2 — a feature indicator fires ("STOP, print... promote to a feature?") | refusal criterion | `refused` |
| Step 4 — test can't be made to fail on unchanged code | precondition missing | `could_not_proceed` |
| Step 6 — a gate failure needs an operator decision | precondition missing | `could_not_proceed` |
| Step 6.5 — Diff self-check finds a Step 2 indicator against the actual diff | refusal criterion | `refused` |
| Step 7 — `gh auth status` fails, `gh` unavailable | precondition missing | `could_not_proceed` |
| "When to break the rules" — scope creep discovered mid-flow | refusal criterion | `refused` |
| Step 9 RESULT `status: blocked` — issue isn't a bug (feature-scoped) | refusal criterion | `refused` |
| Step 9 RESULT `status: blocked` — repro can't reduce to a failing test | precondition missing | `could_not_proceed` |
| Step 9 RESULT `status: blocked` — gate failure requiring operator decision | precondition missing | `could_not_proceed` |

No refusal path is weakened or removed for headless mode: every criterion in
Step 2 and "When to break the rules" still fires exactly as written, and
still stops the branch before any PR is opened. Headless mode only replaces
*who is told* (a recorded outcome instead of a printed question) — never
*what fires*.

**What headless mode does not add.** It does not invoke itself, does not
name a caller or an argument schema, and does not run against a real issue —
that wiring belongs to the caller that invokes `fix-bug` in headless mode
(see `FEAT-2026-0042` gate 2), not to this skill definition.

## Version

**v0.1.** Nine steps; the bug-vs-feature triage and the test-first
discipline are the two load-bearing rules. Expected to grow as the
first 5–10 bugs surface patterns (e.g. when CI's environment-parity
matters, when a fix legitimately needs ≥ 3 files because the bug
spans them). Graduated from the two-PR sequence in PRs #18 + #19 that
established the workflow shape and the `bug_fix_workflow.md` memory
that codified the rules.
