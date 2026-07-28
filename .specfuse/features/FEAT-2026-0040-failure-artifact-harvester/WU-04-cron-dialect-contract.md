---
id: FEAT-2026-0040/T04
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
produces:
  - specfuse/loop/lint_monitoring.py
  - .specfuse/monitoring.yml.example
  - specfuse/loop/data/monitoring.yml.example
  - docs/concepts/monitoring-schema.md
  - tests/test_monitoring_cron_dialect.py
  - tests/test_derive_monitoring_discovery.py
  - tests/test_lint_monitoring.py
model: sonnet
effort: high
gate_set: code
---

# The cron dialect is declared, never inferred — schema, sweep, and enforcement

**Objective.** Give a `heartbeat` target a declared `dialect` alongside its `cron`,
migrate every shipped surface that carries a `cron` to declare one, and then make the
validator enforce the enum **and** the expression's arity against it — in that order,
inside one work unit.

**Context.** Correlation ID `FEAT-2026-0040/T04`. Gate 2, no dependencies. T07's
heartbeat adapter is the consumer: it computes "should this have fired?" and cannot
answer without knowing which dialect the expression is written in. This unit ships
the contract; T07 ships the arithmetic.

**The dialect is declared, not inferred.** A heartbeat check cannot tell a 5-field
expression (standard cron) from a 6-field one (seconds-first, which is what Azure
Functions timer triggers use) by looking at it — `0 2 * * *` and `0 0 2 * * *` are
both well-formed and mean different things. Inference by field count was considered
and **rejected by the operator**: it degrades silently exactly when a new dialect
arrives, which is the worst possible moment for a monitoring tool to start guessing.
A declared dialect turns a mismatch into a validation error at lint time instead of a
wrong verdict at 3am.

**This widens a position 0069 took deliberately, and that is the point.**
`lint_monitoring._check_targets`'s docstring records it in its own words: a target's
required coordinates must be present, but coordinate *contents* — "a cron expression,
a timezone name" — are opaque, "exactly as `invariant.query` is." Checking arity
against a declared dialect crosses that line knowingly, and only for the one
coordinate whose contents a check type must interpret to do its job. `timezone` stays
opaque, `invariant.query` stays opaque, and the docstring must be rewritten to say
which line moved and why — a reader who finds arity checking under a docstring
promising opacity will read it as drift and undo it.

**Expand → migrate → contract, in that order, and the migrate step is a sweep.**
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` is explicit: the migrate step's acceptance
criterion "must be a tree-wide completeness command asserted at zero hits, never a
prose enumeration of surfaces." That gate got the ordering right and still lost $5.26
to a migrate criterion scoped to a *sample* — "a component with the new field exists
and validates" — where the flip needed a *sweep*: "no non-conforming instance remains
anywhere." It passed every criterion it carried, which is why no driver guard caught
it; a correctly-scoped WU and an under-scoped one are indistinguishable from outside.

Flip-first is not merely risky here, it is unsatisfiable. `.specfuse/monitoring.yml.example`
is validated by the `monitoring-example-lint` **code gate**, so tightening the
validator before migrating turns a gate red on a correct tree, and under
FEAT-2026-0051's preflight baseline probe a red base gate halts the run before any
unit dispatches. The three steps live in one WU precisely so no intermediate squash
ever ships a tightened validator against an unmigrated tree.

**The contract this unit ships.**

| dialect value | fields | field order |
|---|---|---|
| `standard-5` | 5 | minute hour day-of-month month day-of-week |
| `seconds-first-6` | 6 | second minute hour day-of-month month day-of-week |

Both names are vendor-neutral by design — the schema "names a symptom, never a
vendor" (`docs/concepts/monitoring-schema.md`), and a dialect named after the product
that popularised it would put a vendor into a neutral enum. The arity is in the name
so the enum-to-arity mapping is readable without opening the validator.

Four validator rules, all `ERROR`-severity findings in the same list every other
finding lands in:

1. A `heartbeat` target carrying `cron` **must** carry `dialect`.
2. `dialect` must be one of the enum above.
3. The `cron` expression's whitespace-separated field count must equal the dialect's
   arity.
4. `dialect` without `cron` is a finding — a dialect declared for no expression means
   the author dropped the expression, not that they meant nothing.

A `heartbeat` target with only `name` and no `cron` stays valid and needs no dialect;
`cron` remains optional. This keeps the escalation predicate satisfiable — see
`GATE-02.md`'s arming section.

**Migration is cheap because discovery already knows the answer.** `derive-monitoring`
generates heartbeat targets from discovered trigger registrations, and the trigger
attribute it reads is what determines the dialect. The reference implementation
(`suggest_checks` in `tests/test_derive_monitoring_discovery.py`) fans a record's
`schedules` into heartbeat targets; a `schedules` entry gains `dialect` and
`suggest_checks` emits it. A generator that emits non-conforming targets would
re-break the tree on the next `/derive-monitoring` run, so it is in scope here and not
deferrable to prose.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

*Expand — the schema accepts a dialect before anything requires one.*

1. `tests/test_monitoring_cron_dialect.py::TestCronDialect::test_dialect_arity_mismatch_is_a_finding`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/loop/lint_monitoring.py` exports a `CRON_DIALECTS` mapping (or an
   equivalent named constant) whose keys are exactly `standard-5` and
   `seconds-first-6` and whose values are the arities `5` and `6`. A test asserts the
   enum's membership by name, so adding a dialect is a visible change and not a silent
   one.
3. A heartbeat target carrying `name`, `cron`, `timezone`, and a conforming `dialect`
   validates clean, and one carrying only `name` also validates clean — `cron` stays
   optional and a cron-less heartbeat target needs no dialect.

*Migrate — every non-conforming instance in the tree is gone, proven by a sweep.*

4. **The sweep.** `tests/test_monitoring_cron_dialect.py::TestShippedSurfacesDeclareDialect::test_no_cron_without_a_conforming_dialect_anywhere`
   walks the repository tree — excluding `.git/` and `.specfuse/features/` — over
   `*.yml`, `*.yaml`, `*.md` (every fenced ```yaml block), and `*.py`, collects
   **every** heartbeat target carrying a `cron`, and asserts that **zero** of them
   lack a `dialect` or carry one whose arity disagrees with the expression. The file
   list is **discovered by walking**, never a hand-written tuple of paths — a
   hand-written list reproduces the author's blind spots, which is
   `[FEAT-2026-0039/T04]`'s failure one level up.
5. **The sweep cannot pass vacuously.** The same test asserts the collected
   cron-carrying-target count is **at least 4** and that the discovered file set
   contains at least `.specfuse/monitoring.yml.example` and
   `specfuse/loop/data/monitoring.yml.example`. Without this, an empty walk satisfies
   "zero non-conforming" — the exact defect 0069's probe found in two of its own
   boundary tests, which stayed green against zero components.
6. The reference implementation emits the field: a `schedules` entry in
   `tests/test_derive_monitoring_discovery.py`'s discovery records carries `dialect`,
   `suggest_checks` renders it into each heartbeat target, and
   `test_discovered_config_passes_lint_monitoring` still passes **after** criterion 8's
   flip lands.
7. `cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example`
   exits 0 — the two are byte-identical today and nothing here may split them.

*Two existing assertions contradict the new contract and must be re-aimed, not
deleted. Both were found by static enumeration at drafting time and are recorded in
`GATE-02-REVIEW.md` §4.*

7a. `tests/test_lint_monitoring.py::test_heartbeat_target_cron_and_timezone_contents_are_opaque`
    (`:468`) asserts that `cron: "this is not a cron expression at all"` validates
    clean. After the flip it does not — that string has 7 fields and declares no
    dialect. **Split** the assertion rather than deleting it: `timezone` contents stay
    opaque (`Not/A_Real_Zone` must still validate clean), and the cron half becomes an
    assertion about what remains opaque — field *values* are not validated, only the
    field *count* against the declared dialect. A test named for opacity that quietly
    stops asserting opacity is how the next author concludes the position was
    abandoned. Its neighbour `test_heartbeat_target_missing_name_is_rejected` (`:455`)
    asserts `len(findings) == 1` on a target carrying `cron` and no `name`; after the
    flip that target yields **two** findings (missing `name`, missing `dialect`). Fix
    the expectation, and keep it an exact count — a `>= 1` would stop distinguishing
    the two rules.
7b. `tests/test_derive_monitoring_discovery.py:962` asserts
    `set(target) == {"name", "cron", "timezone"}` on every generated heartbeat target
    — an exact-set assertion that fails the moment `dialect` is emitted. It must
    become `{"name", "cron", "timezone", "dialect"}`; keep it exact, because a
    loosened `issubset` check would stop catching the field this WU exists to add.

*Contract — the validator enforces what the tree now satisfies.*

8. `validate_monitoring` reports a finding for each of the four rules above, each
   proven by a **negative observation** against a purpose-built bad input:
   cron-without-dialect, an out-of-enum dialect, a 5-field expression declared
   `seconds-first-6`, and a dialect with no cron. Per
   `verification-discipline.md` §3, a validation-rule claim is not verified by a
   passing positive case.
9. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`
   exits 0 **after** the flip — this is the `monitoring-example-lint` code gate, and it
   is the gate that goes red if the flip lands before the migration.
10. `python3 -m unittest tests.test_monitoring_fenced_blocks -v` passes: every fenced
    yaml block across the five declared surfaces still validates clean under the
    tightened validator.

*Documentation and propagation.*

11. `docs/concepts/monitoring-schema.md`'s check-targets table row for `heartbeat`
    documents `dialect` — required whenever `cron` is present — with both enum values,
    their arities, and one sentence on why the dialect is declared rather than
    inferred.
12. The `derive-monitoring` skill states that a generated heartbeat target carries the
    dialect the discovered trigger registration implies. Edit the **canonical** copies
    under `plugins/specfuse/skills/derive-monitoring/`, then run
    `scripts/sync-scaffold.sh`; `git diff --stat` must show the `.specfuse/skills/derive-monitoring/`
    copies changed **without** having been edited by hand. Hand-editing the four
    copies is the drift this repo already built tooling against, and
    `sync-scaffold-bats` checks the sync.

*Whole-gate-set.*

13. The `code` gate set passes in full: `tests`, `lint`, `security`, `coverage`
    (≥90%), `leak-scan`, `monitoring-example-lint`, and the five `bats` suites.
    Placeholders only in every example edited — `acme-*` names, `Etc/UTC` timezones,
    no real organization, host, queue, or workspace name.

**Do not touch.** `specfuse/monitor/` — the harvester core is T01–T03's and T05–T07's;
this unit changes the schema and its validator only, and no artifact field. The
`CHECK_TYPES` enum and `_TARGET_REQUIRED_FIELDS`' existing entries — `dialect` is a new
optional-then-conditional key on `heartbeat` targets, not a change to which coordinates
a target requires. `_TARGETLESS_CHECK_TYPES`. `escalation.py`. `.specfuse/skills/derive-monitoring/`
by hand (criterion 12 is a sync, not an edit). Generated directories, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order, with `monitoring-example-lint` read as this unit's load-bearing gate rather
than a formality. Plus the scoped red/green run in criteria 1 and 4, the four negative
observations in criterion 8, the `cmp` in criterion 7, and the `git diff --stat` check
in criterion 12. Run the sweep test after **every** edit to a YAML-carrying surface,
not once at the end — it is the fastest feedback loop this unit has.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
sweep in criterion 4 finds a non-conforming instance in a surface this WU may not edit
(a generated tree, a vendored copy), which means the migration is larger than one gate
can hold; `_miniyaml` cannot parse a heartbeat target carrying four keys, which would
make the shipped example unrepresentable and is a parser fix, not a schema change;
`GATE-02-REVIEW.md`'s §4 probe finding list disagrees with what you observe locally by
more than the two example files, which means the arming evidence was stale and the
migration surface was never enumerated; or the sweep as written cannot distinguish a
heartbeat target from any other mapping carrying a `cron` key, which is a criterion
defect to report rather than to weaken.
