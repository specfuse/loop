---
gate: 3
status: passed
---

<\!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 3 — doctor + first-run + migrate (terminal, skeleton)

Terminal gate. Gate 2's `plan-next` drafts the substantive WUs and sets the real
`depends_on` for the scaffolded `G3-CLOSE`. Intended scope: `specfuse doctor` (read-only
diagnosis — driver/scaffold versions, plugin state, drift, recommended action), the
first-run scaffold prompt, and the legacy `scripts/`/`skills/` migration-prune
(`specfuse init --migrate`).

## Definition of done

To be written by gate 2's plan-next. The terminal `close` WU collapses
retrospective + lessons + docs + the feature-arc verdict.
