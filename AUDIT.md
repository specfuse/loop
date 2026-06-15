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
| 17 | private-repo-id: `example-org/example-app` | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` — 13 files, ~40 locations (GATE-02-REVIEW.md, GATE-03-REVIEW.md, GATE-04-REVIEW.md, GATE-04.md, PLAN.md, RETROSPECTIVE.md, SMOKE-INIT-2026-0001-F06.md, WU-06, WU-07, WU-97, WU-98, WU-99, WU-100) | **⚠ unclear — operator decide** | keep-as-maintainer-attribution (dogfood history) OR redact-in-place across all FEAT-0003 files |
| 18 | private-repo-id: `example-org/example-app` | `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/PLAN.md:9,15` and `WU-01:17,20,21` | **⚠ unclear — operator decide** | provenance question owned by WU-03; personal-refs triage: keep as dogfood evidence OR redact-in-place |
| 19 | private-repo-id: `example-org` | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/WU-03-cross-pollination-check.md:18,33` | `false-positive` | (none — cross-pollination WU's own prompt names these as the target pattern) |

**Commit history scan results:** 0 matches for all patterns across full `git log --all` history.

### Allowlist — intentionally-kept references

| reference | location | rationale |
|-----------|----------|-----------|
| (none at this time) | — | No maintainer-email attributions or intentional personal references identified. Allowlist to be populated after operator classification of rows 17–18. |

### Escalation note

**Rows 17–18 trigger the escalation condition** ("≥3 matches whose triage classification is
unclear"). The FEAT-2026-0003 cluster alone contains >40 individual locations in 13 files where
`example-org/example-app` appears. Classification is ambiguous:

- **keep-as-maintainer-attribution:** These files document the first dogfood run of the loop
  system against a real orchestrated feature. Keeping them preserves historical context about how
  the tool was validated.
- **redact-in-place:** The private org name `example-org` would be visible to any public
  reader of the OSS repo, which may not be acceptable to that org.

**Operator action required before this WU can be marked complete:**
1. Decide: keep `example-org/example-app` references in FEAT-0003 files, or redact?
2. Decide: keep `example-org/example-app` references in INIT-2026-0001-F06 files, or redact?
   (Note: WU-03 will independently decide provenance; this decision is about personal-refs exposure.)
3. Update rows 17–18 triage column and run T06 (post-remediation rescan).

---

Total findings: 19 rows (excluding commit history, which is clean). Open actions: 10 (rows 1–10, 13 are `redact-in-place`; rows 17–18 are blocked pending operator classification).

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
