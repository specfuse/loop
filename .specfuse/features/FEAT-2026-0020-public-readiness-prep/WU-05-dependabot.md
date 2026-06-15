---
id: FEAT-2026-0020/T14
type: implementation
status: draft
attempts: 0
oracle_env: macos_local
planned_cost_usd: 0.40
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Add .github/dependabot.yml — GitHub Actions + pip ecosystems, weekly

**Objective.** Create `.github/dependabot.yml` configuring Dependabot to watch the
GitHub-Actions and pip dependency ecosystems on a weekly schedule.

**Context.** Part of FEAT-2026-0020 gate 2. The repo has a GitHub Actions workflow
(`.github/workflows/ci.yml`, pinned `actions/checkout@v6`, `actions/setup-python@v6`) and a
Python project installed via `pip install -e '.[dev]'` (so `pyproject.toml` is the manifest
Dependabot's `pip` ecosystem reads). Once public, automated dependency PRs keep both
current. Correlation ID `FEAT-2026-0020/T14`. The **package-ecosystem identifiers**
(`github-actions`, `pip`) and the schedule schema are a cross-surface contract with
Dependabot's documented config format (`/authoring-work-units` §8) — use the documented
identifiers, do not invent.

Binding rules in `.specfuse/rules/` apply.

Red-test exempt: config WU — no behavioral surface introduced.

**Acceptance criteria.**

1. `.github/dependabot.yml` exists with `version: 2` and a valid `updates:` list per
   Dependabot's documented schema.
2. One `updates` entry has `package-ecosystem: "github-actions"`, `directory: "/"`, and a
   `schedule.interval: "weekly"`.
3. One `updates` entry has `package-ecosystem: "pip"`, the directory pointing at the
   `pyproject.toml` location (`/`), and `schedule.interval: "weekly"`.
4. The ecosystem identifiers match Dependabot's documented vocabulary exactly
   (`github-actions`, `pip`) — verified against the source, not invented.
5. No private-org names, personal paths, or internal URLs introduced.

**Do not touch.**

- `.github/workflows/`, `pyproject.toml` (read-only reference; do not edit manifests here).
- Sibling gate-2 WU outputs (README — T01; CONTRIBUTING — T02; SECURITY/CoC — T03;
  templates — T04; leak-scan guard — T06; FLIP-CHECKLIST — T07).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a config-only edit.
- Existence check: `test -f .github/dependabot.yml`.
- Schema sanity: `grep -q "version: 2" .github/dependabot.yml`,
  `grep -q "github-actions" .github/dependabot.yml`, `grep -qw "pip" .github/dependabot.yml`.
- YAML parse: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/dependabot.yml'))"`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. If `pyproject.toml` is NOT the dependency manifest at the assumed directory (e.g. the
   project moved to a `requirements.txt` or a subdir), do NOT guess the `directory:` —
   emit `status: blocked` naming the actual manifest location.
2. If Dependabot's documented ecosystem identifier for Python differs from `pip` at
   dispatch time, follow the documented value (cross-surface contract, §8).
