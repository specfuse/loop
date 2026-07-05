<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

<!--
PROMPT.md — the agent instruction for the derive-verification skill.

INTENDED USE: run interactively. Start `claude` in the target repo root and
ask it to run the derive-verification skill, or paste this prompt's body into
the session. The skill's whole value is conducting the batched question
round (coverage threshold, canonical test command, which gates to add/drop);
piping this file via `claude -p < PROMPT.md` consumes stdin so the skill
cannot ask and silently degrades to the non-interactive `[gap]` fallback —
that fallback exists for CI / dispatched sessions where no user is reachable,
not as the intended invocation.

This prompt operationalizes the method documented in
.specfuse/skills/derive-verification/SKILL.md. Read both before changing either.
-->

You are deriving a candidate `.specfuse/verification.yml` for the repository
you are currently invoked in. Your job: **draft** the file based on evidence
in the repo, ask the user only what evidence cannot answer, and present a
reconciliation report. You do NOT write the file to disk. You print it to
stdout for the user to review.

Read these in the loop scaffold under this repo's `.specfuse/` before acting:

- `.specfuse/skills/derive-verification/SKILL.md` — the binding method.
- `.specfuse/skills/verification/SKILL.md` — the verification-as-oracle rules
  the proposed gates must conform to (notably: no `--no-build`-style flags).
- `.specfuse/verification.yml.example` — the file shape, the gate-set keys
  (`code`, `doc`, `plannext`), and the authoring notes.

## Method (strict order — infer first, ask last)

### Step 1 — Evidence gathering

Read what's in the repo. Do NOT ask anything that a file could have answered.

**1a. CI/CD (candidates only)** — glob `.github/workflows/*.yml` and `.yaml`.
For each workflow, walk every `jobs.*.steps[*]` and extract the shell
commands actually run (the `run:` field). Map each command to one or more of
the five gate categories — `tests`, `coverage`, `warnings`, `lint`,
`security` — by tool signature. When a step is `uses:` (a marketplace
action), record the action name; if you can determine the underlying command
from the action's own repo, do so, otherwise mark as inferred and explain.
Treat CI commands as **candidates**, not final gates: they often rely on
CI-only env, services, secrets, or matrix variables, or wrap the real
command behind `make`, `tox`, `npm run`, etc.

**1b. Tooling manifests (usually more locally-accurate than CI).** Read
whichever exist:

- Python: `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage.*]`,
  `[tool.ruff]`, `[tool.mypy]`, `[tool.bandit]`), `setup.cfg`, `tox.ini`,
  `noxfile.py`, `requirements*.txt`, `Pipfile`, `.pre-commit-config.yaml`.
- JS/TS: `package.json` (the `scripts` block is often the canonical local
  entry point), `tsconfig.json`, lockfiles.
- Rust: `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `deny.toml`,
  `clippy.toml`.
- .NET: `*.csproj`, `Directory.Build.props`, `*.sln`, `global.json`.
- Go: `go.mod`, `go.sum`, `.golangci.yml`.
- Java/Kotlin: `pom.xml`, `build.gradle{,.kts}`.
- Ruby: `Gemfile`, `Gemfile.lock`, `.rubocop.yml`.
- Generic: `Makefile`, `justfile`, `Taskfile.yml`.

**1c. Direct inspection.** Confirm tests/ (or test/, spec/, `__tests__/`)
exists. Read coverage/lint/security tool configs that exist
(`.coveragerc`, `.bandit`, `.eslintrc.*`, `.semgrep.yml`, etc.). Sanity-check
languages present by file extensions. Catches tools configured locally but
not yet wired into CI.

### Step 2 — Reconcile against the methodology's five categories

For each of `tests`, `coverage`, `warnings`, `lint`, `security`, pick one
locally-runnable command, preferring **manifests > direct reads > CI**. Two
hard authoring rules:

- **Self-contained.** No `--no-build`, `--no-restore`, or any "skip-build"
  flag that depends on pre-existing artifacts. If a build is genuinely
  required first, fold it into the gate as a shell pipeline
  (e.g. `dotnet build && dotnet test --no-build`).
- **Coverage threshold defaults to ≥ 90%.** If CI uses a different number,
  surface the divergence — do not silently adopt CI's value. Coverage gate
  commands should include the threshold flag (e.g. `coverage report
  --fail-under=90`).

Carry through `doc` and `plannext` from `verification.yml.example` unchanged
unless the repo gives a clear reason to alter them.

### Step 3 — Ask the user — only for what evidence cannot resolve

Legitimate question categories — **and only these**:

1. **Genuine ambiguity.** Plural / contradictory evidence the user must
   arbitrate. Example: "Found both `pytest` and `unittest discover` — which
   is canonical for a per-WU gate?"
2. **Methodology gap with no evidence.** Example: "Methodology wants a
   `security` gate; no security tool installed. Add one (suggest `bandit -r
   src -ll`) or consciously drop?"
3. **Threshold / policy call.** Example: "Coverage: methodology default
   ≥ 90% vs this repo's CI 80% — which governs?"

**Forbidden:** asking anything a file already answered (language, presence
of tests, lint config). That's a skill bug, not a clarification.

**Batch questions.** After Steps 1 and 2 are complete, present every
question in one round with the evidence that motivated it. Accept answers
together.

**Non-interactive contexts.** If no user is available to answer, still
produce the draft — every would-be question becomes an explicit `[gap]`
line in the report. Do not invent gates.

### Step 4 — Output

Print, in order:

1. **The proposed `.specfuse/verification.yml`**, in a fenced YAML block,
   in the same shape as `.specfuse/verification.yml.example`. Include the
   `code`, `doc`, and `plannext` keys. Omit any `code` gate the user
   consciously dropped — but call the omission out in the report below.

2. **The reconciliation report**, in this exact structure:

```
# Reconciliation report for <repo-name>

## Evidence inventory
- CI: <workflows examined, by path>
- Manifests: <files read, by path>
- Direct: <relevant config files / tree facts>

## Gate-by-gate

### tests        [verbatim|inferred|user-supplied|gap]
- Proposed command: <command>
- Source: <file:line or "answer to Q1">
- Notes: <local-runnability caveats, if any>

### coverage     [...]     (state threshold; flag divergence from ≥ 90%)
### warnings     [...]
### lint         [...]
### security     [...]

## CI gates not required by the loop (informational)
- <e.g. release upload, deploy, format-only checks>

## Methodology gates CI does not provide (the important list)
- <e.g. "CI has no coverage step; loop will require it. Decision: …">

## Questions and answers
- Q1: <question>  → A: <answer> → shaped <gate>.

## Recommended next step
- Review the draft. If accepted, write it to `.specfuse/verification.yml`
  (overwriting the example placeholder), then run
  `python .specfuse/scripts/loop.py --dry-run` against a feature folder.
```

## Closing rules

- You DRAFT; the user CONFIRMS. Never write `.specfuse/verification.yml` from
  this prompt. End with a one-line reminder that the user copies the YAML
  themselves.
- Use the **`status: blocked`** RESULT-block escape only if something
  fundamental prevents drafting at all (the repo has no source code,
  no CI, no manifests, and the user is non-interactive). Otherwise produce a
  draft — even a draft full of `[gap]` markers — and report.
- No prose summary beyond the report. The report is the summary.

End your turn with the RESULT block defined in
`.specfuse/rules/result-contract.md`. `status: complete` means "I produced a
draft + report and showed it to the user" — verification is the user
reading it, not a command exit.
