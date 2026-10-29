---
id: FEAT-2026-0247/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 4.00
produces:
  - specfuse/loop/ids.py
  - specfuse/loop/layout.py
  - specfuse/loop/lint_plan.py
  - specfuse/loop/lint_roadmap.py
  - tests/test_ids.py
  - tests/test_keyed_feature_ids_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T13:14:28.542707+00:00
duration_seconds: 146.131
cost_usd: 0.705571
input_tokens: 42
output_tokens: 17274
---

# T01 — walking skeleton: one ID module, a configured key, and a keyed feature that lints

**Objective.** Make gate 1's `feature_oracle` runnable and turn its clauses 1, 2 and 8
green by wiring the thinnest path end to end: one module owns the feature-ID grammar,
`layout.yml` carries the key, `ids next` allocates, and the two linters accept a keyed
feature. This is the tracer bullet: stubs are allowed here and nowhere else in the gate.

**Context.** `FEAT-2026-0247/T01`. Today twelve sites each carry their own
`FEAT-\d{4}-\d{4}` literal and no Python allocates IDs (`/roadmap-add` does it in
prose). Create `specfuse/loop/ids.py`, standalone like `layout.py` (must not import the
driver):

- `KEY_RE` (`[A-Z][A-Z0-9]{1,5}`), `FEATURE_ID_PATTERN` (the un-anchored
  `FEAT-(?:KEY-)?\d{4}-\d{4}` source string other regexes embed) and an anchored
  `FEATURE_ID_RE`.
- `parse(text) -> FeatureId(key, year, ordinal)` accepting an ID or a folder name
  (`<ID>-<slug>`), returning None otherwise; `anchor(id)` (lower-cased); `sort_key`.
- `next_id(repo_root, year=None)`: max ordinal for the year across roadmap table rows
  and `feature_id:` in `.specfuse/features/*/PLAN.md`, both forms counted, plus one;
  keyed with `ids.key` when set. CLI: `python3 -m specfuse.loop.ids next`.

Extend `specfuse/loop/layout.py` with an `ids` top-level block: `ids.key`, validated
against `KEY_RE`, `layout get ids.key` printing it (empty when unset). Keep the module's
contract: no file or no `ids:` block means today's behaviour.

Point `lint_plan.CORRELATION_ID_RE` and `lint_roadmap`'s `_HEADING_RE`, `_ROW_RE`,
`_ANCHOR_RE` and `_REF_RE` at `ids.FEATURE_ID_PATTERN` (anchors at its lower-cased form).

Create the oracle module `tests/test_keyed_feature_ids_end_to_end.py` with one class per
Definition-of-done clause in `GATE-01.md`. Implement clauses 1, 2 and 8 here; every other
class is `unittest.skip("owned by FEAT-2026-0247/T0N")`.

**Acceptance criteria.**

1. `tests/test_ids.py` and the oracle's clause-1/2/8 classes fail on HEAD (the module
   does not exist) and pass after.
2. `tests/test_ids.py` parses every directory name under `.specfuse/features/` and every
   `| FEAT-` row of `.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md`, asserting
   each yields the ID the existing `FEAT-\d{4}-\d{4}` pattern would have extracted (real
   corpus, not only fixtures).
3. A malformed `ids.key` (`acme`, `A`, `TOOLONG1`, `1ABC`) is an ERROR from
   `layout.validate`; a valid one round-trips through `layout get ids.key`.
4. `python3 -m unittest tests.test_lint_plan_errors tests.test_lint_roadmap tests.test_layout tests.test_layout_validation tests.test_layout_no_layout_goldens -b`
   passes unchanged.
5. `grep -nF 'FEAT-\d{4}-\d{4}' specfuse/loop/lint_plan.py specfuse/loop/lint_roadmap.py`
   returns nothing.

**Do not touch.** The other ten pattern sites (T02). Skills (T03). The roadmap WARN
(T04). Core-owned `.specfuse/rules/correlation-ids.md` and the `CORE_FILES` schemas
(T07). Docs (T06).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_keyed_feature_ids_end_to_end -v -b`.

**Escalation triggers.** If `lint_plan`'s correlation-ID regex cannot embed the shared
pattern without changing what it accepts for legacy IDs, stop: that is a grammar change,
not a refactor. If the oracle's dry-run clause needs anything beyond `--feature` parsing
(the driver's `--feature` check, which T02 owns), stub that one call in the oracle and name T02.
