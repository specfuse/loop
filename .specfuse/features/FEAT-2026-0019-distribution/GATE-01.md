---
gate: 1
status: open        # open | awaiting_review | passed
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — Repackage: pip-installable driver, package as single source

## Definition of done

- `pip install -e .` exposes `specfuse-loop` and `specfuse-lint` console scripts on
  PATH; driver code lives in the `specfuse/loop/` PEP 420 namespace package as the
  single source of truth.
- The vendored `.specfuse/scripts/*.py` still work as thin shims (dogfood + back-compat
  preserved); offline-vendored generation from the package is explicitly deferred.
- The full `code` gate set (tests, coverage ≥ 90%, ruff, bandit) passes against the
  package under `pip install -e .[dev]`.
- A retrospective exists; generalizable lessons are promoted to `.specfuse/LEARNINGS.md`;
  docs/roadmap reflect what was built.
- Gate 2 (Publish) work units are drafted, and `GATE-01-REVIEW.md` is written.

The closing sequence (close-intermediate → plan-next) is part of this gate and is
enforced by the linter. The driver runs the gate unattended, then stops here for
human review-and-arm: read the review artifact, accept or edit gate 2's drafted work
units, flip the accepted ones to `pending`, set this gate's status to `passed`, and
re-run.

## Reflection notes

<Written by the human at review time.>
