---
id: FEAT-2026-0067/T04
type: implementation
status: pending
planned_cost_usd: 2.50
produces:
  - specfuse/loop/rearm_migration.py
  - tests/test_rearm_migration.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
---

# The offline migration must not fold money that is already there

**Objective.** Fix `migrate_file`'s fold-never-ran branch so it does not
double-count a work unit that was re-armed and then never re-dispatched, and
repair the one record in this repository that it already double-counted.

**Context.** Correlation ID `FEAT-2026-0067/T04`. This WU exists because
`G1-CLOSE` reconciled every re-armed WU's frontmatter against its own
`events.jsonl` and found a mismatch it was not allowed to fix — `rearm_migration.py`
is T02's file and the affected record belongs to a `done` feature. Read
`RETROSPECTIVE.md` § *The finding: the migration double-counted one record* and
the FU-1 entry in the hedged-verdict follow-up record first. This WU's whole job
is that entry's stated re-run condition.

**The defect, precisely.** `fold_cumulative_on_rearm` may safely fold `cost_usd`
because it runs **at dispatch**, where `cost_usd` provably holds the prior cycle.
`migrate_file` runs **offline**, where `cost_usd` means "the prior cycle" *or*
"the current cycle" depending on whether a re-dispatch ever happened. The branch
folds `re_arm_history[].prior_cost_usd` into `cumulative_cost_usd` and leaves
`cost_usd` alone — correct when a new cycle ran, a duplicate when none did.

`FEAT-2026-0020/T04` is such a unit: `completed_out_of_loop: true`, re-armed,
never re-dispatched. Its frontmatter now reads `cost_usd 0.16309` +
`cumulative_cost_usd 0.16309` = $0.326180 against an `attempt_outcome` total of
$0.163090. `cumulative_duration_seconds 42.693` duplicates
`duration_seconds 42.693` the same way.

**This is the feature's own lesson turned back on it.** A value with two
meanings, read as if it had one — the exact defect class FEAT-2026-0067 exists
to remove. Say so in the module docstring, so the next person to add an offline
reader of `cost_usd` meets the warning where the mistake happens.

**The fix.** In the fold-never-ran branch, when `cost_usd` already equals the
`re_arm_history` prior-cost sum within the existing `_COST_TOLERANCE_USD`, the
money is already present: reset `cost_usd` to `0.0` in the same write set rather
than adding a second copy. Apply the identical treatment to
`duration_seconds` / `prior_duration_seconds`. When the two differ beyond
tolerance a new cycle genuinely ran, and today's behaviour is already correct —
leave it.

**Do not widen this into a rewrite.** The events-first disagreement check
(`PriorCostDisagreement`), the no-invented-numbers rule, the untouched
`not_rearmed` path, and the single-key no-reflow writer all stay exactly as they
are. This is one conditional and its repair, not a second pass at T02's design.

## Incremental edit to two deliverables T02 already shipped

`specfuse-lint` WARNs that both `produces:` paths were delivered by
`FEAT-2026-0067/T02`, which is correct and expected: this is a follow-up fix to
that WU's output, not a fresh deliverable. Stated here so the warning has a
written answer rather than being waved through.

- **`specfuse/loop/rearm_migration.py`** — one conditional added inside
  `migrate_file`'s fold-never-ran branch, plus a docstring note. No change to
  `_classify`, `_history_sums`, the `PriorCostDisagreement` check, the
  `not_rearmed` path, or the single-key writer.
- **`tests/test_rearm_migration.py`** — new cases appended. No existing test is
  edited or deleted; if one now fails, that is a finding to report, not a test
  to adjust.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`correlation-ids.md`, `security-boundaries.md`.

**Acceptance criteria.**

1. `tests/test_rearm_migration.py::TestRearmMigration::test_never_redispatched_unit_is_not_double_counted`
   exists and **fails on HEAD before this WU runs**, and passes after. The
   fixture is a re-armed, never-re-dispatched WU whose `cost_usd` equals its
   `re_arm_history` prior sum.
2. After migration of that fixture, `cost_usd + cumulative_cost_usd` equals the
   single recorded spend — not twice it. Assert the same for
   `duration_seconds + cumulative_duration_seconds`.
3. A test asserts the re-armed **and re-dispatched** case is unchanged: when
   `cost_usd` differs from the prior sum beyond `_COST_TOLERANCE_USD`, both
   values are preserved and folded exactly as they are today. This is the
   regression that would otherwise trade one double-count for an under-count.
4. Idempotence still holds: a second `migrate_file` call changes nothing.
5. A test asserts a `not_rearmed` WU is still untouched — no read-modify-write,
   no marker.
6. **`FEAT-2026-0020/T04`'s record is repaired** so its
   `cost_usd + cumulative_cost_usd` equals its `attempt_outcome` sum
   ($0.163090), and `duration_seconds + cumulative_duration_seconds` likewise.
   No number appears that is not already in that file or its `events.jsonl`.
7. The full reconciliation from `RETROSPECTIVE.md` § *The finding* is re-run and
   quoted in the RESULT block: every re-armed WU's
   `cost_usd + cumulative_cost_usd` matches its `attempt_outcome` sum, **with
   `FEAT-2026-0060/T01`'s pre-existing $9.23 under-count excluded by name** —
   that one is out of scope by `PLAN.md`, not by this fix, and must not be
   quietly repaired here.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`. Run named suites in-process via `unittest.defaultTestLoader`,
   never by shelling out to `pytest`.

**Do not touch.** `detect_rearm_dispatch` and `fold_cumulative_on_rearm` —
T01's, and correct as they stand; the dispatch-time fold is not the defect.
`specfuse/loop/cost.py` — T03's. `FEAT-2026-0060/T01`'s record, and any other
`done` feature's cost values beyond the single repair criterion 6 names.
`RETROSPECTIVE.md` — the close owns it.

**Verification.** The `code` gate set. Criteria 3 and 7 are load-bearing: without
3 this fix can convert a double-count into an under-count and every other
criterion still passes; without 7 the repair is asserted rather than measured.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`FEAT-2026-0020/T04`'s `cost_usd` turns out **not** to equal its
`re_arm_history` prior sum within tolerance, which would mean the diagnosis in
FU-1 is wrong and the record needs a different repair; the reconciliation after
the fix shows a WU other than `FEAT-2026-0060/T01` still mismatched, which is a
second defect this WU did not scope; or the reset cannot be written in the same
write set as the fold, leaving a window where a file reads neither shape.
