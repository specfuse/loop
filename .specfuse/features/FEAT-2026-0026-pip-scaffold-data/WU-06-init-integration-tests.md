---
id: FEAT-2026-0026/T06
type: implementation
effort: high
status: pending
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - tests/test_init_integration.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse init` end-to-end — full scaffold into a temp repo from the installed wheel

**Objective.** Prove `init_specfuse` + `wire_claude` (T04+T05) produce a complete,
correct, immediately-working `.specfuse/` + `.claude` layout in a fresh temp repo —
including resolution **from the installed wheel**, idempotency/refusal, and
gitignore + plugin-config correctness — as a standing integration test.

**Context.** This is `FEAT-2026-0026/T06`, gate 2, depends on T04 and T05. T02's unit
tests proved the resource API resolves from a built wheel (`pip install` into a clean
venv); this WU extends that proof to the *write* path: a real `init` against a temp repo,
asserting the whole tree + wiring, not just that symbols import. This is the "tests against
a temp repo" deliverable in the gate-2 scope. Mirror T02's installed-wheel approach
(`tests/test_scaffold_resources.py`) for the wheel-resolution leg. Ground in
`.specfuse/rules/result-contract.md`; per LEARNINGS `[FEAT-2026-0019/G1]` the build/wheel
leg is packaging-coupled — expect to run it interactively (atomic), not per-WU dispatch.

**Red-test exempt (§12):** this WU's deliverable **is** the test suite — the test is its
own red→green proof (it fails before T04/T05 exist, passes against them). No separate
red-test fixture.

**Acceptance criteria.**

1. `tests/test_init_integration.py` runs `init_specfuse` + `wire_claude` against a
   `tmp_path` repo and asserts the **full** produced layout: `.specfuse/{templates,rules}/`
   present and byte-faithful to the seed, `.specfuse/VERSION` == `scaffold_version()`,
   `.specfuse/{roadmap.md,LEARNINGS.md,verification.yml}` seeded, `.specfuse/features/`
   present, and the `.claude` surfaces (CLAUDE.md `@rules`, settings allowlist, plugin
   config) + `.gitignore` lines written.
2. **Refusal.** A test asserts a second `init_specfuse` against the same target raises the
   refusal error (T04 AC3) and leaves the existing tree untouched (no partial overwrite).
3. **Idempotency.** A test asserts re-running the `.claude`/`.gitignore` wiring on the
   already-wired repo is a no-op (no duplicate gitignore lines, settings.json stable).
4. **gitignore + plugin-config correctness.** Tests assert the `.gitignore` contains
   exactly the runtime-artifact lines and `.claude/settings.json` parses as JSON with the
   correct marketplace/plugin identifiers (`specfuse/specfuse`, `specfuse@specfuse`).
5. **Installed-wheel resolution.** A test (xfail/skip-guarded if the build toolchain is
   absent, like T02's) builds/installs the wheel into a clean venv and runs `init` from it
   into a temp repo, confirming the write path resolves package data from an installed
   wheel — not just the source tree.
6. `code` gates stay green; the new test file runs under `tests` in
   `.specfuse/verification.yml` and `scripts/smoke-test.sh`; coverage ≥ 90 holds.

**Do not touch.** This repo's own `.specfuse/`, `.claude/`, `.gitignore` (the test writes
to `tmp_path` / a throwaway venv only); `specfuse/loop/` source (T04/T05 own it); the
driver modules; `specfuse/loop/data/` content; secrets; `.git/`.

**Verification.** `code` gates incl. the new integration test; the refusal +
idempotency + plugin-config assertions (AC2–AC4); the installed-wheel leg (AC5,
skip-guarded when the toolchain is unavailable). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the loop sandbox cannot build/install a wheel (no network /
no build backend), keep AC5 skip-guarded and record it under "what the loop did NOT
verify" for the close — do **not** delete the wheel leg (that is the regression T02 exists
to catch). If the integration test reveals that `init_specfuse`/`wire_claude` need a
single orchestrating entry point (one call doing both), emit a note proposing it rather
than duplicating the call sequence across tests and the (cross-repo) CLI.
