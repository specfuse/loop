---
id: FEAT-2026-0027/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.50
effort: high
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - tests/test_doctor.py
produces_driver_helper:
  - doctor
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse doctor` — read-only self-provisioning diagnosis

**Objective.** Add `scaffold.doctor(...)`: a **read-only** diagnosis of the project's
self-provisioning state — installed driver vs project scaffold version, in-repo plugin
config vs what the driver writes, and the **cross-process** Claude-Code-installed plugin
version the in-repo drift warning (T04) can't see — returning structured findings + a
recommended action. It writes nothing.

**Context.** This is `FEAT-2026-0027/T05`, first substantive WU of gate 3 (terminal:
doctor + first-run + migrate). Gate 1 shipped the auto-sync engine; gate 2 (`T04`) made
auto-sync refresh `.claude/settings.json`'s plugin config and **correct + warn on
in-repo drift** (`scaffold.refresh_claude_plugin_config`, `scaffold.py:233`). `doctor` is
the read-only counterpart: it *diagnoses*, never mutates, and surfaces the one drift T04
structurally cannot — a pip-installed `specfuse-loop` vs the plugin Claude Code actually
installed from the marketplace.

Grounding surfaces (verified at draft time):
- Installed driver version: `loop.py:62` `DRIVER_VERSION`. Installed scaffold version:
  `scaffold.scaffold_version()` (`scaffold.py:35`). Project scaffold version:
  `.specfuse/VERSION` (read in `auto_sync`, `loop.py:3525`). Version parse/compare:
  `scaffold._parse_version` (`scaffold.py:295`).
- In-repo plugin config: `.claude/settings.json` keys `extraKnownMarketplaces["specfuse"]`
  / `enabledPlugins["specfuse@specfuse"]` vs `scaffold._MARKETPLACE_VALUE` /
  `_PLUGIN_KEY` (`scaffold.py:174-181`). `refresh_claude_plugin_config` already computes
  this delta — `doctor` reuses it in a **dry-run** (read-only) call.
- Cross-process plugin version: `~/.claude/plugins/installed_plugins.json`, shape
  `plugins["specfuse@specfuse"][].version`. **Confirmed present + readable on this host
  but NOT repo-readable**, absent under CI/sandbox, and for a marketplace plugin the
  `version` is a **git commit SHA, not a semver** (e.g. `655b7d9c5431`) — so it cannot be
  ordered against `DRIVER_VERSION`. `doctor` reports it as an opaque identifier and
  degrades to `unknown` when the manifest is absent. See `GATE-03-REVIEW.md` "If you
  check only three things" #1 and Open question 1.

The cross-repo umbrella `specfuse` CLI (FEAT-2026-0026/0028, `specfuse/specfuse` repo)
owns the user-facing `specfuse doctor` subcommand; this repo ships the **API** it calls,
mirroring how `init` / `upgrade_specfuse` are scaffold-API functions wired from the
cross-repo CLI. **The subcommand name `doctor` and its flags are cross-repo contract
values — verify against `specfuse/specfuse`, do not invent a CLI surface here.** This WU's
loop-dispatchable scope is the API + tests only. Ground in
`.specfuse/rules/result-contract.md`, `never-touch.md`, `security-boundaries.md`.

**Red-test (§12):** `tests/test_doctor.py::TestDoctor::test_reports_scaffold_version_drift`
fails on HEAD (no `doctor` symbol) and passes after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_doctor.py::TestDoctor::test_reports_scaffold_version_drift`
   exists and fails on HEAD before this WU's edits
   (`python3 -m unittest tests.test_doctor.TestDoctor.test_reports_scaffold_version_drift`
   exits non-zero, or the file does not yet exist — both count as red).
2. **`doctor(target, *, installed_driver_version=DRIVER_VERSION-equivalent,
   plugins_manifest_path=None) -> dict`** added to `scaffold.py`. It is **read-only** —
   it MUST NOT write, create, or delete any file (no `init`, no `upgrade`, no
   `refresh_claude_plugin_config` non-dry-run call). It returns a structured report with
   at least: `scaffold_version` (project `.specfuse/VERSION` or `None` if absent),
   `installed_scaffold_version`, `scaffold_status` (one of `current` / `project_behind` /
   `project_ahead` / `no_scaffold`), `plugin_config_drift` (the sorted entry list a
   **dry-run** `refresh_claude_plugin_config` would change — empty ⇒ in-repo config
   current), `installed_plugin_version` (the `specfuse@specfuse` value from the manifest,
   or `None` when unreadable), and `recommended_action` (a human-readable string).
3. **Cross-process plugin read is best-effort + injectable.** `plugins_manifest_path`
   defaults to `~/.claude/plugins/installed_plugins.json`; when the file is absent or
   unparseable, `installed_plugin_version` is `None` and `recommended_action` notes the
   diagnosis is partial — `doctor` does not raise. The parameter exists so tests inject a
   fixture manifest rather than depending on the real home file.
4. **`recommended_action` maps the state.** `project_behind` → recommend a sync/upgrade;
   `project_ahead` → recommend upgrading the driver (never downgrade); non-empty
   `plugin_config_drift` → note a run will correct it; `installed_plugin_version` `None`
   → note the cross-process check was skipped. A fully-current repo recommends nothing
   actionable.
5. The red test (AC1) passes; new unit tests cover each `scaffold_status` branch, the
   drift-present vs drift-absent cases, and the manifest-absent degradation (AC3);
   `code` gates green (coverage ≥ 90); `doctor` performs zero writes (assert no
   filesystem mutation in the read-only test).

**Do not touch.** Gate 1 + gate 2 WUs (T01–T04) and their tests; `auto_sync`'s
decision tree (read its outputs, do not alter it); `refresh_claude_plugin_config`'s
mutating path (call it only with `dry_run=True`); the first-run prompt (T06) and
migration-prune (T07) scope; `.claude/settings.json` itself (doctor reads, never writes);
the cross-repo `specfuse` CLI; secrets; `.git/`. The driver owns all git — edit files
only. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gates (`python3 -m unittest discover -s tests -v` incl.
`tests/test_doctor.py`; `ruff check`; coverage ≥ 90). Symbol check:
`python3 -c "from specfuse.loop.scaffold import doctor"`. Read-only assertion: the
no-write test (AC5). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `installed_driver_version` cannot be obtained without
importing `loop.py` in a way that triggers `auto_sync` side-effects at import time, pass
it in as a parameter rather than reaching across the module boundary — do not introduce
an import cycle. If reconciling the SHA-valued `installed_plugin_version` against the
semver `DRIVER_VERSION` would require inventing a mapping (there is none), report the SHA
opaquely and emit `status: blocked` rather than fabricating a version comparison. If
`doctor` cannot diagnose plugin state without writing (e.g. the only available delta API
mutates), emit `status: blocked` — a read-only diagnosis that writes is a contract
violation. If a required symbol (`doctor`) is absent from the files you edited, emit
`status: blocked` — do not claim complete.
