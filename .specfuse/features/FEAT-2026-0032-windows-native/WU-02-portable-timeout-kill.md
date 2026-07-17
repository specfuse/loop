---
id: FEAT-2026-0032/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
oracle_env: linux_docker
produces: tests/test_timeout_kill_portable.py
produces_driver_helper: run_gate
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Make the gate-timeout kill path cross-platform

**Objective.** Make the gate-command timeout kill work on Windows without
touching the POSIX behavior — so a timed-out gate is actually killed rather than
raising `AttributeError` on an absent `os.killpg`.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 1. The gate
runner spawns the gate command with `subprocess.Popen(..., start_new_session=True)`
(`loop.py:~1889-1892`) and, on `subprocess.TimeoutExpired`, kills the whole group
with `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` (`loop.py:~1908`).
`start_new_session` (setsid), `os.killpg`, `os.getpgid`, and `signal.SIGKILL`
are all POSIX-only. On Windows a timed-out gate would raise `AttributeError`
instead of terminating the child tree.

The Windows equivalent is `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
at spawn plus `taskkill /T /F /PID <pid>` (or `proc.kill()` followed by a
`/T` tree kill) to terminate the child and its descendants on timeout.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**
1. `tests/test_timeout_kill_portable.py::test_win32_timeout_uses_process_group_not_killpg`
   exists and **fails on HEAD before this WU runs** — with `sys.platform` mocked
   to `win32` and `subprocess` patched, it asserts the timeout path terminates
   the child via a Windows process-group / `taskkill` mechanism and never calls
   `os.killpg`. On HEAD the unconditional `os.killpg` path makes this red (or the
   test file does not yet exist — also red).
2. On Windows (`sys.platform == "win32"`) the gate command is spawned with
   `CREATE_NEW_PROCESS_GROUP` and, on `TimeoutExpired`, its process tree is
   killed via `taskkill /T /F` (or equivalent tree kill); no `os.killpg`,
   `os.getpgid`, or `signal.SIGKILL` is referenced on the Windows branch.
3. `tests/test_timeout_kill_portable.py::test_win32_timeout_uses_process_group_not_killpg`
   **passes after this WU's edits**.
4. `tests/test_timeout_kill_portable.py::test_posix_timeout_still_uses_killpg`
   asserts the POSIX branch still spawns with `start_new_session=True` and kills
   with `os.killpg(..., SIGKILL)` — unchanged — and passes.
5. Any existing tests covering the gate runner's timeout behavior pass unmodified.

**Do not touch.** Other gate-1 WU surfaces: the lock (`loop.py:44` /
`_filelock.py`, T01), `_HOME_PATH_RE` (`loop.py:476`, T03),
`.github/workflows/ci.yml` (T04). Secrets, `.git/`. The driver owns all git —
edit files only.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (`tests`,
`lint`, `security`, `coverage --fail-under=90`, `leak-scan`), plus the scoped
red/green proof `python3 -m unittest tests.test_timeout_kill_portable`.

**Escalation triggers.**
- If the POSIX timeout behavior cannot be preserved byte-for-byte while adding
  the Windows branch, emit `status: blocked` with the diff.
- If the gate runner's kill site is not the single site at `loop.py:~1889-1908`
  (a second spawn path exists), enumerate every site (`grep -n
  "start_new_session\|killpg" specfuse/loop/loop.py`) and block if any is left
  unported — a partial fix ships a Windows `AttributeError` on the missed path.

**Note on deferred verification.** This WU's Windows branch is proven in-loop
only by branch-selection unit tests (mocked platform). A *real* timing-out gate
on Windows is NOT exercised by gate 1's CI leg (which does import + `--dry-run`,
no gate execution). Record that gap in the gate-1 close's "What the loop did NOT
verify"; real-Windows timeout kill lands under gate 2's actual gate execution.
