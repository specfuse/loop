---
gate: 2
status: passed
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 — Publish

Completed **interactively** (commit `f4f1d02`), like gate 1 — the distribution
surfaces stay entangled with the packaging harness, so the whole feature is being
built in a live session rather than per-WU loop dispatch (see RETROSPECTIVE.md gate 1
lesson).

## Definition of done

- A tag-triggered GitHub Actions release pipeline (`.github/workflows/release.yml`):
  on `v*`, build wheel + sdist, run the full suite against the built artifact, assert
  tag == pyproject version == `DRIVER_VERSION`, publish to PyPI via OIDC trusted
  publishing. ✓
- Driver/scaffold version-skew guard: `check_scaffold_version()` fails loud at startup
  on a missing/empty/older `.specfuse/VERSION`; `init.sh` stamps and re-stamps it. ✓
- Wheel ships only the `specfuse` package (packages.find scoped). ✓
- 818 tests green; coverage 93% (`--source=specfuse`). ✓

## Operator-owned (external — not done in-loop)

- Configure the PyPI trusted publisher for project `specfuse-loop`.
- Push the first `v*` tag to trigger the real publish.

These are tracked in RETROSPECTIVE.md "What the loop did NOT verify".

## Reflection notes

<Written by the human at review time.>
