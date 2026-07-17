---
id: FEAT-2026-0032/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 0.75
oracle_env: github_actions_ci
produces: .github/workflows/ci.yml
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.14
started_at: 2026-07-17T16:34:00.315655+00:00
duration_seconds: 135.032
cost_usd: 0.334802
input_tokens: 22
output_tokens: 2203
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Add a windows-latest CI leg (import + --dry-run smoke)

**Objective.** Add a `windows-latest` CI job that proves, on a real Windows
runner, that the driver imports and `loop.py --dry-run` walks the bundled
example — the real-Windows oracle for gate 1's T01–T03.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 1, and its
terminal WU (depends on T01, T02, T03). Every CI leg today is `ubuntu-latest`
(`.github/workflows/ci.yml`), so nothing proves the Windows branches T01–T03
add; without a Windows leg the port rots on the next merge. The existing
`smoke-test` job invokes `scripts/smoke-test.sh`, which is Linux-only (apt,
bats, gitleaks) — so this is a **separate job**, not a matrix over the existing
one.

Scope is deliberately import + `--dry-run` only. `loop.py --dry-run`
(`loop.py:3285`) performs no mutation and does NOT execute `verification.yml`
gate commands — so it does not need Git-Bash shell routing or interpreter
normalization (those are gate 2). It exercises exactly the gate-1 surfaces:
module import (T01's `_filelock`), and feature-graph load/walk.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`. Red-test exempt: CI/infra config — the oracle
is the CI run itself, not a unit test (§12 carve-out).

**Acceptance criteria.**
1. `.github/workflows/ci.yml` gains a job running on `windows-latest` that:
   checks out the repo, sets up Python 3.12, `pip install -e .` (runtime only —
   the Windows leg does not need `.[dev]`), then runs, as two steps that must
   each exit `0`:
   - `python -c "import specfuse.loop.loop"`
   - `python .specfuse/scripts/loop.py --dry-run` against the bundled example
     `FEAT-2026-0001-health-endpoint` (use the same invocation
     `docs`/`CONTRIBUTING.md` document for `--dry-run`).
2. The existing `smoke-test` job on `ubuntu-latest` is unchanged — same steps,
   same `runs-on`.
3. The workflow file is valid YAML and parses as a GitHub Actions workflow
   (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`
   exits `0`).
4. The new job is named distinctly (e.g. `windows-smoke`) so its status is
   greppable in `gh pr checks`.

**Do not touch.** Other gate-1 WU surfaces: `_filelock.py` / `loop.py:44`
(T01), the timeout kill path (T02), `_HOME_PATH_RE` (T03). `scripts/smoke-test.sh`
and `.specfuse/verification.yml` (the Windows leg does not run them). Secrets,
`.git/`. The driver owns all git — edit files only.

**Verification.** The `code` gate set still runs on the Linux side unchanged.
This WU's own oracle is the CI run on the PR: the `windows-smoke` job must go
green. Local pre-check: the YAML-validity command in AC 3, and
`python .specfuse/scripts/loop.py --dry-run` against the bundled example exits
`0` on the loop's own (Linux) host as a smoke of the invocation string.

**Escalation triggers.**
- If `loop.py --dry-run` is not the correct flag/invocation, or the bundled
  example path differs from `FEAT-2026-0001-health-endpoint`, emit
  `status: blocked` — do not invent CI steps that will fail only on the runner.
- If `pip install -e .` on Windows pulls a dependency the `[project]`
  `dependencies = []` claim says should not exist, block and report it — that is
  a packaging surprise a human must see.
- If the `windows-latest` runner's default Python launcher is `py`/`python`
  rather than `python3` and the `--dry-run` step needs the interpreter name,
  use `python` (the setup-python shim provides it) — this is the interpreter
  normalization gate 2 generalizes; do not pull that work forward here.
