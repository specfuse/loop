---
id: FEAT-2026-0020/T04
type: implementation
status: blocked_human
attempts: 0
oracle_env: macos_local
planned_cost_usd: 2.00
duration_seconds: 42.693
cost_usd: 0.16309
input_tokens: 9
output_tokens: 1785
---

# Pull all PRs + issues via gh CLI; grep for sensitive references; triage in AUDIT.md

**Objective.** Use `gh` CLI to dump every open/closed issue + PR (title, body, comments)
to a feature-local JSON file, run the T02 grep patterns over that dump, and append
findings + triage decisions to `AUDIT.md §gh-content`.

**Context.** Part of FEAT-2026-0020 gate 1 (audit). GitHub issue + PR content is part of
the public surface — content lives outside `main` but is just as visible. Roadmap detail
calls out issues #23-#28 and #35 as the freshest IaC-agent traffic, most likely to mention
consumer-side specifics; review those line-by-line in addition to the grep sweep.

Binding rules + PLAN.md "Notes" apply.

Red-test exempt: audit/report WU, no behavioral surface introduced.

**Acceptance criteria.**

- `gh auth status` returns OK (operator already authenticated).
- `gh issue list --state all --limit 1000 --json
  number,title,body,author,comments,createdAt,state` saved to
  `.specfuse/features/FEAT-2026-0020-public-readiness-prep/gh-issues.json`.
- `gh pr list --state all --limit 1000 --json
  number,title,body,author,comments,createdAt,state` saved to
  `.specfuse/features/FEAT-2026-0020-public-readiness-prep/gh-prs.json`.
- Same grep patterns as T02 applied to both JSON dumps. Findings recorded in
  `AUDIT.md §gh-content` with columns: `pattern | issue-or-pr# | match-excerpt | triage |
  remediation-command`.
  - `triage` ∈ {`false-positive`, `keep-as-maintainer-attribution`, `edit-via-gh-api`,
    `delete-and-redact-comment`}.
  - `remediation-command` for edit cases: exact `gh issue edit N --body-file <path>` /
    `gh pr edit N` / `gh api -X PATCH repos/:owner/:repo/issues/comments/<id>` command.
- Explicit line-by-line review of issues #23, #24, #25, #26, #27, #28, #35 recorded in a
  §gh-content sub-table even when zero grep matches — verdict per issue.
- Summary line: `Total issues/PRs scanned: I/P. Findings: N. Open actions: M.`

**Do not touch.**

- `gh` write commands themselves (operator runs edits).
- Other audit WUs' AUDIT.md sections.
- `.git/`.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml`.
- Symbol-presence: `grep -q "^## §gh-content$" AUDIT.md`.
- File-presence: `gh-issues.json` + `gh-prs.json` exist and parse as JSON.
- Oracle environment: `macos_local` (developer shell with `gh` authenticated).

**Escalation triggers.**

- `gh auth status` fails → `status: blocked` with the auth command needed.
- `gh` rate-limit hit before the dumps complete → `status: blocked` with retry timing.
- If §gh-content heading is absent after edits, emit `status: blocked`.
