---
gate: 1
status: passed
cost_budget_usd: 36.00
baseline:
  sha: c11dfa5a3126bbb1aefa3b9d2518bcf786ddb72a
  probed_at: 2026-07-30T13:09:00.056678+00:00
  failing: []
---

# Gate 1 — closing-format guard refusals become structurally near-impossible

## Definition of done

- One shared closing-requirement registry defines the closing-artifact shape per WU type
  (`close`, `close-intermediate`, `plan-next`), and every existing post-squash guard in
  `CLOSING_ASSERTIONS_BY_TYPE` reads its requirements from it — behavior-equivalent to the
  current guards, proven by tests.
- `specfuse-lint --closing <feature-dir>` validates a feature's closing artifacts against the
  registry in-session; every finding names the unmet requirement **and** the post-squash guard
  that would fire for it (the FEAT-2026-0070 "earlier enforcer names the later one" rule).
- `dispatch()` pre-creates the closing skeleton for `close` / `close-intermediate` /
  `plan-next` WUs from the registry: RETROSPECTIVE section stubs, the `GATE-{N+1}-REVIEW.md`
  stub on plan-next dispatch, no placeholder `verdict:` value ever written. Pre-creation is
  idempotent: existing artifacts are appended to or left alone, never clobbered.
- `close-discipline.md` §4 and the closing-WU template prose reference the lint as the
  authoring/authoring-time surface instead of restating guard strings; the guard-defensive
  comment boilerplate is deleted from `data/templates/WU.template.md`.
- Full suite green (`python3 -m unittest discover -s tests -v`), lint/security/coverage gates
  green.
- `RETROSPECTIVE.md` exists; lessons promoted to `.specfuse/LEARNINGS.md`; roadmap reflects
  what was built. Terminal verdict recorded by G1-CLOSE.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **§4 runtime probe**: no default value or severity flips in this gate — the lint mode is a
  new opt-in flag, the skeleton changes dispatch side-effects but no gate command semantics.
  n/a.
- **§3 flag-scope table**: no behavior flag introduced. n/a.
- **§2 escalation-predicate satisfiability**: `--closing` findings are advisory in-session
  output, not a blocking validate gate; no "zero issues" predicate is asserted on any external
  input. n/a.

## Reflection notes

<Written by the human at review time.>
