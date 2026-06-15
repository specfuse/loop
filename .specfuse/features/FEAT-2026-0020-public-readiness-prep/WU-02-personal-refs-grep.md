---
id: FEAT-2026-0020/T02
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.20
---

# Grep main for personal/internal references; triage in AUDIT.md §personal-refs

**Objective.** Grep the working tree on `main` (plus commit-message history) for
personal/internal references — local machine paths, personal emails, hostnames, internal
product/channel names — and append a triage table to `AUDIT.md §personal-refs`.

**Context.** Part of FEAT-2026-0020 gate 1 (audit), sibling to T01/T03/T04/T05. Binding
rules and PLAN.md "Notes" apply (destructive remediation is operator-side).

Red-test exempt: audit/report WU, no behavioral surface introduced.

**Acceptance criteria.**

- `AUDIT.md §personal-refs` heading exists.
- Patterns searched (each becomes a sub-table or a column-tagged row):
  - `/Users/` (developer absolute paths)
  - `cbonte99@gmail\.com` (maintainer's personal email — needs explicit allowlist
    decision, not an automatic redact)
  - `@gmail\.com` (other personal emails)
  - `\.local\b` (`.local` hostnames)
  - any in-tree references to private Slack channel names, internal product code names,
    or other private-repo identifiers — operator names these in the WU prompt before
    dispatch if applicable; if none, record `(none)` in the §personal-refs preamble.
- Scans cover: `git ls-files | xargs grep -nE <pattern>` for working tree; AND
  `git log --all --format='%H %s%n%b' | grep -nE <pattern>` for commit messages.
  Both result sets recorded.
- §personal-refs table columns: `pattern | location (file:line OR commit:offset) |
  triage | remediation-command`.
  - `triage` ∈ {`false-positive`, `keep-as-maintainer-attribution`, `redact-in-place`,
    `history-rewrite`}.
- An explicit allowlist section documents intentionally-kept references (e.g. maintainer
  email in CONTRIBUTING-equivalent or LEARNINGS attribution lines).
- Summary line: `Total findings: N. Open actions: M.`

**Do not touch.**

- The redact/history-rewrite operations themselves (operator runs).
- Other audit WUs' AUDIT.md sections.
- `.git/`.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml`.
- Symbol-presence: `grep -q "^## §personal-refs$" AUDIT.md`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

- ≥3 matches whose triage classification is unclear (could be either keep or redact) →
  `status: blocked`. Operator decides classification batch.
- If `AUDIT.md §personal-refs` is absent after edits, emit `status: blocked`.
