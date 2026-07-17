---
id: FEAT-2026-0032/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
oracle_env: linux_docker
produces: tests/test_interpreter_normalization.py
produces_driver_helper: normalize_interpreter
model: sonnet
effort: medium
gate_set: code
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Normalize `python3` to the running interpreter on Windows

**Objective.** Resolve `python3`-style commands to the Windows interpreter
(`python` / `py` / the running `sys.executable`) for both the gate runner and the
smoke-import runner on Windows, so a target repo's gate commands and the driver's
`python3 -c "from X import Y"` smoke imports run unchanged — while leaving the
POSIX path untouched.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 2. Depends
on **T05** (Git-Bash routing), which established the Windows branch of the gate
runner; this WU slots interpreter normalization into the gate command string
*before* T05's `bash -c` handoff, and applies the same normalization to the
smoke-import runner.

Two call sites carry a literal `python3` that has no launcher on native Windows
(Windows Python ships `python` and the `py` launcher, not `python3`):
- **Gate commands.** Target repos hardcode `python3` in `verification.yml` (this
  repo's own `tests` gate is `python3 -m unittest discover ...`; `leak-scan` is
  `python3 .specfuse/scripts/leak_scan.py --all`). The command string reaches
  `verify()` (`loop.py:~1872`) and, on Windows, T05 hands it to `bash -c` — but
  Git-Bash does not provide `python3` either unless the interpreter is on PATH
  under that name.
- **Smoke imports.** `run_smoke_imports` (`loop.py:~1717`) runs each
  `python3 -c "from X import Y"` line matched by `SMOKE_IMPORT_RE`
  (`loop.py:~1697`, which already tolerates `python3?`). The command string still
  literally says `python3`.

The decision (PLAN.md): **`python3` is normalized in the driver, not pushed onto
target authors.** The driver resolves the interpreter so the non-technical user's
gate commands run unmodified.

**Interpreter choice.** Resolve to a name/path that exists on the Windows host:
`python` (what `actions/setup-python` puts on PATH), the `py` launcher, or
`sys.executable`. Prefer a form that survives being passed through Git-Bash
`bash -c` — a bare `python` token is safer than a raw `sys.executable` absolute
path, whose backslashes MSYS/Git-Bash can mangle (a **cross-repo contract** — see
`GATE-02-REVIEW.md`). Normalize only the leading `python3` token; do not rewrite
`python3` occurring inside a quoted argument.

Bind by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**
1. `tests/test_interpreter_normalization.py::test_win32_gate_command_python3_normalized`
   exists and **fails on HEAD before this WU runs** — with `sys.platform` mocked
   to `win32`, it asserts a gate command beginning `python3 ...` is rewritten so
   the interpreter token is the resolved Windows interpreter (not the literal
   `python3`) before the command is spawned. On HEAD no normalization exists, so
   this is red (or the test file does not yet exist — also red).
2. `tests/test_interpreter_normalization.py::test_win32_smoke_import_python3_normalized`
   asserts the same normalization is applied to `run_smoke_imports` command
   strings on Windows (`python3 -c "from X import Y"` → resolved interpreter).
3. On Windows a new `normalize_interpreter()` helper resolves the leading
   `python3` token to the running Windows interpreter, and is applied at both the
   gate-command site (`verify()`) and the smoke-import site
   (`run_smoke_imports`). On POSIX the command strings are unchanged.
4. `tests/test_interpreter_normalization.py::test_posix_python3_unchanged` asserts
   that with `sys.platform` non-`win32`, both a gate command and a smoke-import
   command keep the literal `python3` — no normalization on POSIX — and passes.
5. Both named win32 tests **pass after this WU's edits**; the existing
   smoke-import tests and gate-runner tests pass unmodified on POSIX.

**Do not touch.** T05's bash-routing decision (this WU composes with it, does not
revert it — normalization happens on the command string; bash routing happens on
the spawn). `CLAUDE_CMD` / dispatch (T07). `.github/workflows/ci.yml` (T08).
`.specfuse/verification.yml` (do not weaken a gate to pass). Secrets, `.git/`. The
driver owns all git — edit files only.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
scoped red/green proof
`python3 -m unittest tests.test_interpreter_normalization` and the
symbol-existence check
`python3 -c "from specfuse.loop.loop import normalize_interpreter"` (or the exact
public symbol name chosen — the check must name it).

**Escalation triggers.**
- If the resolved interpreter form cannot be verified to survive a Git-Bash
  `bash -c` round-trip on a real Windows runner from the sandbox, implement the
  safest documented form (bare `python`) and note the residual risk; the
  real-runner proof is deferred to T08. Do NOT invent a path.
- If `SMOKE_IMPORT_RE` must change to admit the normalized command and the change
  would broaden what free-form Python the driver will execute (a security
  regression — see the runner's docstring), emit `status: blocked` rather than
  loosening the pattern.
- If `normalize_interpreter` is absent from the files you edited, or either call
  site still passes a literal `python3` on Windows, emit `status: blocked` — do
  not claim complete.
