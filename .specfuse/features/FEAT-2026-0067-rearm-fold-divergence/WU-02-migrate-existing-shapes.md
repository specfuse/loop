---
id: FEAT-2026-0067/T02
type: implementation
status: done
planned_cost_usd: 3.00
produces:
  - specfuse/loop/rearm_migration.py
  - tests/test_rearm_migration.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.2
started_at: 2026-08-05T04:15:13.908982+00:00
attempts: 1
duration_seconds: 824.828
cost_usd: 2.200223
input_tokens: 202
output_tokens: 32098
---

# Every existing re-armed WU carries one shape, explicitly

**Objective.** Stamp `folded_through_re_arm` onto every re-armed work unit in
this repository, so T01's marker never has to infer anything, and handle the
two fold-never-ran units with a decision that is written down.

**Context.** Correlation ID `FEAT-2026-0067/T02`. Read `PLAN.md` first, then
T01 — this WU closes the exposure T01's docstring names.

**The exposure T01 leaves open.** T01 treats an absent marker as `0`. Six
existing WUs were already folded under the old logic and carry no marker, so
on a hypothetical next dispatch they would fold a second time. They are all
`done` and will not be re-dispatched, which makes this a latent rather than
live defect — but "it cannot happen today" is not a contract, and the roadmap
row rules out silently outliving these records.

**The census, to be re-run and not trusted.** At drafting:

```
re-armed WUs: fold ran = 6    fold never ran = 2
```

Re-run it as the WU's first action. If the numbers differ from these, stop and
report rather than migrating against a stale picture — the disagreement is
itself the finding.

**The two shapes need different decisions, and only you can make the second.**

- **fold-ran** (`cumulative_cost_usd` present): stamp
  `folded_through_re_arm = re_arm_count`. Mechanical, no judgement.
- **fold-never-ran** (`cumulative_cost_usd` absent, `re_arm_history[].prior_*`
  populated): two defensible options. **(a)** Migrate: fold the recorded
  `prior_*` values into `cumulative_*` and stamp the marker, so every record
  reads the same way. **(b)** Annotate: leave the values alone, stamp the
  marker to match `re_arm_count`, and record in the WU body why the historical
  split was preserved. Choose one, apply it to both units, and state the reason
  in the RESULT block. Do not apply (a) to one and (b) to the other.

**Cost values are not to be invented.** Under either option, no number appears
that was not already in the file. `re_arm_history[].prior_cost_usd` is the
recorded prior spend; `events.jsonl` is authoritative if they disagree. If they
disagree, report it — that is a second finding, not a rounding problem.

**Ship the migration as code, not as a one-off edit.** A downstream project
upgrading past this contract has the same two shapes in its own feature
folders. `specfuse/loop/rearm_migration.py` performs the stamp and is
importable and testable; running it against this repo is how this repo's own
records get migrated.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`correlation-ids.md`, `security-boundaries.md`.

**Acceptance criteria.**

1. `tests/test_rearm_migration.py::TestRearmMigration::test_fold_ran_wu_is_stamped_not_refolded`
   exists and **fails on HEAD before this WU runs**, and passes after.
2. A test asserts a fold-ran fixture gains `folded_through_re_arm == re_arm_count`
   and that its `cumulative_cost_usd` is **unchanged** — stamping is not folding.
3. A test asserts a fold-never-ran fixture is handled per the chosen option,
   and that the resulting file satisfies `detect_rearm_dispatch` returning
   False (no fold owed) — the migration's whole purpose.
4. A test asserts the migration is idempotent: running it twice changes nothing
   on the second pass.
5. A test asserts a WU that was never re-armed (`re_arm_count` absent) is left
   completely untouched — no marker, no accumulators, no reformatting.
6. The migration is applied to this repository's own records, and the census is
   re-run afterwards showing every re-armed WU carrying a marker. Quote both
   census runs (before and after) in the RESULT block.
7. Frontmatter round-trips without collateral reformatting: assert a migrated
   file's non-marker keys and body are byte-identical to before, so the stamp
   cannot silently rewrite unrelated records.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`. Run named suites in-process, never via `pytest`.

**Do not touch.** `detect_rearm_dispatch` and `fold_cumulative_on_rearm` —
T01's. `specfuse/loop/cost.py` — T03's. Any `done` feature's cost values beyond
what option (a) explicitly folds, and no `RETROSPECTIVE.md`.

**Verification.** The `code` gate set. Criteria 2 and 7 are load-bearing: a
migration that re-folds while stamping, or that reformats records it touches,
does more damage than the divergence it repairs.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the re-run census disagrees with the numbers above; a fold-never-ran unit's
`re_arm_history[].prior_cost_usd` disagrees with its `events.jsonl` total
(report both figures, migrate neither); or stamping cannot be done without the
frontmatter writer reordering or reformatting untouched keys, which would make
the migration's blast radius larger than its purpose.
