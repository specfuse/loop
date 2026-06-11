---
feature_id: FEAT-2026-0014
title: GitHub Actions Node.js 20 deprecation bump
slug: gha-node20-bump
branch: feat/FEAT-2026-0014-gha-node20-bump
roadmap_goal: Bump GitHub Actions to versions supporting Node.js 24 natively, ahead of the 2026-06-16 deprecation, so CI keeps running without warnings.
autonomy_default: auto
status: done
---

# Plan: GitHub Actions Node.js 20 deprecation bump

GitHub deprecates Node.js 20 actions on 2026-06-16 (forced upgrade to Node
24); Node 20 leaves runners 2026-09-16. The repo's only workflow,
`.github/workflows/ci.yml`, currently pins `actions/checkout@v4` and
`actions/setup-python@v5` — both still Node-20-based, both emit the
deprecation warning today. This feature bumps those pins to the Node-24
generation (`@v6` major tags) and verifies CI runs without the deprecation
warning before the forced-upgrade date.

This file owns the **shape**. WU files own their own status; the GATE file
owns gate status.

## Scope OUT

- Bumping Python version (3.12 stays). Python and action runtime are
  orthogonal.
- Migrating away from major-tag pinning (`@v6`) to SHA pinning or exact
  patch pins — current style is preserved.
- Adding new workflow jobs or replacing `smoke-test.sh`.
- Auditing other actions that may transitively depend on Node 20 (none in
  this repo today; revisit only if AC4 catches one).

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0014/T01
        file: WU-01-bump-action-versions.md
        depends_on: []
      - id: FEAT-2026-0014/G1-CLOSE
        file: WU-90-close.md
        depends_on:
          - FEAT-2026-0014/T01
```

## Notes

- Single gate, one substantive WU, one `close` ceremony (valid per
  FEAT-2026-0005 for single-gate features). Mirrors FEAT-2026-0008's shape.
- Dependencies live here, not in WU frontmatter.
- Time-bounded: forced-upgrade date 2026-06-16. Today is 2026-06-11.
