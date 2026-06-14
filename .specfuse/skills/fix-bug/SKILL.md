---
name: fix-bug
description: Triage and fix a reported bug — 1 bug = 1 branch = 1 PR, test-first. Use when the user references a GitHub issue number, asks to fix a bug, or pastes a bug report. Refuses if the work is large/complex/risky and proposes promoting to a feature instead. Triggers — "/fix-bug", "fix issue", "fix bug", "address issue NN", "patch NN", pasting an issue URL.
---

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

- `gh issue view <issue-number>` (or accept the body if user pasted it).
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
fail on unchanged code, fix landed, all gates pass, commit + push + PR
opened, PR URL surfaced. `status: blocked` is reserved for: the
issue isn't a bug (feature-scoped — `/draft-feature` instead), the
repro can't be reduced to a failing test (insufficient information),
or a gate failure that requires operator decision.

## What this skill does NOT do

- **Does not auto-merge the PR.** Operator-owned decision.
- **Does not create a feature folder.** Bugs are out-of-methodology.
- **Does not modify roadmap.md.** Bugs don't get roadmap rows.
- **Does not modify LEARNINGS.md.** Unless the fix surfaces a durable
  rule that would change future bug fixes or feature authoring, the
  commit message + PR body carry the full audit.
- **Does not run the loop driver.** No `loop.py` invocation.
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

## Version

**v0.1.** Nine steps; the bug-vs-feature triage and the test-first
discipline are the two load-bearing rules. Expected to grow as the
first 5–10 bugs surface patterns (e.g. when CI's environment-parity
matters, when a fix legitimately needs ≥ 3 files because the bug
spans them). Graduated from the two-PR sequence in PRs #18 + #19 that
established the workflow shape and the `bug_fix_workflow.md` memory
that codified the rules.
