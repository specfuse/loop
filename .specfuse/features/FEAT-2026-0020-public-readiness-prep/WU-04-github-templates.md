---
id: FEAT-2026-0020/T13
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 0.50
duration_seconds: 139.105
cost_usd: 0.343543
input_tokens: 14
output_tokens: 4427
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Add .github/ issue templates (bug, feature, methodology-question) + pull_request_template

**Objective.** Create the GitHub contribution-machinery templates under `.github/`: three
issue templates (bug report, feature request, methodology question) and a single
`pull_request_template.md`.

**Context.** Part of FEAT-2026-0020 gate 2. `.github/` currently holds only `workflows/`;
this WU adds the contributor-facing templates GitHub surfaces in the issue/PR UI on the
public flip. Correlation ID `FEAT-2026-0020/T13`. The issue-template **field names and the
form schema** (`name:`, `about:`/`description:`, `labels:`, body structure) are a
cross-surface contract with GitHub's template format (`/authoring-work-units` §8) — use the
documented GitHub schema, do not invent field keys. Markdown (`.md` front-matter) templates
are sufficient; GitHub issue-forms (`.yml`) are an optional upgrade the operator may pick at
arming (flagged in `GATE-02-REVIEW.md` Cross-repo contracts).

Binding rules in `.specfuse/rules/` apply.

Red-test exempt: config/content WU — no behavioral surface introduced.

**Acceptance criteria.**

1. `.github/ISSUE_TEMPLATE/` contains three templates: a **bug report**, a **feature
   request**, and a **methodology question** (the last reflecting this repo's
   self-developing methodology, e.g. "how does a gate / work unit work").
2. Each issue template carries valid GitHub template front-matter (`name`, `about` or
   `description`, optional `labels`) per GitHub's documented schema — field keys match the
   GitHub contract, not invented names.
3. `.github/pull_request_template.md` exists with a checklist that mirrors CONTRIBUTING's
   "Before opening a PR" guidance (scope, tests run, linked issue).
4. Any `labels:` referenced exist or are flagged in `GATE-02-REVIEW.md` as labels the
   operator must create on the GitHub side (no silently-invented label namespace).
5. No private-org names, personal paths, or internal URLs introduced.

**Do not touch.**

- `.github/workflows/` (CI is owned elsewhere; this WU adds templates only).
- Sibling gate-2 WU outputs (README — T01; CONTRIBUTING — T02; SECURITY/CODE_OF_CONDUCT —
  T03; dependabot — T05; leak-scan guard — T06; FLIP-CHECKLIST — T07).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a config-only edit.
- Existence checks: `ls .github/ISSUE_TEMPLATE/*.md 2>/dev/null | wc -l` is ≥ 3, and
  `test -f .github/pull_request_template.md`.
- Front-matter sanity: each `.github/ISSUE_TEMPLATE/*.md` begins with a `---` front-matter
  block containing a `name:` key.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. If a template references a `labels:` value that does not exist and the operator has not
   confirmed it should be created GitHub-side, do NOT invent it silently — flag it in
   `GATE-02-REVIEW.md` Cross-repo contracts and emit `status: blocked` if the contract is
   load-bearing for the template to render.
2. If GitHub's documented template schema disagrees with the field keys drafted here at
   dispatch time, follow the documented schema (cross-surface contract, §8) — do not loosen
   to match a guessed key.
