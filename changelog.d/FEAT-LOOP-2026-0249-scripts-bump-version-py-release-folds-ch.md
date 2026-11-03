---
class: changed
trace: FEAT-LOOP-2026-0249
---
`scripts/bump_version.py` `release()` folds `changelog.d/` fragments into `Unreleased` before stamping and removes them afterward, all-or-nothing; adopter release scripts must call `collate` before stamping.
