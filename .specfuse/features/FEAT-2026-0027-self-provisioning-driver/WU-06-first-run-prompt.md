---
id: FEAT-2026-0027/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
effort: medium
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_autosync_firstrun.py
produces_driver_helper:
  - auto_sync
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# First-run scaffold prompt before self-provisioning a fresh repo

**Objective.** Gate `auto_sync`'s **create** branch behind a first-run consent prompt:
when no `.specfuse/` exists and a TTY is attached, show what will be created and ask
before scaffolding; on decline, abort with opt-out guidance; with no TTY (CI), proceed
with a one-line notice so automation never blocks.

**Context.** This is `FEAT-2026-0027/T06`, gate 3. Gate 1's `auto_sync`
(`loop.py:3477`) replaced fail-loud `check_scaffold_version` with create / overlay /
no-op / never-downgrade branches. The **create** branch (`loop.py:3514`,
`if not specfuse_dir.exists()`) today calls `_scaffold.init(target)` **unconditionally** —
so running `specfuse-loop` in the wrong directory silently writes a full `.specfuse/`
tree. This WU adds the missing first-run affordance: a memoryless user gets one chance to
confirm before a fresh repo is self-provisioned.

Reuse the consent pattern gate 1's T03 already established: the TTY overwrite prompt in
`auto_sync`'s older-modified branch (`loop.py:3586-3612`, `sys.stdin.isatty()` guard +
`input(...)`), and its non-TTY fallback (skip + warn, never block, `loop.py:3641`). The
`--no-autosync` flag + `.specfuse/config` `autosync: false` opt-outs (T03) already
short-circuit `auto_sync` before the create branch — confirm they still do, and that the
first-run prompt is **only** reached when auto-sync is enabled and `.specfuse/` is absent.
The create branch also calls `refresh_claude_plugin_config` (T04) — that must still run
when the user confirms, and must NOT run when the user declines.

This is single-repo and fully loop-dispatchable: the prompt lives in `auto_sync`
(`loop.py`), surfaced directly through `specfuse-loop`; no cross-repo CLI involved.
Ground in `.specfuse/rules/result-contract.md`, `never-touch.md`.

**Red-test (§12):**
`tests/test_autosync_firstrun.py::TestFirstRun::test_create_aborts_on_tty_decline`
fails on HEAD (create is unconditional) and passes after.

**Acceptance criteria.**

1. **Red test first.**
   `tests/test_autosync_firstrun.py::TestFirstRun::test_create_aborts_on_tty_decline`
   exists and fails on HEAD before this WU's edits
   (`python3 -m unittest tests.test_autosync_firstrun.TestFirstRun.test_create_aborts_on_tty_decline`
   exits non-zero, or the file does not yet exist — both count as red).
2. **TTY confirm.** When `.specfuse/` is absent, auto-sync is enabled, and
   `sys.stdin.isatty()` is true, `auto_sync` prints what will be created (the target
   path) and reads a `[Y/n]` answer (default **yes** on empty input). On yes it proceeds
   to `init` + `refresh_claude_plugin_config` exactly as today.
3. **Decline aborts cleanly.** On an explicit no, `auto_sync` creates **nothing** (no
   `.specfuse/`, no `.claude/settings.json` write) and prints a one-line notice naming
   the `--no-autosync` flag / `.specfuse/config` `autosync: false` opt-out, then returns
   without raising. The driver run is left to proceed/exit as it would with no scaffold —
   this WU does not change run-level control flow beyond skipping the create.
4. **Non-TTY proceeds.** With no TTY, the create branch proceeds (init + plugin refresh)
   after printing a single-line notice that it self-provisioned `.specfuse/` — never
   prompting, never blocking (CI parity with T03's non-TTY behavior).
5. **Opt-outs still short-circuit first.** `--no-autosync` and `.specfuse/config`
   `autosync: false` skip `auto_sync` entirely — the first-run prompt is never reached
   under either opt-out (assert in tests).
6. The red test (AC1) passes; new unit tests cover tty-confirm-proceeds,
   tty-decline-aborts-no-writes, non-tty-proceeds-with-notice, and both opt-outs-skip;
   `code` gates green (coverage ≥ 90); `auto_sync` still never runs `git`.

**Do not touch.** Gate 1 + gate 2 WUs (T01–T04) and their tests; the overlay / equal /
never-downgrade branches of `auto_sync` (this WU touches only the **create** branch +
its new prompt); `refresh_claude_plugin_config` (call it unchanged on confirm); the
doctor (T05) and migration-prune (T07) scope; `scaffold.init`'s internals; secrets;
`.git/`. The driver owns all git — edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** `code` gates (`python3 -m unittest discover -s tests -v` incl.
`tests/test_autosync_firstrun.py`; `ruff check`; coverage ≥ 90). Symbol check:
`python3 -c "from specfuse.loop.loop import auto_sync"`. The decline-writes-nothing
assertion (AC3) and the non-tty-proceeds assertion (AC4). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If declining the first-run prompt cannot abort the create
without also suppressing a later, unrelated phase of the run (i.e. the create branch's
return value feeds run-level control flow in a way this WU's scope can't safely change),
emit `status: blocked` and name the coupling rather than guessing the run-abort
semantics. If the existing T03 consent prompt and the new first-run prompt would collide
(both firing on the same run), surface it — a fresh repo hits create, not overlay, so
they should be mutually exclusive; if they aren't, that's a design conflict to flag, not
paper over. If `auto_sync` is absent from the files you edited or the create branch is
unchanged, emit `status: blocked` — do not claim complete.
