---
id: FEAT-2026-0032/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.90
oracle_env: linux_docker
produces: tests/test_claude_resolution.py
produces_driver_helper: resolve_claude_cmd
model: sonnet
effort: medium
gate_set: code
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Resolve the bare `claude` CLI on Windows (shutil.which + PATHEXT)

**Objective.** Resolve the bare `claude` command to an executable Windows path
(honoring `PATHEXT`, so `claude.cmd` is found) before the driver dispatches an
agent session with `shell=False`, so agent dispatch works on native Windows —
while leaving the POSIX path untouched.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 2.
`CLAUDE_CMD` (`loop.py:79`) is `["claude", "-p", "--model", ...]` and `dispatch()`
invokes it via `subprocess.run(cmd, ...)` with `shell=False` (`loop.py:~1606`).
On Windows, `subprocess` with `shell=False` calls `CreateProcess`, which does
**not** consult `PATHEXT` — a bare `claude` argv[0] is not resolved to the
`claude.cmd` shim that the Claude Code Windows install ships. Dispatch would fail
with a "file not found" error before any agent runs.

The fix (PLAN.md / GATE-02.md DoD): resolve `claude` via `shutil.which("claude")`,
which honors `PATHEXT` (so `claude.cmd` / `claude.exe` is found), and substitute
the resolved path as argv[0] on Windows. On POSIX, `shell=False` with a bare
`claude` already resolves via PATH — leave it unchanged.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**
1. `tests/test_claude_resolution.py::test_win32_claude_resolved_via_which`
   exists and **fails on HEAD before this WU runs** — with `sys.platform` mocked
   to `win32` and `shutil.which("claude")` patched to return a `...\claude.cmd`
   path, it asserts the dispatched argv[0] is the resolved `claude.cmd` path (not
   the bare literal `"claude"`). On HEAD no resolution exists, so this is red (or
   the test file does not yet exist — also red).
2. On Windows a new `resolve_claude_cmd()` helper resolves the bare `claude` to
   the `shutil.which("claude")` result and substitutes it as argv[0]; the rest of
   `CLAUDE_CMD` (flags, `{model}`/`{effort}` substitution, `--output-format json`)
   is unchanged. On POSIX argv[0] stays the bare `claude`.
3. `tests/test_claude_resolution.py::test_win32_claude_resolved_via_which`
   **passes after this WU's edits**.
4. `tests/test_claude_resolution.py::test_win32_claude_missing_fails_loud`
   asserts that when `shutil.which("claude")` returns `None` on Windows, dispatch
   (or the helper) raises/exits with a message naming `claude` and PATH — it does
   not spawn a bare `claude` that will fail with an opaque OS error.
5. `tests/test_claude_resolution.py::test_posix_claude_unchanged` asserts that
   with `sys.platform` non-`win32`, argv[0] is still the bare `claude` — no
   resolution on POSIX — and passes.

**Do not touch.** The gate runner and smoke-import runner (`verify()`,
`run_smoke_imports`) — T05/T06. `.github/workflows/ci.yml` (T08).
`.specfuse/verification.yml`. Secrets, `.git/`. The driver owns all git — edit
files only.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
scoped red/green proof `python3 -m unittest tests.test_claude_resolution` and the
symbol-existence check
`python3 -c "from specfuse.loop.loop import resolve_claude_cmd"` (or the exact
public symbol name chosen — the check must name it).

**Escalation triggers.**
- The Claude Code Windows install shim name (`claude.cmd` vs `claude.exe`) is a
  **cross-repo contract** (see `GATE-02-REVIEW.md`) that cannot be verified from
  the Linux sandbox and is not exercised by CI (CI does not dispatch an agent).
  Implement against `shutil.which` (which is name-agnostic — it honors `PATHEXT`)
  and cover it with a mocked test; the real-Windows resolution is a post-merge
  manual check recorded in the gate-2 close's "What the loop did NOT verify". Do
  NOT hardcode a shim filename.
- If `resolve_claude_cmd` is absent from the files you edited, or dispatch still
  passes a bare `claude` argv[0] on Windows, emit `status: blocked` — do not
  claim complete.
