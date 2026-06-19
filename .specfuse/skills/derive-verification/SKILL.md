---
name: derive-verification
description: "Interactively draft a comprehensive `.specfuse/verification.yml` for a target single-repo project by inspecting its CI/CD, tooling manifests, and code \u2014 asking the user only what evidence cannot resolve \u2014 and reconciling the findings against the Specfuse methodology's five gate categories. Drafts; never auto-writes. Use this when bootstrapping the loop in a project that already has CI or tooling worth deriving gates from."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Derive verification (interactive)

This skill produces a candidate `.specfuse/verification.yml` for a target repo by
combining **evidence in the repo** with **a small number of targeted questions
the user alone can answer**. The output is always *proposed*; the user reviews
it before it lands at `.specfuse/verification.yml`. Posture mirrors `plan-next`:
draft, then arm.

**Run interactively.** The skill's whole value is conducting the batched
question round in §3 (coverage threshold, canonical test command, which gates
to add/drop), so it needs a user it can ask. The non-interactive `[gap]`
fallback documented below is a degraded mode for when no human is available
(CI, dispatched session, no stdin) — not the intended path. Invoking via
`claude -p < PROMPT.md` consumes stdin and silently degrades to gap-mode;
use an interactive `claude` session and ask it to run this skill instead.

The companion `PROMPT.md` is what the user pipes to `claude -p`. This SKILL.md
is the method that prompt operationalizes — read it as the contract.

## Why this exists

Hand-writing `verification.yml` against the methodology's five gate categories is
mechanical work that mostly already exists in the repo: CI workflows declare
test, lint, coverage, security, and warning gates; tooling manifests declare the
same in language-native form; the file tree confirms what's actually installed.
The error-prone parts are (a) noticing CI commands that aren't locally runnable
as written, and (b) reconciling what CI says against what the methodology
requires. This skill automates the gathering and reconciliation; the human
arbitrates the gaps.

The single guarantee the skill makes: **every gate in the produced file traces
back to evidence the user can audit, or to a question the user explicitly
answered.** No silent invention.

## Hard rules

- **Draft, do not write.** The produced YAML is printed to stdout and discussed
  with the user. It is only written to `.specfuse/verification.yml` after the
  user explicitly says so, and even then only if the existing file is either
  absent or backed up. This matches `plan-next`'s "drafts but never arms"
  posture — see `docs/methodology.md` §7.
- **Infer first, ask last.** A question is legitimate only if no file in the
  repo could have answered it. Asking "what language is this?" when a
  `pyproject.toml` exists is a skill bug, not a clarification.
- **Self-contained gate commands.** Per
  `.specfuse/skills/verification/SKILL.md`, never propose `--no-build`,
  `--no-restore`, or any "skip-build" flag — those trigger the stale-artifact
  trap when the driver re-runs the gate against whatever's on disk. If a build
  step is genuinely required before tests run, fold it into the gate's command
  as a shell pipeline.
- **Empty gate set ≠ pass.** `loop.py`'s `verify()` treats a missing or empty
  set for a unit's type as a configuration failure. The draft must not leave a
  required set empty without the user *consciously* accepting the consequence —
  and even then the gap is flagged loudly in the reconciliation report.
- **One repo, one CI system, v1.** GitHub Actions only. The skill's structure
  separates "discover candidate gates from CI" from "reconcile against the
  methodology," so other CI systems can be added by replacing only the
  discovery step. See [§ Seams](#seams).

## The five gate categories (the methodology contract)

From `docs/methodology.md` §5, mirrored in `.specfuse/verification.yml.example`'s
`code` set. For `implementation` work units, all five must pass:

| Gate | What it proves | Methodology default |
|------|---------------|---------------------|
| `tests` | The full test suite passes — zero failures, zero errors. | exit 0 from a real test runner |
| `coverage` | Line coverage at or above threshold. | **≥ 90%** |
| `warnings` | Zero compiler / build warnings. | warnings-as-errors |
| `lint` | Lint clean. | exit 0 from the linter in check mode |
| `security` | OWASP-aligned scan clean at the configured severity. | zero high/critical |

Plus two non-implementation gate sets the example file defines: `doc` (for
`retrospective`/`lessons`/`docs` work units — typically "artifact exists and
changed") and `plannext` (for `plan-next` — runs `lint_plan.py`). The skill
**does not invent** these; it carries them through from the example unless the
project's evidence makes a change obviously needed (rare).

## The method (in strict order)

This ordering is the whole point. Infer first, ask last.

### Step 1 — Evidence gathering, in priority order

Read what's there, in this order. Each layer corrects the previous.

#### 1a. CI/CD (candidates only)

GitHub Actions: glob `.github/workflows/*.yml` (and `*.yaml`). For each
workflow, walk the jobs and steps. Map step-level commands to gate categories
by keyword and tool signature:

- `tests` — `pytest`, `unittest`, `npm test`, `yarn test`, `pnpm test`,
  `cargo test`, `go test`, `dotnet test`, `mvn test`, `gradle test`, `jest`,
  `vitest`, `phpunit`, `rspec`, `bundle exec rspec`, `mix test`, `swift test`.
- `coverage` — `coverage`, `coverage.py`, `pytest-cov`, `--cov`, `nyc`, `c8`,
  `jest --coverage`, `cargo llvm-cov`/`cargo tarpaulin`, `go test -cover`,
  `dotnet test --collect:"XPlat Code Coverage"`, `codecov`, `coveralls`.
- `warnings` — `-Werror`, `--warnings-as-errors`, `RUSTFLAGS=-Dwarnings`,
  `dotnet build -warnaserror`, `tsc --noEmit` with `noEmitOnError`,
  `mvn -Dmaven.compiler.failOnWarning=true`.
- `lint` — `ruff`, `flake8`, `pylint`, `black --check`, `isort --check`, `mypy`,
  `eslint`, `tsc --noEmit`, `cargo clippy`, `golangci-lint`, `dotnet format
  --verify-no-changes`, `prettier --check`, `pre-commit run --all-files`,
  `rubocop`, `shellcheck`, `hadolint`.
- `security` — `bandit`, `safety`, `pip-audit`, `npm audit`, `yarn audit`,
  `osv-scanner`, `semgrep`, `cargo audit`, `gosec`, `dotnet list package
  --vulnerable`, `trivy`, `grype`, `snyk`, `dependency-check`,
  `gitleaks`/`trufflehog` (secret scan).

**Mark all CI-derived commands as candidates,** not as final gates. Reasons CI
commands often fail locally:

- `uses: some-action@v1` hides the real shell command behind a marketplace
  action. The action's `action.yml` may be readable, but often the command is
  wrapped further.
- `make test` or `tox -e py312` is indirection; the underlying command lives in
  the Makefile or `tox.ini`.
- Commands that assume CI-only environment: secrets in env vars, network
  services started by an earlier step, container images set up by `services:`,
  matrix variables.
- Setup steps (`actions/setup-python`, `actions/cache`, dependency installs)
  often precede the gate commands — locally the user is expected to have
  installed those once.

#### 1b. Project tooling manifests (often more locally-accurate)

Read whatever exists. These are usually the **most reliable source** for a
locally-runnable command:

- **Python:** `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage.*]`,
  `[tool.ruff]`, `[tool.mypy]`, `[tool.bandit]`, `[project.optional-dependencies]`),
  `setup.cfg`, `tox.ini`, `noxfile.py`, `requirements*.txt`, `Pipfile`,
  `.pre-commit-config.yaml`.
- **JavaScript / TypeScript:** `package.json`'s `scripts` block (often the
  canonical local entry points: `npm run test`, `npm run lint`), `tsconfig.json`
  (strictness / `noEmit`), `pnpm-lock.yaml` / `yarn.lock` / `package-lock.json`
  (proves what's installed).
- **Rust:** `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`,
  `deny.toml` (cargo-deny), `clippy.toml`.
- **.NET:** `*.csproj`, `Directory.Build.props`, `*.sln`, `global.json`,
  `nuget.config`. Look for `TreatWarningsAsErrors`, `<EnableNETAnalyzers>`,
  test-project SDK (`Microsoft.NET.Sdk.Web` etc.).
- **Go:** `go.mod`, `go.sum`, `.golangci.yml`.
- **Java / Kotlin:** `pom.xml`, `build.gradle{,.kts}`, `gradle/wrapper/`.
- **Ruby:** `Gemfile`, `Gemfile.lock`, `.rubocop.yml`.
- **Generic:** `Makefile`, `justfile`, `Taskfile.yml`, lockfiles in general
  (they reveal *which* version of which tool is actually installed —
  contradictions between CI and the lockfile are real signals).

Lockfiles in particular often reveal tools that aren't yet wired into CI.
A `pytest-cov` in `poetry.lock` with no coverage step in CI is a likely
coverage gate the user can adopt locally.

#### 1c. Direct repo inspection

Sanity-check the previous two layers against ground truth:

- A `tests/` (or `test/`, `spec/`, `__tests__/`) directory exists → tests gate
  is real.
- Coverage config (`.coveragerc`, `[tool.coverage.*]` in pyproject,
  `coverage.json`, `vitest.config.ts` with `coverage:`).
- Security tool config (`.bandit`, `.semgrep.yml`, `bandit.yaml`,
  `gitleaks.toml`).
- Lint config (`.eslintrc.*`, `.flake8`, `ruff.toml`, `tslint.json`,
  `.rubocop.yml`).
- Source-file extensions to confirm language(s) present (rules out a Python
  question when a `pyproject.toml` plus a `src/*.py` tree exists).

### Step 2 — Reconcile against the methodology's five categories

For each of `tests`, `coverage`, `warnings`, `lint`, `security`, decide:

1. **Is there a locally-runnable command?** Prefer manifests (1b) > direct
   tooling reads (1c) > CI commands (1a). Rewrite CI commands when manifests
   give a cleaner local form (e.g. CI runs `tox -e py312-test` → propose
   `pytest -q` if `tox.ini`'s `py312-test` env is just `pytest`).
2. **Does it pass the authoring rule?** No `--no-build`, no `--no-restore`,
   no flag that depends on prior artifacts. If the natural form is unsafe
   (`dotnet test --no-build` in CI), rewrite as a self-contained pipeline
   (`dotnet build && dotnet test --no-build`) or drop `--no-build` entirely.
3. **Does the methodology default need overriding?** Coverage defaults to
   **≥ 90%** in the loop's gates. If CI uses a different number, surface the
   divergence — do not silently adopt CI's lower (or higher) value. Same for
   security severity thresholds.
4. **Carry through the example's non-`code` gates** (`doc`, `plannext`)
   unchanged unless something in the repo says otherwise (rare and worth a
   question).

### Step 3 — Ask the user — only for what evidence cannot resolve

A question is legitimate only when it falls into one of three categories:

- **Genuine ambiguity** — plural / contradictory evidence. Example: "Found
  `pytest` in `pyproject.toml` and `unittest discover` in CI; which is the
  canonical command for a per-WU gate?"
- **Methodology gap with no evidence** — the methodology asks for a category
  the repo lacks. Example: "Methodology wants a `security` gate; I found no
  security tool installed or configured. Add one now (suggest `bandit -r src
  -ll` for Python / `npm audit --audit-level=high` for JS — say which) or
  consciously drop the security gate?"
- **Threshold / policy call** — a number the methodology defaults but the
  repo or the user might want differently. Example: "Coverage: methodology
  default is ≥ 90%; this repo's CI uses 80%. Which threshold should govern
  the local gate?"

**Forbidden questions** — anything answerable by reading a file. "What
language is this?" with a `pyproject.toml` present; "Do you have tests?"
with a `tests/` directory present; "What's your lint config?" with
`.ruff.toml` present. Lazy questioning defeats the purpose of the skill.

**Batch questions.** Compile all of them after Steps 1 and 2, present them
together with their evidence context, and accept answers in one round. Do not
drip questions one at a time across the conversation.

**Non-interactive fallback.** If the skill is run in a context where the user
cannot answer (CI invocation, dispatched session, no stdin), it still produces
a draft — every would-be question becomes an explicit `[gap]` line in the
report rather than a guess. Silence is never permission to invent a gate.

### Step 4 — Output

Two artifacts, in this order:

#### 4a. The proposed `.specfuse/verification.yml`

A complete YAML file written to stdout (not to disk), with the same shape as
`.specfuse/verification.yml.example`:

```yaml
code:
  - name: tests
    command: "<self-contained command>"
  - name: coverage
    command: "<self-contained command, includes --fail-under or equivalent>"
  - name: warnings
    command: "<self-contained command>"
  - name: lint
    command: "<self-contained command>"
  - name: security
    command: "<self-contained command>"

doc:
  - name: artifact-changed
    command: "git -C {feature_dir} diff --quiet HEAD -- . && exit 1 || exit 0"

plannext:
  - name: plan-lint
    command: "python .specfuse/scripts/lint_plan.py {feature_dir}"
```

Every entry in the `code` set has a `name` from the methodology's five
categories. A category the user consciously dropped is omitted — but the
report calls out the omission.

#### 4b. The reconciliation report

A structured per-category readout. Every gate the skill proposes carries a
**confidence tag**, every gap is named, and every question the user answered
is recorded. The tags:

- `[verbatim]` — extracted directly from a local manifest or a command that
  the user can already run today. High confidence.
- `[inferred]` — reverse-engineered (e.g. derived from a CI marketplace
  action, or rewritten from `make test` indirection). User must verify
  before committing.
- `[user-supplied]` — the user answered a question; this is what they said
  and how it shaped the gate.
- `[gap]` — methodology wants this category, no evidence and/or the user
  consciously dropped it. Names the consequence (e.g. "no security gate;
  `verify()` for `implementation` units will not check for vulnerabilities
  — accept by leaving omitted, or add a tool").

Report template:

```
# Reconciliation report for <repo-name>

## Evidence inventory
- CI: <workflows examined, by path>
- Manifests: <files read, by path>
- Direct: <relevant config files / tree facts noted>

## Gate-by-gate

### tests        [verbatim|inferred|user-supplied|gap]
- Proposed command: <command>
- Source: <file:line or "user answer to Q1">
- Notes: <local-runnability caveats, etc.>

### coverage     [...]   (with threshold; flag divergence from ≥ 90%)
### warnings     [...]
### lint         [...]
### security     [...]

## CI gates not required by the loop (informational)
- <e.g. release upload steps, deploy steps, format-only checks the user already runs pre-commit>

## Methodology gates CI does not provide (the important list)
- <e.g. "CI has no coverage step; loop will require coverage. Decision: …">

## Questions and answers
- Q1: <question>  → A: <answer> → shaped <gate>.
- Q2: …

## Recommended next step
- Review the draft above; if accepted, write it to `.specfuse/verification.yml`
  (overwriting the example placeholder), then run
  `python .specfuse/scripts/loop.py --dry-run` against a feature folder to
  confirm the loop loads it cleanly.
```

## Seams

The skill is deliberately structured so the CI-reading step is replaceable
without touching the reconciliation logic.

| Step | Generic | GitHub-Actions-specific |
|------|---------|--------------------------|
| 1a CI discovery | "Find candidate gate commands from CI" | Read `.github/workflows/*.yml`; walk `jobs.*.steps[*].run`; resolve `uses:` to action repos when needed |
| 1b tooling manifests | Generic (per language) | — |
| 1c direct inspection | Generic | — |
| 2 reconcile | Generic | — |
| 3 ask | Generic | — |
| 4 output | Generic | — |

Adding GitLab CI, CircleCI, Jenkins, etc. is a v2 change to step 1a only.
Mark any new CI parser as a discovery-time concern; the methodology mapping
in step 2 stays fixed.

## What this skill does *not* do

- It does not run any of the commands it proposes. It is an authoring aid,
  not a smoke test. Once the file is accepted, the user runs `loop.py
  --dry-run` (which uses the file but doesn't execute the gates) and then
  the first real feature exercises the gates for real.
- It does not modify `.specfuse/scripts/loop.py`, `lint_plan.py`, or the
  methodology. If applying this skill reveals that those need to change,
  the skill stops and reports the need — it never edits them as part of its
  work.
- It does not auto-run from `init.sh`. `init.sh` stays deterministic and
  agent-free; the closing instructions point at this skill as an optional
  next step.

## Worked example

See the "Dogfood: deriving against `specfuse-loop` itself" section in the
commit that introduced this skill — that walk-through demonstrates the
output format on a real Python repo with a CI workflow and a `tests/`
directory, and shows where the skill defers to questions versus where it
infers cleanly.
