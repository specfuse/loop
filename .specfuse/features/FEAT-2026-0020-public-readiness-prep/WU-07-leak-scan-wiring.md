---
id: FEAT-2026-0020/T16
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Wire the leak-scan detector into its three callers — pre-commit hook + CI gate

**Objective.** Make the `leak_scan` detector (WU-06) enforce on commits and in CI: ship a
repo-tracked `pre-commit` hook that runs `leak_scan --staged` and blocks on a hit, and add
a `leak-scan` entry to `.specfuse/verification.yml`'s `code` set (mirrored into
`scripts/smoke-test.sh` and `.github/workflows/ci.yml` per the three-surface sync rule).

**Context.** Part of FEAT-2026-0020 gate 2; depends on WU-06 (`FEAT-2026-0020/T15`), which
ships `.specfuse/scripts/leak_scan.py` with `scan_staged()`. This WU is the "three callers"
half of `GATE-02.md`'s Required deliverable: (b) CI gate and (a) pre-commit hook. The
history-audit caller (c) already exists as `scrub-history.sh --verify-only`. Correlation ID
`FEAT-2026-0020/T16`.

Constraints carried from `GATE-02.md` and the learnings:
- The hook must be **read-only, fast, sandbox-safe** — no heavy/destructive work (memory
  `[prepush_hook_sandbox_corruption]`: a hook running under sandbox-off can wreck the repo).
  The hook cannot live in `.git/hooks/` (that is `never-touch.md` §3); ship it in-repo
  (e.g. `.specfuse/hooks/pre-commit`) and document install via `git config core.hooksPath`.
- `--no-verify` escape hatch documented for emergencies.
- CI is the real backstop because hooks are not enforced and `--no-verify` bypasses them.
- The hook is an **executable operator artifact** → `/authoring-work-units` §11 applies:
  `shellcheck` + `bash -n` + a bats happy-path test with `leak_scan`/`git` stubbed.

Binding rules in `.specfuse/rules/` apply. Adding a gate to `verification.yml` is permitted
(it is NOT on the never-touch list); **weakening or removing a gate to pass is forbidden**.

**Acceptance criteria.**

1. A repo-tracked pre-commit hook (e.g. `.specfuse/hooks/pre-commit`) exists, runs
   `leak_scan --staged` (or `python3 .specfuse/scripts/leak_scan.py --staged`), exits
   non-zero on a hit and zero on a clean staged set, and is read-only + sandbox-safe (no
   filter-repo, no network, no writes).
2. The hook's install path is documented (e.g. `git config core.hooksPath .specfuse/hooks`)
   and the `--no-verify` emergency bypass is documented in the hook header or
   `FLIP-CHECKLIST`-adjacent docs (WU-08 references it).
3. `.specfuse/verification.yml` `code` set gains a `leak-scan` entry whose command runs the
   detector over the repo (CI-surface mode), failing the gate on a hit.
4. `scripts/smoke-test.sh` and `.github/workflows/ci.yml` are updated to run the same
   `leak-scan` command — the three surfaces stay in sync (the file's own AUTHORING RULE).
5. **§11 operator-script gates** on the hook: `bash -n .specfuse/hooks/pre-commit` parses
   clean; `shellcheck .specfuse/hooks/pre-commit` is clean (or every disable carries a
   justification); at least one bats happy-path test exists with `leak_scan`/`git` stubbed,
   asserting the hook's exit code on clean vs planted-leak staged input.
6. `code` gates (including the new `leak-scan` gate itself) pass on the current clean tree.

**Do not touch.**

- `.specfuse/scripts/leak_scan.py` and `tests/test_leak_scan.py` — WU-06 owns the detector;
  this WU consumes it. (If the detector's interface is wrong, escalate — do not patch it
  here.)
- `.git/hooks/*` — `never-touch.md` §3; ship the hook in-repo and install via config.
- Other gate-2 WU outputs (README/CONTRIBUTING/SECURITY/templates/dependabot/checklist).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `bash -n .specfuse/hooks/pre-commit && shellcheck .specfuse/hooks/pre-commit`.
- bats happy-path: `bats tests/leak_scan_hook.bats` (or the repo's bats location) — green.
- The new `leak-scan` gate runs and passes on HEAD: execute the exact command added to
  `.specfuse/verification.yml`'s `code` set and confirm exit 0 on the clean tree.
- Sync check: the `leak-scan` command string appears in all three of
  `.specfuse/verification.yml`, `scripts/smoke-test.sh`, `.github/workflows/ci.yml`.
- `code` gates per `.specfuse/verification.yml`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. **Detector interface mismatch.** If `leak_scan.py` does not expose a `--staged` /
   CI-surface CLI the hook and gate can call, emit `status: blocked` — the fix belongs in
   WU-06, not in a widened scope here.
2. **No bats gate exists.** If `.specfuse/verification.yml` has no gate that runs bats and
   adding the bats test would have nowhere to run, emit `status: blocked` and propose a
   hygiene precursor to add the bats runner (`/authoring-work-units` §11).
3. **Hook would need non-trivial/destructive work to pass.** If making the hook reliable
   tempts you toward heavy or write-side work in the hook, STOP — emit `status: blocked`
   (memory `[prepush_hook_sandbox_corruption]`: the hook must stay read-only and fast).
