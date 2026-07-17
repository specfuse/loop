---
feature_id: FEAT-2026-0032
title: Non-WSL Windows execution (native driver + Git-Bash)
slug: windows-native
branch: feat/FEAT-2026-0032-windows-native
roadmap_goal: Run the specfuse-loop driver on native Windows without WSL — importable, gate commands executing through Git-Bash, home-path redaction correct — proven by a windows-latest CI leg, so corporate-managed and non-technical Windows users can run the loop.
autonomy_default: review
status: active
planned_cost_usd: 6.90
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Non-WSL Windows execution (native driver + Git-Bash)

The loop needs WSL to run on Windows today. WSL is blocked on many
corporate-managed devices and too heavy for non-technical users — exactly the
population a turnkey local executor should serve. The driver itself is
dependency-free stdlib Python (`requires-python >=3.10`, no runtime deps), and
`specfuse init` is already pure Python (`scaffold.py`, FEAT-2026-0026). WSL is
load-bearing only at a small, enumerable set of POSIX call sites — not across
"the loop" broadly.

**Scope: driver runtime only.** A Windows *user* installs via pip and runs the
driver; they never touch the `.sh` installers, git hooks, or `bats` gates —
those are contributor dev-tooling, dev-checkout-only, never shipped to target
repos (verified: no `.sh` is invoked from the Python driver). And the shell
strategy below makes Git-Bash a hard prerequisite anyway, so every Windows
machine running this already has `bash.exe` — the bash scripts and hooks run
under it incidentally. Porting them to native PowerShell would be work for zero
new beneficiary, so it is out of scope.

**Decisions (set at draft time):**

- **Git-Bash is the shell.** Git for Windows ships `bash.exe`; every dev with
  git has it, no admin, no WSL feature — corporate-safe. Gate commands
  (`shell=True`, `loop.py:1735,1890`) route through `bash -c` on Windows, so a
  target repo's existing `verification.yml` (`&&`, `exit 1 || exit 0`, `bats`,
  glob) keeps working unmodified. That compatibility is the whole prize; a
  PowerShell-native strategy would reject every gate command in the wild.
- **`python3` is normalized in the driver, not pushed onto target authors.**
  Target repos hardcode `python3` in gate commands and the smoke-import regex
  (`SMOKE_IMPORT_RE`, `loop.py:1700`); Windows launchers are `python`/`py`.
  The driver resolves the interpreter so the non-technical user's gate commands
  run unchanged. (Gate 2.)
- **The lock stays SIGKILL-safe.** `import fcntl` is top-level (`loop.py:44`) —
  the module cannot even *import* on Windows today. A `_filelock` shim selects
  `fcntl.flock` on POSIX, `msvcrt.locking` on Windows, preserving the
  kernel-releases-the-lock-on-process-death property (including SIGKILL) that
  `flock` gives us. Pidfiles are explicitly ruled out — the pid-holder is dead,
  the file remains, the next launch stalls or skips (LEARNINGS FEAT-2026-0004).
- **Redaction ships correct or not at all.** `_HOME_PATH_RE` (`loop.py:476`)
  matches only POSIX home paths; on Windows it silently fails to redact
  `C:\Users\name\`, leaking into `events.jsonl` and PR bodies. This rides in
  gate 1 with the core runtime fixes — a Windows port must not ship with
  redaction quietly disabled.
- **CI is the real-Windows oracle.** The driver runs in a Linux loop sandbox,
  so each WU lands platform-branch logic unit-tested on Linux (mock
  `sys.platform`, feed `C:\Users\…` strings, assert the Windows branch is
  selected and constructed correctly). Real Windows behavior is proven by a
  `windows-latest` CI leg — today every leg is `ubuntu-latest`, so without it
  the port rots on merge. Autonomy is `review` precisely because so much
  verification is deferred off the Linux sandbox.

**Out of scope:** removing/breaking WSL (it keeps working); PowerShell-native
hooks or installers; porting the dev `bats` / `init.sh` / `scripts/*.sh`
surface (Git-Bash covers them); ARM-Windows; a repo-level default base or any
non-runtime concern. The contended-lock SIGKILL-handoff case (two drivers, one
killed) is not verifiable even on Windows CI without a flaky spawn-and-kill
test — it is deferred to a post-merge manual check, recorded in the close WU's
"What the loop did NOT verify."

This file owns the **shape**. Two gates: gate 1 makes the driver import and run
on native Windows (proven by a CI leg doing import + `--dry-run`); gate 2 makes
gate commands execute correctly through Git-Bash. Gate 1 has 4 substantive WUs,
so it carries the full `close-intermediate` → `plan-next` closing sequence
(`docs/methodology.md` §6). Gate 2 is skeletal now — its substantive WUs are
drafted by gate 1's `plan-next` — and pre-declares its terminal `close` so the
linter reads gate 1 as non-terminal.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0032/T01
        file: WU-01-portable-filelock.md
        depends_on: []
      - id: FEAT-2026-0032/T02
        file: WU-02-portable-timeout-kill.md
        depends_on: []
      - id: FEAT-2026-0032/T03
        file: WU-03-windows-home-redaction.md
        depends_on: []
      - id: FEAT-2026-0032/T04
        file: WU-04-windows-ci-leg.md
        depends_on:
          - FEAT-2026-0032/T01
          - FEAT-2026-0032/T02
          - FEAT-2026-0032/T03
      - id: FEAT-2026-0032/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0032/T01
          - FEAT-2026-0032/T02
          - FEAT-2026-0032/T03
          - FEAT-2026-0032/T04
      - id: FEAT-2026-0032/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on:
          - FEAT-2026-0032/G1-CLOSE-INTERMEDIATE
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0032/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on: []
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- T01, T02, T03 are mutually independent; T04 (the CI leg) needs all three so
  the driver it imports on `windows-latest` actually carries the fixes.
- **Oracle split.** T01's POSIX lock, T02's POSIX kill, and T03's redaction are
  fully in-loop-verifiable against a real Linux sandbox. Their Windows branches
  are verified by *branch-selection* unit tests (mocked `sys.platform`) in-loop,
  with real-Windows behavior proven by T04's `windows-latest` leg (import +
  `--dry-run`). Two Windows behaviors are NOT provable by that leg — a
  timing-out gate's `taskkill` path (T02) and the contended-lock SIGKILL handoff
  (T01) — and are enumerated as deferred in the gate-1 close.
- Gate 2 pre-declares `G2-CLOSE` only so the linter treats the last non-empty
  gate as terminal; `plan-next` inserts gate 2's substantive WUs *before* it and
  updates its `depends_on`.
- This feature keeps WSL working; it adds a native path beside it.
