---
id: FEAT-2026-0026/T05
type: implementation
effort: high
status: draft
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_wiring.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `.gitignore` + `.claude` wiring — merge-safe, from package resources

**Objective.** Add the `.claude` and `.gitignore` wiring that makes a scaffolded repo
immediately working: write the runtime-artifact `.gitignore` lines (from the packaged
`gitignore.snippet`), the CLAUDE.md `@rules` import block, the loop-script settings
allowlist, and the Claude Code plugin config (`extraKnownMarketplaces` +
`enabledPlugins`) — all **merge-safe** (create-if-missing, never clobber a user file).

**Context.** This is `FEAT-2026-0026/T05`, gate 2, depends on T04 (`init_specfuse` writes
the `.specfuse/` tree first). This is the "parity with `init.sh` INIT minus the symlink
trick" half: `init.sh` bridged skills with relative symlinks (`init.sh:270-302`); the
forward path replaces that with the Claude Code **plugin** (`/plugin marketplace add
specfuse/specfuse`; plugin `specfuse@specfuse`, per `init.sh:380-381` + the deprecation
banner), so this WU writes the plugin config **instead of** symlinks. The CLAUDE.md
`@rules` block (`init.sh:307-311`), the settings allowlist (`init.sh:341-349`), and the
runtime-artifact `.gitignore` lines (`init.sh:589-593`, also shipped as the seed's
`gitignore.snippet`) carry over. Add these as functions in `specfuse.loop.scaffold`,
callable independently and from T04's flow. Pure stdlib (`json` for merge-safe settings).
Ground in `.specfuse/rules/result-contract.md`.

**Red-test (§12):** `tests/test_scaffold_wiring.py::test_wiring_is_merge_safe` fails on
HEAD (functions absent) and passes after this WU; paired with
`test_wiring_writes_all_surfaces`.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_wiring.py::test_wiring_is_merge_safe` exists
   and fails on HEAD before this WU's edits (import error / missing symbol).
2. `specfuse/loop/scaffold.py` gains a `wire_claude(target)` (+ `.gitignore` writer) that,
   against a target repo, writes:
   - `.gitignore` runtime-artifact lines from the packaged `gitignore.snippet`
     (`.specfuse/.loop.lock`, `.specfuse/.scratch-*`, `.specfuse/scripts/__pycache__/`),
     appended if the file exists, created if not;
   - `.claude/CLAUDE.md` containing the `@.specfuse/rules/...` import block for all four
     binding rules;
   - `.claude/settings.json` with the loop-script Bash allowlist;
   - `.claude/settings.json` (or the documented plugin-config location) with
     `extraKnownMarketplaces` for the `specfuse/specfuse` marketplace and `enabledPlugins`
     enabling `specfuse@specfuse`.
3. **Merge-safe.** Re-running against a target that already has each surface does **not**
   duplicate lines or clobber user content: existing `.gitignore` lines are not
   re-appended; an existing `CLAUDE.md` that already imports the rules is left alone (or a
   missing block is appended without dropping user text); `settings.json` is parsed as
   JSON and merged (allow-list entries and plugin keys added, existing keys preserved) —
   never overwritten wholesale. Proven by an idempotency test (write twice → second write
   is a no-op / stable).
4. **Plugin config correctness.** A test asserts the written `settings.json` parses as
   valid JSON and contains the marketplace + enabled-plugin entries with the exact
   marketplace/plugin identifiers (`specfuse/specfuse`, `specfuse@specfuse`).
5. **No symlinks.** The wiring writes **no** symlinks under `.claude/skills/` (the plugin
   replaces the bridge); a test confirms no symlink is created.
6. The red test (AC1) and `test_wiring_writes_all_surfaces` pass after the edits; `code`
   gates stay green (coverage ≥ 90 on `specfuse/`).

**Do not touch.** This repo's own `.claude/`, `.gitignore`, and `.specfuse/` (tests write
to `tmp_path` only — never the repo root); `specfuse/loop/data/` content; the driver
modules; T04's `init_specfuse` filesystem contract beyond calling it; secrets; `.git/`.

**Verification.** `code` gates (tests incl. the new file, coverage ≥ 90, ruff, bandit);
the red→green proof (AC1, AC6); the idempotency/merge-safe test (AC3); the
JSON-validity + plugin-identifier test (AC4); the no-symlink assertion (AC5). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the canonical plugin-config schema (which JSON file,
`extraKnownMarketplaces` vs `enabledPlugins` exact shapes) cannot be determined from the
seed or `init.sh` and would have to be invented, emit `status: blocked` and name the
schema gap — a wrong plugin-config shape silently breaks skill discovery in the
scaffolded repo. If the settings allowlist should reference the pip commands
(`specfuse-loop`/`specfuse-lint`) instead of `init.sh`'s legacy script paths, surface it
(it is an open question logged in GATE-02-REVIEW.md) rather than deciding unilaterally.
