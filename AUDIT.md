# AUDIT.md — Public-readiness audit (FEAT-2026-0020)

Produced by gate-1 audit work units. Each section is owned by one WU.
Destructive remediation (redact/history-rewrite) is operator-side; the loop
verifies the result in T06 (post-remediation rescan).

---

## §secrets

**Produced by:** FEAT-2026-0020/T01 (WU-01-secret-history-scan). Consolidated into
this canonical AUDIT.md by T04 (originally written to the feature-local copy).

**Tool:** gitleaks v8.30.1 (installed via `brew install gitleaks`)

**Scan command:**
```
gitleaks detect --source . --log-opts="--all" --report-format json \
  --report-path .specfuse/features/FEAT-2026-0020-public-readiness-prep/gitleaks.json
```

Triage of every finding from `gitleaks.json` (full git history, 261 commits,
~4.40 MB scanned).

| finding | commit | path | rule | triage | remediation-command |
|---------|--------|------|------|--------|---------------------|
| *(none)* | — | — | — | — | — |

Total findings: 0. Open actions: 0.

---

## §personal-refs

**Produced by:** FEAT-2026-0020/T02 (WU-02-personal-refs-grep)

**Operator-named private Slack channel / internal product code names to search:**
(none named in WU prompt)

**Private repo identifiers discovered during scan:** `example-org/example-app`,
`example-org/orchestrator` — found in FEAT-0003 dogfood files and the
cross-pollinated INIT-2026-0001-F06 feature. See escalation note below.

**Scan commands run:**

```
# Working tree
git ls-files | xargs grep -nE '/Users/'
git ls-files | xargs grep -nE 'cbonte99@gmail\.com'
git ls-files | xargs grep -nE '@gmail\.com'
git ls-files | xargs grep -nE '\.local\b'
git ls-files | xargs grep -nE 'example-org|example|Example'

# Commit messages
git log --all --format='%H %s%n%b' | grep -nE '/Users/'
git log --all --format='%H %s%n%b' | grep -nE 'cbonte99@gmail\.com|@gmail\.com'
git log --all --format='%H %s%n%b' | grep -nE '\.local\b'
```

### Findings table

| # | pattern | location (file:line OR commit:offset) | triage | remediation-command |
|---|---------|---------------------------------------|--------|---------------------|
| 1 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-1.md:64,67` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>' <file>` |
| 2 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-2.md:52,55` | `redact-in-place — applied (commit b5d5404)` | same |
| 3 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-3.md:52,55` | `redact-in-place — applied (commit b5d5404)` | same |
| 4 | `/Users/` | `.specfuse/features/FEAT-2026-0003-github-feature-pick/GATE-03-REVIEW.md:211` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>' <file>` |
| 5 | `/Users/` | `.specfuse/features/FEAT-2026-0011-scoring-framework/PLAN.md:23` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>)]*|<local-path>|g' <file>` |
| 6 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-1.md:10,56` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>' <file>` |
| 7 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-2.md:10,56` | `redact-in-place — applied (commit b5d5404)` | same |
| 8 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-3.md:10,56` | `redact-in-place — applied (commit b5d5404)` | same |
| 9 | `/Users/` | `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-09-docs-and-roadmap-archive.md:60,138,139,142,143,144` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>' <file>` |
| 10 | `/Users/` | `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/events.jsonl:39,40` | `redact-in-place — applied (commit b5d5404)` | edit blocked_reason JSON strings to replace `<redacted-path>` with relative path |
| 11 | `/Users/` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-02-personal-refs-grep.md:44` | `false-positive` | (none — search pattern in this WU's own prompt) |
| 12 | `/Users/` | `.specfuse/roadmap.md:459` | `false-positive` | (none — grep pattern example in audit planning text) |
| 13 | `/Users/` | `docs/handoff-github-feature-pick.md:27,28,29` | `redact-in-place — applied (commit b5d5404)` | `sed -i '' 's|<redacted-path>' docs/handoff-github-feature-pick.md` |
| 14 | `@gmail.com` | `.specfuse/roadmap.md:460` | `false-positive` | (none — grep pattern example in audit planning text) |
| 15 | `cbonte99@gmail.com` | (no matches in working tree or commit history) | N/A | (none) |
| 16 | `\.local\b` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-02-personal-refs-grep.md:48` | `false-positive` | (none — search pattern in this WU's own prompt) |
| 17 | private-repo-id: `example-org/example-app` | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` — 13 files, ~40 locations | `redact-in-place — applied (commit 7b3267c)` | substituted `example-org/example-app → example-org/example-app`, `example-org/orchestrator → example-org/orchestrator`, `exampleEndpoint → exampleEndpoint` |
| 18 | private-repo-id: `example-org/example-app` | `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/PLAN.md:9,15` and `WU-01:17,20,21` | `removed (commit 7b3267c)` | leaked feature folder deleted entirely per FEAT-2026-0020/T03 cross-poll verdict |
| 19 | private-repo-id: `example-org` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-03-cross-pollination-check.md:22,37` | `false-positive` | (none — cross-pollination WU's own prompt names these as the target pattern) |
| 20 | `/Users/`, `example-org` | `AUDIT.md` (§personal-refs table cells, remediation-command column, escalation-note body) | `false-positive` | (none — audit document quoting historical findings and redaction actions; meta-reference, not a live leak) |
| 21 | `example-org` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/events.jsonl:5,6` | `false-positive` | (none — events.jsonl records blocked_reason text that named the private org as context for the escalation; audit trail should not be redacted) |
| 22 | `/Users/`, `example-org` | commit history — `b5d5404` body (lines 7,15,18-20), `7b3267c` body (lines 39,43-46), `20918f4` body (lines 6-7), `63bec507` body (line 3116), `be7785b` body (lines 3682,3824) | `history-rewrite` | `git filter-repo` phase 2 (deferred — same sweep as §cross-poll scrub; operator runs after all gate-1 in-place remediations complete) |

**Commit history scan results (post-remediation rescan):**

Working-tree pattern scan produced no matches outside of false-positive locations (rows 11–12, 14, 16, 19–21). Commit-message history, however, contains real hits: remediation commit `b5d5404` records the `<redacted-path>` strings it redacted (in its body); `7b3267c` records the `example-org` substitutions it applied; `20918f4` (re-arm) references both; older dogfood commits (`63bec507`, `be7785b`) contain `example-org/example-app` in context lines. All classified `history-rewrite` (row 22), deferred to phase 2 alongside the §cross-poll scrub. See §cross-poll history-scrub note for the `git filter-repo` command.

### Allowlist — intentionally-kept references

| reference | location | rationale |
|-----------|----------|-----------|
| (none at this time) | — | No maintainer-email attributions or intentional personal references identified. Allowlist to be populated after operator classification of rows 17–18. |

### Escalation note — RESOLVED

Rows 17–18 classified `redact-in-place` (and `removed` for the leaked INIT-F06 folder) by the
operator. Phase-1 remediation applied:

- **Commit `7b3267c`** (`chore(audit): redact example-org / exampleEndpoint refs; delete leaked
  INIT-F06 folder`): substituted `example-org` → `example-org`, `example-org/example-app` →
  `example-org/example-app`, `example-org/orchestrator` → `example-org/orchestrator`,
  `exampleEndpoint` → `exampleEndpoint` across 19 tracked files; deleted
  `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/`.
- **Second pass** (this commit): redacted `<redacted-path>` → relative paths and
  `<redacted-path>)]+` → `<local-path>` across rows 1–10 and 13 in 9 more
  files (FEAT-2026-0002 + FEAT-2026-0014 + FEAT-2026-0016 attempt logs + work artifacts +
  FEAT-2026-0011/PLAN.md).
- **History**: deferred to phase 2 (`git-filter-repo`) after every gate-1 finding is remediated.
  Old commits on the feature branch still reference the redacted strings; main's first publishable
  commit is the merge commit of this branch.

---

Total findings: 22 rows (19 working-tree + row 20 AUDIT.md meta + row 21 events.jsonl + row 22 commit-history). Open actions: 1 — row 22 (`history-rewrite`, phase 2 deferred). All working-tree rows remediated phase 1 (in-place redaction, commits 7b3267c + b5d5404). Phase 2 (`git filter-repo`) deferred until every gate-1 audit-class finding is remediated.

---

## §cross-poll

**Produced by:** FEAT-2026-0020/T03 (WU-03-cross-pollination-check)

### Full repo scan — non-`FEAT-*` correlation-ID directories

Command run:

```
find .specfuse/features -maxdepth 1 -type d | sort
```

Only one non-`FEAT-*` directory found:

```
.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec
```

No `BUG-*` or `TASK-*` directories present.

### git log for suspect directory

```
git log --follow --format='%h %ad %an %s' --date=short -- .specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/
```

Output:

```
be7785b 2026-06-06 Christian Labonté feat: GitHub feature-pick for the loop (FEAT-2026-0003) (#1)
```

Single commit. Directory entered this repo as part of PR #1 (FEAT-2026-0003 dogfood run). The commit is a specfuse-loop commit, but the directory content belongs to example-org.

### Provenance evidence

`PLAN.md` inside the directory contains:

- `feature_id: INIT-2026-0001/F06` — INIT-* is example-org's correlation-ID family; specfuse-loop uses FEAT-* exclusively.
- `source_issue_url: https://github.com/example-org/example-app/issues/287` — private example-org GitHub repo.
- `branch: feat/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec`

Content references private non-public repo. History-scrub required.

### Cross-poll table

| path | first-commit | author | provenance-verdict | remediation-command |
|------|-------------|--------|--------------------|---------------------|
| `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec` | `be7785b 2026-06-06` | Christian Labonté | `leaked-from-example` | `git rm -rf .specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec && git commit -m "chore: remove leaked example-org feature directory"` — **plus history-scrub** (see note below) |

**History-scrub note:** Directory introduced in `be7785b` contains `https://github.com/example-org/example-app/issues/287` (private repo URL). After `git rm` + commit, run `git filter-repo --path .specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec --invert-paths` (or equivalent BFG) to expunge from all history before publishing. Force-push all branches after scrub. Invalidate any existing clones/forks.

### Summary

Total non-`FEAT-*` directories scanned: **1**. Leaked-from-example verdicts: **1**. Operator action required before repo is public-safe.

---

## §licenses

**Produced by:** FEAT-2026-0020/T05 (WU-05-license-header-sweep)

### Repo-root LICENSE verdict

`LICENSE` present at repo root. Content: Apache License, Version 2.0 (confirmed by first two lines). **Identity: ✓ Apache-2.0.**

---

### Proposed header templates

Header blocks to insert, by file type. Templates defined once; table references them by name.

**`[PY-HEADER]`** — for `.py` files. Insert at top (or after shebang line 1 if present):

```
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
```

**`[MD-NOFM-HEADER]`** — for `.md` files without YAML frontmatter. Insert at very top of file:

```
<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

```

**`[MD-FM-HEADER]`** — for `.md` files with YAML frontmatter (`---` opener). Insert after the closing `---` line, before the body:

```

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

```

---

### Findings table

Scan command:

```
find .specfuse/scripts .specfuse/skills .specfuse/rules .specfuse/templates \
  -type f \( -name '*.py' -o -name '*.sh' -o -name '*.md' \)
```

Detection: header present if `Apache License, Version 2.0` OR `SPDX-License-Identifier: Apache-2.0` appears in first 30 lines.

| file | has-header | proposed-header-block |
|------|------------|----------------------|
| `.specfuse/rules/correlation-ids.md` | ✗ | `[MD-NOFM-HEADER]` |
| `.specfuse/rules/never-touch.md` | ✗ | `[MD-NOFM-HEADER]` |
| `.specfuse/rules/result-contract.md` | ✗ | `[MD-NOFM-HEADER]` |
| `.specfuse/rules/security-boundaries.md` | ✗ | `[MD-NOFM-HEADER]` |
| `.specfuse/scripts/_miniyaml.py` | ✓ | — |
| `.specfuse/scripts/adopt_feature.py` | ✓ | — |
| `.specfuse/scripts/gate_eval.py` | ✓ | — |
| `.specfuse/scripts/gh_backend.py` | ✓ | — |
| `.specfuse/scripts/gh_features.py` | ✓ | — |
| `.specfuse/scripts/lint_plan.py` | ✓ | — |
| `.specfuse/scripts/loop.py` | ✓ | — |
| `.specfuse/scripts/validate-event.py` | ✗ | `[PY-HEADER]` (insert after shebang line 1) |
| `.specfuse/skills/abandon-feature/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/adopt-feature/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/arm-gate/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/authoring-work-units/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/derive-verification/PROMPT.md` | ✗ | `[MD-NOFM-HEADER]` |
| `.specfuse/skills/derive-verification/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/draft-feature/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/feature-conversion/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/fix-bug/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/gate-status/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/learnings-suggest/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/migrate-to-auto-close/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/pick-feature/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/unblock-wu/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/verification/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/skills/wrap-feature/SKILL.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/templates/GATE.template.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/templates/PLAN.template.md` | ✗ | `[MD-FM-HEADER]` |
| `.specfuse/templates/WU.template.md` | ✗ | `[MD-FM-HEADER]` |

**Total files scanned: 31. Missing headers: 24. Coverage: 22.6%.**

### Escalation — coverage below 80% threshold

Coverage 22.6% is well below the ≥80% operator-pre-approved threshold. 24 files missing headers across `.specfuse/rules/` (4), `.specfuse/scripts/` (1), `.specfuse/skills/` (17), `.specfuse/templates/` (3). Scale and uniformity suggest script-insert is the correct remediation strategy, not hand-edit. **Operator decision required before T06 (header insertion) is dispatched.**

Options:
1. **Script-insert (recommended):** Write a one-shot script that iterates the 24 missing files, detects frontmatter vs. no-frontmatter vs. shebang, and inserts the appropriate template. T06 runs the script and verifies.
2. **Hand-edit:** Edit each of 24 files individually. Feasible but tedious and error-prone at this count.
3. **Exclude .md files:** If per-file headers in documentation/skill files are considered excessive, update scope to `.py`/`.sh` only — reduces missing count to 1 (`validate-event.py`), coverage becomes 7/8 = 87.5%. Operator call.

---

## §gh-content

**Produced by:** FEAT-2026-0020/T04 (WU-04-gh-content-sweep)

GitHub issue + PR content is part of the public surface — it lives outside `main`
but is just as visible once the repo flips public. This section scans every
open/closed issue and PR (title, body, comments) for the same patterns as
§personal-refs.

**Dumps:** `.specfuse/features/FEAT-2026-0020-public-readiness-prep/gh-issues.json`
(11 issues) + `gh-prs.json` (27 PRs), produced via:

```
gh issue list --state all --limit 1000 --json number,title,body,author,comments,createdAt,state
gh pr   list --state all --limit 1000 --json number,title,body,author,comments,createdAt,state
```

**Patterns applied (same as T02):** `/Users/`, `cbonte99@gmail\.com`, `@gmail\.com`,
`\.local\b`, plus the private-org identifiers established by T02/T03
(`example-org`, `example-iac`, `example`, `exampleEndpoint`,
`INIT-2026-0001-F06`). No matches in comments; all matches in issue/PR **bodies**.

**Redaction scheme (mirrors commit `7b3267c`):** `example-org/example-iac
→ example-org/example-iac`, `example-iac → example-iac`, `example-org →
example-org`, `argocd.example.host → argocd.example.host`, `exampleEndpoint →
exampleEndpoint`, `INIT-2026-0001-F06 → example-feature`.

> ⚠️ **GitHub retains edit history.** `gh issue edit` / `gh pr edit` change only the
> *current* body; GitHub keeps prior revisions viewable via the "edited" dropdown,
> which becomes public when the repo flips. Redaction-via-edit therefore does NOT
> expunge — it is acceptable for private-org *names* (the operator's call here) but
> would be INSUFFICIENT for credentials. For true expunge, delete + recreate the
> issue/PR or contact GitHub support. Analogous to the §personal-refs/§cross-poll
> `history-rewrite` deferral.

### Findings table

| pattern | issue-or-pr# | match-excerpt | triage | remediation-command |
|---------|--------------|---------------|--------|---------------------|
| `example-iac` | issue #12 | `Project: \`example-iac\`, feature FEAT-2026-0019` (+2 more: "Related lessons in example-iac", "example-iac/.specfuse/scripts/loop.py vendored") | `edit-via-gh-api` | redact body → `gh issue edit 12 --body-file <redacted.md>` |
| `example-iac` | issue #15 | `Both surfaced via \`example-iac\`` (+1: "Any example-iac feature whose roadmap row…") | `edit-via-gh-api` | redact body → `gh issue edit 15 --body-file <redacted.md>` |
| `example-org/example-iac` | issue #24 | `Resolved on the consumer side via [example-org/example-iac PR #110](https://github.com/example-org/example-iac/pull/110)` (incl. private repo URL) | `edit-via-gh-api` | redact body incl. URL → `gh issue edit 24 --body-file <redacted.md>` |
| `example-iac` | issue #25 | `\`example-iac\` shipped 3 features on 2026-06-14` | `edit-via-gh-api` | redact body → `gh issue edit 25 --body-file <redacted.md>` |
| `argocd.example.host` | issue #26 | `\`curl -k https://argocd.example.host/healthz\`` (private internal hostname) | `edit-via-gh-api` | redact body → `gh issue edit 26 --body-file <redacted.md>` |
| `example-iac` | issue #27 | `\`example-iac\` 2026-06-14 Argo CD session` | `edit-via-gh-api` | redact body → `gh issue edit 27 --body-file <redacted.md>` |
| `example-iac` | issue #28 | `\`example-iac\` 2026-06-14 Argo CD session: 3 retr…` | `edit-via-gh-api` | redact body → `gh issue edit 28 --body-file <redacted.md>` |
| `example-org/example-iac` | issue #35 | `\`example-org/example-iac\` FEAT-2026-0030 at \`c0f267a\`` (+ "live example-iac run, FEAT-2026-0030/T05") | `edit-via-gh-api` | redact body → `gh issue edit 35 --body-file <redacted.md>` |
| `example-org/example-app`, `INIT-2026-0001-F06` | pr #1 | `all proven live against \`example-org/example-app#287\` = \`INIT-2026-0001/F06\`` + `adopted \`INIT-2026-0001-F06-…\` folder committed` | `edit-via-gh-api` | redact body → `gh pr edit 1 --body-file <redacted.md>` |
| `example-iac` | pr #14 | `\`example-iac\` FEAT-2026-0019: 6 attempts, ~$14.…` (+1) | `edit-via-gh-api` | redact body → `gh pr edit 14 --body-file <redacted.md>` |
| `example-iac` | pr #36 | `In the live \`example-iac\` reproducer this happened twice` (+1: "Live verification.yml from example-iac") | `edit-via-gh-api` | redact body → `gh pr edit 36 --body-file <redacted.md>` |
| `example-org`, `INIT-2026-0001-F06`/`exampleEndpoint` | pr #38 | `looks like a leak from example-org` + `INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec` | `edit-via-gh-api` | redact body → `gh pr edit 38 --body-file <redacted.md>` |
| `/Users/` | pr #38 | `In-repo personal references grep (\`/Users/\`, personal emails, internal channels)` | `false-positive` | (none — literal pattern name in this feature's own PR description, not a path) |

### Line-by-line review — called-out issues #23–#28, #35

Per WU prompt, these freshest IaC-agent issues get an explicit per-issue verdict
even where the grep produced zero matches.

| issue | state | grep matches | verdict |
|-------|-------|--------------|---------|
| #23 (`loop.py: intermediate auto-close path fires twice…`) | CLOSED | none | **clean** — no private refs; pure upstream bug report. No action. |
| #24 (`init.sh should propagate __pycache__…`) | CLOSED | `example-org/example-iac` + private PR URL | **redact** (edit-via-gh-api) — see table. |
| #25 (`Tighten verdict semantics…`) | CLOSED | `example-iac` | **redact** (edit-via-gh-api). 2 comments — both clean. |
| #26 (`New WU type: post_install_verification…`) | CLOSED | `argocd.example.host` hostname | **redact** (edit-via-gh-api). 2 comments — both clean. |
| #27 (`operator scripts require shellcheck + bats…`) | CLOSED | `example-iac` | **redact** (edit-via-gh-api). |
| #28 (`Retrospective template: "What did the loop NOT verify?"`) | CLOSED | `example-iac` | **redact** (edit-via-gh-api). |
| #35 (`_miniyaml: same-indent block sequences rejected`) | CLOSED | `example-org/example-iac` FEAT-2026-0030 | **redact** (edit-via-gh-api). 1 comment — clean. |

### Summary

Total issues/PRs scanned: **11 / 27**. Findings: **12 items** (27 raw pattern
matches; 1 false-positive item — pr #38 `/Users/`). Open actions: **12** — all
`edit-via-gh-api` body redactions, operator-side, mirroring commit `7b3267c`'s
substitution scheme. Same private-org cluster as §personal-refs but on the GitHub
surface, which the in-repo redaction commits (`7b3267c`, `b5d5404`) did not reach.
See edit-history caveat above.
