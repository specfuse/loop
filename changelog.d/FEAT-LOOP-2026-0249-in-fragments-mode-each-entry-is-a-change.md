---
class: added
trace: FEAT-LOOP-2026-0249
---
In `fragments` mode each entry is a `changelog.d/<trace>-<slug>.md` file (`class` and `trace` in frontmatter, one-line body), so concurrent PRs no longer conflict on `CHANGELOG.md`.
