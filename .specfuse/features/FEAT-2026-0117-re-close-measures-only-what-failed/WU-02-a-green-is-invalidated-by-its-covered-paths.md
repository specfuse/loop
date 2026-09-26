---
id: FEAT-2026-0117/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
produces_driver_helper:
  - derive_criterion_covers
  - invalidate_carried_entries
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/criteria_state.py
  - tests/test_carried_green_invalidated_by_diff.py
---

# A carried green is invalidated when the gate diff touches a path it covers

**Objective.** Never carry a narrow green past a change to the thing it
measured: seed each criteria entry with the paths it covers, and on a re-close
reset any carried entry whose covered paths appear in the gate diff since
`proved_at_sha`.

**Context.** FEAT-2026-0117/T02. #3313 names this as the decision to make at
drafting: "a carry-forward that survives a code change to the thing it measured
would be worse than no carry-forward". Two helpers. `derive_criterion_covers(wu,
oracle_command)` in `specfuse/loop/criteria_state.py` returns the unit's
`produces:` paths plus the test module path the oracle names (`tests.foo_bar` →
`tests/foo_bar.py`; a `-Dtest=` class → its `src/test/**` file when one exists);
the skeleton step writes it as `- **covers:**` on each seeded entry (existing
entries without it gain it on the next seed). `invalidate_carried_entries(entries,
touched_paths)` in `loop.py` runs in the skeleton step after T01's reset: an
entry with `carried_from_attempt` whose `covers` intersects `touched_paths` —
from `git diff --name-only <proved_at_sha> HEAD` — resets to `unverified` with
the reason `invalidated_by: <path>`; an entry with no `covers` is never carried.
`build_reverification_worklist` lists invalidated entries under "Re-verify" with
the path that invalidated them. Red test first.

**Acceptance criteria.**

1. `tests/test_carried_green_invalidated_by_diff.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b`
   exits 0.
2. That module asserts, over two `loop.run()` passes with a commit between
   them that edits one covered path: the entry covering it is `unverified` with
   `invalidated_by` naming the path on the second dispatch, and its sibling
   whose covered paths are untouched is still carried.
3. It also asserts `derive_criterion_covers` for a unittest oracle and a Maven
   `-Dtest=` oracle, and that an entry with empty `covers` is listed under
   "Re-verify".
4. `python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e tests.test_criteria_state tests.test_criteria_worklist tests.test_lint_closing_criteria -v -b`
   exits 0 with no edit to the last three modules.

**Do not touch.** T01's reset split; `judge.py` and Measurements (T03);
`.specfuse/rules/` and `docs/` (T04); `lint_closing.py` (if close-l rejects the
new `covers`/`invalidated_by` fields, block and name the check);
`.specfuse/verification.yml`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if `proved_at_sha` recorded
by real closes is not an ancestor of HEAD on the re-arm path (a squash or rebase
between closes) — say what the diff base should be instead; or if close-l
rejects the added fields.
