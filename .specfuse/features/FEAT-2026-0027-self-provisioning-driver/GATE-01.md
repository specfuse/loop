---
gate: 1
status: open
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — auto-sync engine

## Definition of done

- A `.specfuse/.scaffold-manifest` (sha256 per versioned file) is written at
  init/upgrade; `scaffold.detect_modified` reports user-edited versioned files.
- `loop.py` startup runs `auto_sync` (replacing `check_scaffold_version`): missing →
  create; older + clean → overlay; older + modified → defer/prompt; equal → no-op;
  newer → refuse (never downgrade). `--no-autosync` + `.specfuse/config` toggle disable
  it; `--dry-run` reports read-only; never auto-commits.
- A retrospective exists; lessons promoted to `.specfuse/LEARNINGS.md`; docs/roadmap
  reconciled. Gate 2 (plugin-config + drift) work units drafted; `GATE-02-REVIEW.md` written.

The closing sequence (close-intermediate → plan-next) is enforced by the linter. The
driver stops here for human review-and-arm.

## Reflection notes

<Written by the human at review time.>
