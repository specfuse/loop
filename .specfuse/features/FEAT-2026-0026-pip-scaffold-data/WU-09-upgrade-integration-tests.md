---
id: FEAT-2026-0026/T09
type: implementation
effort: high
status: done
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - tests/test_upgrade_integration.py
attempts: 1
duration_seconds: 421.005
cost_usd: 0.914567
input_tokens: 20
output_tokens: 17372
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse upgrade` end-to-end — overlay against a real existing `.specfuse/` from the wheel

**Objective.** Prove `upgrade_specfuse` (T07) overlays a complete, correct upgrade onto a
**real, already-initialized** `.specfuse/` in a temp repo — versioned files refreshed,
user-authored files untouched, removed-versioned files pruned, never-downgrade refused,
`VERSION` stamped, `.claude` wiring refreshed — including resolution **from the installed
wheel**, as a standing integration test.

**Context.** This is `FEAT-2026-0026/T09`, gate 3 (terminal), depends on T07 (the upgrade
core) and reuses T04's `init_specfuse` to build the starting `.specfuse/` state. Mirror
T06's installed-wheel approach (`tests/test_init_integration.py`,
`tests/test_scaffold_resources.py`): a real `init` to lay the baseline, mutate it (stamp an
older VERSION, write sentinel user content, plant a stray versioned file), then `upgrade`
and assert the post-state. This is the "upgrade against a temp repo with an existing
`.specfuse/`" deliverable in the gate-3 scope. Per LEARNINGS `[FEAT-2026-0019/G1]` the
build/wheel leg is packaging-coupled — expect to run it **interactively (atomic)**, not
per-WU loop dispatch. Ground in `.specfuse/rules/result-contract.md`.

**Red-test exempt (§12):** this WU's deliverable **is** the integration test — the test is
its own red→green proof (it fails before T07's `upgrade_specfuse` exists, passes against
it). No separate red-test fixture.

**Acceptance criteria.**

1. **Versioned refreshed.** `tests/test_upgrade_integration.py` `init`s a `tmp_path` repo,
   mutates a versioned file (e.g. edits `.specfuse/rules/result-contract.md`), runs
   `upgrade_specfuse`, and asserts the versioned files (`templates/`, `rules/`,
   `verification.yml.example`) are byte-faithful to the seed again and
   `.specfuse/VERSION == scaffold_version()`.
2. **User-authored untouched.** Sentinel content written into `.specfuse/LEARNINGS.md`,
   `.specfuse/verification.yml`, `.specfuse/roadmap.md`, and a file under
   `.specfuse/features/` is **byte-unchanged** after upgrade (T07 AC3, end-to-end).
3. **Prune removed-versioned.** A stray `.specfuse/rules/obsolete.md` planted before upgrade
   is **gone** after; a `.specfuse/scripts/` or `.specfuse/skills/` directory planted before
   upgrade is **left intact** (legacy migration out of scope — T07 AC4).
4. **Never-downgrade.** Stamping `.specfuse/VERSION` to a value **newer** than
   `scaffold_version()` makes `upgrade_specfuse` raise the downgrade error and leave the tree
   untouched (T07 AC5, end-to-end).
5. **`.claude` refreshed + idempotent.** After upgrade the `.claude` surfaces (CLAUDE.md
   `@rules`, settings allowlist, plugin config) + `.gitignore` lines are present and a second
   `upgrade_specfuse` is a no-op (no duplicate gitignore lines, `settings.json` stable).
6. **Installed-wheel resolution.** A test (xfail/skip-guarded if the build toolchain is
   absent, like T06's) builds/installs the wheel into a clean venv and runs `upgrade` from it
   against a temp repo, confirming the overlay resolves package data from an installed wheel —
   not just the source tree.
7. `code` gates stay green; the new test file runs under `tests` in
   `.specfuse/verification.yml` and `scripts/smoke-test.sh` (if present); coverage ≥ 90 holds.

**Do not touch.** This repo's own `.specfuse/`, `.claude/`, `.gitignore` (the test writes to
`tmp_path` / a throwaway venv only); `specfuse/loop/scaffold.py` (T07 owns it); `init.sh`
(T08 owns it); the driver modules; `specfuse/loop/data/` content; secrets; `.git/`. The
driver owns all git — edit files only.

**Verification.** `code` gates incl. the new integration test; the versioned-refresh +
preserve + prune + never-downgrade assertions (AC1–AC4); the `.claude`-refresh/idempotency
test (AC5); the installed-wheel leg (AC6, skip-guarded when the toolchain is unavailable).
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the loop sandbox cannot build/install a wheel (no network / no
build backend), keep AC6 skip-guarded and record it under "what the loop did NOT verify" for
the close — do **not** delete the wheel leg (it is the regression T02/T06 exist to catch). If
the integration test reveals that `upgrade_specfuse` diverges from `init_specfuse` on a
surface both should share (e.g. the `.claude` wiring shape differs between init and upgrade),
emit a note proposing reconciliation rather than asserting the divergent behavior as correct.
