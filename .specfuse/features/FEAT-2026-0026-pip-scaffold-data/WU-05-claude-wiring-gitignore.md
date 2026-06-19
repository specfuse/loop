---
id: FEAT-2026-0026/T05
type: implementation
effort: high
status: pending
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
   - `.claude/settings.json` with the **pip-command** Bash allowlist
     (`Bash(specfuse-loop:*)`, `Bash(specfuse-lint:*)`) — NOT init.sh's legacy
     `.specfuse/scripts/*.py` paths; a 0026-scaffolded repo is pip-native with no
     vendored scripts (OQ3 resolved at arm time);
   - `.claude/settings.json` plugin config with this **authoritative shape** (OQ2
     resolved — verified against Claude Code docs this session, do not invent):
     `{"extraKnownMarketplaces": {"specfuse": {"source": {"source": "github", "repo": "specfuse/specfuse"}}}, "enabledPlugins": {"specfuse@specfuse": true}}`.
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
7. **Orchestrator (OQ6 resolved).** `specfuse/loop/scaffold.py` gains
   `init(target, *, ci_check=None)` that calls `init_specfuse(target, ci_check=ci_check)`
   then `wire_claude(target)` — one entry point so callers (tests, the cross-repo
   `specfuse` CLI) don't duplicate the sequence. A test covers the combined flow.

**Do not touch.** This repo's own `.claude/`, `.gitignore`, and `.specfuse/` (tests write
to `tmp_path` only — never the repo root); `specfuse/loop/data/` content; the driver
modules; T04's `init_specfuse` filesystem contract beyond calling it; secrets; `.git/`.

**Verification.** `code` gates (tests incl. the new file, coverage ≥ 90, ruff, bandit);
the red→green proof (AC1, AC6); the idempotency/merge-safe test (AC3); the
JSON-validity + plugin-identifier test (AC4); the no-symlink assertion (AC5). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** The plugin-config schema (AC2) and the allowlist target (pip
commands, AC2) are resolved at arm time — use them as given; do not re-invent or
re-litigate. If, while implementing, the resolved plugin-config shape is rejected by
`claude plugin`/Claude Code as malformed (i.e. the pinned schema is wrong despite the
doc check), emit `status: blocked` with the exact error rather than guessing an
alternative shape — a wrong shape silently breaks skill discovery in the scaffolded repo.
