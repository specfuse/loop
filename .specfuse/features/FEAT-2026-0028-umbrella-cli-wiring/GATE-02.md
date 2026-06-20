---
gate: 2
status: open
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 — Umbrella CLI rewire (terminal, interactive, skeleton)

Terminal gate, **interactive / cross-repo** (lives in `specfuse/specfuse`, not this
repo — the loop driver cannot dispatch it). Gate 1's `plan-next` drafts the substantive
WUs and sets the real `depends_on` for the scaffolded `G2-CLOSE`. Intended scope: rewire
the umbrella `cli.py` — `cmd_init` → `specfuse.loop.scaffold.init(target, ci_check=...)`,
`cmd_upgrade` → `upgrade_specfuse(target)` then pip-upgrade + plugin hint, wire
`--dry-run`, and tests against the real scaffold API.

## Definition of done

To be written by gate 1's plan-next. The terminal `close` WU collapses
retrospective + lessons + docs + the feature-arc verdict, recording what the loop could
not verify (the umbrella repo's own tests run in that repo).
