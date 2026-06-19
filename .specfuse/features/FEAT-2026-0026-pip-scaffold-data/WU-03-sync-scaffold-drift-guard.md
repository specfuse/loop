---
id: FEAT-2026-0026/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - scripts/sync-scaffold.sh
  - tests/test_scaffold_data_in_sync.py
duration_seconds: 513.539
cost_usd: 1.317362
input_tokens: 130
output_tokens: 22015
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# sync-scaffold script + drift guard

**Objective.** Keep the packaged scaffold data (`specfuse/loop/data/`) a faithful copy
of the canonical `.specfuse/` sources: a `sync-scaffold.sh` maintainer script that
copies, and a drift-guard test that fails CI if they diverge.

**Context.** This is `FEAT-2026-0026/T03`, depends on T01 (the package data exists).
Canonical lives in `.specfuse/{templates,rules,...}` (the repo dogfoods them); T01
copied them into the package. Without a guard, a future edit to a canonical rule/template
would silently ship a stale copy in the wheel — the exact two-source drift the loop hit
with skills (resolved there by `sync-skills.sh`). This mirrors that pattern. Ground in
`.specfuse/rules/never-touch.md` and `/authoring-work-units` §11 (operator scripts).

**Red-test (§12):** the drift-guard test `tests/test_scaffold_data_in_sync.py::test_package_data_matches_canonical`
fails on HEAD if any packaged file differs from canonical; it is the standing guard.
(If T01 synced perfectly it may pass immediately — in that case introduce a deliberate
one-byte mismatch to prove the test catches it, then re-sync; document the proof in the
RESULT notes.)

**Acceptance criteria.**

1. `scripts/sync-scaffold.sh`: copies canonical `.specfuse/{templates,rules}`,
   `verification.yml.example`, `roadmap.template.md`, `LEARNINGS.template.md`, `VERSION`
   into `specfuse/loop/data/` (and regenerates `gitignore.snippet` from init.sh's
   gitignore lines, or copies a canonical snippet). Idempotent; prints what it synced.
2. **Operator-script (§11):** `shellcheck scripts/sync-scaffold.sh` clean,
   `bash -n` parses, and `tests/sync_scaffold.bats` has ≥ 1 happy-path test with
   external commands stubbed.
3. `tests/test_scaffold_data_in_sync.py::test_package_data_matches_canonical` asserts
   every file under `specfuse/loop/data/` byte-matches its canonical `.specfuse/` source
   (and vice-versa — no orphan/missing files).
4. **Drift caught:** demonstrate the guard fails on a divergence (AC red-test note),
   then `scripts/sync-scaffold.sh` restores parity and the test passes.
5. `scripts/smoke-test.sh` / `.specfuse/verification.yml` run the new test in the suite.

**Do not touch.** Canonical `.specfuse/` content (the script copies FROM it); the driver
modules; `.specfuse/features/`, LEARNINGS, roadmap; secrets; `.git/`.

**Verification.** `code` gates incl. the drift-guard test; `shellcheck` + `bash -n` +
`bats` on the script (AC2); the demonstrated fail→sync→pass (AC4). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the canonical→package mapping is ambiguous for any file
(e.g. `gitignore.snippet` has no single canonical source), emit `status: blocked` and
propose where the canonical snippet should live rather than hardcoding lines in two
places.
