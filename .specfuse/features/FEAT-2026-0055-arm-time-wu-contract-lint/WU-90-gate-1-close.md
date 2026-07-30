---
id: FEAT-2026-0055/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
# Load-bearing close: §1 fresh oracle re-runs + §3 consumer-visible contract enumeration
# (template + skill prose changes reach every scaffold consumer; T03 changes an existing
# guard's accepted inputs). Auto-close must not skip it.
auto_close_disabled: true
model: opus
effort: high
gate_set: plannext
driver_version: 0.7.0
started_at: 2026-07-30T15:27:18.386869+00:00
# Attempt 1 returned not_met (2026-07-30): check_produces_boundary blind to the bold-preamble
# Do-not-touch form + 15 false ERRORs — see RETROSPECTIVE.md §2a/§3. T05 owns the fix; this
# close re-runs after it. Prior attempt's driver stats live in events.jsonl.
---

# Gate 1 close — the WU contract is armed-checked, unified, and surfaced

**Objective.** Terminal close for FEAT-2026-0055: verify the two lint checks, the unified
semantics, and the prose handoff end-to-end; record the verdict; enumerate consumer-visible
changes. Run `specfuse-lint --closing` on this feature before reporting.

**Context.** Terminal gate close, depends on T05 (attempt 1's `not_met` findings — see
`RETROSPECTIVE.md` §2a/§3 — are fixed there; re-verify them fresh, do not inherit T05's
self-report). Binding rules:
`.specfuse/rules/result-contract.md`, `verification-discipline.md`, `operator-escalation.md`.

**Acceptance criteria.**

- **Oracles re-run fresh (§1):** full suite, ruff, bandit, coverage — run this session, exit
  codes read directly, never T01–T04 self-reports.
- **End-to-end on fixtures, fresh:** the T04-deadlock fixture ERRORs and names
  `assert_produces_in_diff`; the delivered-path fixture WARNs naming both WUs; a glob
  declaration passes both deliverable gates on a real dispatch-shaped fixture.
- **Satisfiability sweep re-run:** `specfuse-lint` over every feature folder in this repo —
  zero ERROR findings, expected WARNs enumerated. WARNs fire on dispatchable WUs only; a
  feature whose WUs are all `done` produces none by design (attempt 1 proved the T01/T02
  self-WARN is unobservable at close time — verify the WARN rule on the 2b fixture instead,
  and do not require it in the sweep).
- **This feature lints clean under its own rules:** `specfuse-lint
  .specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint` exit 0.
- A `## Cost analysis` section in `RETROSPECTIVE.md` reconciling `planned_cost_usd` ($22.00 +
  per-WU frontmatter) against events.jsonl actuals, delta named.
- A `## What the loop did NOT verify` section — expected entry: the portfolio measure (zero
  produces-class refusals) verifies on the next generator-class feature; name that re-run
  condition. If empty, write `(nothing — every acceptance criterion was verified in-loop)`.
  More than 2 entries or >30% of criteria flags single-gate sizing under `## What I'd change`.
- **Consumer-visible contract changes enumerated, blocked on operator acknowledgment (§3):**
  the widened `assert_declared_deliverables` semantics (T03), the template `produces` note,
  and the skill-prose changes. Not `n/a`.
- Hedged follow-up record (§2) on `met_locally` — per unmet criterion: verbatim criterion, why
  unverifiable here, exact upgrade condition.
- Lessons promoted to `.specfuse/LEARNINGS.md`, or the exact phrase `nothing generalizes` in
  `RETROSPECTIVE.md`.
- Roadmap row reflects the outcome. (PLAN.md status flip is the driver's — do not write it.)

**Do not touch.** Driver code and prose surfaces (`specfuse/loop/**`, `plugins/**`,
`.specfuse/templates/**` — T01–T04 own them; a verification-found defect escalates rather than
gets patched here); other features' folders; `.git/`.

**Verification.** Fresh full-suite run + `specfuse-lint --closing
.specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint` exit 0 + `specfuse-lint
.specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint` exit 0.

**Escalation triggers.** Do not close `met` on fixture behavior argued from source reading —
each rule's fixture must be executed fresh this session. If the satisfiability sweep ERRORs on
any existing feature, that is the feature's core defect: `not_met`, name the finding.
