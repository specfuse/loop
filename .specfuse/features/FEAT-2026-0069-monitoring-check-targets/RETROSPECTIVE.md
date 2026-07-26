# FEAT-2026-0069 — Retrospective

Non-terminal close. This file is written by `G1-CLOSE-INTERMEDIATE` and covers
**gate 1 only**. There is no feature-arc verdict here and no terminal flip — gate 2
(`/derive-monitoring` re-keying) is undrafted at the time of writing, and `WU-92`
carries the terminal close.

---

## Gate 1 — the schema expresses per-target enumeration, and the validator enforces it

**Outcome: all five substantive work units `done`.** T01, T02, T03H, T03, T04. Gate 1's
definition of done is met for every clause that gate 1 can decide; the two clauses it
cannot decide are enumerated under *What the loop did NOT verify* rather than counted as
met.

**What shipped.** `monitoring.yml` checks gained a `targets[]` list — the unit of
failure-artifact enumeration, separate from `component`, which stays the unit of
deployment and attribution. The validator enforces the axis distinction per check type.
`queue-stalled` joined the check-type enum (issue #247). Every shipped YAML surface in
the repo was migrated, and the contract then flipped so a target-less `dlq` is a finding.

### Gate-level summary

| | |
|---|---|
| substantive WUs | 5 (T01, T02, T03H, T03, T04) — 4 planned, 1 inserted mid-gate |
| attempts | 8 across 5 WUs (5 passing, 3 non-passing — all 3 on T03) |
| human escalations | 1 (`spinning_signature_repeat`, T03) |
| re-arms | 1 (T03, after T03H landed) |
| substantive wall clock | 3619s ≈ 60.3 min |
| substantive spend | **$11.94** |
| `CHECK_TYPES` | 5 → 6 |
| shipped YAML surfaces migrated | 6 files (2 `monitoring.yml.example` copies, 2 `monitoring.overrides.yml.example` copies, 2 `derive-monitoring/SKILL.md` copies) |

### Per-WU outcome

#### T01 — `targets` accepted and structurally validated (1 attempt, $0.74 vs $3.00)

**Worked, first attempt, cheapest WU in the gate.** The expand step: `targets` is
accepted everywhere it will ever be legal, required nowhere. Delivered
`_check_targets()` in `specfuse/loop/lint_monitoring.py` with two lookup tables —
`_TARGET_REQUIRED_FIELDS` (per-type required coordinates) and `_TARGETLESS_CHECK_TYPES`
(`error-logs`, `http-5xx`) — plus tests in `tests/test_lint_monitoring.py`.

The design constraint that made this cheap was set at plan time, not discovered here:
`targets` was built as the generalization of the existing `fingerprint_by` pattern (a
per-check keying field the validator requires structurally and never interprets), so
there was no new concept to invent. The pre-flight `_miniyaml` probe recorded in
`PLAN.md` also held — the parser needed no changes for a list-of-mappings under a key of
a list item, so no parser work appeared, exactly as planned.

**Nothing failed.**

#### T02 — migrate the shipped surfaces (1 attempt, $1.51 vs $2.50)

**Passed on its own criteria, and that is the problem.** T02 added a multi-trigger
functions-host component carrying `targets[]` to `.specfuse/monitoring.yml.example` and
its packaged copy, wrote the `## Check targets` section of
`docs/concepts/monitoring-schema.md`, and updated the `derive-monitoring` skill and
`tests/test_monitoring_example.py`. Every acceptance criterion it carried was met.

**What it did not do was migrate.** Its criteria tested "a component with `targets`
exists and validates" rather than "no target-less `dlq` check remains anywhere in the
tree." Three pre-existing target-less `dlq` checks survived — in
`.specfuse/monitoring.overrides.yml.example` (and its packaged copy) and in the
`derive-monitoring` skill's second worked example. The gate's whole ordering premise
(expand → migrate → contract) depends on the migrate step being tree-wide, and this one
was sample-wide. T03 inherited a non-conforming tree and burned three attempts on it.

#### T03H — the hygiene WU T02 should have been (1 attempt, $0.83 vs $2.00)

**Inserted mid-gate**, after T03's escalation, with the tree-wide acceptance criterion
T02 lacked. Gave every remaining shipped `dlq` check its `targets`, across
`.specfuse/monitoring.overrides.yml.example`, `specfuse/loop/data/monitoring.overrides.yml.example`,
both `derive-monitoring/SKILL.md` copies, both `monitoring.yml.example` copies, and
`tests/test_monitoring_example.py`. Passed first attempt in 436s.

That it cost $0.83 against T03's $7.65 is the whole lesson of this gate: the work T02
skipped was cheap; discovering it through a contract flip was not.

#### T03 — the contract flip (4 attempts total, $7.65 vs $3.00, 1 escalation)

**The gate's only failure, and its only overrun.** Made `targets` required on `dlq`, and
carried the minimal discovery reference-implementation change PLAN.md §10 pre-registered
as a cross-gate coupling.

- **Attempt 1** ($1.85, 378s) — `failed`, class `tests`. `tests`, `coverage`, and
  `monitoring-example-lint` all red. The flip was correct; the tree was not conforming.
- **Attempt 2** ($0.68, 205s) — `no_deliverable_files`. The driver's produces-vs-diff
  guard (specfuse-loop ≥ 0.3.21) refused the pass: the squash diff named only the WU's
  own file and `events.jsonl`. An attempt spent on analysis with no edits, which
  `result-contract.md` closing obligation 4 names explicitly.
- **Attempt 3** ($2.73, 655s) — `failed`, same class and same signature as attempt 1
  (`$ python3 -m unittest discover -s tests -v`). Driver escalated:
  `spinning_signature_repeat`.
- **Re-armed after T03H, attempt 1** ($2.38, 637s) — `passed`.

**The escalation worked as designed.** Three attempts against an identical failure
signature is exactly the shape the spinning guard exists to catch, and the human
diagnosis that followed (`T02's migration was sample-wide, not tree-wide`) was not
available to any of the three sessions from inside the WU. The re-armed attempt passed
first try against an unchanged WU body — the WU was never wrong; its precondition was.

**Also delivered here, and worth naming:** the discovery reference implementation
(test-local, in `tests/test_derive_monitoring_discovery.py`) gained a neutral
`subscriptions` field on the component record, `render_monitoring_yml()` learned to emit
a nested list-of-mappings, and `suggest_checks()` now emits **no** `dlq` check at all for
a message-consuming component with no known subscriptions — rather than fabricating a
target. Bounded deliberately: the real re-keying stays in gate 2.

#### T04 — the `queue-stalled` check type (1 attempt, $1.21 vs $2.50)

**Worked, first attempt.** Added `queue-stalled` to `CHECK_TYPES`, an example block to
both `monitoring.yml.example` copies, the docs table row, and validator tests. Shipped
atomically because it had to: `tests/test_monitoring_example.py` asserts the shipped
example exercises *every* member of `CHECK_TYPES` and that the docs table documents every
member, so enum-only would have gone red instantly. PLAN.md §10 pre-registered that
coupling and the WU was shaped around it — this is a case where the pre-flight paid.

`targets` is required on `queue-stalled` **from birth**, so it never had a permissive
period to migrate out of. The whole expand → migrate → contract dance was needed only for
`dlq`, which shipped permissive in FEAT-2026-0039.

### Failure-class breakdown

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| tests | 2 | $ python3 -m unittest discover -s tests -v |
| null | 1 |  |
| **total** | **3** | — |

All three non-passing attempts are T03's. The `null` row is attempt 2's
`no_deliverable_files` outcome, which the driver classifies before a gate ever runs, so
it carries no failure class or signature.

### Surprises

1. **A WU can pass every criterion it carries and still leave the gate's precondition
   unmet.** T02 is not a hollow pass — it wrote real content into seven files and its
   oracles genuinely went green. It is a *scope* miss: the criteria described a sample,
   the gate needed a sweep. The driver has guards for hollow passes; it has none for this,
   because from the outside a correctly-scoped WU and an under-scoped one look identical.

2. **The expand → migrate → contract ordering was correct and still insufficient.**
   `PLAN.md` reasoned the ordering out explicitly and at length — flip-first is
   unsatisfiable by construction under FEAT-2026-0051's preflight baseline probe, since a
   red base gate halts before any WU dispatches. That reasoning was right. What it did not
   do was put a *tree-wide* assertion on the migrate step, so the ordering was correct
   while its middle step was not. Ordering discipline without a completeness oracle on the
   migrate step buys less than it looks like it buys.

3. **The three `bats` gates cannot run under this session's default sandbox.**
   `mktemp -d` returns `Operation not permitted`, so `sync-scaffold-bats`,
   `init-sh-shim-bats`, and `leak-scan-hook` report 13 failures that are entirely
   environmental. Re-run outside the sandbox, all three are green. Any close in this repo
   that reports a `code`-set result must say which sandbox it ran under, or the numbers
   are not comparable.

4. **`invariant` silently permits `targets` with no required coordinates.** It is absent
   from both `_TARGET_REQUIRED_FIELDS` and `_TARGETLESS_CHECK_TYPES`, so it falls through
   to "permitted, nothing required." That is a defensible default, but it was never a
   decision — no WU criterion names it and the docs table has no `invariant` row. Fixed in
   the docs by this close; flagged to the human in the contract-change list because it is
   a real schema position nobody chose.

---

## Oracles re-run fresh (`close-discipline.md` §1)

Re-run in this session, exit codes read directly. **No producing WU's self-report was
inherited.** All results agree with the WUs' reported outcomes — no disagreement to
escalate.

### The full `code` gate set (10 gates)

| gate | command | exit | result |
|---|---|---|---|
| `tests` | `python3 -m unittest discover -s tests -v` | `0` | `Ran 1473 tests in 45.868s` / `OK (skipped=3)` |
| `lint` | `ruff check specfuse .specfuse/scripts tests scripts` | `0` | `All checks passed!` |
| `security` | `bandit -r specfuse .specfuse/scripts -ll` | `0` | by severity: High 0, Medium 0, Low 75 (the `-ll` filter reports medium+; 0 reported) |
| `coverage` | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | `0` | `TOTAL 3841 225 94%` |
| `leak-scan` | `python3 .specfuse/scripts/leak_scan.py --all` | `0` | `leak-scan: gitleaks 8.30.1` / `leak-scan: clean` |
| `monitoring-example-lint` | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | `0` | `OK — monitoring config is structurally valid (or absent).` |
| `leak-scan-hook` | `bats tests/leak_scan_hook.bats` | `0` | 3 ok / 0 not-ok — **sandbox off** |
| `sync-scaffold-bats` | `bats tests/sync_scaffold.bats` | `0` | 5 ok / 0 not-ok — **sandbox off** |
| `init-sh-shim-bats` | `bats tests/init_sh_shim.bats` | `0` | 5 ok / 0 not-ok — **sandbox off** |
| `init-skills-bats` | `bats tests/init_skills_idempotent.bats` | `0` | 1 ok / 0 not-ok |

The three marked **sandbox off** first ran green-to-red under the session's default
sandbox with `mktemp: mkdtemp failed on <tmpdir>: Operation not permitted` in `setup`,
before any assertion executed. Re-run with the sandbox disabled, all three pass. The
failure is the sandbox, not the tree; recorded here so the number is not read as a
regression.

### Criterion-named oracles

| check | command | exit | result |
|---|---|---|---|
| shipped example validates | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | `0` | structurally valid |
| example copies in sync | `cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example` | `0` | identical |
| overrides copies in sync | `cmp .specfuse/monitoring.overrides.yml.example specfuse/loop/data/monitoring.overrides.yml.example` | `0` | identical |
| plan structurally valid (AC9) | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets` | `0` | `OK — ... is structurally valid.` + the expected cost-delta `WARN` |

The plan lint's `WARN: planned_cost_usd $34.00 differs from sum of WU planned costs
$28.00 (delta 18%, threshold 10%)` is the warning `PLAN.md`'s Notes pre-register, and it
is non-fatal (exit `0`). The delta has *narrowed* since drafting — the Notes predicted
$26.00 and 24%; T03H's insertion moved the sum to $28.00 and the delta to 18%. It
converges the rest of the way when `G1-PLAN` drafts gate 2's WUs.

---

## Cost analysis

### Per work unit

| WU | planned | actual | attempts | delta |
|---|---|---|---|---|
| T01 | $3.00 | $0.74 | 1 | **−$2.26 (−75.3%)** |
| T02 | $2.50 | $1.51 | 1 | −$0.99 (−39.5%) |
| T03H | $2.00 | $0.83 | 1 | −$1.17 (−58.3%) |
| T03 | $3.00 | **$7.65** | 4 | **+$4.65 (+154.8%)** |
| T04 | $2.50 | $1.21 | 1 | −$1.29 (−51.6%) |
| **substantive total** | **$11.00** as drafted / **$13.00** re-planned | **$11.94** | 8 | see below |

T03's $7.65 breaks down as $1.85 + $0.68 + $2.73 (the three escalating attempts) +
$2.38 (the re-armed attempt that passed) = $7.65.

### Gate-level reconciliation

Gate 1 was drafted at **$21.00** — $11.00 substantive (T01 $3.00, T02 $2.50, T03 $3.00,
T04 $2.50) plus $10.00 planning (`close-intermediate` $5.00 + `plan-next` $5.00, the
floor from `planning-discipline.md` §5). Inserting T03H mid-gate re-planned it to
**$23.00**.

**Actual substantive spend: $11.94.**

- Against the **as-drafted $11.00**: **+$0.94, a +8.6% overrun.**
- Against the **re-planned $13.00**: −$1.06, an −8.1% underrun.

**The honest figure is the overrun.** The re-planned $13.00 only looks better because
T03H was added *in response to the failure* — re-basing the plan onto the miss and then
measuring against the re-based plan reports the miss as accuracy. Gate 1 cost more than
it was planned to cost.

**Direction and cause of the miss.** Four of five WUs came in between 39% and 75% under.
The entire overrun — and $3.71 more than the entire overrun — is T03's three wasted
attempts ($5.26 before the re-arm). Had T02 been scoped tree-wide, gate 1's substantive
spend would have been roughly $6.68 against $11.00, a ~39% underrun consistent with every
other WU in the gate. **The gate did not overrun on estimation; it overrun on one
under-scoped acceptance criterion, once, for $5.26.**

**Closing-WU spend is not reconciled here.** `events.jsonl` records attempt costs at
outcome time, so this session cannot read its own attempts (2 prior, this is the third),
and `G1-PLAN` has not run. The gate's full $21.00/$23.00 reconciliation is only
completable by `WU-92` at the terminal close, which should read this section rather than
recompute it. Note for that close: this close's own attempt count is itself a cost signal
worth reporting.

---

## What the loop did NOT verify

Three entries. **This exceeds the two-entry threshold in the close's AC3, so gate sizing
is flagged under *What I'd change*** — with the qualification that all three share one
structural root cause, per the rule promoted from FEAT-2026-0039/G2-CLOSE.

### 1. That `/derive-monitoring` emits 1 component with N targets for a deployable carrying N triggers

*The criterion.* `GATE-02.md`'s definition of done, restated in `PLAN.md`'s gate 2 sketch:
discovery run against a repo whose single deployable carries N triggers emits **1
component with N targets**, not N components.

*Why deferred.* Not a sandbox limit and not an oversight — it is the gate cut. Gate 1
makes the **schema** able to express the right answer; it does not make **discovery** able
to produce it. `discover_components` still keys on trigger attributes and still returns
one component per trigger. `GATE-01.md` states this explicitly under *What this gate
deliberately does NOT prove*, and it is repeated here so the schema's correctness is not
read as the feature's completion.

*Where verification happens.* Gate 2, on the fixture whose single deployable carries N
triggers — which is a gate 2 deliverable precisely because FEAT-2026-0039's Stack A
fixture (one trigger per deployable) structurally could not express the bug.

### 2. That every target coordinate is mechanically extractable

*The criterion.* The originating issue's claim, recorded in `PLAN.md`'s gate 2 sketch:
subscription names come from the trigger attribute, function names from the
`[Function(nameof(...))]` form, and cron plus IANA timezone from named constants on the
timer classes — so discovery can generate target lists and regenerate them as triggers are
added, without asking the operator anything.

*Why deferred.* Cross-repo. The claim is confirmed only against a downstream backend
outside this tree. Gate 1 verifies **nothing** about it: it defines what a target
coordinate *is* and validates its *presence*, and never touches extraction.

*Where verification happens.* Gate 2, and only against a real repo. **Gate 2 must not
treat a fixture it authors as evidence for this claim** — a hand-written fixture confirms
that the extraction code reads the fixture, not that real code is shaped that way. The
arming review should require the evidence source to be named before this is armed.

### 3. That FEAT-2026-0040's adapter interface has a machine-checkable answer to "per component or per target"

*The criterion.* `GATE-01.md`'s definition of done, clause 5.

*Why deferred.* FEAT-2026-0040 does not exist. What gate 1 can verify — and did, by fresh
oracle re-run — is that the schema now *expresses* the distinction and that the validator
*enforces* it per check type. Whether that answer is machine-checkable **by the adapter
interface** cannot be observed against an interface that has not been written. Marking
this clause met on the schema's correctness alone would be the same category error as
reading gate 1 as the feature's completion.

*Where verification happens.* FEAT-2026-0040's own gates. The binding constraint
`PLAN.md` records for it — **0040's fingerprint model must include the target key**, or 20
DLQ targets collapse into one issue and this feature's attribution is lost at the last
step — is the concrete thing to check there, and it is recorded in the roadmap's 0040
blocker note as well as here.

### The shared root cause

All three deferrals are the same shape: **gate 1 is a schema gate, and all three unmet
clauses are about *consumers* of the schema** — discovery (1), a downstream repo (2), an
unbuilt adapter (3). None of them is severable by splitting gate 1 differently; splitting
it three ways produces three gates carrying the same three deferrals. See *What I'd
change* for what this means for the definition of done rather than for the gate size.

---

## Consumer-visible contract changes (`close-discipline.md` §3)

**This list is submitted for human acknowledgment at the gate-1 review-and-arm
checkpoint; it is not self-acknowledged.** Gate 1 halts at `awaiting_review` and gate 2
cannot be armed without a human passing through it — that checkpoint is where the
signature goes. **Item 1 is breaking.** Do not arm gate 2 without reading this table.

| # | surface | change | breaking? | evidence |
|---|---|---|---|---|
| **1** | `dlq` check | **`targets` is now REQUIRED.** Each entry needs `subscription` and `function`. A target-less `dlq` check validated clean before this gate and is now a finding: `'dlq' check requires 'targets' — each target needs 'subscription' and 'function'` | **YES — breaking** | `lint_monitoring.py:230-235`; T03's negative tests in `tests/test_lint_monitoring.py`; the flip is what made T03's first three attempts red against the un-migrated tree |
| 2 | `CHECK_TYPES` | **New check type `queue-stalled`.** Enum grew 5 → 6. Consumers switching exhaustively on check type see a new value | additive to the enum; breaking for exhaustive switches | `lint_monitoring.py:45-47`; docs table row; example block in both `monitoring.yml.example` copies |
| **3** | `error-logs`, `http-5xx` | **`targets` is now REJECTED.** Before gate 1 no `targets` concept existed and the validator ignored unknown check keys, so a check carrying one validated clean. It is now a finding: `'<type>' check must not carry 'targets'` | **YES — a previously-ignored field is now rejected** | `lint_monitoring.py:268, 288-289`; `_TARGETLESS_CHECK_TYPES` |
| 4 | `heartbeat` check | `targets` optional; each entry requires `name`, with `cron` and `timezone` accepted and opaque | additive | `lint_monitoring.py:264`; docs table |
| 5 | `queue-stalled` check | `targets` required **from birth** — no permissive period, so nothing to migrate | additive (new type) | `lint_monitoring.py:236-242, 265` |
| 6 | `invariant` check | `targets` **permitted, with no required coordinates.** A fall-through: `invariant` is in neither `_TARGET_REQUIRED_FIELDS` nor `_TARGETLESS_CHECK_TYPES` | additive — **but never an explicit decision.** Flagged for the human: confirm this is the intended position | `lint_monitoring.py:262-268`; no WU criterion names it |
| 7 | validator finding strings | New finding messages (targets required / must-not-carry / must be a list / must not be empty / missing coordinate). Any consumer parsing findings as text sees new strings | additive | `_check_targets`, `lint_monitoring.py:283-311` |
| 8 | scaffold seed files | `.specfuse/monitoring.yml.example`, `specfuse/loop/data/monitoring.yml.example`, `.specfuse/monitoring.overrides.yml.example`, `specfuse/loop/data/monitoring.overrides.yml.example` all changed content. A project running `init.sh` or `specfuse upgrade` now seeds targets-bearing examples | additive; content-only, no file added, removed, or renamed | `cmp` on both copy pairs → exit `0` (in sync) |
| 9 | `derive-monitoring` skill prose | Both `SKILL.md` copies now show `targets[]` on `dlq` in every worked example. This close additionally corrected the surrounding prose, which still said a single-subscription consumer stays target-less — now invalid | additive; prose only | both copies byte-identical (`cmp` → `0`) |

**Removals and renames: none.** No field, check type, file, CLI flag, or console script
was removed or renamed anywhere in gate 1. Every change above is either an addition or a
tightening of an existing field's validation.

**Not consumer-visible, stated to prevent misreading.** The discovery reference
implementation changed behavior — `suggest_checks()` now emits **no** `dlq` check for a
message-consuming component with no known subscriptions, rather than a target-less one,
and takes targets from a neutral `subscriptions` list — but it lives in
`tests/test_derive_monitoring_discovery.py`, not in the shipped `specfuse` package. There
is no published Python API change. Gate 2's re-key is what makes this behavior real, and
gate 2's skill prose must mirror it.

**No live consumer requires migration.** `PLAN.md` records this as confirmed with the
operator at drafting: the only `monitoring.yml` ever drafted against this schema is
FEAT-2026-0039 gate 2's FU-1 output, which is uncommitted. That is an operator statement,
not something this session verified — but the breaking change in item 1 has no known
deployed config to break. T03's finding message names the fix inline for exactly this
reason: there is no migration document to fall back on.

---

## What I'd change

### Gate sizing is flagged — three deferred entries against a two-entry threshold, one root cause

AC3's threshold fires (3 > 2). Reporting it as required, and then reporting what it
actually means: **this is not an oversized gate.** All three deferrals are consumers of
the schema gate 1 builds, and no cut of gate 1 severs them — splitting it three ways
produces three gates carrying the same three deferrals. Per the rule promoted from
FEAT-2026-0039/G2-CLOSE, mis-attributing a structural limit to gate sizing sends the next
plan to fix the wrong thing.

What *would* have helped is `GATE-01.md`'s definition of done not carrying clause 5
("FEAT-2026-0040's adapter interface has a machine-checkable answer…") at all. That clause
asserts a property of an artifact in a different, unwritten feature. A gate's definition
of done should be decidable by that gate. Recast as "the schema expresses and the
validator enforces the per-component/per-target distinction" it is decidable, and it is
what gate 1 actually proved.

### The migrate step of expand → migrate → contract needs a tree-wide oracle, not a sample

This gate's single failure and single overrun trace to one thing: T02's acceptance
criteria described a sample ("a component with `targets` exists and validates") where the
contract flip needed a sweep ("no target-less `dlq` remains anywhere in the tree"). T03H
— written with the sweep criterion — passed first attempt for $0.83. The three attempts
that discovered the gap cost $5.26.

The fix is mechanical and belongs in the WU-authoring step, not in the executing session:
a migrate WU's acceptance criterion must be a **command whose output is the completeness
proof** — a repo-wide grep or a lint run over every surface, asserted at zero hits — never
an enumeration of surfaces in prose. `LEARNINGS.md` already carries
`[FEAT-2026-0039/T04]` on hand-written fan-out lists reproducing the previous author's
blind spots; this is the same failure at the criterion level rather than the body level,
and it is promoted accordingly.

### Sandbox posture belongs in the close's evidence, not just its result

Three of ten `code` gates fail under the default sandbox for reasons that have nothing to
do with the tree (`mktemp -d` → `Operation not permitted` in `setup`, before any
assertion). A close that reported "7/10 green" would be reporting the sandbox. Every close
in this repo should state which sandbox each gate ran under. Cheap to say, and the
alternative is a fabricated regression.

### `invariant`'s targets position should be decided, not inherited

`invariant` permits `targets` with no required coordinates purely because it is absent
from two lookup tables. Nothing in gate 1 decided that. Gate 2 or the terminal close
should either give `invariant` a required coordinate, add it to `_TARGETLESS_CHECK_TYPES`,
or record the permissive position as deliberate — with a test asserting the chosen
behavior, so the next reader finds a decision instead of a fall-through.

### Residual staleness this close deliberately did not fix

`_check_targets`'s docstring in `specfuse/loop/lint_monitoring.py` still reads "`targets`
itself is required only for `dlq`". T04 then made it required on `queue-stalled` too, so
the docstring is wrong. Left untouched on purpose: this is a close WU, and a close editing
shipped source is the pattern that makes closes untrustworthy. `docs/concepts/monitoring-schema.md`
was rewritten by this close to state the matrix authoritatively and no longer defers to
that docstring, so no reader is routed to the wrong text. **Fix it in gate 2's first
WU** — it is a two-word correction and it should not survive the feature.

### Smaller things

- **T03's WU body was never wrong.** It passed first attempt on re-arm with no edits to
  its criteria. Worth recording against the reflex to rewrite an escalated WU: the
  escalation was about a precondition, and rewriting the WU would have been three more
  wasted attempts.
- **The `no_deliverable_files` outcome earned its place.** T03 attempt 2 spent $0.68 on
  analysis with no edits, and the driver's produces-vs-diff guard refused it rather than
  letting it read as a pass.
- **`PLAN.md`'s §10 pre-flight paid for itself twice** — the `_miniyaml` probe (no parser
  WU appeared) and the `CHECK_TYPES` exhaustiveness coupling (T04 shipped atomically and
  passed first try). It did not catch the T02 scope gap, because §10 enumerates *test*
  couplings and this was a *criterion-completeness* gap. Different check, worth adding.
