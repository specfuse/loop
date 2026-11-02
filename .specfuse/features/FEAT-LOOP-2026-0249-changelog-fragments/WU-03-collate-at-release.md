---
id: FEAT-LOOP-2026-0249/T03
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/changelog_fragments.py
  - scripts/bump_version.py
  - tests/test_changelog_fragments.py
model: sonnet
effort: medium
gate_set: code
---

# T03 — collate fragments at release

**Objective.** Turn clause 3 and clause 5's release half green: a released section contains
every fragment, parses clean, and leaves no consumed fragment.

**Context.** `FEAT-LOOP-2026-0249/T03`; decisions 3 and 6 in `PLAN.md`. Add a shipped `collate` subcommand
and a function `scripts/bump_version.py`'s `release()` calls, because `scripts/` is this
repository's own release script and adopters run theirs.

- Collation folds each fragment into `Unreleased` through `append_entry`, in sorted filename
  order, so output is deterministic. `stamp_release` is unchanged and runs after.
- All fragments are validated and the result parsed before any write or delete. Any problem
  refuses, naming the file, with the tree untouched.
- Collation runs whatever the mode; `changelog.d/` may disappear afterward.
- `release()`'s existing rule holds: a rejected stamp leaves the tree untouched, fragments included.

**Acceptance criteria.**

1. The oracle's clause-3 class is unskipped, fails on HEAD and passes after, driving `release()`
   with an injected umbrella version, and asserts a double-stamp refusal leaves every fragment in place.
2. Clause 5's release test passes: with no fragments, `release()` output is byte-identical to
   stamping alone.
3. `python3 -m unittest tests.test_changelog_release_wiring tests.test_changelog_append_only -b` passes.

**Do not touch.** `changelog.py`'s `stamp_release`. `CHANGELOG.md`'s existing sections.
The closing guards (T02).

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If `check_changelog_append_only.py` reports drift on a collated release,
block with the finding: `released_section_drift` is not to be weakened.
