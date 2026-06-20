---
id: FEAT-2026-0027/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
effort: high
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - specfuse/loop/loop.py
  - tests/test_autosync_plugin.py
produces_driver_helper:
  - refresh_claude_plugin_config
duration_seconds: 627.923
cost_usd: 1.483218
input_tokens: 1585
output_tokens: 29149
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Auto-sync refreshes the `.claude` plugin config + warns on drift

**Objective.** Make `auto_sync` (loop.py) keep the Claude plugin config current on
**every** run — including the steady-state equal-version branch where it currently
no-ops — and correct a *drifted* `specfuse` marketplace value (today's wiring only
adds entries when absent, never updates them), warning the operator when it had to.

**Context.** This is `FEAT-2026-0027/T04`, the single substantive WU of gate 2.
Gate 1 shipped the auto-sync engine (`auto_sync` in `specfuse/loop/loop.py:3477`).
FEAT-2026-0026's `wire_claude` / `_write_settings_json` (`specfuse/loop/scaffold.py:210`)
already write `.claude/settings.json`'s `extraKnownMarketplaces["specfuse"]` +
`enabledPlugins["specfuse@specfuse"]`, and `init` / `upgrade_specfuse` call it — so
auto-sync's **create** and **older-overlay** branches already refresh the plugin
config indirectly. Two gaps remain, and they are this WU's whole scope:

1. **Steady-state runs never refresh it.** `auto_sync`'s equal-version branch
   (`loop.py:3544`) returns with no writes, so a plugin entry a user/Claude-Code
   removed, or a stale marketplace value, is never re-asserted on a normal run.
2. **`_write_settings_json` is additive-only** (`scaffold.py:228-234`): it sets the
   marketplace value / plugin flag *only when the key is absent*. If the installed
   driver's `_MARKETPLACE_VALUE` (`scaffold.py:175`) changes between versions, the
   project keeps the stale value — silent driver/plugin drift.

The cross-process drift (a pip-installed driver vs the plugin Claude Code installed
from the marketplace) is **not** readable from the repo and is **out of scope** here
— it is gate 3's `doctor` diagnosis. This WU covers only the in-repo,
mechanically-checkable drift: the project's `.claude/settings.json` `specfuse`
entries vs what the installed driver writes. See `GATE-02-REVIEW.md` for the
boundary and open questions. Ground in `.specfuse/rules/result-contract.md` and
`.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_autosync_plugin.py::TestAutosyncPlugin::test_equal_version_refreshes_plugin_config`
and `::test_drifted_marketplace_value_corrected` fail on HEAD (equal-branch no-ops;
`_write_settings_json` never updates an existing value) and pass after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_autosync_plugin.py::TestAutosyncPlugin::test_equal_version_refreshes_plugin_config`
   exists and fails on HEAD before this WU's edits
   (`python3 -m unittest tests.test_autosync_plugin.TestAutosyncPlugin.test_equal_version_refreshes_plugin_config`
   exits non-zero, or the file does not yet exist — both count as red).
2. **`refresh_claude_plugin_config(target) -> list[str]`** added to `scaffold.py`:
   parse-merge-rewrite `.claude/settings.json` so that, idempotently, (a) a missing
   or removed `enabledPlugins["specfuse@specfuse"]` is restored to `true`; (b) a
   missing **or value-drifted** `extraKnownMarketplaces["specfuse"]` is set to the
   installed `_MARKETPLACE_VALUE`; (c) every other settings key (permissions, the
   user's own marketplaces/plugins) is preserved untouched. Returns the sorted list
   of changed entry names (empty list ⇒ already current). `wire_claude` reuses it so
   the additive-only value-drift gap is closed on the init/upgrade paths too.
3. **`auto_sync` refreshes on every applied branch.** On the **create**, **equal**,
   and **older-overlaid** branches `auto_sync` calls `refresh_claude_plugin_config`
   so a steady-state (equal) run re-asserts the plugin config. The **newer-than-installed
   refuse** branch and the **`--no-autosync` / `autosync: false`** opt-outs still skip
   it entirely (never-downgrade + opt-out are absolute).
4. **Drift warning.** When `refresh_claude_plugin_config` returns a non-empty change
   list on a non-create run, `auto_sync` prints a `WARNING:` to `stderr` naming the
   changed entries (driver/plugin config drift was corrected). On a clean run it
   prints nothing (no diff noise).
5. **`--dry-run` stays read-only.** On `--dry-run`, `auto_sync` computes and prints
   the would-be plugin-config changes but writes nothing to `.claude/settings.json`.
6. The red tests (AC1) pass; new unit tests cover each branch (restore-removed-plugin,
   correct-drifted-value, no-op-when-current, dry-run-writes-nothing, opt-outs-skip);
   `code` gates green (coverage ≥ 90); `auto_sync` still never runs `git`.

**Do not touch.** Gate 1's WUs (T01–T03) and their tests; the manifest /
`detect_modified` logic (T01); the version-decision tree in `auto_sync` beyond adding
the plugin-refresh calls + the drift warning; `wire_claude`'s `.gitignore` /
`CLAUDE.md` writers (this WU touches only the settings.json plugin-config path);
gate-3 `doctor` scope; secrets; `.git/`. The driver owns all git — edit files only.

**Verification.** `code` gates (`python3 -m unittest discover -s tests -v` incl.
`tests/test_autosync_plugin.py`; `ruff check`); the red→green proof (AC1, AC6); a
no-op-when-current assertion (AC4) and a writes-nothing-on-dry-run assertion (AC5).
Symbol checks:
`python3 -c "from specfuse.loop.scaffold import refresh_claude_plugin_config"` and
`python3 -c "from specfuse.loop.loop import auto_sync"`. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If updating an existing `extraKnownMarketplaces["specfuse"]`
value would clobber a deliberate user customization (i.e. the `specfuse` key is meant
to be user-owned, not driver-owned provenance), emit `status: blocked` rather than
guessing — `GATE-02-REVIEW.md` Open question 1 flags this as the one decision that
changes the contract. If gate 3's `doctor` scope appears to already own the in-repo
drift warning (making AC4 redundant), surface it rather than shipping a duplicate
warning path.
