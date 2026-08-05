---
id: FEAT-2026-0067/T03
type: implementation
status: done
planned_cost_usd: 2.00
produces:
  - specfuse/loop/data/templates/WU.template.md
  - .specfuse/templates/WU.template.md
  - specfuse/loop/cost.py
  - tests/test_fold_contract_documented.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.2
started_at: 2026-08-05T04:28:58.942822+00:00
attempts: 1
duration_seconds: 665.581
cost_usd: 1.109617
input_tokens: 46
output_tokens: 8979
---

# The written contract says what the code now does

**Objective.** State in the frontmatter contract that `cumulative_*` is
unconditionally the lifetime accumulator, and update `cost.py`'s documentation
so it no longer describes two supported shapes.

**Context.** Correlation ID `FEAT-2026-0067/T03`. Read `PLAN.md` first. T01
changes the behaviour; this WU makes the documents agree with it. A contract
that still describes the old ambiguity is how the next reader gets misled —
which is the harm this feature exists to remove.

**`cost.py`'s docstring is the strongest evidence the ambiguity was real.** It
names "fold-ran" and "fold-never-ran" as two shapes a reader must handle. After
T01 and T02, new records have one shape. The docstring must say so, and must
say what the fallback branch is now *for*: pre-migration records in projects
that have not upgraded, not an ongoing design.

**`wu_lifetime_cost_usd` keeps its behaviour.** Events-first precedence is
unchanged and its frontmatter fallback still sums `cost_usd + cumulative_cost_usd`
— which remains correct under the converged contract. This WU changes what the
documentation *claims*, not what the function *does*. If you find yourself
editing its logic, stop: that is out of scope and an escalation.

**The template ships to every downstream project.** `WU.template.md` has two
copies — the canonical `specfuse/loop/data/templates/` one and the vendored
`.specfuse/templates/` one. They must be byte-identical or the scaffold sync
guard fails with an error that reads like an unrelated problem.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_fold_contract_documented.py::TestFoldContract::test_template_documents_cumulative_as_lifetime`
   exists and **fails on HEAD before this WU runs**, and passes after.
2. `WU.template.md`'s frontmatter notes document `folded_through_re_arm` and
   state that `cumulative_*` accumulates across every re-arm — including one
   whose prior cycle cost nothing. A test asserts both copies contain it.
3. A test asserts the two `WU.template.md` copies are byte-identical.
4. `cost.py`'s module docstring no longer presents fold-never-ran as a
   supported ongoing shape; it names it as a pre-migration legacy the fallback
   still tolerates, and points at FEAT-2026-0067. A test asserts the docstring
   mentions the migration rather than describing two live shapes.
5. A test asserts `wu_lifetime_cost_usd`'s behaviour is unchanged: same result
   for an events-bearing WU and for a frontmatter-only WU as before this WU ran.
   Documentation changed, logic did not.
6. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`. Run named suites in-process, never via `pytest`.

**Do not touch.** `detect_rearm_dispatch`, `fold_cumulative_on_rearm` — T01's.
`rearm_migration.py` — T02's. `wu_lifetime_cost_usd`'s **logic** — this WU
edits its docstring only.

**Verification.** The `code` gate set. Criterion 5 is load-bearing: a
documentation WU that quietly changes a cost reader's behaviour would alter
what `arm_eval` sees, which is a different feature.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the template's frontmatter notes cannot state the contract without also
changing a field's meaning for already-drafted WUs downstream; or `cost.py`'s
fallback turns out to be reachable in a way the converged contract makes wrong,
which would mean T01's change has a consumer impact this feature scoped out.
