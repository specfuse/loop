---
id: FEAT-2026-0020/T11
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 0.50
duration_seconds: 108.15
cost_usd: 0.235013
input_tokens: 9
output_tokens: 3004
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Expand CONTRIBUTING.md — issues, PRs, tests, and the methodology-dogfood expectation

**Objective.** Extend the existing `CONTRIBUTING.md` so an external contributor knows how
to file an issue, open a PR, run the tests/gates locally, and understand that this repo
develops itself through its own loop methodology (the dogfood expectation).

**Context.** Part of FEAT-2026-0020 gate 2. `CONTRIBUTING.md` already exists with strong
"Ground rules" + "Before opening a PR" + "Reporting" sections (see the file). This WU adds
the missing contributor-onboarding surfaces — how tests run (`scripts/smoke-test.sh`,
`code` gates from `.specfuse/verification.yml`), the PR-scoping convention, and an explicit
note that substantive changes go through a Specfuse feature folder (`.specfuse/features/`)
rather than ad-hoc commits. Correlation ID `FEAT-2026-0020/T11`. Grounding: existing
`CONTRIBUTING.md`, `.github/workflows/ci.yml`, `.specfuse/verification.yml`,
`docs/methodology.md`, the `/fix-bug` skill (1 bug = 1 branch = 1 PR).

Binding rules in `.specfuse/rules/` apply.

Red-test exempt: content/docs WU — no behavioral surface introduced.

**Acceptance criteria.**

1. `CONTRIBUTING.md` has a section describing **how to run tests/gates locally** that
   names the real commands (`./scripts/smoke-test.sh` and/or the `code`-gate commands from
   `.specfuse/verification.yml`), runnable as written.
2. `CONTRIBUTING.md` describes the **PR workflow** (branch, scope-one-change-per-PR,
   reference an issue) consistent with the existing "Before opening a PR" guidance.
3. `CONTRIBUTING.md` states the **methodology-dogfood expectation**: non-trivial changes
   are planned as a Specfuse feature (gates + work units under `.specfuse/features/`);
   bugs follow the 1-bug-1-branch-1-PR rule.
4. The existing "Ground rules" content (OSS hygiene, boring-beats-clever, shared-contract)
   is preserved, not replaced.
5. No private-org names, personal paths/emails, or internal URLs introduced.

**Do not touch.**

- Any file other than `CONTRIBUTING.md`.
- Sibling gate-2 WU outputs (README — T01; SECURITY/CODE_OF_CONDUCT — T03; `.github/`
  templates — T04; dependabot — T05; leak-scan guard — T06; FLIP-CHECKLIST — T07).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a docs-only edit.
- Existence checks: `grep -qiE "smoke-test|verification.yml" CONTRIBUTING.md` and
  `grep -qiE "feature|work unit|gate" CONTRIBUTING.md`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. If the documented test commands do not match what `.github/workflows/ci.yml` /
   `.specfuse/verification.yml` actually run, do NOT paper over the drift — emit
   `status: blocked` (a CONTRIBUTING that documents stale commands misleads every
   contributor).
2. If a residual gate-1 leak is found in the existing file, emit `status: blocked` rather
   than silently fixing — flag for a hygiene WU.
