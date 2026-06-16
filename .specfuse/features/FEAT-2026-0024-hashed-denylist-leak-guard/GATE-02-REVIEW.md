<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate-2 review — issue/PR-body leak guard (issue #46)

Written by `FEAT-2026-0024/G1-PLAN`. Summarizes what gate 1 shipped, the gate-2
substantive WUs drafted here, and the open decisions the operator resolves
before arming gate 2.

## Gate-1 summary

Gate 1 shipped the hashed-denylist core (#45): a salted-SHA-256 sliding-window
matcher (`normalize_token`, `hash_token`, `load_hashed_denylist`,
`hashed_denylist_hits`) plus the `--hash-denylist` generator and the
`scan_repo` wiring, so the CI `--all` gate gains private-org-name coverage using
only the **committed** `leak_denylist.hashes` — the gitignored plaintext denylist
never reaches the public repo. T01 (core) and T02 (CI wiring + generator) both
passed, the committed `.hashes` is clean against the repo's own tracked content,
and gate 1 auto-closed on the v1 on-plan predicate. Gate-1 total cost: **$4.69**
(per `RETROSPECTIVE.md`). The hashing design's honesty caveat — low-entropy org
names + a public salt are obfuscation, not secrecy — ships verbatim in every
generated `.hashes` header.

## Gate-2 substantive WUs

**`FEAT-2026-0024/T03` — content-scan runner
(`WU-03-content-scan-runner.md`).** The unit-testable seam: a Python runner
`leak_scan_content.py` that parses a GitHub event payload
(`$GITHUB_EVENT_PATH`), extracts the present title/body/comment fields, scans
each with the gate-1 scanner + committed hashed denylist + gitleaks, and exits
non-zero on a hit naming the offending field. Red-test-first: a `tmp_path`
event JSON with a planted placeholder denylist hit → non-zero; a clean payload →
0. `depends_on: []` — gate 1 is the barrier; the hashed denylist already exists.
Python, so the `code` gate set covers it fully (no shellcheck/bats). The
runner's planted hit and `.hashes` are built in `tmp_path` so no committed
fixture carries a denylisted string (a committed hit would trip `leak-scan
--all`).

**`FEAT-2026-0024/T04` — Action workflow + docs
(`WU-04-action-workflow-and-docs.md`).** Wires the T03 runner to a GitHub
Action `.github/workflows/leak-scan-content.yml` triggered on `issues` +
`pull_request` (opened/edited) + `issue_comment` (created/edited); the runner's
non-zero exit fails the check. Default behavior is **fail the check** —
`permissions: contents: read` only, no write scope. Bundles the docs deliverable
`docs/leak-scan-content-action.md` documenting the guard and the
edit-history-not-expunged limitation. **Red-test exempt** (workflow YAML +
docs): the runner carries the behavioral test; the live trigger is
operator-verified post-merge. `depends_on: [T03]`. Docs are bundled here rather
than a standalone `docs`-type WU because a `docs`-type unit placed mid-gate
collides with the closing-sequence detector in `lint_plan.py` (`docs` is a
closing type), which would reject the gate's shape.

Gate-2 close is the pre-existing terminal `G2-CLOSE`
(`WU-90-gate-2-close.md`), now `depends_on: [T03, T04]`.

## Open verifications (operator decisions before arming)

1. **Runner language — Python vs shell.** Drafted as **Python**
   (`leak_scan_content.py`), so it imports `leak_scan` as a library and is
   covered by the existing `code` gate set (unittest + coverage + ruff +
   bandit). A shell runner would instead require the `/authoring-work-units` §11
   treatment (shellcheck + `bash -n` + a bats happy-path). Confirm Python, or
   re-scope T03 to shell and add the §11 gates.

2. **`schedule:` trigger.** Drafted with `issues` + `pull_request` +
   `issue_comment` triggers and **no** `schedule:`. A periodic re-scan of open
   issues/PRs is an option (catches content edited before the Action existed)
   but adds noise and `gh api` reliance. Confirm whether to add `schedule:`.

3. **Fail vs comment vs both.** Drafted to **fail the check** only (needs no
   write token). Posting a comment that names the offending field needs
   `issues: write` / `pull-requests: write` and a token scope — confirm whether
   the Action should fail, comment, or both. If comment, T04's `permissions:`
   and AC2 change.

4. **How comments are read.** Drafted to scan only the fields in the **event
   payload** (title + body + the single triggering comment). Scanning the full
   comment history needs `gh api` / the REST API — LEARNINGS
   `[FEAT-2026-0014/T01/gh-claudeP-broken]` flags `gh` inside dispatched
   subprocesses as unreliable. Confirm event-payload-only scope (recommended),
   or accept the `gh api` path with its reliability caveat.

5. **Live-trigger oracle is operator-deferred.** Per PLAN.md "Gate-2 oracle",
   issue #46's headline acceptance — the live `issues`/`pull_request` Action
   flagging a planted string in a real issue/PR body — runs only in GitHub
   Actions and is operator-verified post-merge (open a test issue with a planted
   placeholder, confirm the check fails), logged in `G2-CLOSE`'s `## What the
   loop did NOT verify`. No `act`/Docker emulation in-loop.

## Cross-repo / invented strings (verify against the authoritative source)

Per `/authoring-work-units` §8, every value below names another system's
vocabulary and must be confirmed against GitHub's workflow schema before arming
— a `plan-next` draft confidently invents internally-consistent cross-repo
values it cannot see.

| Value | Where used | Authoritative source | Status |
| --- | --- | --- | --- |
| `issues` types `opened`/`edited` | T04 `on:` block | GitHub Actions `on.issues.types` schema | unchecked |
| `pull_request` types `opened`/`edited` | T04 `on:` block | GitHub Actions `on.pull_request.types` schema | unchecked |
| `issue_comment` types `created`/`edited` | T04 `on:` block | GitHub Actions `on.issue_comment.types` schema | unchecked |
| `permissions: contents: read` | T04 `permissions` | GitHub Actions permissions scopes | unchecked |
| `GITHUB_EVENT_PATH` env var | T03 runner, reads the event payload path | GitHub Actions default environment variables | unchecked |
| event-payload field paths (`issue.body`, `pull_request.title`, `comment.body`) | T03 runner field extraction | GitHub webhook event payload schemas | unchecked |

Placeholder org names in the drafts (e.g. `acme-widget`) are deliberate
non-real stand-ins — no real private literal appears in any gate-2 artifact, per
`security-boundaries.md` and the gate's reason for existing.
