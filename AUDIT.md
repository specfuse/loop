# AUDIT.md — Public-readiness audit (FEAT-2026-0020)

Produced by gate-1 audit work units. Each section is owned by one WU.
Destructive remediation (redact/history-rewrite) is operator-side; the loop
verifies the result in T06 (post-remediation rescan).

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
| 1 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-1.md:64,67` | `redact-in-place` | `sed -i '' 's|<redacted-path>' <file>` |
| 2 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-2.md:52,55` | `redact-in-place` | same |
| 3 | `/Users/` | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/work/FEAT-2026-0002_T03/attempt-3.md:52,55` | `redact-in-place` | same |
| 4 | `/Users/` | `.specfuse/features/FEAT-2026-0003-github-feature-pick/GATE-03-REVIEW.md:211` | `redact-in-place` | `sed -i '' 's|<redacted-path>' <file>` |
| 5 | `/Users/` | `.specfuse/features/FEAT-2026-0011-scoring-framework/PLAN.md:23` | `redact-in-place` | `sed -i '' 's|<redacted-path>)]*|<local-path>|g' <file>` |
| 6 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-1.md:10,56` | `redact-in-place` | `sed -i '' 's|<redacted-path>' <file>` |
| 7 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-2.md:10,56` | `redact-in-place` | same |
| 8 | `/Users/` | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/work/FEAT-2026-0014_T01/attempt-3.md:10,56` | `redact-in-place` | same |
| 9 | `/Users/` | `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-09-docs-and-roadmap-archive.md:60,138,139,142,143,144` | `redact-in-place` | `sed -i '' 's|<redacted-path>' <file>` |
| 10 | `/Users/` | `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/events.jsonl:39,40` | `redact-in-place` | edit blocked_reason JSON strings to replace `<redacted-path>` with relative path |
| 11 | `/Users/` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-02-personal-refs-grep.md:25` | `false-positive` | (none — search pattern in this WU's own prompt) |
| 12 | `/Users/` | `.specfuse/roadmap.md:459` | `false-positive` | (none — grep pattern example in audit planning text) |
| 13 | `/Users/` | `docs/handoff-github-feature-pick.md:27,28,29` | `redact-in-place` | `sed -i '' 's|<redacted-path>' docs/handoff-github-feature-pick.md` |
| 14 | `@gmail.com` | `.specfuse/roadmap.md:460` | `false-positive` | (none — grep pattern example in audit planning text) |
| 15 | `cbonte99@gmail.com` | (no matches in working tree or commit history) | N/A | (none) |
| 16 | `\.local\b` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-02-personal-refs-grep.md:29` | `false-positive` | (none — search pattern in this WU's own prompt) |
| 17 | private-repo-id: `example-org/example-app` | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` — 13 files, ~40 locations | `redact-in-place — applied (commit 7b3267c)` | substituted `example-org/example-app → example-org/example-app`, `example-org/orchestrator → example-org/orchestrator`, `exampleEndpoint → exampleEndpoint` |
| 18 | private-repo-id: `example-org/example-app` | `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/PLAN.md:9,15` and `WU-01:17,20,21` | `removed (commit 7b3267c)` | leaked feature folder deleted entirely per FEAT-2026-0020/T03 cross-poll verdict |
| 19 | private-repo-id: `example-org` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-03-cross-pollination-check.md:18,33` | `false-positive` | (none — cross-pollination WU's own prompt names these as the target pattern) |

**Commit history scan results:** 0 matches for all patterns across full `git log --all` history.

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

Total findings: 19 rows (excluding commit history, which is clean). Open actions: 0 — all rows remediated phase 1 (in-place redaction on `main`). Phase 2 (`git-filter-repo` history rewrite) deferred until every gate-1 audit-class finding is remediated.

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
