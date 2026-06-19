---
gate: 3
status: open
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 3 — `specfuse upgrade` + init.sh shim (terminal, skeleton)

Terminal gate. Gate 2's `plan-next` drafts the substantive WUs and sets the real
`depends_on` for the scaffolded `G3-CLOSE`. Intended scope: `specfuse upgrade <repo>`
overlays versioned files from package resources (preserve user-authored, prune
internal, stamp VERSION, refresh `.claude`), **version-gated / never-downgrade**;
`init.sh` shrinks to a thin shim calling `specfuse init`/`upgrade`.

## Definition of done

To be written by gate 2's plan-next. The terminal `close` WU collapses
retrospective + lessons + docs + the feature-arc verdict.
