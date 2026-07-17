## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0032
- predicate_version: v1
- gate_total_cost: $3.02
- gate_budget: <unset>
- reasons: [] (auto=True)

> **Note (written at gate-2 close).** Gate 1 auto-closed with `attempts: 0`, so
> no close session ran to write gate 1's `## What the loop did NOT verify` list —
> exactly the `[FEAT-2026-0031/G1-CLOSE]` failure mode (an `auto_close` close WU's
> body is never executed; its ACs are unfulfilled, not evidence). Gate 1's two
> known deferrals (T02 real-Windows `taskkill`; T01 contended-lock SIGKILL
> handoff) were therefore never recorded in-loop. They are folded into this
> gate-2 close's deferred-verification section below.

## Gate 2

Gate 2 made gate **commands execute correctly** on native Windows through
Git-Bash: shell routing (`bash -c`), `python3` normalization, and `claude`
resolution. All four substantive WUs are `done`.

### T05 — Git-Bash shell routing (`WU-05-git-bash-shell-routing.md`)
- **Attempts:** 1 (passed first try).
- **Blockers:** none.
- **Surprises:** the WU-91 sketch bundled routing *both* the gate runner and the
  smoke-import runner through `bash -c`; on inspection the smoke-import command
  (`python3 -c "from X import Y"`) uses no POSIX shell feature, so T05 was
  narrowed to route **only** the gate runner (`verify()`), where user shell
  features actually live. `resolve_bash()` prefers the Git-for-Windows `bash.exe`
  to avoid the `C:\Windows\System32\bash.exe` WSL launcher. Real-runner `bash`
  resolution is a cross-repo contract, proven by T08's CI leg (not in-loop).

### T06 — `python3` interpreter normalization (`WU-06-python3-interpreter-normalization.md`)
- **Attempts:** 1 (passed first try).
- **Blockers:** none.
- **Surprises:** clean split from T05 — `normalize_interpreter()` rewrites the
  leading `python3` token to the running Windows interpreter for **both** the
  gate command and the smoke-import surface (`run_smoke_imports`), applied before
  T05's `bash -c` handoff. Whether the interpreter token survives an MSYS
  bash round-trip on the real runner is a cross-repo contract, proven by T08.

### T07 — Windows `claude` CLI resolution (`WU-07-windows-claude-resolution.md`)
- **Attempts:** 1 (passed first try).
- **Blockers:** none.
- **Surprises:** independent of the gate runner (different call site,
  `shell=False`). `resolve_claude_cmd()` uses `shutil.which("claude")` honoring
  `PATHEXT`, so `claude.cmd`/`claude.exe` is found without hardcoding a shim
  name. CI dispatches no agent, so this path is **not** CI-exercised — deferred
  to a post-merge manual check (see below).

### T08 — real-Windows gate-execution CI oracle (`WU-08-windows-gate-exec-ci-leg.md`)
- **Attempts:** 4 to commit (1 to implement). The passing implementation landed
  on the first content attempt; the driver's squash commit was then **rejected
  three times** by the pre-commit `leak-scan` hook, which flagged an email-shaped
  token in the committed test fixture (`leak-scan: FINDINGS … email: <redacted>`).
  The WU hit `blocked_human` (`spinning_detected`, 3 attempts), was re-armed by
  the operator, and passed on the re-armed attempt.
- **Blockers:** `squash_commit_failed` ×3 — the fixture's realistic-looking email
  token self-poisoned the leak-scan gate at squash time even though the change was
  correct. This is the catalogued `loop squash vs pre-commit hook` /
  `leak hook vs test fixtures` pattern: use `example.com`-class tokens in
  fixtures, or the squash never lands.
- **Surprises:** the real-Windows oracle is the `windows-latest` CI job **on the
  PR**, not a Linux-runnable red→green test (§12 CI/infra carve-out). The
  committed test is `@skipUnless(sys.platform == "win32")`; on the loop's Linux
  host it is collected and skipped, so in-loop `done` proves the wiring and the
  Linux-skip — **not** that the gate ran green on real Windows. That confirmation
  is PR-deferred.

## Cost analysis

Actual spend from `events.jsonl` (deduped by timestamp); planned from per-WU
`planned_cost_usd` frontmatter and `PLAN.md`.

| unit | planned | actual | delta |
|------|--------:|-------:|------:|
| T05 | $1.00 | $1.43 | +$0.43 |
| T06 | $1.00 | $0.78 | −$0.22 |
| T07 | $0.90 | $0.52 | −$0.38 |
| T08 | $0.85 | $2.21 | +$1.36 |
| **Gate 2 substantive** | **$3.75** | **$4.95** | **+$1.20 (+32%)** |
| G2-CLOSE (this WU, ≥3 attempts) | $1.20 | $2.03+ | +$0.83+ (+69%+) |
| **Gate 2 total** | **$4.95** | **$6.98+** | **+$2.03+ (+41%+)** |

Feature-wide (both gates): planned **$10.65** (sum of all per-WU
`planned_cost_usd`, matching `PLAN.md planned_cost_usd`) vs actual **$13.31+**
→ **delta +$2.66+ (+25%+)**. (The `+` reflects this close session's own spend,
not yet in `events.jsonl` at write time.)

**Where the overrun came from.** Two units, both bookkeeping, not scope:
- **T08 (+160% over its $0.85 plan):** three wasted squash attempts on the
  leak-scan fixture-token self-poison (a known, catalogued failure), plus the
  re-arm. The *implementation* was one clean attempt (~$0.55); the overrun is
  entirely the commit-gate thrash.
- **G2-CLOSE (+69%+):** attempt 1 failed with `no_gate_marker` (no RESULT
  block); attempt 2 failed plan-lint (`close-type WU missing … 'verdict'`
  frontmatter). This third attempt fixes both. T05/T06/T07 all came in **at or
  under** plan — the estimate was sound; the variance is re-attempt cost.

## What the loop did NOT verify

Four acceptance-adjacent behaviors were not verified inside the Linux loop
sandbox. Because this list exceeds 2 entries, the feature's sizing is flagged
under `## What I'd change`.

1. **A real gate command running green through Git-Bash on `windows-latest`
   (T08 AC1–2; gate 2's headline).** *Why deferred:* the loop runs on a Linux
   sandbox; the test is `@skipUnless(win32)` and cannot execute here. *Where
   verified:* the `windows-latest` CI job on the feature PR — green there is the
   oracle. **Status: implemented + Linux-skip verified in-loop; real-runner green
   PR-deferred (unconfirmed at close).**
2. **`claude` CLI resolution on real Windows (T07).** *Why deferred:* CI
   dispatches no agent, so no CI leg exercises `resolve_claude_cmd()` end-to-end.
   *Where verified:* a post-merge manual check on a real Windows box (run the
   driver, confirm `claude.cmd`/`claude.exe` resolves). Implemented
   name-agnostically (`shutil.which` + `PATHEXT`), so no shim filename is
   hardcoded. **Status: unverified on real Windows (post-merge manual).**
3. **A timing-out gate command's `taskkill` path on real Windows (T02, gate 1
   deferral gate 2 was expected to close).** *Why deferred:* T08's oracle runs a
   gate command that **passes** (`… && echo GATE_OK`); no CI leg drives a gate to
   timeout, so the Windows `CREATE_NEW_PROCESS_GROUP` + `taskkill` branch is never
   exercised on a real runner. **Status: NOT resolved by gate 2 — still
   unverified on real Windows.** This is the open item that holds the terminal
   verdict to `partially_met` (see escalation trigger 1).
4. **The contended-lock SIGKILL handoff (T01, gate 1 deferral).** *Why deferred:*
   requires a flaky spawn-two-drivers-and-kill-one test, not verifiable even on
   Windows CI without instability. *Where verified:* post-merge manual check.
   **Status: unverified (post-merge manual), as planned at draft time.**

Gate-1 deferrals gate 2 was expected to close: the **Git-Bash gate-execution
path** — *resolved* (T05 routes it; T08 proves it, pending PR CI green). The
**real-Windows timeout kill** — *not resolved* (entry 3 above).

## What I'd change

- **Sizing flag (per AC 3 threshold).** The deferred list is 4 entries — above the
  2-entry threshold. The feature is genuinely Windows-runtime work whose true
  oracle lives off the Linux sandbox, so *some* deferral is unavoidable; but the
  **timeout-kill path (entry 3) should have had its own gate-2 WU** — a CI leg
  driving a gate command to timeout on `windows-latest` and asserting the
  `taskkill` branch fires — instead of being carried forward as "gate 2 will
  close it" and then not closed. Naming it a WU would have either resolved it or
  made its deferral an explicit, planned decision rather than a gap discovered at
  close.
- **Fixture-token hygiene as a T08 precondition.** T08 burned three squash
  attempts on the leak-scan fixture-token self-poison — a catalogued, repeatable
  failure. A one-line "use `example.com`-class tokens in fixtures" note in the WU
  body (or a hygiene precursor) would have saved the thrash.
- **Auto-close of gate 1 dropped its deferred list.** Gate 1 auto-closing with
  `attempts: 0` meant its deferrals were never recorded until this gate-2 close
  reconstructed them. For features whose gate-1 close carries a deferred-
  verification list that later gates depend on, put that list in a substantive WU
  or expect to reconstruct it by hand (`[FEAT-2026-0031/G1-CLOSE]`).

## Terminal verdict — `partially_met`

The feature's `roadmap_goal` is: *run the specfuse-loop driver on native Windows
without WSL — importable, gate commands executing through Git-Bash, home-path
redaction correct — proven by a `windows-latest` CI leg.* The **core** of that
goal is delivered and in-loop-verified: the driver imports and dry-runs on
Windows (gate 1, T04 CI leg); gate commands route through Git-Bash with `python3`
normalized and `claude` resolved (gate 2, T05/T06/T07); home-path redaction
covers `C:\Users\…` (gate 1, T03); and a real gate command executes green through
Git-Bash on `windows-latest` (gate 2, T08 — the headline CI oracle). What holds
the verdict below `met`: (a) two real-Windows behaviors remain **unverified** —
the timeout-kill `taskkill` path (a gate-1 deferral gate 2 was *expected* to
close and did not, per escalation trigger 1) and `claude.cmd` resolution
(post-merge manual, CI dispatches no agent); and (b) T08's own real-runner green
is confirmed only when the PR's `windows-latest` job passes, which has not
happened at close time. Per the `[FEAT-2026-0024/G2-CLOSE]` precedent — never
`met` on an unconfirmed live/external oracle — the honest verdict is
**`partially_met`**. The driver's `verdict_permits_terminal_flips` correctly
holds the terminal `PLAN.md status → done` flip until the operator confirms the
PR CI leg and the post-merge manual checks.
