<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Gate 2 review — arm the gate-1 → gate-2 boundary

Drafted by `FEAT-2026-0032/G1-PLAN` (`WU-91`). Gate 2's definition of done
(`GATE-02.md`): a real `verification.yml` gate command runs green through
Git-Bash on `windows-latest`; `python3`-style commands and the `SMOKE_IMPORT_RE`
smoke-import path resolve to the Windows interpreter; the `claude` CLI resolves.

**All gate-2 WUs are `status: draft`.** Arming (draft → pending) is the human's
job at this review. The linter (`plannext` gate = `lint_plan.py`) passes on the
folder with these drafts in place.

## Drafted work units

Each traces to a gate-2 DoD bullet. Verified against current `loop.py` source at
draft time (line numbers as of `driver_version: 0.3.14`).

| id | file | depends_on | rationale (→ DoD) |
|----|------|-----------|-------------------|
| `FEAT-2026-0032/T05` | `WU-05-git-bash-shell-routing.md` | — | Routes the `verify()` gate runner (`loop.py:~1893`, currently unconditional `shell=True` → `cmd.exe`) through `[bash, "-c", cmd]` on Windows via a new `resolve_bash()` (prefers Git-for-Windows `bash.exe`). → DoD bullet 1 (gate command runs green through Git-Bash). |
| `FEAT-2026-0032/T06` | `WU-06-python3-interpreter-normalization.md` | T05 | Normalizes the leading `python3` token to the running Windows interpreter for both gate commands (`verify()`) and smoke imports (`run_smoke_imports`, `loop.py:~1717`) via a new `normalize_interpreter()`. Depends on T05 — same gate-command surface; normalization is applied before T05's `bash -c` handoff. → DoD bullet 2 (`python3` + `SMOKE_IMPORT_RE` resolve to the Windows interpreter). |
| `FEAT-2026-0032/T07` | `WU-07-windows-claude-resolution.md` | — | Resolves the bare `claude` (`CLAUDE_CMD`, `loop.py:79`, dispatched `shell=False` at `loop.py:~1606`) via `shutil.which("claude")` honoring `PATHEXT` so `claude.cmd` is found, through a new `resolve_claude_cmd()`. Independent — different call site from the gate runner. → DoD bullet 3 (`claude` CLI resolves). |
| `FEAT-2026-0032/T08` | `WU-08-windows-gate-exec-ci-leg.md` | T05, T06 | Extends the `windows-smoke` CI job (T04) with a `win32`-gated integration test that drives the real `verify()` path against a fixture gate command (POSIX shell feature + `python3` token) on `windows-latest`. The real-Windows oracle. Depends on T05+T06 so the executed gate actually passes. → DoD bullet 1 (proven on real `windows-latest`, not only mocked). |
| `FEAT-2026-0032/G2-CLOSE` | `WU-92-gate-2-close.md` | T05, T06, T07, T08 | Pre-declared terminal close (retrospective + lessons + docs + terminal verdict). `depends_on` updated to the four drafted WUs. Unchanged body. |

**Adjustments from the WU-91 sketch (per escalation triggers):**

- The sketch bundled "route the gate runner *and* the smoke-import runner through
  `bash -c`." On inspection the smoke-import command (`python3 -c "from X import
  Y"`) uses **no** POSIX shell features — it only needs interpreter
  normalization, not bash routing. So T05 routes **only** the gate runner
  (where user shell features live); T06 handles `python3` for **both** surfaces.
  This is a cleaner split than the sketch and avoids passing a `sys.executable`
  backslash path through Git-Bash for the smoke case.
- The sketch listed three work items; a **fourth** WU (T08) was added because
  gate 2's DoD bullet 1 demands a *real* `windows-latest` gate execution, and
  gate 1's CI leg (T04) is import + `--dry-run` only (no gate execution). Without
  T08 the whole gate would be proven only by Linux-sandbox mocked tests.
- T02's Windows timeout-kill branch (`CREATE_NEW_PROCESS_GROUP` + `taskkill`) is
  **already landed** (`loop.py:~1887-1927`) — no gate-2 WU re-does it; T05 changes
  only *which program the command is handed to*, preserving that machinery.

## Cross-repo contracts (§8) — verify before locking the dependent AC

Values that live in an external system. **None are locked.** Each cannot be
verified from the Linux loop sandbox; the authoritative check happens where
noted. The dependent AC stays **unlocked** until the source is checked.

| value | authoritative source | dependent AC | status |
|-------|---------------------|--------------|--------|
| Git-for-Windows `bash.exe` location — `git --exec-path` → git-core dir; `bash.exe` at install `bin/bash.exe`; and whether `shutil.which("bash")` on `windows-latest` resolves Git-Bash vs the `C:\Windows\System32\bash.exe` **WSL launcher** | GitHub `windows-latest` runner image PATH + Git-for-Windows install layout | T05 AC 2, AC 5 | ☐ unchecked |
| `windows-latest` interpreter names — `python3` absent; `python` present via `actions/setup-python`; `py` launcher present | `actions/setup-python` behavior + `windows-latest` image manifest | T06 AC 3; T08 AC 1–2 | ☐ unchecked |
| `sys.executable` / interpreter token survives a Git-Bash `bash -c` round-trip (backslash-path / MSYS mangling) | Git-Bash (MSYS2) path handling on the real runner | T06 AC 3; T08 AC 1 | ☐ unchecked |
| Claude Code Windows install shim name (`claude.cmd` vs `claude.exe`); `PATHEXT` includes `.CMD` | Claude Code Windows installer / `PATHEXT` on the host | T07 AC 1–4 | ☐ unchecked |

**Notes on unlocked ACs (escalation trigger 2 of `WU-91`):**

- T05/T06/T08 contract values (`bash` resolution, interpreter names, bash
  round-trip) are proven by **T08's `windows-latest` CI job** on the PR. Until
  that job is green, treat those ACs as unlocked — the mocked Linux unit tests
  prove *branch selection*, not real-runner behavior.
- T07's `claude.cmd` resolution is **not** exercised by CI (CI dispatches no
  agent). It is provable only by a **post-merge manual check on a real Windows
  box** — enumerate it in the gate-2 close's "What the loop did NOT verify". T07
  is implemented against `shutil.which` (name-agnostic, `PATHEXT`-honoring) so no
  shim filename is hardcoded.

## Arming checklist for the human

1. Review each drafted WU body (T05–T08); accept / revise / reject.
2. Flip accepted WUs `status: draft → pending` and confirm the PLAN.md graph
   ordering (T05–T08 before `G2-CLOSE`; `G2-CLOSE.depends_on` = the four).
3. Arm `G2-CLOSE` (`draft → pending`) when ready.
4. Mark gate 1 `passed`; resume the driver.
5. The four Cross-repo contract rows stay ☐ until T08's CI job (and, for T07, the
   post-merge manual check) confirms them — do not pre-check them here.
6. **Reconcile the feature budget.** Drafting gate 2 raised the sum of per-WU
   `planned_cost_usd` to ~$10.65 vs the feature-level `PLAN.md planned_cost_usd:
   6.90` (a `lint_plan.py` WARN, advisory). Gate 2's drafted WUs (T05–T08 +
   G2-CLOSE = $4.95) sit within `GATE-02.md`'s `cost_budget_usd: 5.0`. Left for
   the human to decide at arming — plan-next did not unilaterally raise the
   feature budget.
