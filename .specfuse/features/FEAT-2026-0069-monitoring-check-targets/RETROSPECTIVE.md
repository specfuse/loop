# FEAT-2026-0069 — Retrospective

**Terminal close.** This file now covers the **full feature arc**, both gates.

It was written in two passes and the two are kept distinct on purpose. Everything under
*Gate 1* was written by `G1-CLOSE-INTERMEDIATE` at the non-terminal close, when gate 2 was
undrafted; it is left as it was written, because a close's record of what it knew at the
time is worth more than a tidied one. Everything from *Gate 2* onward was written by
`G2-CLOSE`, the terminal close, and the feature-level sections — cost, planning floor,
deferred verification, contract changes — are that pass's and supersede their gate-1-scoped
counterparts rather than repeating them.

**Verdict: `met`** — upgraded from `met_locally` on 2026-07-26, post-close, after **FU-1 and
FU-3 were discharged on real evidence**. See *FU-1 and FU-3 — DISCHARGED* under the hedged
follow-up record: `/derive-monitoring` was run against the downstream .NET backend, the repo
that originated issue #245, and returned **2 components from 33 trigger registrations** with
every target coordinate extracted mechanically and a draft that validates clean.

FU-2 is **not** discharged and is not this feature's to discharge — it asserts about
FEAT-2026-0040's adapter interface, an artifact that does not exist. It is 0040's
acceptance criterion and must not be re-listed on a future FEAT-2026-0069 surface.

The consumer-visible contract-change list was acknowledged by the operator at the terminal
review checkpoint; the upgrade to `met` is what carries that signature.

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

### Gate 1 — oracles re-run fresh (`close-discipline.md` §1)

> Written at the gate-1 close. The terminal close's own fresh re-run is
> *Oracles re-run fresh — the terminal close* below, and it is the one that decides the
> feature.

Re-run in that session, exit codes read directly. **No producing WU's self-report was
inherited.** All results agree with the WUs' reported outcomes — no disagreement to
escalate.

#### The full `code` gate set (10 gates)

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

#### Criterion-named oracles

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

### Gate 1 — cost analysis

> Written at the gate-1 close, which could not read its own attempts or `G1-PLAN`'s. The
> feature-level `## Cost analysis` below completes it with the figures that were not
> available then; this section is left as written.

#### Per work unit

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

#### Gate-level reconciliation

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

### Gate 1 — what the loop did NOT verify

> Written at the gate-1 close. Entry 1 below was **discharged by gate 2** and is no longer
> deferred; entries 2 and 3 carry forward. The feature-level
> `## What the loop did NOT verify` is the current list.

Three entries. **This exceeds the two-entry threshold in the close's AC3, so gate sizing
is flagged under *What I'd change*** — with the qualification that all three share one
structural root cause, per the rule promoted from FEAT-2026-0039/G2-CLOSE.

#### 1. That `/derive-monitoring` emits 1 component with N targets for a deployable carrying N triggers

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

#### 2. That every target coordinate is mechanically extractable

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

#### 3. That FEAT-2026-0040's adapter interface has a machine-checkable answer to "per component or per target"

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

#### The shared root cause

All three deferrals are the same shape: **gate 1 is a schema gate, and all three unmet
clauses are about *consumers* of the schema** — discovery (1), a downstream repo (2), an
unbuilt adapter (3). None of them is severable by splitting gate 1 differently; splitting
it three ways produces three gates carrying the same three deferrals. See *What I'd
change* for what this means for the definition of done rather than for the gate size.

---

### Gate 1 — consumer-visible contract changes (`close-discipline.md` §3)

> Written at the gate-1 close and **acknowledged at the gate-1 arming checkpoint**
> (`GATE-02-REVIEW.md` § 8 *Arming checklist*, `GATE-01.md` § *Reflection notes*). Carried
> forward verbatim by the terminal close, which adds gate 2's rows and re-submits the whole
> list; **item 6 is superseded** — see `## Consumer-visible contract changes` below.

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

### Gate 1 — what I'd change

> Written at the gate-1 close. Four of its six items were **routed into gate 2 and are now
> done** (`invariant`'s position → `T05`; the stale docstring → `T05`). The feature-level
> `## What I'd change` below is the terminal pass and does not repeat these.

#### Gate sizing is flagged — three deferred entries against a two-entry threshold, one root cause

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

#### The migrate step of expand → migrate → contract needs a tree-wide oracle, not a sample

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

#### Sandbox posture belongs in the close's evidence, not just its result

Three of ten `code` gates fail under the default sandbox for reasons that have nothing to
do with the tree (`mktemp -d` → `Operation not permitted` in `setup`, before any
assertion). A close that reported "7/10 green" would be reporting the sandbox. Every close
in this repo should state which sandbox each gate ran under. Cheap to say, and the
alternative is a fabricated regression.

#### `invariant`'s targets position should be decided, not inherited

`invariant` permits `targets` with no required coordinates purely because it is absent
from two lookup tables. Nothing in gate 1 decided that. Gate 2 or the terminal close
should either give `invariant` a required coordinate, add it to `_TARGETLESS_CHECK_TYPES`,
or record the permissive position as deliberate — with a test asserting the chosen
behavior, so the next reader finds a decision instead of a fall-through.

#### Residual staleness this close deliberately did not fix

`_check_targets`'s docstring in `specfuse/loop/lint_monitoring.py` still reads "`targets`
itself is required only for `dlq`". T04 then made it required on `queue-stalled` too, so
the docstring is wrong. Left untouched on purpose: this is a close WU, and a close editing
shipped source is the pattern that makes closes untrustworthy. `docs/concepts/monitoring-schema.md`
was rewritten by this close to state the matrix authoritatively and no longer defers to
that docstring, so no reader is routed to the wrong text. **Fix it in gate 2's first
WU** — it is a two-word correction and it should not survive the feature.

#### Smaller things

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

---

## Gate 2 — discovery emits one component with N targets, not N components

**Outcome: all four substantive work units `done`, each on its first attempt, no
escalations, no re-arms, $4.43 against $12.00 planned.** T05, T06, T07, T08. Gate 2's
definition of done is met and was re-verified fresh in this session.

**What shipped.** `discover_components` was re-keyed: a component now exists because a
*deployment* artifact names it, and a trigger registration is evidence of that deployable's
type and the source of its target list — never a component in its own right. The emitted
record carries `subscriptions` and `schedules`; `http_serving` and `message_consuming` are
derived from matched triggers instead of hand-declared. `suggest_checks` fans `schedules`
into per-schedule `heartbeat` targets. A third fixture stack — one deployable, 3
subscriptions, 2 schedules — makes the definition of done a test that either passes or does
not. And `invariant`'s accidental permissive `targets` fall-through became a decision:
rejected, because `fingerprint_by` is already that check type's enumeration key.

### Gate-level summary

| | |
|---|---|
| substantive WUs | 4 (T05, T06, T07, T08) — all as drafted by `G1-PLAN`, all armed unmodified |
| attempts | 4 across 4 WUs (4 passing, 0 non-passing) |
| human escalations | 0 |
| re-arms | 0 |
| substantive wall clock | 1707s ≈ 28.5 min |
| substantive spend | **$4.43** against $12.00 planned (**−63.1%**) |
| `_TARGETLESS_CHECK_TYPES` | 2 → 3 (`invariant` added) |
| fixture stacks in the discovery module | 2 → 3 (Stack C: 1 deployable, 3 subscriptions, 2 schedules) |

**The contrast with gate 1 is the finding of this gate and it is not luck.** Gate 1: 5 WUs,
8 attempts, 3 failures, 1 escalation. Gate 2: 4 WUs, 4 attempts, 0 failures. The difference
is `G1-PLAN`'s §4 runtime probe — it applied the re-key locally, ran the full 1473-test
oracle twice, and pasted the resulting four-failure list verbatim into `T06`'s body. `T06`
therefore did not discover its own breakage attempt by attempt; it was handed the list. See
*Planning-floor revision* — this is the direct evidence that the expensive `plan-next` was
not waste.

### Per-WU outcome

#### T05 — `invariant`'s `targets` position, decided (1 attempt, $0.86 vs $2.00)

**Worked, first attempt.** Added `invariant` to `_TARGETLESS_CHECK_TYPES`, so an `invariant`
check carrying `targets` is now the finding `'invariant' check must not carry 'targets'`.
Corrected `_check_targets`'s docstring, which T04 had made wrong. Added the `invariant` row
to `docs/concepts/monitoring-schema.md`'s matrix.

This is gate 1's *Residual staleness this close deliberately did not fix* item, routed here
on purpose because a close editing shipped source is the pattern that makes closes
untrustworthy. Both halves landed in one $0.86 WU. The reasoning behind *reject* rather than
*permit* is the one `PLAN.md`'s existing-mechanism search already recorded: `targets` is the
generalization of `fingerprint_by`, and `invariant` is the one check type that already
carries `fingerprint_by` as required — permitting both gives one check two competing
enumeration keys with nothing in the schema saying which wins, and FEAT-2026-0040's
fingerprint model would inherit the ambiguity.

**The cheapest moment was taken.** Gate 1's permissive fall-through had never been merged or
released, so rejecting now is a decision rather than a breaking change. The reverse ordering
stays available: a rejected field can be permitted later without breaking anyone.

**Nothing failed.**

#### T06 — the re-key (1 attempt, $1.25 vs $4.00)

**The axis-defining work unit, and it passed first attempt against a $4.00 estimate — the
WU `G1-PLAN` judged most likely to need a second pass.** `discover_components` now matches
candidates on `deployment_markers` bounded by a `scope_prefix`, consumes a sibling
`patterns["triggers"]` table within that scope, and derives `http_serving` /
`message_consuming` from what matched. Both existing fixture stacks were migrated to the new
contract. `_with_subscriptions` — T03's deliberate stand-in for the evidence gate 2 derives —
was deleted along with all four call sites.

**AC6 is the part worth remembering.** The probe found that two of gate 1's
provider-neutrality boundary tests passed on an *empty* component list (`len([]) == len([])`,
`sorted([]) == sorted([])`, two empty sets are disjoint). They were satisfiable by a
discovery function that returns nothing. T06 added non-emptiness assertions as a rider. That
defect was pre-existing, invisible to every gate, and found only because someone ran the
change and read the *passes* as carefully as the failures.

**Nothing failed.**

#### T07 — the N-trigger fixture and per-schedule heartbeat targets (1 attempt, $1.29 vs $3.50)

**Gate 2's falsifiable core.** `_STACK_C_PATTERNS` / `_STACK_C_TREE` declare one deployable
(`acme-functions-host`) whose scope holds 3 `subscription` triggers and 2 `schedule`
triggers. The oracle asserts all four clauses at once: one component; the `dlq` check carries
exactly 3 `{subscription, function}` targets; the `heartbeat` check carries exactly 2
`{name, cron, timezone}` targets; and the rendered YAML passes `validate_monitoring` with
zero findings. `suggest_checks` gained the `schedules` fan-out that makes the third clause
possible — before it, a multi-schedule host still got one target-less `heartbeat`, so a
single silent timer among several stayed invisible. That is the defect `PLAN.md` opens with,
and this is where it closes.

**The cardinality is the point.** Both trigger kinds carry cardinality > 1, so no per-target
assertion can be satisfied by accident — the rule
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` promoted after FEAT-2026-0039's one-trigger-per-deployable
fixture structurally could not express this bug class.

**What it does not prove is written into the fixture itself**, per AC8: it is evidence the
algorithm fans a trigger table into a target list, not evidence that real repositories are
shaped so a trigger table can be built without asking the operator. That distinction is the
first entry in *What the loop did NOT verify*.

**Nothing failed.**

#### T08 — the skill's method prose (1 attempt, $1.03 vs $2.50)

**Worked, first attempt.** Step 1, the Seams table, and `PROMPT.md` now describe
deployment-keyed discovery: a component is a deployable, a trigger is evidence of its type
and the source of its target list, and the operative reason is stated — the role name a
telemetry backend reports is per-process, so N components would each carry the same
role-name-keyed query and produce N duplicate findings per exception. Canonical copy in
`plugins/specfuse/skills/` edited first, then propagated by `scripts/sync-scaffold.sh`; both
copies byte-identical.

**Step 3's question list stayed at five, deliberately.** Target lists are derived from
trigger evidence and are never an operator question; a coordinate discovery cannot name means
the check is omitted rather than asked about. Asking an operator to enumerate subscriptions
would be a Forbidden question by the skill's own definition — which is the property that
makes the whole feature worth having.

**Nothing failed.**

### Failure-class breakdown

| failure_class | non-passed attempts |
|---|---|
| — | 0 |
| **total** | **0** |

Gate 2 has no failure-class table worth the name. Recorded as a zero rather than omitted,
because the zero is the evidence for the planning-floor argument below.

### Surprises

1. **The gate that was supposed to be hard was the cheap one.** `T06` was the re-key —
   a change to the `patterns` table contract, flagged in `PLAN.md`'s sketch as
   *"treat it as such"*, given the gate's largest estimate and named in `GATE-02.md` as
   the WU most likely to need a re-attempt. It passed first try for $1.25. The reason is
   entirely traceable: it was handed an enumerated failure list instead of discovering one.

2. **A grep-based acceptance criterion matched a substring and reported the wrong answer.**
   `T06`'s AC7 asserts `grep -c "_with_subscriptions" tests/test_derive_monitoring_discovery.py`
   returns `0`. Re-run fresh in this close it returns **`1`** — and the deliverable is
   nonetheless fully met. The single hit is inside the *method name*
   `test_message_consuming_with_subscriptions_emits_one_target_per_entry`, added by `T07`
   afterwards. The helper itself is gone: `grep -n "def _with_subscriptions"` and a
   word-boundary search for call sites both return nothing. A criterion written as a bare
   substring grep, with no word boundary and no anchor, is satisfiable and falsifiable by
   unrelated edits in a later WU. See *What I'd change*.

3. **Two boundary tests could pass on an empty result and no gate could see it.** Covered
   under T06 above; repeated here because the shape generalizes beyond this feature. A test
   asserting a *relation* between two derived collections (equal lengths, disjoint sets,
   stable ordering) is vacuously true on empty inputs. Every such test needs a
   non-emptiness assertion or it is guarding nothing.

---

## Oracles re-run fresh — the terminal close (`close-discipline.md` §1)

Every command below was run **in this session**, exit codes read directly. **No producing
WU's self-report was inherited.** Sandbox posture is stated per gate, per
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`.

### The four criterion-named gate-2 oracles

Run as one scoped command:

```
python3 -m unittest \
  tests.test_lint_monitoring.TestInvariantTargetsRejected \
  tests.test_derive_monitoring_discovery.TestDeploymentKeyedDiscovery \
  tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers \
  tests.test_derive_monitoring_skill_registration.TestStep1IsDeploymentKeyed -v
→ Ran 5 tests ... OK          exit 0
```

| WU | oracle | exit | what it proves |
|---|---|---|---|
| `T05` | `TestInvariantTargetsRejected` | `0` | 2 tests — `invariant` + `targets` is a finding; `invariant` without `targets` and with `fingerprint_by` still validates clean (the §2 satisfiability check) |
| `T06` | `TestDeploymentKeyedDiscovery` | `0` | one deployment artifact + two in-scope triggers → **1** component |
| `T07` | `TestOneDeployableManyTriggers` | `0` | **this is the definition of done.** 1 deployable, 3 subscriptions, 2 schedules → 1 component, 3 `dlq` targets, 2 `heartbeat` targets, zero validator findings on the rendered YAML |
| `T08` | `TestStep1IsDeploymentKeyed` | `0` | Step 1 names deployment evidence as the key and names both `subscriptions` and `schedules` as record fields |

**Gate 2's definition of done is asserted on `T07`'s oracle, re-run fresh here, exit `0`.**
It was not inherited from `T07`'s RESULT block.

### The full `code` gate set (10 gates)

| gate | command | exit | result | sandbox |
|---|---|---|---|---|
| `tests` | `python3 -m unittest discover -s tests -v` | `0` | `Ran 1480 tests in 57.732s` / `OK (skipped=3)` | on |
| `lint` | `ruff check specfuse .specfuse/scripts tests scripts` | `0` | `All checks passed!` | on |
| `security` | `bandit -r specfuse .specfuse/scripts -ll` | `0` | High 0, Medium 0, Low 75 (the `-ll` filter reports medium+; 0 reported) | on |
| `coverage` | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | `0` | `TOTAL 3841 225 94%` | on |
| `leak-scan` | `python3 .specfuse/scripts/leak_scan.py --all` | `0` | `leak-scan: gitleaks 8.30.1` / `leak-scan: clean` | on |
| `monitoring-example-lint` | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | `0` | `OK — monitoring config is structurally valid (or absent).` | on |
| `init-skills-bats` | `bats tests/init_skills_idempotent.bats` | `0` | 1 ok / 0 not-ok | on |
| `leak-scan-hook` | `bats tests/leak_scan_hook.bats` | `0` | 3 ok / 0 not-ok | **off** |
| `sync-scaffold-bats` | `bats tests/sync_scaffold.bats` | `0` | 5 ok / 0 not-ok | **off** |
| `init-sh-shim-bats` | `bats tests/init_sh_shim.bats` | `0` | 5 ok / 0 not-ok | **off** |

**10 of 10 green.** The three marked **off** were run first under the session's default
sandbox and failed identically to gate 1's close, in `setup`, before any assertion:

```
mktemp: mkdtemp failed on /var/folders/.../tmp.U82KlqHImb: Operation not permitted
```

Re-run with the sandbox disabled, all three pass. This is the second consecutive close in
this feature to hit it and the rule from
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` held: reporting 7/10 would have manufactured a
regression. The test count rose 1473 → 1480 across gate 2 (+7).

### Regeneration into a clean directory (AC5's stale-artifact clause)

The feature's one generated artifact is the vendored skill tree: `.specfuse/skills/` is a
byte-for-byte copy of `plugins/specfuse/skills/` produced by `scripts/sync-scaffold.sh`, and
`T08` edited the canonical copy. Asserting `cmp` on the committed pair would pass against
stale output, so the pair was regenerated from scratch:

```
CLEAN=$(mktemp -d)
cp -R .specfuse plugins "$CLEAN/"; cp scripts/sync-scaffold.sh "$CLEAN/scripts/"
rm -rf "$CLEAN/.specfuse/skills" "$CLEAN/specfuse/loop/data"   # wipe the generated trees
mkdir -p "$CLEAN/specfuse/loop/data"
REPO_ROOT="$CLEAN" SPECFUSE_CORE=/nonexistent "$CLEAN/scripts/sync-scaffold.sh"
→ 25 file(s) updated.   exit 0

diff -r "$CLEAN/.specfuse/skills" .specfuse/skills          → exit 0  (identical)
diff -r "$CLEAN/specfuse/loop/data" specfuse/loop/data      → only `docs/` absent
```

The generated trees were **deleted before regeneration**, so nothing could be inherited. The
regenerated output is byte-identical to what is committed for every path the generator owns.
The single `diff -r` difference is `specfuse/loop/data/docs/`, which `sync-scaffold.sh` does
not manage at all — it mirrors the repo's `docs/` tree, which the clean room deliberately did
not contain, and it is guarded independently by `tests/test_scaffold_data_in_sync.py:78`
under the (green) `tests` gate. Not drift.

### Criterion-named symbol and artifact checks

| check | command | result |
|---|---|---|
| `T05` AC2 | `python3 -c "from specfuse.loop.lint_monitoring import _TARGETLESS_CHECK_TYPES as t; assert 'invariant' in t"` | exit `0`; set is `['error-logs', 'http-5xx', 'invariant']` |
| `T05` AC5 | `grep -c "required only for" specfuse/loop/lint_monitoring.py` | `0` — stale docstring phrase gone |
| `T06` AC2 | `grep -c "evidence_markers" tests/test_derive_monitoring_discovery.py` | `0` — old contract gone |
| `T06` AC7 | `grep -c "_with_subscriptions" tests/test_derive_monitoring_discovery.py` | **`1`, not `0`** — see below |
| `T07` symbol check | `grep -c "^_STACK_C_PATTERNS\|^_STACK_C_TREE" tests/…_discovery.py` | `2` |
| `T08` AC7 | `cmp` on both `SKILL.md` and `PROMPT.md` copy pairs | exit `0` — byte-identical |
| gate 1 carry-forward | `cmp` on both `monitoring*.yml.example` copy pairs | exit `0` — byte-identical |

**The one disagreement between a fresh re-run and a WU's stated criterion, and why it is not
an escalation.** `T06`'s AC7 asserts the `_with_subscriptions` grep returns `0`; it returns
`1`. Read directly, the hit is:

```
760:    def test_message_consuming_with_subscriptions_emits_one_target_per_entry(self):
```

— a substring inside a **test method name** that `T07` added after `T06` ran. The
deliverable AC7 actually names is met and was confirmed by two narrower commands:
`grep -n "def _with_subscriptions"` → no match, and
`grep -nE "(^|[^a-zA-Z0-9])_with_subscriptions\("` (word-boundary call sites) → no match.
The helper is deleted and has no callers. **The criterion's wording is wrong, not the
work** — recorded as a finding under *What I'd change* and promoted to `LEARNINGS.md`,
because the same criterion could equally have returned `0` while the helper survived under
a different name.

### Plan lint (AC11)

```
python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets
```

First run in this session exited **`1`**:

```
ERROR: WU-92-gate-2-close.md: close-type WU missing or invalid 'verdict' frontmatter
       (must be one of: met, met_locally, partially_met, not_met).
```

That is the lint doing its job — a close-type WU in a non-terminal status must carry the
verdict it is claiming (`specfuse/loop/lint_plan.py:525-538`). `verdict: met_locally` was
written into `WU-92`'s frontmatter and the lint re-run exits `0`, carrying the expected
non-fatal cost-delta `WARN` described under *Cost analysis*.

---

## Cost analysis

Actuals are read from `events.jsonl` (`attempt_outcome` payloads, summed per WU). Every
figure below is spend the loop actually recorded; nothing is estimated.

### Per work unit, whole feature

| gate | WU | type | planned | actual | attempts | delta |
|---|---|---|---|---|---|---|
| 1 | T01 | implementation | $3.00 | $0.74 | 1 | −$2.26 (−75.3%) |
| 1 | T02 | implementation | $2.50 | $1.51 | 1 | −$0.99 (−39.5%) |
| 1 | T03H | implementation | $2.00 | $0.83 | 1 | −$1.17 (−58.3%) |
| 1 | T03 | implementation | $3.00 | **$7.65** | 4 | **+$4.65 (+154.8%)** |
| 1 | T04 | implementation | $2.50 | $1.21 | 1 | −$1.29 (−51.6%) |
| 1 | G1-CLOSE-INTERMEDIATE | close-intermediate | $5.00 | **$10.01** | 2 | **+$5.01 (+100.3%)** |
| 1 | G1-PLAN | plan-next | $5.00 | **$16.44** | 2 | **+$11.44 (+228.7%)** |
| 2 | T05 | implementation | $2.00 | $0.86 | 1 | −$1.14 (−57.0%) |
| 2 | T06 | implementation | $4.00 | $1.25 | 1 | −$2.75 (−68.8%) |
| 2 | T07 | implementation | $3.50 | $1.29 | 1 | −$2.21 (−63.1%) |
| 2 | T08 | implementation | $2.50 | $1.03 | 1 | −$1.47 (−58.8%) |
| 2 | G2-CLOSE | close | $8.00 | *not readable in-session* | 1 | see below |
| | **total excluding `G2-CLOSE`** | | **$35.00** | **$42.82** | **16** | **+$7.82 (+22.3%)** |

`G2-CLOSE`'s own cost cannot appear here: `events.jsonl` records an attempt's cost at
outcome time, so this session cannot read its own attempt. Gate 1's close recorded the same
limitation and it is structural, not an omission.

### The variance split by cause, not by gate

This is the whole point of the section. A single blended percentage over $35.00 → $42.82
(+22.3%) hides three completely different stories.

| cohort | planned | actual | delta | attempts | non-passing |
|---|---|---|---|---|---|
| **implementation WUs, all 9** | $25.00 (as re-planned) / $23.00 (as drafted) | **$16.37** | **−$8.63 (−34.5%)** / −$6.63 (−28.8%) | 12 | 3 |
| **implementation WUs excluding T03's failure** | — | **$11.11** | — | 9 | 0 |
| **the two gate-1 closing WUs** | $10.00 | **$26.45** | **+$16.45 (+164.5%)** | 4 | 2 |

Three separate findings, and they do not average:

1. **The estimating was good, and it got better.** All nine implementation WUs came in
   under, ten of twelve attempts passed, and the gate-2 four came in 63% under as a block.
   Nothing here needs re-calibration.
2. **One under-scoped acceptance criterion cost $5.26.** T03's three pre-escalation attempts
   are the entire implementation-side overrun and then some. Priced against the $0.83 the
   hygiene WU cost once it was written correctly, that is a 6.3× premium for discovering a
   migrate-step gap through a contract flip instead of through a criterion.
3. **A rules-supplied constant cost $16.45**, which is more than three times the T03 defect
   and more than the entire gate-2 substantive spend. It is not an estimating error by any
   author; §5 told them what to write. That gets its own section below.

### Reconciliation against `PLAN.md`'s $34.00

**`PLAN.md`'s $34.00 is reconciled against as drafted, not re-baselined**, per
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`'s rule against measuring a gate against a plan
re-based onto its own failure. Neither number was adjusted to make them meet.

| figure | value |
|---|---|
| `PLAN.md` `planned_cost_usd`, as drafted and never revised | **$34.00** |
| sum of all twelve WUs' `planned_cost_usd` | **$43.00** |
| actual spend, gates 1 + 2, excluding `G2-CLOSE` | **$42.82** |
| — gate 1 ($11.94 substantive + $26.45 closing) | $38.39 |
| — gate 2 substantive | $4.43 |

- **Against `PLAN.md`'s $34.00: +$8.82, a +25.9% overrun** — and `G2-CLOSE` has still to
  land on top of it. At its $8.00 estimate the feature closes near **$50.82, +49%**.
- **Against the $43.00 WU sum: +$7.82 on $35.00 of comparable line items, +22.3%.**

**The honest reading is the +25.9%, and it is not what it looks like.** Gate 1 alone cost
$38.39 — it exceeded the whole-feature plan before gate 2 dispatched a single WU. Subtract
the two closing WUs' $16.45 overrun and the feature lands at $26.37 against $34.00, a 22%
*underrun*. The feature did not overrun because anyone mis-judged the work.

### The lint cost-delta WARN

```
WARN: PLAN.md: planned_cost_usd $34.00 differs from sum of WU planned costs $43.00
      (delta 26%, threshold 10%). Review estimates.
```

Non-fatal, exit `0`, and **left standing deliberately** — for the third and final time in
this feature's history. `PLAN.md`'s Notes predicted the delta would converge once `G1-PLAN`
drafted gate 2 ($26.00 sum, 24% under). It did not: it crossed zero and reopened on the
other side ($40.00, then $43.00 after `GATE-02.md` raised `G2-CLOSE` $5.00 → $8.00 — now
26% *over*). Both the wrong prediction and the figures it was wrong about are left in
`PLAN.md` rather than tidied, because a plan edited to agree with its outcome records
nothing. The WARN is the signal working.

---

## Planning-floor revision

**This section is a deliverable, not an observation.** `planning-discipline.md` §5 sets a
flat **$5.00** floor for `plan-next` / `close` / `close-intermediate`. This is the third
feature to pay for that constant, and FEAT-2026-0049 produced the identical evidence and
had it recorded as *provenance for* the floor rather than as a reason to move it. That is
the failure this section exists to break.

### This feature's own per-type actuals

| WU type | this feature | prior data | §5 floor | ratio to floor |
|---|---|---|---|---|
| `plan-next` | **$16.44** (`G1-PLAN`, 2 attempts) | $15.65 (FEAT-2026-0049) | $5.00 | **3.3×** |
| `close-intermediate` | **$10.01** (`G1-CLOSE-INTERMEDIATE`, 2 attempts) | $5.67 (FEAT-2026-0049) | $5.00 | **2.0×** |
| `close` | drafted at **$8.00** (`GATE-02.md`'s prospective correction); actual not readable in-session | — | $5.00 (raised at arming) | — |
| `implementation` | $16.37 across 9 WUs vs $25.00 planned | — | n/a | **0.65×** |

### Do these support, weaken, or refine the proposed replacements?

`[FEAT-2026-0069/GATE-1-ARM]` in `.specfuse/LEARNINGS.md` proposes **$12.00** for
`plan-next` and **$8.00** for `close` / `close-intermediate`.

**They support both figures, and they refine the reasoning behind them in one way that
matters.**

- **`plan-next` at $12.00: supported, and it is still a floor rather than an expectation.**
  Two independent observations now sit at $15.65 and $16.44 — the proposal is *below* both,
  which is correct for a floor but means a `plan-next` drafted at $12.00 should still be
  expected to run over. Two data points do not justify $16.00; they comfortably justify
  abandoning $5.00.
- **`close` / `close-intermediate` at $8.00: supported.** $5.67 and $10.01 straddle it.
  `GATE-02.md` applied it prospectively to `G2-CLOSE` at arming, which is the first time any
  surface in this repo has drafted a closing WU against the corrected figure.
- **The refinement: both overruns are two-attempt WUs, and the first attempt of each was
  `closing_deliverable_missing`.** `G1-CLOSE-INTERMEDIATE` spent $4.45 then $5.57;
  `G1-PLAN` spent $8.61 then $7.83. In both cases roughly half the spend went to an attempt
  the driver refused. So the floor is not only mis-priced for the *work* — it is priced as
  if closing WUs pass first try, and in this feature neither did. A floor that assumed one
  retry would have landed near the truth from single-attempt reasoning.
- **The counter-evidence, stated because it changes what the revision means.** The
  $16.44 `plan-next` was not waste. Its §4 runtime probe applied the re-key locally, ran
  the full oracle twice, and enumerated four failures into `T06`'s body verbatim. Gate 2
  then ran **4 WUs, 4 attempts, 0 failures, $4.43 against $12.00** — against gate 1's 5 WUs,
  8 attempts, 3 failures. The expensive planning bought the cheap gate. **The revision
  should raise the floor because planning costs that much and is worth it, not because
  planning WUs are wasteful.** A revision framed as "planning is overspending" would invite
  the wrong correction — cheaper probes — and cost the next feature a gate.

### The concrete next action

**Issue #260** — *"planning-discipline §5's flat $5.00 planning-WU floor is wrong for
plan-next — three features have now paid for it"* — is **open** and is the tracking artifact.
It was filed at gate-1 arming. Two surfaces must change and both are named:

1. **`.specfuse/rules/planning-discipline.md` §5** — replace the flat $5.00 with the
   per-type floors ($12.00 `plan-next`, $8.00 `close` / `close-intermediate`), and add the
   retry observation above: the floor is for a WU that passes first try, which closing WUs
   in this feature did not.
2. **`.specfuse/templates/WU.template.md:31-32`** — the authoring comment quotes the flat
   $5.00 verbatim (*"draft `planned_cost_usd` at a **floor of $5.00**"*). It is the surface
   a drafting agent actually reads, so a rule change that misses it changes nothing in
   practice. Both this file and its `specfuse/loop/data/` packaged copy are involved; the
   copy is produced by `scripts/sync-scaffold.sh` and guarded by
   `tests/test_scaffold_data_in_sync.py`.

**This close does not make those edits.** Both files are production surfaces of the
methodology scaffold and `WU-92`'s *Do not touch* is explicit that this WU closes rather
than implements — a close editing shipped rules is the pattern that makes closes
untrustworthy, which is the same reasoning that routed gate 1's `invariant` fix to `T05`
instead of doing it inline. **Recommended disposition: #260 becomes a small standalone
feature or a `fix/` branch before the next multi-gate feature is drafted**, because every
feature drafted against the current §5 inherits the mis-priced budget on day one.

**A third dataset now exists and it is recorded where it will be found.** The
`[FEAT-2026-0069/G2-CLOSE]` LEARNINGS entry carries these figures, the retry observation,
and the counter-evidence, so #260 does not have to be re-derived from `events.jsonl`.

---

## What the loop did NOT verify

**Three entries.** Gate 1 had three; **entry 1 was discharged by gate 2** and two carry
forward, joined by one new entry that gate 2's shape made visible. The count is unchanged at
3, which exceeds the two-entry threshold, so gate sizing is flagged under *What I'd change* —
where the finding is again that none of the three is severable by cutting gates differently.

### Discharged since gate 1

**That `/derive-monitoring` emits 1 component with N targets for a deployable carrying N
triggers.** Gate 1's entry 1. **Now verified**, by
`tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers`, re-run fresh in this
session at exit `0`, on a fixture carrying 3 subscriptions and 2 schedules. Removed from the
deferred list.

### 1. That every target coordinate is mechanically extractable from real code

*The criterion.* The originating issue's claim, carried in `PLAN.md`'s gate 2 sketch:
subscription names come from the trigger attribute, function names from the
`[Function(nameof(...))]` form, and cron plus IANA timezone from named constants on the timer
classes — so discovery can generate target lists, and regenerate them as triggers are added,
without asking the operator anything.

*Why deferred.* **Cross-repo, and deliberately not faked.** The claim is confirmed only
against a downstream backend outside this tree. `T07` authored a fixture inside gate 2 and
that fixture is evidence the *algorithm* fans a trigger table into a target list — it is not
evidence that real repositories are shaped so a trigger table can be built mechanically.
`T07`'s AC8 required the fixture's own comment to say which half it proves, precisely so a
later reader cannot mistake one for the other. `GATE-02-REVIEW.md` open question 5 asked
whether to attempt this inside gate 2 and the answer at arming was no.

*Where verification happens.* **An operator running `/derive-monitoring` against a real
multi-trigger repo, post-merge** — the same operator step FEAT-2026-0039 recorded for its own
skill. The honest alternative, if it is to be verified inside the loop, is a follow-up unit
against a *named* real repo, never a richer fixture.

### 2. That FEAT-2026-0040's adapter interface has a machine-checkable answer to "per component or per target"

*The criterion.* `GATE-01.md`'s definition of done, clause 5.

*Why deferred.* FEAT-2026-0040 does not exist. What this feature verifies — by fresh oracle
re-run, twice over now — is that the schema *expresses* the distinction, that the validator
*enforces* it per check type, and that discovery *produces* it. Whether that answer is
machine-checkable **by the adapter interface** cannot be observed against an interface nobody
has written.

*Where verification happens.* FEAT-2026-0040's own gates. The concrete thing to check there
is the binding constraint restated below.

### 3. That the `derive-monitoring` *skill*, executed end-to-end by an agent, produces this result

*The criterion.* `GATE-02.md`'s definition of done as literally worded: *"`/derive-monitoring`,
run against a repo whose single deployable carries N triggers, emits 1 component with N
targets."*

*Why deferred.* The oracle verifies the algorithm and the prose separately, not the
composition. `discover_components` / `suggest_checks` / `render_monitoring_yml` are a
**test-local reference implementation** — there is no `specfuse/loop/` module for them, by
design — and the skill is prose that points at that module. `T07` proves the reference
implementation emits 1 component with 5 targets; `T08` proves the prose describes
deployment-keyed discovery with `subscriptions` and `schedules` on the record. What no test
in this repo can assert is that an agent following the prose reproduces the algorithm's
result on a tree it has never seen.

*Why it is listed even though it looks like a technicality.* It is the same gap that
produced this feature. FEAT-2026-0039's gates were green and its skill still emitted 30
components on the first real repo, because a passing fixture and an agent-executed skill are
different oracles. Naming it keeps the next reader from reading gate 2's green as "the skill
is proven."

*Where verification happens.* The same operator run as entry 1 — one `/derive-monitoring`
against a real multi-trigger repo discharges both.

### The shared root cause, restated for the arc

Gate 1's close observed that all three of its deferrals were about *consumers* of the schema.
The arc's three are the same shape one level out: a **real repo** (1), an **unbuilt feature**
(2), and an **agent following prose** (3). None is an artifact this tree contains, so no cut
of the gates reaches any of them. Two of the three are discharged by a single operator
action.

---

## Hedged follow-up record (`close-discipline.md` §2)

**Verdict at close: `met_locally`; upgraded to `met` post-close.** Gate 2's definition of
done was met on the evidence this environment could produce. Three criteria were not
decidable here. Each entry below gives the criterion, why it was unverifiable in this
environment, and the **exact re-run condition** that upgrades it to `met` — preserved as
written at close time, because the re-run conditions are what the discharge was executed
against and rewriting them afterwards would destroy the audit trail.

**FU-1 and FU-3 have since been discharged** by exactly the run FU-1 specifies; see the
*DISCHARGED* section following FU-3. **FU-2 remains open by design** — it is 0040's.

### FU-1 — the mechanical-extractability claim

*Criterion, verbatim (`GATE-02.md`, definition of done):* **"Target lists are generated
mechanically from trigger evidence, with no operator question added."**

*Why unverifiable here.* Verified for the fixture; unverifiable for the claim. Every tree
this session can reach was authored inside this feature, so any evidence it produces is
evidence about its own fixture. The claim is about the shape of *real* repositories.

*Exact re-run condition that upgrades to `met`.* An operator, post-merge, runs
`/derive-monitoring` against a repository whose single deployable carries ≥ 3 message
subscriptions and ≥ 2 schedules, and records in a follow-up note: (a) the number of
components discovered — must be the number of deployables, not the number of triggers; (b)
for each `dlq` check, whether every `subscription` and `function` coordinate was extracted
without an operator question; (c) for each `heartbeat` check, whether every `name`, `cron`,
and `timezone` was extracted the same way; (d) any coordinate that required asking. **Any
entry in (d) refines the claim rather than refuting it** — the skill's stated rule is that a
coordinate discovery cannot name means the check is omitted, not that the operator is asked,
so a (d) entry is a finding about which coordinates are extractable, and belongs on issue
#245.

### FU-2 — the adapter-interface clause

*Criterion, verbatim (`GATE-01.md`, definition of done, clause 5):* **"FEAT-2026-0040's
adapter interface has a machine-checkable answer to 'do I enumerate per component or per
target'."**

*Why unverifiable here.* The artifact it asserts about does not exist. This is the clause
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` already named as undecidable-by-construction — a
gate's definition of done must be decidable by that gate.

*Exact re-run condition that upgrades to `met`.* FEAT-2026-0040's own gate that introduces
the adapter interface asserts, in a test, that an adapter enumerates over `check["targets"]`
when present and over the component otherwise, **and** that its fingerprint includes the
target key (see the next section). This is not this feature's to close and should not be
re-listed on a future FEAT-2026-0069 surface; it is 0040's acceptance criterion.

### FU-3 — the skill-executed-end-to-end clause

*Criterion, verbatim (`GATE-02.md`, definition of done):* **"`/derive-monitoring`, run
against a repo whose single deployable carries N triggers, emits 1 component with N targets —
not N components."**

*Why unverifiable here.* The reference implementation is test-local and the skill is prose;
no test in this repo composes them. Verified: the algorithm (fresh, exit `0`) and the prose
(fresh, exit `0`). Unverified: an agent following the prose against an unseen tree.

*Exact re-run condition that upgrades to `met`.* The same operator run as FU-1, with the one
additional assertion that closes this specific clause: the drafted `monitoring.yml` contains
**one** component block per deployable, and that component's `dlq` check carries one target
per subscription. FU-1 and FU-3 are discharged by one run and should be scheduled as one
follow-up.

---

## FU-1 and FU-3 — DISCHARGED 2026-07-26, post-close, on real evidence

Both were discharged by the single operator run their re-run conditions specify, executed
against **the downstream .NET backend** — the .NET repo whose FEAT-2026-0039 FU-1 run
originated issue #245. Discharging them against the originating repo rather than a
substitute closes the loop on the actual reported defect.

**Verdict upgraded `met_locally` → `met` on the strength of this section.** FU-2 is
unaffected and remains 0040's; see below.

### The falsifiable core, measured

| | |
|---|---|
| Trigger registrations in the tree | **33** (20 subscriptions + 13 schedules) |
| Components emitted | **2** |
| Deployables | **2** |

Pre-gate-2 discovery would have returned 33. The re-key returns 2. `GATE-02.md`'s
definition of done — *"emits 1 component with N targets — not N components"* — holds on a
real repository, not only on `_STACK_C_TREE`.

The two components are `backend-api` (Dockerfile + `charts/backend-api/Chart.yaml` +
compose `api:8080`) and the functions host (Dockerfile + its compose service), the latter carrying all 33 triggers.

### Clause-by-clause against FU-1's re-run condition

- **(a) component count = deployable count, not trigger count** — 2 and 2. ✅
- **(b) every `dlq` coordinate extracted without an operator question** — **20/20**.
  `subscription` from the `ServiceBusTrigger` attribute's second argument, `function` from
  `[Function(nameof(...))]`. ✅
- **(c) every `heartbeat` coordinate extracted the same way** — names **13/13**, crons
  **13/13**, timezones **10/13**. The 9 constant-based crons resolve via
  `const string Cron = "..."` **declared in the same file as the trigger class**, so
  resolution is a same-file lookup, not cross-file symbol resolution. ✅ with the (d)
  refinements below.
- **(d) coordinates that required asking** — **none.** No target coordinate was an
  operator question. Two *refinements* about coordinate quality, filed upstream:
  - **`the backend repo's #469`** — the repo mixes 5-field and 6-field NCRONTAB
    spellings (10 vs 3). `*/5 * * * *` and `0/10 * * * * *` differ in meaning by 60×
    depending on assumed dialect. Extraction succeeds; *interpretation* is ambiguous, and
    a heartbeat check computing "should this have fired by now?" cannot resolve it from
    the emitted config. **This is the sharpest finding of the run** and it argues the
    schema's opaque `cron` may eventually need a dialect discriminator — recorded here,
    not acted on, because it is 0040's to feel first.
  - **`the backend repo's #470`** — 3 of 13 timers declare no timezone and silently
    run UTC while 10 declare `America/Toronto`. Absence is not neutral: it means UTC, and
    a check configured from the code inherits that without stating it.

  Per this record's own rule, **both refine the claim rather than refute it** — they are
  findings about *which* coordinates are cleanly interpretable, and they belong on #245's
  family. Neither required asking the operator for a target.

### FU-3 — the skill-executed-end-to-end clause

The run was performed by an agent **following `SKILL.md`'s prose**, in method order
(deployment evidence → scoped triggers → audit → questions → output), against a tree the
prose had never been applied to. That is exactly the composition FU-3 named as unverified:
*"an agent following the prose against an unseen tree."*

The drafted `monitoring.yml` — 110 lines, 20 `dlq` targets, 13 `heartbeat` targets —
returns **zero findings** from `python3 .specfuse/scripts/lint_monitoring.py`. Nothing was
written into the target repo; the skill's draft-never-write rule held.

### What the run found that the fixture could not

1. **A Dockerfile alone is not a deployable.** the project's CLI project has one, but no compose
   service, no chart, and a bare `dotnet <cli>.dll` entrypoint — a one-shot tool. Excluding it was a judgement the pattern table must encode, and no fixture in
   this repo models a Dockerfile-bearing non-deployable. **Worth adding to `SKILL.md`
   Step 1 and to a future fixture.**
2. **The diagnosability audit's role-name property fired, correctly, and was already
   tracked.** the HTTP API project stamps a `CloudRoleNameInitializer("backend-api")`; the
   functions host has none and inherits the Azure Function App name. An existing upstream
   issue in that repo (#376) covers it (API half landed, worker half open) — so
   the audit reproduced a known real gap rather than inventing one, which is the better
   evidence for the audit's value. Component `name` was set to the Function App name from the IaC module precisely so the property can hold once
   #376's worker half lands.
3. **`Section__Key` credentials are the real spelling here.** The repo uses
   `AzureServiceBus__ConnectionString`. That form was rejected by `_ENV_VAR_NAME_RE` until
   issue #246 was fixed earlier the same day — **before that fix this project's real
   credential names were unwritable in `monitoring.yml`.** Unplanned corroboration that
   #246 was a real defect and not a style preference.
4. **A schema gap the fixture could never have surfaced, because it needs a second
   project to see.** Telemetry binds per *environment*, so all components in one
   environment share one telemetry instance. Correct for this project — confirmed by the
   operator, who chose a single workspace-based App Insights deliberately — but the
   operator also stated that other projects give each component its own instance, which
   the schema cannot express. Filed as **#262**, and explicitly distinguished there from
   `PLAN.md`'s recorded `environments` × `components` non-goal: that one is about
   *membership*, this one about *binding*. It lands on 0040's adapter contract.
5. **Operator follow-through provisioning is real work, now tracked.** The monitor must
   not reuse the app's credentials — the existing Service Bus worker SAS carries
   listen+send+manage where a DLQ peek needs Listen only. Filed as
   the infrastructure repo's #316.

### Scope honesty about this run

The agent that performed it had, earlier in the same session, run shallow greps over the
target repo (trigger counts and file inventories) while advising which repo to use. So it
was **not a fully naive reader of that tree**. Those looks were counts, not method
application — no component discovery, no scoping, no coordinate extraction — and the run
itself followed the prose from Step 1. Recorded because "the prose works for an agent that
already glanced at the repo" is a marginally weaker claim than "works cold", and the
difference should not be silently rounded away.

The **two-environment neutrality claim remains unverified.** This run exercised one stack
(.NET/Azure). A Python repo in the same workspace was examined and rejected as FU evidence
— its four deployables are single-purpose, so it has no N-triggers-on-one-host shape — but
it would be a genuine test of the "a new stack is a new pattern table, never a change to
`discover_components`" claim, which gate 2 asserted with two synthetic fixtures and has
never run against a real non-.NET repo. **Not a FEAT-2026-0069 obligation** — the feature
never claimed it — but the natural next probe.

---

**No entry above is a `blocked` condition.** Each is a claim this environment structurally
cannot decide, which is what `met_locally` means. None of the escalation triggers in `WU-92`
fired: no fresh oracle re-run disagreed with a WU's outcome on substance (the one grep
discrepancy is a criterion-wording defect, diagnosed and recorded, not a deliverable gap),
and gate 2's definition of done **can** be honestly asserted — the N-trigger fixture does
yield one component with N targets.

---

## Consumer-visible contract changes (`close-discipline.md` §3)

**Whole-feature enumeration, both gates. This list is submitted for human acknowledgment at
the terminal review checkpoint and is NOT self-acknowledged.** The `met_locally` verdict
keeps the gate at `awaiting_review` and leaves the roadmap and `PLAN.md` un-flipped, so that
checkpoint exists and is where the signature goes. **Items 1, 3, and 11 are breaking.**
Item 10 supersedes item 6 and is a tightening that breaks nobody — the position it replaces
was never released.

Gate 1's nine items are carried forward as tabled — they were acknowledged at the gate-1
arming checkpoint (`GATE-02-REVIEW.md` § 8, `GATE-01.md` § *Reflection notes*) and are not
re-derived here. **Item 6 is superseded**; items 10–15 are gate 2's.

### Carried forward from gate 1 — the schema surface

| # | surface | change | breaking? |
|---|---|---|---|
| **1** | `dlq` check | **`targets` now REQUIRED**, each entry needing `subscription` + `function` | **YES** |
| 2 | `CHECK_TYPES` | new check type `queue-stalled`; enum 5 → 6 | additive; breaking for exhaustive switches |
| **3** | `error-logs`, `http-5xx` | **`targets` now REJECTED** — a previously-ignored field is now a finding | **YES** |
| 4 | `heartbeat` check | `targets` optional; entries require `name`, with `cron` / `timezone` accepted and opaque | additive |
| 5 | `queue-stalled` check | `targets` required from birth — no permissive period | additive (new type) |
| ~~6~~ | ~~`invariant` check~~ | ~~`targets` permitted, no required coordinates — a fall-through, never a decision~~ | **SUPERSEDED by item 10** |
| 7 | validator finding strings | new finding messages; consumers parsing findings as text see new strings | additive |
| 8 | scaffold seed files | four `*.example` files changed content; `init.sh` / `specfuse upgrade` now seed targets-bearing examples | additive, content-only |
| 9 | `derive-monitoring` skill prose | both `SKILL.md` copies show `targets[]` on `dlq` in every worked example | additive, prose |

Full detail for items 1–9, including evidence per row, is in *Gate 1 — consumer-visible
contract changes* above.

### Added by gate 2

| # | surface | change | breaking? | evidence |
|---|---|---|---|---|
| **10** | `invariant` check | **`targets` is now REJECTED**, superseding item 6's permissive fall-through. `invariant` joined `_TARGETLESS_CHECK_TYPES`; an `invariant` check carrying `targets` produces `'invariant' check must not carry 'targets'`. **This is a decision, not an inheritance** — the reason is that `fingerprint_by` is already that check type's required enumeration key, and permitting both would hand FEAT-2026-0040's fingerprint model two competing keys with nothing in the schema saying which wins | **a tightening — but breaking for nobody.** Gate 1's permissive position was never merged or released, so no consumer has seen it. Rejecting now is free; rejecting after a release would not have been | `TestInvariantTargetsRejected`, 2 tests, exit `0` fresh; `_TARGETLESS_CHECK_TYPES == ['error-logs','http-5xx','invariant']` |
| **11** | the `patterns` table contract | **BREAKING.** `evidence_markers` **removed**; the hand-declared `http_serving` / `message_consuming` booleans **removed** as inputs. **Added:** `deployment_markers` (markers on deployment artifacts) and `scope_prefix` (the relpath prefix bounding a deployable's own files) per candidate, plus a new sibling table `patterns["triggers"]` — a flat list whose entries carry `marker`, a `kind` in `{http, subscription, schedule}`, and that kind's coordinates. **Anyone who wrote a pattern table against gate 1's shape must rewrite it** | **YES — breaking** | `grep -c "evidence_markers" …_discovery.py` → `0`; `TestDeploymentKeyedDiscovery` exit `0`; the contract table in `WU-06` |
| 12 | the emitted component record | **Added:** `subscriptions` (`{subscription, function}` per entry) and `schedules` (`{name, cron, timezone}` per entry), both in trigger-table order. `http_serving` / `message_consuming` remain on the record but are now **derived** from matched triggers rather than read from the candidate — same field, different provenance | additive to the record; the provenance change is behavioural | `TestOneDeployableManyTriggers` exit `0`; `WU-06` AC3 |
| 13 | `suggest_checks` output | `heartbeat` now carries a `targets` list built one-per-entry from the record's `schedules`. A component with **no** schedules still gets a **target-less** `heartbeat` — not an empty list, which the validator would reject | additive; changes emitted YAML for any multi-schedule component | `TestHeartbeatTargetsFromSchedules`; `WU-07` AC4/AC5 |
| 14 | `render_monitoring_yml` output | emitted `cron` values are now **quoted**, matching `.specfuse/monitoring.yml.example`. Output-format change only; `_miniyaml` parses both spellings | additive, cosmetic — but byte-comparisons against previously rendered output will differ | `WU-07` AC6 |
| 15 | `derive-monitoring` skill method prose | Step 1, the Seams table, and `PROMPT.md` rewritten: a component is a deployable, a trigger is evidence of its type and the source of its target list. The Seams table's step-1 stack-specific input is now two tables (deployment markers + scope prefix; the trigger table) instead of "per-stack evidence markers". **This is the operator-facing half of item 11** — anyone authoring a pattern table follows this prose | prose, but describes a breaking contract | `TestStep1IsDeploymentKeyed` exit `0`; both copies byte-identical after clean-room regeneration |

### Removals and renames across the whole feature

Gate 1 had none. **Gate 2 has three**, all in the reference implementation's contract:

- `evidence_markers` — **removed** from the `patterns` candidate shape (item 11).
- `http_serving` / `message_consuming` as **declared inputs** — removed; the field names
  survive on the emitted record as derived values (item 12).
- `_with_subscriptions` — the test helper T03 introduced as a deliberate stand-in for
  evidence gate 2 derives. **Deleted with all four call sites**, so no downstream assertion
  can pass on test-injected subscription data rather than on discovered data.

No file, check type, CLI flag, or console script was removed or renamed anywhere in the
feature.

### The published-API question, answered explicitly

**No shipped Python API changed in either gate.** The discovery algorithm lives in
`tests/test_derive_monitoring_discovery.py` — test-local by design; there is no
`specfuse/loop/` module for it. Items 11–14 are therefore breaking for **pattern-table
authors**, of whom there are exactly two known instances, both fixtures inside this repo.
`GATE-02-REVIEW.md` open question 2 asked whether to version the contract and the answer at
arming was *accept now, unversioned* — versioning a contract with two in-repo consumers
would be ceremony. **The consumer that will feel item 11 is the next person who writes a
pattern table for a new stack**, and item 15 is the prose that tells them how.

The one shipped-package change in the whole feature is `specfuse/loop/lint_monitoring.py` —
items 1–7 and 10 — which is real, published, and where the breaking changes live.

### Acknowledgment checklist — for the human at the terminal review

`close-discipline.md` §3 requires a human signature on this list and **no agent session can
supply one**. The `met_locally` verdict is what routes it: the gate stays `awaiting_review`
and the terminal flips are withheld, so this checkpoint is reached before the feature can be
marked done. Sign here, then flip.

- [ ] Items 1–9 (gate 1's schema surface) re-confirmed as previously acknowledged; **item 6
      is withdrawn**, superseded by item 10.
- [ ] **Item 10** — `invariant` rejects `targets`. Confirm this is the position you want
      before it is released; after release the same change is breaking.
- [ ] **Item 11 — BREAKING.** The `patterns` table contract removes `evidence_markers` and
      the declared dials. Accepted unversioned at gate-1 arming
      (`GATE-02-REVIEW.md` open question 2); re-confirm now that it has actually landed.
- [ ] Items 12–15 (record shape, `suggest_checks` output, quoted `cron`, skill prose) read.
- [ ] The three removals — `evidence_markers`, the declared dials, `_with_subscriptions` —
      acknowledged as the feature's only removals.
- [ ] The FEAT-2026-0040 constraint below read and confirmed present in the roadmap.

---

## The downstream constraint for FEAT-2026-0040

**Fingerprints must include the target key.**

This is the single thing that can silently undo this feature. Without it, an adapter that
harvests 20 DLQ targets and fingerprints per *component* collapses them into one issue — and
the per-subscription attribution this feature paid two gates for is lost at the last step,
with every gate in 0040 green. It fails silently: the harvester works, issues are filed, and
the only symptom is that a dead-lettered message on subscription 7 looks exactly like one on
subscription 12.

**Concretely, for 0040's adapter interface:** enumeration runs over `check["targets"]` when
present and over the component otherwise; the fingerprint of a finding derived from a target
includes that target's coordinates (`subscription` + `function` for `dlq`, `name` for
`heartbeat`), not only the component name. `invariant` is the deliberate exception — item 10
rejected `targets` there because `fingerprint_by` is already its enumeration key, so 0040's
model must read `fingerprint_by` for `invariant` and `targets` for everything else. **That
split is the schema's answer to "do I enumerate per component or per target," and it is now
machine-readable.**

**Confirmed present in the roadmap.** `.specfuse/roadmap.md`'s FEAT-2026-0040 detail section
carries it under **Blocked by**, verbatim: *"Note for this feature: **fingerprints must
include the target key**, or 20 DLQ targets collapse into one issue and 0069's attribution is
lost at the last step."* It is also recorded in `PLAN.md`'s *OUT — owned by FEAT-2026-0040*
scope boundary. This close verified the roadmap text rather than assuming it, and extended
the 0069 detail section with the `invariant` / `fingerprint_by` exception, which was decided
after that note was written.

---

## What I'd change

Gate 1's six items are above and four of them were routed into gate 2 and are done. These are
the arc's.

### Grep-based acceptance criteria need word boundaries, and this one nearly reported a false failure

`T06`'s AC7 — *"`grep -c "_with_subscriptions" tests/…_discovery.py` returns `0`"* — returns
`1` on a fresh re-run, while the deliverable it describes is completely met. The hit is a
substring inside a test method name added by a **later WU in the same gate**. Two ways this
bites, and the second is worse:

- **False failure**, which is what happened here. A close re-running the criterion literally
  and reporting `blocked` would have escalated a naming coincidence.
- **False pass**, which is the one to fear. The same criterion returns `0` if the helper is
  renamed rather than deleted. A bare substring grep is not evidence of absence.

The fix is mechanical and belongs in WU authoring: a grep criterion asserting a symbol's
absence must anchor on the **definition** (`grep -c "def _with_subscriptions"`) or use a word
boundary (`grep -cE "\b_with_subscriptions\b"`), and should say which. This is the same
family as `[FEAT-2026-0039/G2-CLOSE]`'s rule about criteria naming a test runner the repo
does not have — a command written into a criterion is only an oracle if it measures the thing
the sentence claims.

### Tests asserting a relation between derived collections need a non-emptiness assertion

Two of gate 1's provider-neutrality boundary tests passed on an empty component list, and no
gate could see it, because `len([]) == len([])`. They were the tests guarding the feature's
neutrality property, and they were satisfiable by a discovery function returning nothing.
`T06` AC6 fixed it as a rider.

The general rule: **any test whose assertion is a relation between two derived collections —
equal lengths, disjoint sets, stable ordering, round-trip identity — is vacuously true on
empty inputs and must assert non-emptiness first.** This is not a variant of the hollow-pass
problem the driver already guards; the test does real work and its assertion is real. It is
just true of nothing. Worth a grep across this repo's boundary tests, not only this module.

### Gate sizing is flagged, and again it is not the right lever

Three deferred entries against a two-entry threshold, so the flag fires. Reporting what it
means, per `[FEAT-2026-0039/G2-CLOSE]`'s rule against mis-attributing structural limits to
gate sizing: **none of the three is severable by cutting gates differently.** They require a
real repository, an unwritten feature, and an agent executing a skill — no artifact in this
tree, at any gate size, reaches them.

What *would* change the number is a different definition-of-done discipline, and gate 1's
close already named half of it (a gate's DoD must be decidable by that gate). The arc adds
the other half: **`GATE-02.md`'s DoD is written in terms of the skill (`/derive-monitoring`,
run against a repo…) while its oracle is the reference implementation.** Written as what gate
2 can decide — *"`discover_components` and `suggest_checks`, over a fixture whose one
deployable carries N triggers, yield one component with N targets, and the skill's prose
describes that algorithm"* — it is exactly true, exactly what was proved, and entry 3
disappears from the deferred list as a wording artifact rather than surviving as a real gap.
The genuine gap (an agent following the prose) then belongs where FU-1 already puts it: a
named post-merge operator run.

### The planning floor is the most expensive thing in this feature and it is not fixed yet

$16.45 of overrun from a rules-supplied constant — more than three times the feature's one
real defect, and more than gate 2's entire substantive spend. This close produced the
`## Planning-floor revision` section, the third dataset, and the two concrete file targets on
issue #260. **What it could not do is make the edit**, because those are production surfaces
and this is a close. The lesson only lands if #260 is worked before the next multi-gate
feature is drafted; until then every new plan inherits the same mis-priced budget on day one,
and the fourth feature pays.

### Smaller things

- **`GATE-02.md`'s prospective budget correction was right and should be the pattern.** At
  arming, `G2-CLOSE` was raised $5.00 → $8.00 and the gate ceiling $22.00 → $26.00, against
  the corrected floors rather than §5's. That is a **prospective** correction to a WU that
  had not run — not a re-baseline of a plan onto its own overrun — and the distinction is
  exactly the one `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` draws. `PLAN.md`'s $34.00 stayed
  untouched and the widened lint WARN was left as the signal.
- **The runtime probe is the highest-leverage thing in the methodology right now.** One probe
  in `G1-PLAN` turned the feature's most-feared WU into a first-attempt $1.25 pass. Gate 1,
  planned without one for its own WUs, spent $5.26 discovering a precondition. Same feature,
  same author, same driver.
- **Arming all four gate-2 drafts unmodified was correct and is worth recording**, because
  the reflex at a review checkpoint is to edit something. The review was good enough to arm
  as-is, and the human's own additions were the two things review documents cannot do for
  themselves: verifying `T05`'s flip was satisfiable on the real tree, and reading
  `G1-PLAN`'s own cost out of `events.jsonl` after it had been reported unavailable.
- **Sixteen files in this folder carried stray tool-call closing tags**, propagated because
  each agent used the files it read as templates. Stripped at arming. Worth a lint rule: an
  artifact that agents read as a template propagates its defects at the rate agents read it.
