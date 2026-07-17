---
id: FEAT-2026-0032/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 1.00
oracle_env: linux_docker
produces: tests/test_bash_routing.py
produces_driver_helper: resolve_bash
model: sonnet
effort: medium
gate_set: code
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Route the gate-command runner through Git-Bash on Windows

**Objective.** Make the `verify()` gate runner execute a target repo's
`verification.yml` gate commands through Git-Bash (`bash -c`) on Windows instead
of `cmd.exe`, so gate commands that use POSIX shell features (`&&`,
`exit 1 || exit 0`, globs, `bats`, pipes) run unchanged — while leaving the POSIX
path byte-for-byte as it is.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 2. The gate
runner spawns each gate command with `subprocess.Popen(command, shell=True, ...)`
in `verify()` (`specfuse/loop/loop.py:~1893`). On Windows `shell=True` runs the
command through `cmd.exe`, which does not understand the POSIX shell syntax that
real `verification.yml` gate commands routinely use (see this repo's own
`.specfuse/verification.yml`: `coverage run ... && coverage report`,
`git ... --quiet HEAD -- . && exit 1 || exit 0`, `bats tests/*.bats`). Every such
gate would fail or misbehave on native Windows today.

The decision (PLAN.md): **Git-Bash is the shell.** Git for Windows ships
`bash.exe`; every dev with git has it, no admin, no WSL feature. Routing gate
commands through `bash -c` on Windows keeps a target repo's existing gate
commands working unmodified — that compatibility is the whole prize.

The Windows branch of the timeout-kill defense already landed in T01/T02
(`CREATE_NEW_PROCESS_GROUP` + `taskkill` at `loop.py:~1887-1927`); this WU changes
only *which program the command string is handed to*, not the process-group /
timeout machinery, which must keep working on both platforms.

**Bash resolution.** Prefer the Git-for-Windows `bash.exe` specifically. Deriving
it from `git --exec-path` (whose result is the git-core dir inside the Git
install; `bash.exe` is the install's `bin/bash.exe`) is more reliable than a bare
`shutil.which("bash")`, which on a Windows host can resolve to
`C:\Windows\System32\bash.exe` — the **WSL launcher**, which fails when no distro
is installed. If no Git-Bash can be found, fail loud with an actionable
"install Git for Windows" message rather than silently falling back to `cmd.exe`.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/correlation-ids.md`,
`.specfuse/skills/verification/SKILL.md`. Do not restate them.

**Acceptance criteria.**
1. `tests/test_bash_routing.py::test_win32_gate_routes_through_bash` exists and
   **fails on HEAD before this WU runs** — with `sys.platform` mocked to `win32`
   and `subprocess.Popen` patched, it runs one gate through `verify()` and
   asserts the command was spawned as a `[bash, "-c", <command>]` argv (argv[0]
   basename is `bash`/`bash.exe`, argv[1] is `-c`, argv[2] is the original gate
   command) with `shell=False`. On HEAD the unconditional `shell=True` string
   spawn makes this red (or the test file does not yet exist — also red).
2. On Windows (`sys.platform == "win32"`) `verify()` spawns each gate command as
   `[bash, "-c", command]` with `shell=False`, where `bash` is resolved by a new
   `resolve_bash()` helper that prefers the Git-for-Windows `bash.exe`. The
   process-group / timeout-kill behavior added by T02 is preserved unchanged on
   both platforms (the `CREATE_NEW_PROCESS_GROUP` spawn kwarg and `taskkill`
   timeout path still apply).
3. `tests/test_bash_routing.py::test_win32_gate_routes_through_bash` **passes
   after this WU's edits**.
4. `tests/test_bash_routing.py::test_posix_gate_still_uses_shell_true` asserts the
   POSIX branch (`sys.platform != "win32"`) still spawns with `shell=True` and the
   bare command string, `start_new_session=True` — unchanged — and passes.
5. `tests/test_bash_routing.py::test_no_bash_found_fails_loud` asserts that when
   `resolve_bash()` finds no Git-Bash on Windows, `verify()` (or `resolve_bash()`)
   raises/exits with a message naming "Git for Windows" — it does NOT silently
   fall back to `cmd.exe`.
6. The existing gate-runner tests (timeout kill, degraded-oracle detection) pass
   unmodified on POSIX.

**Do not touch.** The smoke-import runner (`run_smoke_imports`,
`loop.py:~1717`) and the `python3` interpreter-name normalization — that is T06,
which depends on this WU and slots interpreter normalization into the same gate
command *before* the bash handoff. `CLAUDE_CMD` / dispatch (T07).
`.github/workflows/ci.yml` (T08). `.specfuse/verification.yml` (do not weaken a
gate to pass). Secrets, `.git/`. The driver owns all git — edit files only, never
run `git`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (`tests`,
`lint`, `security`, `coverage --fail-under=90`, `leak-scan`), plus the scoped
red/green proof `python3 -m unittest tests.test_bash_routing` and the
symbol-existence check
`python3 -c "from specfuse.loop.loop import resolve_bash"` (or the exact public
symbol name chosen — the check must name it).

**Escalation triggers.**
- If a real Git-for-Windows layout cannot be confirmed from the sandbox (the
  `git --exec-path` → sibling `bin/bash.exe` relative path is a **cross-repo
  contract** — see `GATE-02-REVIEW.md`), implement the resolution against the
  documented layout and cover it with a mocked test; do NOT invent an absolute
  path. The real-runner proof is deferred to T08's `windows-latest` gate leg.
- If routing the command through `bash -c` on POSIX (unifying both platforms)
  would change any existing POSIX gate's behavior, do NOT — keep POSIX on
  `shell=True` and branch only the Windows path. Emit `status: blocked` with the
  diff if the POSIX path cannot be preserved.
- If `resolve_bash` is absent from the files you edited, or `verify()` still
  spawns `shell=True` unconditionally on Windows, emit `status: blocked` — do not
  claim complete.
