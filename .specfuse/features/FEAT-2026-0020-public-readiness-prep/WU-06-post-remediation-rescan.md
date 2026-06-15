---
id: FEAT-2026-0020/T06
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
---

# Re-run T01/T02/T05 scans after operator remediation; record §verification verdict

**Objective.** After the operator has executed every remediation command logged by
T01..T05 (history rewrites, in-place redactions, gh edits, license-header inserts), re-run
the gitleaks scan, the personal-refs grep, and the license-header scan, and append a
§verification verdict to `AUDIT.md` recording the result of each rescan plus an overall
audit verdict.

**Context.** Final substantive WU in FEAT-2026-0020 gate 1. Depends on T01..T05. PLAN.md
"Notes": destructive remediation is operator-side; this WU is the verification handshake
that closes the loop. If the operator has not yet run the remediations, this WU emits
`status: blocked_human` and the gate halts cleanly.

Binding rules apply.

Red-test exempt: audit/report WU, no behavioral surface introduced.

**Acceptance criteria.**

- Rescan A (secrets): re-run T01's `gitleaks detect --source . --log-opts="--all"
  --report-format json --report-path .../gitleaks-rescan.json`. Verdict `clean` iff every
  remaining match cross-references an `AUDIT.md §secrets` row whose triage is
  `false-positive`.
- Rescan B (personal-refs): re-run T02's grep over working tree + commit-message history.
  Verdict `clean` iff every remaining match cross-references a §personal-refs row whose
  triage is either `false-positive` or `keep-as-maintainer-attribution`.
- Rescan C (license headers): re-run T05's iteration. Verdict `clean` iff zero missing
  headers (or operator-pre-approved residual count documented in §licenses).
- `AUDIT.md §verification` heading exists with a table: `scan | report-path | result-
  count | residual-after-triage | timestamp | verdict (clean / pending-action: N)`.
- Final line of §verification reads exactly one of:
  - `audit verdict: green` — when all three rescans are `clean`.
  - `audit verdict: red — see open actions` — otherwise.
- This WU does NOT re-run T03 (cross-poll) or T04 (gh-content) — those are one-shot
  verdicts; T06's job is the scanner-based rescans.

**Do not touch.**

- Remediation operations themselves (operator runs).
- T01..T05's AUDIT.md sections (only §verification is owned here).
- `.git/`.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml`.
- Symbol-presence: `grep -q "^## §verification$" AUDIT.md`, `grep -qE "^audit verdict:
  (green|red)" AUDIT.md`.
- File-presence: `gitleaks-rescan.json` exists and parses as JSON.
- Oracle environment: `macos_local`.

**Escalation triggers.**

- Any rescan returns matches that are NOT covered by an existing triaged row → emit
  `status: blocked_human` with the open-action list. Operator runs missing remediations,
  re-arms via `/unblock-wu`.
- Operator has not yet run remediations (rescan output matches pre-remediation T01/T02/T05
  output) → `status: blocked_human` with the command list.
- If §verification heading or `audit verdict:` line is absent after edits, emit
  `status: blocked`.
