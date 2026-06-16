---
id: FEAT-2026-0024/T04
type: implementation
model: opus
effort: high
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: github_actions_ci
produces: [".github/workflows/leak-scan-content.yml", "docs/leak-scan-content-action.md"]
duration_seconds: 132.527
cost_usd: 0.720689
input_tokens: 8795
output_tokens: 5865
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# GitHub Action workflow + docs — wire the content-scan runner to issue/PR triggers, document the edit-history limitation

**Objective.** Ship the GitHub Action `.github/workflows/leak-scan-content.yml`
that invokes the T03 runner on `issues` + `pull_request` (and `issue_comment`)
open/edit events and fails the check on a hit, plus
`docs/leak-scan-content-action.md` documenting the guard and the
edit-history-not-expunged limitation. This completes issue #46's public-surface
coverage.

**Context.** This is `FEAT-2026-0024/T04`; `depends_on: [FEAT-2026-0024/T03]` —
the runner (`leak_scan_content.py`) is the behavioral seam; this WU only wires
it and documents it. Read T03's body for the runner's contract: it reads the
event payload at `$GITHUB_EVENT_PATH` and exits non-zero on a hit.

**Red-test exempt: workflow YAML + docs — the runner (T03) carries the
behavioral unit test; the live `issues`/`pull_request` trigger runs only in a
real GitHub Actions environment and is operator-verified post-merge (PLAN.md
"Gate-2 oracle"; logged in `G2-CLOSE`'s `## What the loop did NOT verify`). Do
NOT plan `act`/Docker emulation in-loop.**

The workflow's shape (the runner reads `GITHUB_EVENT_PATH`, which Actions sets
automatically, so the job only checks out the repo and runs the runner):

```yaml
on:
  issues:
    types: [opened, edited]
  pull_request:
    types: [opened, edited]
  issue_comment:
    types: [created, edited]
permissions:
  contents: read
jobs:
  leak-scan-content:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: python3 .specfuse/scripts/leak_scan_content.py
```

Default behavior is **fail the check** on a hit (a non-zero runner exit fails
the job) — it needs only `contents: read`, no write scope, no token-scope risk.
Posting a comment that names the offending field is an operator-confirmable
enhancement (`pull-requests: write` / `issues: write`), flagged in
`GATE-02-REVIEW.md` Open Verifications, not built here.

Reference the binding rules under `.specfuse/rules/`. The driver owns all git;
edit files only.

**Acceptance criteria.**

1. `.github/workflows/leak-scan-content.yml` exists and is valid YAML, with an
   `on:` block triggering `issues` (opened/edited) + `pull_request`
   (opened/edited) + `issue_comment` (created/edited), and a job that checks out
   the repo, sets up Python, and runs
   `python3 .specfuse/scripts/leak_scan_content.py`. Verified:
   `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/leak-scan-content.yml'))"`
   parses without error and the parsed `on:` keys include `issues`,
   `pull_request`, and `issue_comment`.

2. The workflow declares `permissions:` with `contents: read` and **no write
   scope** (default fail-the-check behavior needs no write token). A
   symbol-existence grep confirms the runner invocation line is present:
   `grep -q 'leak_scan_content.py' .github/workflows/leak-scan-content.yml`.

3. `docs/leak-scan-content-action.md` exists and documents: (a) what the Action
   scans (issue/PR title, body, and the triggering comment via the event
   payload) and that it fails the check on a hit; (b) the **edit-history
   limitation** — the guard stops *new* leaks on open/edit but cannot expunge
   already-published body revisions (GitHub retains edit history); removing a
   published revision stays a delete+recreate / GitHub-Support operation; (c)
   that full-comment-history scanning is out of scope (the runner scans the
   event payload's fields only). Verified: `test -s
   docs/leak-scan-content-action.md` and the file contains the strings
   `edit history` and `event payload`.

4. The `plannext`/`doc` gates pass and `leak-scan --all` stays clean — the new
   files introduce no committed denylisted string, email, user-path, or
   private-host literal.

**Do not touch.** This WU creates exactly **2 new files**
(`.github/workflows/leak-scan-content.yml`, `docs/leak-scan-content-action.md`)
and edits **0 existing files**. Do NOT modify `leak_scan_content.py` (T03 owns
the runner) or `leak_scan.py`, any other `.github/workflows/*` file, the gate-1
WU files, `verification.yml`, other features, secrets, or `.git/`. The driver
owns all git — edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc`/`plannext` gates plus the YAML-parse check (AC1),
the runner-invocation grep (AC2), and the docs-content checks (AC3).
`leak-scan --all` must stay clean. The live `issues`/`pull_request`-triggered
run is **operator-verified post-merge**, not in-loop (PLAN.md "Gate-2 oracle").

**Escalation triggers.**

1. **Runner absent.** If `.specfuse/scripts/leak_scan_content.py` does not exist
   (T03 incomplete), emit `status: blocked` — this WU only wires a runner that
   must already exist.

2. **Comment-reading approach forced onto `gh`.** If wiring the workflow appears
   to require reading full comment history via `gh api` / `claude -p` (the
   surface LEARNINGS `[FEAT-2026-0014/T01/gh-claudeP-broken]` flags as
   unreliable), do NOT commit that brittle path — keep the runner on the event
   payload and surface the choice in `GATE-02-REVIEW.md` Open Verifications.

3. **Invented workflow contract value.** If any trigger type, `permissions:`
   scope, or token name cannot be confirmed against GitHub's authoritative
   workflow schema (`/authoring-work-units` §8), flag it in `GATE-02-REVIEW.md`
   Cross-repo contracts rather than committing an unverified value.
