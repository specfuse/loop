<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Content leak-scan GitHub Action

`.github/workflows/leak-scan-content.yml` extends the leak-scan guard from
committed files to the **public text surface** of the repository: the title and
body of issues and pull requests, and the body of the comment that triggered the
run. It wires the T03 content-scan runner
(`.specfuse/scripts/leak_scan_content.py`) to live GitHub events and fails the
check on any finding.

This is the public-surface half of issue #46. The file-commit half is the
existing `leak-scan` gate run from `ci.yml`; the two are complementary — one
sees diffs, the other sees the text people type into the GitHub UI.

## What it scans

The Action triggers on:

- `issues` — `opened`, `edited`
- `pull_request` — `opened`, `edited`
- `issue_comment` — `created`, `edited`

On each event GitHub Actions writes the event payload to a JSON file and exports
its path as `$GITHUB_EVENT_PATH`. The runner reads that **event payload** and
scans the fields present for the triggering event:

| Event                | Fields scanned                          |
| -------------------- | --------------------------------------- |
| `issues`             | `issue.title`, `issue.body`             |
| `pull_request`       | `pull_request.title`, `pull_request.body` |
| `issue_comment`      | `comment.body`                          |

Each field is run through the gate-1 scanner (`leak_scan.scan_text` — structural
patterns, the plaintext denylist, and gitleaks) plus the committed hashed
denylist. A finding makes the runner exit non-zero, which **fails the check**.

## Default behavior: fail the check

A hit fails the job and nothing more. This needs only:

```yaml
permissions:
  contents: read
```

No write scope, no token-scope risk. Failing the check is the signal; the author
sees a red check and edits the offending text out.

Posting a comment that names the offending field is a deliberate **non-goal** of
this workflow — it would require `pull-requests: write` / `issues: write`, a
broader token scope. That enhancement is operator-confirmable and tracked in
`GATE-02-REVIEW.md` Open Verifications, not built here.

## Limitation: edit history is not expunged

The guard stops *new* leaks landing on open/edit, but it **cannot expunge a leak
that was already published**. GitHub retains the full **edit history** of an
issue or PR body and of comments: even after the current revision is cleaned, an
earlier revision containing the leak remains viewable through the edit-history
("· edited") view.

Consequences:

- A check that goes red tells the author to fix the *current* text. It does not
  remove the leaked value from the prior revision GitHub has already stored.
- Genuinely removing a published revision stays a manual, out-of-band operation
  — **delete and recreate** the issue/PR/comment, or contact **GitHub Support**
  to purge the retained history. The Action neither performs nor can perform
  that step.

Treat the check as a *gate on new content*, not a *redaction tool* for content
already in GitHub's hands. A value that reached a published revision should be
rotated as if leaked, regardless of any later edit.

## Out of scope: full comment-history scanning

The runner scans the **event payload**'s fields only — the single piece of new
content the event carries. It does **not** walk the full comment history of a
thread. Doing so would require pulling history via the REST API
(`gh api` / `claude -p`), a path the surface LEARNINGS flag as unreliable inside
dispatched subprocesses (`FEAT-2026-0014/T01/gh-claudeP-broken`). Whole-history
scanning therefore stays an Open Verification for the operator, not a committed
behavior of this Action.

## Operator verification

The live `issues` / `pull_request` / `issue_comment` triggers run only in a real
GitHub Actions environment and are **operator-verified post-merge** (PLAN.md
"Gate-2 oracle"), logged under `## What the loop did NOT verify` in the gate-2
close. The in-loop checks cover the workflow's YAML validity and the runner
invocation; the T03 runner carries the behavioral unit test.
