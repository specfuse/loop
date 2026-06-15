---
id: FEAT-2026-0020/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.50
duration_seconds: 202.208
cost_usd: 0.453855
input_tokens: 20
output_tokens: 4854
---

# Run gitleaks across full git history; triage every finding in AUDIT.md

**Objective.** Scan the full reachable git history of this repo with `gitleaks`,
capture the JSON report, and append a triage table to `AUDIT.md §secrets` listing every
finding + per-finding triage decision + the exact remediation command the operator will
run between WU dispatches.

**Context.** Part of FEAT-2026-0020 gate 1 (audit). The five audit WUs (T01..T05) each
produce one section of `AUDIT.md`; T06 verifies the post-remediation re-scan. Destructive
operations (history rewrite, secret rotation) execute OUTSIDE the loop — see
PLAN.md "Notes". Binding rules: `.specfuse/rules/{result-contract,never-touch,
security-boundaries,correlation-ids}.md`. Verification: `.specfuse/skills/verification/SKILL.md`.

Red-test exempt: audit/report WU, no behavioral surface introduced.
Per `/authoring-work-units` §12, audit WUs that only produce a report are exempt from
the red→green proof requirement.

**Acceptance criteria.**

- `gitleaks` v8+ is available on PATH (preinstalled or `brew install gitleaks` /
  homebrew-equivalent documented in the AUDIT preamble).
- Command `gitleaks detect --source . --log-opts="--all" --report-format json
  --report-path .specfuse/features/FEAT-2026-0020-public-readiness-prep/gitleaks.json`
  runs to completion. Non-zero exit (matches found) is acceptable — the report still
  populates.
- `.specfuse/features/FEAT-2026-0020-public-readiness-prep/AUDIT.md` exists and contains
  a level-2 heading `## §secrets`.
- §secrets contains a table with columns: `finding | commit | path | rule | triage |
  remediation-command`.
  - `triage` value is one of: `false-positive`, `redact`, `rotate-and-redact`.
  - `remediation-command` is empty for `false-positive`; for `redact` / `rotate-and-redact`
    it is the exact `git filter-repo` / BFG / rotate-then-redact command sequence.
- Every JSON match from gitleaks.json appears as a row in the §secrets table.
- §secrets ends with a summary line: `Total findings: N. Open actions: M.` where M counts
  rows whose triage is NOT `false-positive`.

**Do not touch.**

- Git history (`.git/`). Operator runs all rewrites.
- Other audit WUs' AUDIT.md sections (T02..T06 own their own subheadings).
- Repo source code beyond `AUDIT.md` + `gitleaks.json` under the feature folder.
- Secrets themselves — record finding identity (commit + path + rule), do NOT include the
  matched secret value in the table.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml` (tests, coverage, warnings, lint, security).
- Symbol-presence: `grep -q "^## §secrets$" AUDIT.md` returns 0.
- File-presence: `gitleaks.json` exists and parses as JSON.
- Oracle environment: `macos_local` (developer shell, gitleaks via brew).

**Escalation triggers.**

- `gitleaks` install fails or requires network beyond the sandbox's approved hosts →
  `status: blocked` with the install command needed.
- gitleaks.json contains a finding whose triage cannot be decided from path + rule alone
  (e.g. ambiguous high-entropy string in a config file) → emit `status: blocked` rather
  than guess. Operator decides.
- If `AUDIT.md §secrets` is absent after edits, emit `status: blocked` — do not claim
  complete.
