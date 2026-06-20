---
id: FEAT-2026-0026/T08
type: implementation
effort: medium
status: done
planned_cost_usd: 1.50
produces:
  - init.sh
  - tests/init_sh_shim.bats
  - .specfuse/verification.yml
attempts: 1
duration_seconds: 330.962
cost_usd: 0.853756
input_tokens: 865
output_tokens: 14615
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `init.sh` thin shim — delegate to the pip CLI, keep the deprecation banner

**Objective.** Shrink `init.sh` from a ~600-line scaffolder to a **thin shim** that
delegates to the pip CLI (`specfuse init` / `specfuse upgrade`), preserving the existing
deprecation banner. The bash copy/overlay logic is now redundant with T04–T07's in-process
scaffold; this WU makes `init.sh` a forwarding wrapper so the two paths can't drift. Actual
**deletion** of `init.sh` is the later v1.1 cut (PLAN decision) and is **out of scope**.

**Context.** This is `FEAT-2026-0026/T08`, gate 3 (terminal), depends on T04 + T05 + T07
(the in-process `init` / `upgrade` the shim forwards to). Today `init.sh` does the full
scaffold itself: INIT mode (`init.sh:391-415`) and `--upgrade` mode (`init.sh:438-490`),
plus the `deprecation_banner()` (`init.sh:~370`). The forward path is the pip CLI: the
banner already points at `pip install specfuse` → `specfuse init` / `specfuse upgrade`. This
WU keeps the banner and the CLI surface (`init.sh [--upgrade] [--dry-run] <target>`) but
replaces the body with a delegation to `specfuse`. `init.sh` is an **executable operator
script** → `/authoring-work-units` §11 applies (shellcheck + `bash -n` + bats happy-path).
Ground in `.specfuse/rules/result-contract.md` and `.specfuse/rules/never-touch.md`.

**Red-test (§12 via §11):** `tests/init_sh_shim.bats` happy-path asserts the shim invokes
the stubbed `specfuse` CLI with the right subcommand + forwards `<target>`. It **fails on
HEAD** (current `init.sh` runs its own `cp`/overlay loop and never execs `specfuse`) and
passes after this WU.

**Acceptance criteria.**

1. **Red test first.** `tests/init_sh_shim.bats` exists and **fails on HEAD** before this
   WU's edits (current `init.sh` does not invoke a `specfuse` CLI — the stub asserting the
   delegated call is never hit).
2. `init.sh` is rewritten as a shim that:
   - prints the existing deprecation banner (verbatim content preserved — same forward-path
     guidance: `pip install specfuse`, `specfuse init` / `specfuse upgrade`, the plugin
     marketplace lines),
   - parses the same surface it does today (`--upgrade`, `--dry-run`, a `<target>`
     positional) and **delegates**: no flag → `specfuse init <target>`; `--upgrade` →
     `specfuse upgrade <target>`; `--dry-run` forwarded as the CLI's equivalent flag,
   - `exec`s (or runs and propagates the exit code of) the `specfuse` CLI — the shim's exit
     status is the CLI's,
   - errors with a clear message + non-zero exit if `specfuse` is not on `PATH` (point the
     operator at `pip install specfuse`).
3. **No scaffolding logic remains.** The bash copy/overlay/seed machinery is gone:
   `grep -c 'overlay_item\|VERSIONED_ITEMS\|deploy_scripts\|cp -[rR]' init.sh` returns `0`.
   The shim is materially smaller (a `wc -l init.sh` well under 100 lines).
4. **Operator-script gates (§11).** `bash -n init.sh` parses clean; `shellcheck init.sh`
   yields zero warnings (or every `# shellcheck disable=...` carries an inline reason);
   `tests/init_sh_shim.bats` has ≥ 1 happy-path test per mode (init, upgrade) with the
   `specfuse` CLI replaced by a PATH-shimmed stub asserting the call shape + exit code, and
   a `specfuse`-absent error-path test (AC2 last bullet).
5. **Gate wired.** `.specfuse/verification.yml`'s `code` set gains an entry running the new
   bats file (e.g. `init-sh-shim-bats: bats tests/init_sh_shim.bats`), alongside the
   existing `sync-scaffold-bats` / `leak-scan-hook` entries — so the driver actually runs
   it. Do not weaken or remove any existing gate.

**Do not touch.** `specfuse/loop/scaffold.py` and the driver modules (T04/T05/T07 own the
in-process logic the shim calls); `specfuse/loop/data/`; this repo's `.specfuse/` content
other than the single `verification.yml` gate-entry addition (AC5); other gates in
`verification.yml`; secrets; `.git/`. The driver owns all git — edit files only.

**Verification.** `code` gates incl. the new `init-sh-shim-bats` entry; `bash -n init.sh`
+ `shellcheck init.sh` (AC4); the no-scaffolding-logic grep (AC3); the bats happy-path +
absent-CLI tests (AC4). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** **(a)** If the cross-repo `specfuse` umbrella CLI does **not** yet
expose `init` / `upgrade` subcommands (it lives in a separate distribution; this feature
delivers the `specfuse.loop.scaffold` API it calls), the shim cannot be end-to-end verified
in this repo — keep the bats test against a **stub** `specfuse` (asserting the call shape,
not a real run) and record the real-CLI leg under "what the loop did NOT verify" for the
close; do **not** invent CLI flags that aren't pinned. **(b)** If `--dry-run`'s CLI
equivalent is not defined by the `specfuse` CLI contract, emit `status: blocked` naming the
unmapped flag rather than dropping the flag silently (a silently-ignored `--dry-run` would
scaffold for real when an operator expected a preview).
