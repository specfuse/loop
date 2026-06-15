---
id: FEAT-2026-0020/T03
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 0.80
---

# Verify provenance of suspect cross-repo content; record verdict in AUDIT.md

**Objective.** Confirm the provenance of
`.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/` (and any
other non-`FEAT-*` correlation IDs), record the verdict in `AUDIT.md §cross-poll`, and
list the remediation command if the content leaked from a different repo.

**Context.** Part of FEAT-2026-0020 gate 1 (audit). The roadmap detail flags
`INIT-2026-0001-F06-*` as likely leaked from `example-org`. specfuse-loop uses the
`FEAT-*` correlation-ID family exclusively. Binding rules + PLAN.md "Notes" apply.

Red-test exempt: audit/report WU, no behavioral surface introduced.

**Acceptance criteria.**

- `AUDIT.md §cross-poll` heading exists.
- For `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/`:
  capture and record `git log --follow --format='%h %ad %an %s' --date=short -- <path>`
  output in the §cross-poll subsection.
- Full repo scan: `find .specfuse/features -maxdepth 1 -type d -name 'INIT-*' -o -name
  'BUG-*' -o -name 'TASK-*'` — every non-`FEAT-*` correlation-ID directory enumerated.
- §cross-poll table columns: `path | first-commit | author | provenance-verdict |
  remediation-command`.
  - `provenance-verdict` ∈ {`belongs (specfuse-loop)`, `leaked-from-example`,
    `leaked-from-other`, `unknown`}.
  - `remediation-command` for `leaked-*`: exact `git rm -rf <path> && git commit` plus
    history-scrub instruction if the leak's commits contain non-public content.
- A summary line names total count + count of leaked-* verdicts.

**Do not touch.**

- The file deletions themselves (operator runs after operator-confirmation).
- Other audit WUs' AUDIT.md sections.
- `.git/`.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- Code gates per `.specfuse/verification.yml`.
- Symbol-presence: `grep -q "^## §cross-poll$" AUDIT.md`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

- Provenance cannot be determined from `git log --follow` (e.g. directory was imported
  via a squash from an unrelated commit) → `status: blocked`. Operator decides.
- If §cross-poll heading is absent after edits, emit `status: blocked`.
