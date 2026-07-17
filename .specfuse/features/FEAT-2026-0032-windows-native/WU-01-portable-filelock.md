---
id: FEAT-2026-0032/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.00
oracle_env: linux_docker
produces: ["specfuse/loop/_filelock.py", "tests/test_filelock_portable.py"]
produces_driver_helper: acquire_tree_lock
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.14
started_at: 2026-07-17T16:07:07.007745+00:00
duration_seconds: 349.34
cost_usd: 1.063703
input_tokens: 54
output_tokens: 12030
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Make the working-tree lock portable (fcntl → cross-platform shim)

**Objective.** Replace the top-level `import fcntl` with a `_filelock` shim so
the driver imports and acquires its single-driver working-tree lock on Windows,
while keeping the exact SIGKILL-safe semantics it has on POSIX.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 1. Today
`specfuse/loop/loop.py:44` does `import fcntl` at module top level — a POSIX-only
stdlib module absent on Windows CPython, so `import specfuse.loop.loop` raises
`ModuleNotFoundError` before anything runs. The lock is acquired in
`acquire_tree_lock()` (`loop.py:~1207-1224`) via
`fcntl.flock(fd, LOCK_EX | LOCK_NB)` against `.specfuse/.loop.lock`.

The locking primitive MUST keep the property FEAT-2026-0004 chose it for: the
kernel releases the advisory lock automatically on process exit, **including
SIGKILL**, with no cleanup step. Pidfiles are explicitly forbidden — the
pid-holder is dead, the file remains, and the next launch stalls or skips the
check (LEARNINGS `[FEAT-2026-0004/G1-LESSONS]`). Windows' `msvcrt.locking`
(over `LockFileEx`) has the same release-on-handle-close / process-death
property, so it is the correct Windows counterpart.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/correlation-ids.md`, and
`.specfuse/skills/verification/SKILL.md`. Do not restate them.

**Acceptance criteria.**
1. `tests/test_filelock_portable.py::test_loop_imports_with_fcntl_absent` exists
   and **fails on HEAD before this WU runs** — it simulates `fcntl` being
   unavailable (e.g. remove it from `sys.modules` / block its import) and asserts
   `import specfuse.loop.loop` succeeds. On HEAD the top-level `import fcntl`
   makes this raise, so the test is red (or the test file does not yet exist —
   also red).
2. `specfuse/loop/loop.py` contains no top-level `import fcntl`; all lock
   acquisition/release routes through a new `specfuse/loop/_filelock.py` that
   selects `fcntl.flock` on POSIX and `msvcrt.locking` on Windows, chosen by
   `sys.platform`.
3. `tests/test_filelock_portable.py::test_loop_imports_with_fcntl_absent`
   **passes after this WU's edits**.
4. `tests/test_filelock_portable.py::test_posix_uses_fcntl_flock` asserts the
   POSIX branch calls `fcntl.flock` with `LOCK_EX | LOCK_NB`, and
   `::test_win32_branch_uses_msvcrt_locking` asserts (with `sys.platform`
   mocked to `win32`) that the Windows branch calls `msvcrt.locking` and never
   references `fcntl` — both pass.
5. The existing single-driver-lock behavior is unchanged on POSIX: every test in
   `tests/test_driver_lock.py` passes unmodified.
6. `_filelock.py`'s module docstring states the SIGKILL-release rationale and
   that pidfiles are ruled out (one sentence each) — the next reader must not
   "simplify" it to a pidfile.

**Do not touch.** Other gate-1 WU surfaces: the gate-timeout kill path
(`loop.py:~1889-1908`, T02), `_HOME_PATH_RE` (`loop.py:476`, T03),
`.github/workflows/ci.yml` (T04). Secrets, `.git/` internals. The driver owns
all git — edit files only, never run `git`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v`), `lint` (`ruff check ...`),
`security` (`bandit ...`), `coverage` (`--fail-under=90`), `leak-scan`. Plus the
scoped red/green proof
`python3 -m unittest tests.test_filelock_portable` and the symbol-existence
check `python3 -c "from specfuse.loop._filelock import acquire_tree_lock"` (or
the exact public symbol name chosen — the check must name it).

**Escalation triggers.**
- If `specfuse/loop/_filelock.py` is absent from the files you edited, or
  `loop.py` still imports `fcntl` at top level, emit `status: blocked` — do not
  claim complete.
- If the existing `tests/test_driver_lock.py` cannot pass through the shim
  without a behavior change on POSIX, emit `status: blocked` with the diff —
  changing lock semantics is out of this WU's scope.
- If preserving SIGKILL-release on Windows appears to require a pidfile or a
  cleanup step, stop and block — that contradicts the binding rationale; a human
  must decide.
