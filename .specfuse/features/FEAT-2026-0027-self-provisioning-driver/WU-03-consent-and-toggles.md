---
id: FEAT-2026-0027/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_autosync_consent.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Auto-sync consent + toggles (TTY prompt, --no-autosync, config)

**Objective.** Add the human-consent layer on top of T02's auto-sync: prompt before
overwriting user-modified versioned files when a TTY is present (else skip + warn), plus
a `--no-autosync` flag and a `.specfuse/config` toggle to disable auto-sync entirely.

**Context.** This is `FEAT-2026-0027/T03`, depends on T02 (the auto-sync core, which on
the "older + modified" branch already skips modified files + warns). This WU upgrades that
branch: on a TTY, prompt the operator to overwrite/keep each modified file (or all);
without a TTY (CI / `claude -p`), keep the T02 default (skip + warn, never block). Adds
the opt-out surfaces. `sys.stdin.isatty()` gates interactivity; no new deps. Ground in
`.specfuse/rules/result-contract.md`.

**Red-test (§12):** `tests/test_autosync_consent.py::test_modified_prompts_on_tty` and
`::test_no_autosync_flag_skips` fail on HEAD and pass after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_autosync_consent.py::test_modified_prompts_on_tty`
   exists and fails on HEAD before this WU's edits.
2. **TTY consent.** When auto-sync would overwrite ≥ 1 modified versioned file and
   `sys.stdin.isatty()` is true, the operator is prompted (overwrite / keep, per-file or
   all); accepted files are overlaid, kept files are left + noted. Tested with `isatty`
   and input mocked.
3. **No-TTY default preserved.** When not a TTY, modified files are skipped + warned (the
   T02 default) — the run is never blocked waiting on input.
4. **`--no-autosync` flag.** A new `loop.py` CLI flag fully skips auto-sync (no create, no
   overlay) and proceeds to `run`; a test asserts no scaffold writes occur with the flag.
5. **`.specfuse/config` toggle.** An `autosync: false` entry in a `.specfuse/config`
   (documented minimal format) disables auto-sync the same way; a test covers it. Absent
   config → auto-sync on (default).
6. The red tests (AC1) pass; `code` gates green (coverage ≥ 90).

**Do not touch.** T01's manifest/`detect_modified`; T02's decision tree beyond the
"older + modified" consent branch + the new flag/config plumbing; the dispatch/verify
loop; secrets; `.git/`.

**Verification.** `code` gates incl. `tests/test_autosync_consent.py`; the red→green proof
(AC1, AC6); the TTY-prompt + no-TTY-skip branches (AC2, AC3); the flag + config opt-outs
(AC4, AC5). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If a `.specfuse/config` file/format already exists for another
purpose (grep before inventing), align with it rather than introducing a second config
surface; if none exists and the format is non-obvious, emit `status: blocked` proposing
the minimal shape rather than guessing.
