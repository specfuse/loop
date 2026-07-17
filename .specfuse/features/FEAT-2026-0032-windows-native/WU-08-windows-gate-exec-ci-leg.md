---
id: FEAT-2026-0032/T08
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.85
oracle_env: github_actions_ci
produces: ["tests/test_windows_gate_exec.py", ".github/workflows/ci.yml"]
model: sonnet
effort: medium
gate_set: code
duration_seconds: 729.185
cost_usd: 1.662945
input_tokens: 102
output_tokens: 13393
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Prove a real gate command runs green through Git-Bash on windows-latest

**Objective.** Extend the `windows-latest` CI leg so that, on a real Windows
runner, the driver's gate runner (`verify()`) executes a real `verification.yml`-
style gate command — one that uses POSIX shell features and `python3` — green
through Git-Bash. This is the **real-Windows oracle** for gate 2's DoD: gate
commands actually execute correctly on native Windows, not merely in mocked
branch-selection unit tests.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 2, and its
CI-oracle WU. Depends on **T05** (Git-Bash routing) and **T06** (`python3`
normalization) so the executed gate command actually passes on Windows. Gate 1's
`windows-smoke` job (T04, in `.github/workflows/ci.yml`) proves import +
`loop.py --dry-run` — which by design does NOT execute gate commands. Nothing on
a real Windows runner yet proves the bash-routing + interpreter-normalization
path this gate adds; without it, T05/T06 are proven only by Linux-sandbox mocked
tests and the port's gate-execution promise rots on the next merge.

The oracle is a committed, `win32`-gated integration test that drives the real
`verify()` code path against a fixture gate command exercising both new
behaviors:
- a POSIX shell feature that `cmd.exe` cannot run (e.g. `... && echo GATE_OK`,
  or `exit 1 || exit 0`), proving T05's `bash -c` routing, and
- a leading `python3` token, proving T06's interpreter normalization
  (e.g. `python3 -c "import specfuse.loop.loop" && echo GATE_OK`).

The test is skipped on non-Windows (so the Linux `code` gate is unaffected); it
executes for real only on the `windows-latest` job, where the PR check going
green is the oracle.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`. Red-test exempt: CI/infra oracle — the exit
condition is the `windows-latest` CI run on the PR, not a Linux-runnable
red→green unit test (§12 carve-out, as with T04). The committed test *is* the
oracle body; on Linux it is `skipUnless(sys.platform == "win32")` and does not run.

**Acceptance criteria.**
1. `tests/test_windows_gate_exec.py` exists with a `win32`-gated
   (`@unittest.skipUnless(sys.platform == "win32", ...)`) test that invokes the
   driver's real gate runner (`verify()`) against a fixture `verification.yml`
   gate command which (a) uses a POSIX shell feature `cmd.exe` cannot execute and
   (b) begins with a `python3` token, and asserts the gate reports PASS. On Linux
   the test is skipped (does not run); it is not a mock — on Windows it drives the
   real code path end-to-end.
2. `.github/workflows/ci.yml`'s `windows-smoke` job (from T04) gains a step that
   runs this test on `windows-latest` (e.g.
   `python -m unittest tests.test_windows_gate_exec -v`) and must exit `0`. The
   existing import + `--dry-run` steps and the `ubuntu-latest` `smoke-test` job
   are unchanged.
3. The workflow file is valid YAML and parses as a GitHub Actions workflow
   (`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
   exits `0`).
4. On the loop's own (Linux) host the new test is collected and **skipped**, so
   `python3 -m unittest discover -s tests` stays green — the test does not fail or
   error on Linux.

**Do not touch.** The driver implementation surfaces `verify()` /
`run_smoke_imports` / `CLAUDE_CMD` (T05/T06/T07 — this WU only *exercises* them,
does not modify them). The `ubuntu-latest` `smoke-test` job and
`scripts/smoke-test.sh`. `.specfuse/verification.yml`. Secrets, `.git/`. The
driver owns all git — edit files only.

**Verification.** The Linux `code` gate set runs unchanged (the new test is
skipped on Linux). Local pre-check: the YAML-validity command in AC 3, and
`python3 -m unittest discover -s tests` shows the new test collected + skipped.
This WU's real oracle is the `windows-smoke` job on the PR: its gate-exec step
must go green on `windows-latest`.

**Escalation triggers.**
- If `verify()` cannot be driven from a test without standing up the full loop
  machinery (WorkUnit + feature_dir + event log), scope the fixture as narrowly
  as the code allows and note what the test does NOT cover; do not fake a PASS by
  re-implementing the routing inside the test rather than calling the driver's
  own code path.
- The `windows-latest` interpreter names (`python`/`py`, `python3` absent) and
  the runner's `bash` resolution are **cross-repo contracts** (see
  `GATE-02-REVIEW.md`) confirmed only when this job runs. If the job fails on a
  contract mismatch (wrong interpreter token, WSL `bash` resolved instead of
  Git-Bash), that is signal for T05/T06 to adjust — emit `status: blocked` naming
  the mismatch rather than papering over it in the CI step.
