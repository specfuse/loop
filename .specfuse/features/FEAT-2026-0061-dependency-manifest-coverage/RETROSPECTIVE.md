## Gate 1 — auto-closed (predicate=v1)

On-plan close; full retrospective ceremony skipped per
`evaluate_auto_close`.

- feature_id: FEAT-2026-0061
- predicate_version: v1
- gate_total_cost: $3.06
- gate_budget: $16.50
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This terminal gate auto-closed on-plan; the full close ceremony did not
run, so the per-criterion deferred-verification list was **not**
enumerated, and there is no downstream gate to reconcile it. Before
treating the feature as fully verified, the operator MUST confirm every
acceptance criterion was actually verified in-loop (not only by artifact
shape). Any AC deferred to a post-merge or real-system step must be
recorded and completed now.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02 criteria=26 predicate=v1 -->

- **FEAT-2026-0061/T01** (`WU-01-manifest-recognition-surface.md`)
  - deferred: `tests/test_arm_eval.py::ArmEvalTest::test_decision_class_paths_fires_on_maven_manifest`
  - deferred: That same test passes after this WU's edits, and
  - deferred: The recognition surface is stated in **one place** — a single table or mapping
  - deferred: A test asserts `fired` for each covered exact-match manifest: `pom.xml`,
  - deferred: A test asserts `fired` for each covered pattern: a `*.csproj` path and the
  - deferred: A test asserts `not_evaluable` for a `produces:` entry with a glob (`src/**`) and
  - deferred: A test asserts the **precedence** rule directly: a WU producing both `pom.xml`
  - deferred: A test asserts an ordinary source path (`specfuse/loop/foo.py`) still reports
  - deferred: The `clean` reason string names the coverage scope the verdict was decided
  - deferred: The `not_evaluable` reason string names **which** produced path could not be
  - deferred: Every entry remaining in the named-uncovered list carries a written reason, in
  - deferred: The lockfile treatment is stated explicitly in a comment beside the table, per
  - deferred: The pre-existing tests `test_decision_class_paths_fires_on_dependency_manifest`
  - deferred: A tree-wide sanity sweep is run and its counts recorded in the result:
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
- **FEAT-2026-0061/T02** (`WU-02-stop-class-doc-coverage.md`)
  - deferred: §3 of `docs/concepts/autonomy-stop-classes.md` names the **full covered list** as
  - deferred: The list in the document matches the table in `specfuse/loop/arm_eval.py` exactly.
  - deferred: §3 documents the two `not_evaluable` triggers — the named-uncovered list and the
  - deferred: §3 documents the **precedence** rule: a covered hit fires even when an
  - deferred: §3 states the class's limit plainly, in the shape §2's "v1 approximation" block
  - deferred: The named-uncovered list is reproduced with each entry's reason, matching T01's
  - deferred: The existing **Fires when:**, **Veto channel:**, and **Clearing action:**
  - deferred: `specfuse/loop/data/docs/concepts/autonomy-stop-classes.md` is byte-identical to
  - deferred: `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits zero.
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
  - deferred: `leak-scan` clean — this WU writes prose, and
