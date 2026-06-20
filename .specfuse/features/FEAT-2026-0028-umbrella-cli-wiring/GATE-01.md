---
gate: 1
status: awaiting_review
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — docs in the pip seed

## Definition of done

- The methodology docs (`deploy_docs` set) ship as package data under
  `specfuse/loop/data/docs/`, included in the wheel.
- `scaffold.py` `init_specfuse` writes `.specfuse/docs/`; `upgrade_specfuse` overlays
  `docs/` in its versioned footprint (existing repos get docs on upgrade).
- `sync-scaffold.sh` + the drift-guard test cover `docs/`.
- A retrospective exists; lessons promoted to `.specfuse/LEARNINGS.md`; docs/roadmap
  reconciled. Gate 2 (umbrella CLI rewire) work units drafted; `GATE-02-REVIEW.md` written.

The closing sequence (close-intermediate → plan-next) is enforced by the linter. The
driver stops here for human review-and-arm.

## Reflection notes

<Written by the human at review time.>
