---
gate: 2
status: passed
---

<\!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 — plugin-config + drift (skeleton)

Un-drafted. Gate 1's `plan-next` drafts this gate. Intended scope: auto-sync refreshes
the `.claude` plugin config (`extraKnownMarketplaces` + `enabledPlugins`) on sync; warn
on driver/plugin version drift.

## Definition of done

Gate 2 is done when `auto_sync` keeps the `.claude` plugin config current on every
applied run — not just at init/upgrade — and surfaces in-repo driver/plugin drift:

- **T04** — `auto_sync` calls a new `scaffold.refresh_claude_plugin_config` on the
  create / equal / older-overlaid branches, restoring a removed
  `enabledPlugins["specfuse@specfuse"]` and correcting a drifted
  `extraKnownMarketplaces["specfuse"]` value (closing `_write_settings_json`'s
  additive-only gap), preserving all other settings keys, and warning when it had to
  correct drift. `--dry-run` reports without writing; `--no-autosync` /
  `autosync: false` / never-downgrade still skip it.

**Scope note (escalation honored).** Gate 2 collapsed to a single substantive WU:
FEAT-2026-0026's `wire_claude` already writes the plugin config and `upgrade_specfuse`
refreshes `.claude`, so only the steady-state-refresh + value-drift gaps remained. The
cross-process driver-vs-Claude-Code-plugin drift is **not** repo-readable and is
deferred to gate 3's `doctor`. Rationale + open questions live in `GATE-02-REVIEW.md`.
