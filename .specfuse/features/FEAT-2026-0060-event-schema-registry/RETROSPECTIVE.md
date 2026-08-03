# Retrospective — FEAT-2026-0060, Driver-local event schema registry

## Gate 1 — The driver's own event log validates, and the next unsanctioned type is caught in CI

Gate 1 is terminal. The closing sequence is this single `close` WU: there is no
`plan-next`, no gate 2, and no `GATE-02-REVIEW.md`.

**What shipped.** A driver-owned registry
(`specfuse/loop/data/schemas/driver-event.schema.json`) sanctioning the nine
event types the loop driver emits with no orchestrator-side counterpart;
fall-through resolution in `validate_event.py` (vendored envelope first,
driver-local registry second) implemented on a deep copy so the vendored file on
disk is never mutated; a drift guard deriving the emitted-type set at test time
from `build_event` call sites ∪ the corpus; and an `event-type-gate` entry in
this repository's `.specfuse/verification.yml` and `scripts/smoke-test.sh`
running the validator over every `.specfuse/features/*/events.jsonl`.

**The premise held.** Before this feature, 359 of 1043 corpus events (34%) failed
envelope validation on `event_type` alone. After it, zero do.

### Oracle re-runs (close-discipline §1)

Every oracle below was run fresh in this session. Exit codes read directly; no
producing WU's self-report was inherited. The test suite and gate commands were
run unsandboxed — the sandbox falsely reds ~11 tests in this repository.

| # | Oracle | Command | Exit | Result |
|---|--------|---------|------|--------|
| 1 | `code`: tests | `python3 -m unittest discover -s tests -v` | **0** | `Ran 2034 tests in 87.652s` / `OK (skipped=3)` |
| 2 | `code`: lint | `ruff check specfuse .specfuse/scripts tests scripts` | **0** | `All checks passed!` |
| 3 | `code`: security | `bandit -r specfuse .specfuse/scripts -ll` | **0** | 0 medium+, 0 high (the one high-severity `shell=True` is `# nosec B602`-suppressed with a reason) |
| 4 | `code`: coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** | `TOTAL 6191 395 94%` — 4 points of headroom over the 90 floor |
| 5 | `code`: leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | **0** | `leak-scan: gitleaks 8.30.1` / `leak-scan: clean` |
| 6 | T01's suite | `python3 -m unittest tests.test_validate_event_driver_types` | **0** | `Ran 12 tests` / `OK` |
| 7 | T02's drift guard | `python3 -m unittest tests.test_driver_event_registry_covers_emitters` | **0** | `Ran 3 tests` / `OK` |
| 8 | The new gate | `python3 .specfuse/scripts/event_type_gate.py` | **0** | `ok: no event_type validation errors across 43 events.jsonl file(s)` |
| 9 | Vendored envelope untouched | `git diff --exit-code specfuse/loop/data/schemas/event.schema.json` | **0** | clean (also clean against `main`: `git diff --exit-code main -- <same path>` → 0) |

Criteria 5 and 7 are satisfied by rows 1–9. Row 9 is the load-bearing one: the
whole premise of the driver-local design is that the vendored file this
repository does not own is never edited, and it was not — the fall-through
unions the two enums on an in-memory `copy.deepcopy`, leaving the file on disk
byte-identical to `main`.

#### Criterion 6 — the corpus-wide validator run

Run over **every** `.specfuse/features/*/events.jsonl`, 43 files, 1043 events:

```
files=43  total_errors=279  event_type_errors=0  correlation_id_errors=279  other_errors=0
```

**`event_type` errors: zero.** That is the dimension this feature owns, and it is
the dimension both T01 (criterion 9) and T02 (criterion 7) were explicitly
rescoped to after a prior T01 attempt correctly escalated the contradiction
between "zero total errors" and the vendored-schema do-not-touch list.

**Total errors: 279, all `correlation_id`.** The vendored envelope's pattern
`^(FEAT|INIT)-\d{4}-\d{4}(/F\d{2})?(/T\d{2})?$` rejects the closing-sequence
(`G<n>-CLOSE`, `G<n>-PLAN`) and hygiene (`TNNH`) ID shapes that
`.specfuse/rules/correlation-ids.md` documents as valid. Fixing that means
editing the vendored file, which is precisely what this feature was designed to
avoid; it is filed as FEAT-2026-0073. Criterion 6 as written asks for a zero
*total*, and 279 is not zero — see **What the loop did NOT verify**, item 1, and
the verdict.

This is **not** registry incompleteness, so the escalation trigger's prescribed
remedy — a re-dispatch of T01 — provably cannot fix it: T01 is forbidden from
touching the only file that could.

#### The end-to-end evidence — this feature's own log

```
$ python3 -m specfuse.loop.validate_event --file \
    .specfuse/features/FEAT-2026-0060-event-schema-registry/events.jsonl
ok: 24 event(s) validated against event.schema.json (with per-type payload
schemas under events/ where present)
exit 0
```

**Zero errors of any class**, including `correlation_id` — every event in this
feature's own log carries a `/T01` or `/T02` correlation ID, which the vendored
pattern accepts. This is the strongest single piece of evidence the feature
works, and it is a live end-to-end test rather than bookkeeping: 12 of those 24
events (8 `attempt_outcome`, 4 `re_arm_dispatched`) are types that would have
failed validation before T01 landed. Half this feature's own audit trail was
unvalidatable until the feature that produced it fixed it.

Two honest qualifications on the WU's framing of this evidence:

- The WU anticipated `auto_close_decision` appearing in this log. It does not —
  this gate never auto-closed, so no such event was emitted. `attempt_outcome`
  and `re_arm_dispatched` carry the demonstration instead.
- This close's own events (`attempt_outcome`, `task_completed`) are flushed at
  *outcome* time, i.e. after this file is written, so they are not in the run
  above. Their behaviour was verified directly instead, by taking a real event
  off this log and swapping only the fields a close emits:

```
FEAT-2026-0060/T01         attempt_outcome      event_type_errors=0  total=0  | clean
FEAT-2026-0060/G1-CLOSE    attempt_outcome      event_type_errors=0  total=1  | correlation_id pattern
FEAT-2026-0060/G1-CLOSE    auto_close_decision  event_type_errors=0  total=1  | correlation_id pattern
```

The close's own events resolve on `event_type` and trip only the known
FEAT-2026-0073 pattern gap — exactly the predicted split, confirmed rather than
assumed.

#### Criterion 9 — the drift guard observed failing

A guard never seen failing is the exact thing this feature exists to prevent, so
T02's report was not trusted. The check was re-run here against the guard's
**real assertion path**, not its helper: the test module was imported and its
call-site derivation monkeypatched (out of tree — no repository file was
modified) to inject a synthetic type, then
`TestRegistryCoversEmitters.test_every_emitted_type_is_registered` was executed.

```
FAIL: test_every_emitted_type_is_registered
AssertionError: Lists differ: ['synthetic_unregistered_type_from_close'] != []
 : event_type(s) emitted by the driver (build_event call sites and/or this
 repo's own events.jsonl corpus) that resolve against neither the vendored
 envelope enum nor driver-event.schema.json:
 ['synthetic_unregistered_type_from_close'].
 validate_event.py will reject every event of this type.
Ran 1 test — FAILED (failures=1)
```

The guard fails, and it **names the offender** (T02's criterion 4). It is not
cosmetic.

Worth distinguishing: T02's in-tree `test_guard_fails_on_an_unregistered_type`
exercises the `_missing_types` helper, which is a weaker claim than "the guard
fails". The run above closes that gap by driving the real assertion.

#### Criterion 8 — the derived type list versus PLAN.md's seven

T01 registered **nine** types. `PLAN.md` recorded **seven**. The roadmap row that
opened this feature named **three**.

| Source | Count | Types |
|--------|-------|-------|
| Roadmap row (filing time) | 3 | `gate_reached`, `attempt_outcome`, `arm_predicate_evaluated` |
| `PLAN.md` corpus sweep (2026-08-02) | 7 | the above + `auto_close_decision`, `re_arm_dispatched`, `plan_next_draft_lint`, `unsandboxed_dispatch` |
| T01's union derivation (shipped) | 9 | the above + **`gate_auto_armed`**, **`re_arm_rejected`** |

**The difference is +2, and its cause is structural, not clerical.**
`gate_auto_armed` and `re_arm_rejected` are emitted by real `build_event` call
sites that have never fired in any recorded run. A corpus sweep is a *lagging*
indicator and cannot see them by construction, no matter how carefully it is
run. Only call-site derivation reaches them — which is why T01's third re-arm
widened criterion 3 from "the corpus" to "the union of `build_event` call sites
and the corpus", and why T02 correctly blocked rather than editing the registry
it was built to guard.

**Read as drift-rate evidence, this is the argument for T02 existing at all.**
The roadmap row named 33% of the true set. The corpus sweep, taken deliberately
and one day before implementation, reached 78%. Neither number was stable long
enough to be worth trusting: four of the seven appeared *after* the roadmap row
was filed. A measurement that decays this fast is not a fact to record in a
document — it is a computation that has to be re-run, which is exactly what the
drift guard now does on every test run.

### Consumer-visible contract changes (close-discipline §3)

**Additions shipped to downstream projects** via `specfuse init` / `specfuse
upgrade`:

1. **`schemas/driver-event.schema.json`** — a new packaged scaffold file,
   registered in `test_scaffold_resources.py`, `test_scaffold_init.py`
   (`_EXPECTED_TREE` and `_VERSIONED_SEED_TO_TARGET`) and
   `test_init_integration.py`. It is listed as `UNMIRRORED_TRACKED` in
   `test_scaffold_data_in_sync.py` because this repository owns it outright, so
   there is no `.specfuse/schemas/` counterpart to byte-match against.
2. **`validate_event.load_driver_event_types()`** — new public module-level
   function returning the registry as a `frozenset[str]`. Additive.
3. **`validate_event.DRIVER_SCHEMA_PATH`** — new module-level constant. Additive.
4. **`validate_event.load_validator()` behaviour change** — the returned
   validator's `event_type` enum is now the vendored 28 unioned with the 9
   driver-local types. This is the one *behavioural reversal* in the set: a
   consumer who previously relied on `load_validator()` **rejecting**
   `attempt_outcome` now gets acceptance. That inversion is the entire point of
   the feature, and it is permissive — it widens what validates, so it cannot
   turn an existing green check red.

**Additions scoped to this repository only — NOT shipped:**

5. **`.specfuse/scripts/event_type_gate.py`**, plus the `event-type-gate` entry
   in this repository's `.specfuse/verification.yml` and the matching line in
   `scripts/smoke-test.sh`.

**Removals: none. Renames: none.**

#### A correction to this WU's own premise about the gate

This work unit names the new `verification.yml` gate as "the headline entry", on
the stated grounds that *"a downstream project upgrading the scaffold gains a
gate that will fail if its driver emits a type this registry does not sanction."*
**As built, that is not what happened, and the close should say so rather than
repeat it.**

`event_type_gate.py` lives in `.specfuse/scripts/` and appears in no scaffold
manifest — not `test_scaffold_resources.py`, not `test_scaffold_init.py`, not
`test_init_integration.py` — and not in
`specfuse/loop/data/verification.yml.example`. A repo-wide grep for
`event_type_gate` returns exactly three hits, all of them this repository's own
surfaces (`scripts/smoke-test.sh:63-64`, `.specfuse/verification.yml:49`). Its
own docstring states the posture explicitly: *"Repo-internal hygiene tooling
(like leak_scan.py) — not shipped scaffold API."* That matches the standing
decision that this repository's hygiene guards are not target-scaffold surface.

So the gate is named explicitly, as criterion 10 requires — and its real blast
radius is this repository, not downstream consumers. **No downstream build can
go red from this feature.** The only shipped surface is a permissive schema and
three additive Python symbols.

**Human acknowledgment.** Because the enumerated list is additive and permissive
with no removal, rename, or narrowing anywhere in it, there is nothing here that
requires a blocking acknowledgment before the feature can close. That is the
reviewed claim, recorded deliberately rather than left as an absence. The gate
review remains the acknowledgment surface if the operator disagrees.

## Cost analysis

Computed from `events.jsonl`, which is the only surface that never loses a cycle
— per `LEARNINGS [FEAT-2026-0053/G3-CLOSE]`. Every `attempt_outcome` payload's
`cost_usd` is summed; there are 8 of them across 6 dispatches.

| WU | Planned | Actual | Attempts | Dispatches | Delta |
|----|---------|--------|----------|------------|-------|
| T01 | $4.50 | **$16.3033** | 6 | 4 (1 + 3 re-arms) | **+$11.80 (+262%)** |
| T02 | $3.50 | **$2.3891** | 2 | 2 (1 + 1 re-arm) | −$1.11 (−32%) |
| G1-CLOSE | $5.00 | not yet recorded | — | 1 | — |
| **Total** | **$13.00** | **$18.6924** | 8 | 6 | **+$5.69 (+44%)** |

The close's own `attempt_outcome` is flushed at outcome time, i.e. after this
file is written, so it is structurally absent from the figure above. Against the
two WUs that *are* complete, planned $8.00 versus actual $18.69 is **+$10.69, or
+134%** — that is the honest read of the overrun, and the $13.00 comparison
flatters it by crediting $5.00 of unspent close budget.

**Summing every field a WU's lifetime is spread across.** Frontmatter `cost_usd`
alone is wrong by a factor of six here, and the reconciliation is worth showing
because the trap is silent:

```
T01: cost_usd 2.593786                          (current dispatch, last attempt)
   + re_arm_history[0].prior_cost_usd 5.308758
   + re_arm_history[1].prior_cost_usd 4.478344
   + re_arm_history[2].prior_cost_usd 3.922447
   = 16.303335   ==  events.jsonl sum 16.3033    ✓

T02: cost_usd 1.814714 + re_arm_history[0].prior_cost_usd 0.574386
   =  2.389100   ==  events.jsonl sum  2.3891    ✓
```

A close reading only `cost_usd` would have reported T01 at **$2.59** — 16% of the
truth. `cumulative_cost_usd` ($4.478344) is no better: it is a snapshot of one
prior dispatch, not a lifetime total. Three of T01's four dispatches live only in
`re_arm_history`.

Wall-clock: 5239.9 seconds of attempt time, 1.46 hours, across 8 attempts.

### Gate budget reconciliation

`GATE-01.md` declares `cost_budget_usd: 28.00`. This work unit's criterion 3
names **$18.00** — the *original* figure, before the operator raised it on
2026-08-03 at $14.28 spent. Both are reconciled here.

| Budget | Actual gate spend | Verdict |
|--------|-------------------|---------|
| $18.00 (original, named in criterion 3) | $18.6924 | **overrun by $0.69 (3.8%)** |
| $28.00 (raised 2026-08-03) | $18.6924 | $9.31 headroom, before this close's spend |

**Stated plainly: the original $18.00 budget was breached.** The raise to $28.00
was made before the breach and it funded the completion, so no work stopped —
but the raise does not retroactively make the original estimate correct, and
recording it as "within budget" would be reading the answer off the number that
was moved to fit.

The overrun's causes are already recorded in `GATE-01.md` and hold up against
the event log: two T01 attempts lost to a driver gate-reporting defect ($5.31,
fixed in #322 / FEAT-2026-0068), one T01 attempt spent correctly escalating an
unsatisfiable acceptance criterion ($4.48, authoring defect), and one T02 attempt
spent correctly escalating an incomplete registry ($0.57, authoring defect). None
of it was scope creep.

**A caveat on the brake, per `LEARNINGS [FEAT-2026-0053/G3-CLOSE]`.** The budget
predicate runs *before* each dispatch, so spend inside the final unit of a gate
is structurally invisible to it. This close's own spend is therefore unobservable
by the brake, and the $18.6924 above will be an undercount of the gate's true
total by whatever this session costs. That is a known driver property, not a
measurement error here.

### Failure-class breakdown

Eight attempts: three passed, five did not. **$11.91 of $18.69 — 64% — bought
non-passing attempts.**

| Class | Count | Spend | WU | What it actually was |
|-------|-------|-------|----|----------------------|
| `tests` | 2 | $5.31 | T01 | **Not a test failure.** Both attempts were shown an identical uninformative gate-report tail (`$ python3 -m unittest discover -s tests -v` with no diagnosis), which is *why* their failure signatures matched and `spinning_signature_repeat` fired. One unreadable report was misread as a spin. Fixed at source in #322 / FEAT-2026-0068. |
| `agent_reported_blocked` | 2 | $5.05 | T01 ($4.48), T02 ($0.57) | **Both escalations were correct.** T01 found criterion 9 demanded zero total validator errors while criterion 5 forbade the only file that could deliver them — an authored contradiction; it became FEAT-2026-0073 and the criterion was rescoped to `event_type`. T02 found T01's registry incomplete (`gate_auto_armed`, `re_arm_rejected` missing) and blocked rather than editing the registry it exists to guard. |
| `produces_not_in_diff` | 1 | $1.55 | T01 | The driver's produces-vs-diff guard refusing a claimed pass whose `produces:` path (`validate_event.py`) showed no working-tree change. The guard did its job. |
| *(passed)* | 3 | $6.78 | T01 ($3.92 + $1.04), T02 ($1.81) | — |

**The distribution is the finding.** Of the $11.91 spent on non-passing attempts,
$5.05 bought two *correct* escalations that improved the plan — money well spent
by design. $5.31 bought nothing at all, because a defect in the driver's own
reporting made two genuine failures undiagnosable and then indistinguishable
from each other. The spinning guard cannot tell a real spin from two identical
blank reports, and it charged three attempts' worth of budget to find that out.

## What the loop did NOT verify

**Four items.** This is not an empty list.

1. **Criterion 6's literal wording: "the total error count … must be zero."**
   Actual: 279, every one a `correlation_id` pattern rejection, zero
   `event_type`. *Why not verified here:* unsatisfiable within this feature's
   scope by explicit prior decision — the fix requires editing
   `specfuse/loop/data/schemas/event.schema.json`, which is this feature's
   central do-not-touch and the premise of the entire driver-local design. T01's
   criterion 9 and T02's criterion 7 were both rescoped to `event_type` for
   exactly this reason after a prior attempt correctly escalated it. *Where it
   is actually verified:* **FEAT-2026-0073**, filed for it. *Exact re-run
   condition to upgrade to `met`:* after FEAT-2026-0073 lands, re-run the
   corpus-wide validator over all `.specfuse/features/*/events.jsonl`; the total
   error count must read 0.

2. **`gate_auto_armed` and `re_arm_rejected` have never been emitted.** They are
   registered and the registry is closed around them, but no real event of
   either type has ever existed to validate. Their inclusion rests on call-site
   derivation, which is sound but is not the same as an observed event. *Where
   it is actually verified:* the first recorded run in which either code path
   fires — `loop.py`'s `gate_events.append` auto-arm branch and the
   `spinning_reproduction_missing` re-arm-rejection branch respectively.

3. **Payload shapes for all nine driver-local types are unguarded by
   construction.** The registry and the drift guard cover **event type names
   only**; `PLAN.md` scopes per-type payload schemas explicitly OUT, and
   `load_per_type_validator` treats their absence as contract-conformant rather
   than a gap. A type passing the guard is not a claim its payload is validated.
   This is stated in the drift guard's own docstring, per
   `LEARNINGS [FEAT-2026-0071/G1-CLOSE]`. *Where it is actually verified:*
   nowhere, until per-type payload schemas are authored — which needs its own
   feature and a failing check behind it.

4. **A live scaffold upgrade of a real target project was not exercised.** That
   `schemas/driver-event.schema.json` reaches a downstream project is asserted by
   the manifest and init-integration tests, which run against temp directories.
   No actual project was upgraded from this session. *Where it is actually
   verified:* `tests/test_init_integration.py` and `tests/test_scaffold_init.py`
   at packaging level; a live `specfuse upgrade` against a real target remains
   unrun.

**Auto-close debt (close-g).** None. Gate 1 is the only gate in this feature, so
there is no predecessor gate that could have auto-closed, and no
`specfuse:autoclose-debt` marker exists anywhere in the feature directory. The
gate ran its full close ceremony.

## Findings

**A registry derived from a corpus is derived from a lagging indicator.** This is
the sharpest thing the feature taught, and it cost a full re-arm to learn. T01's
first successful attempt did precisely what its criterion said — swept the
corpus, found seven types, shipped them — and shipped an incomplete registry,
because two of the nine are emitted by code paths that have never fired. The
criterion was not sloppily written; it was written against the wrong source. The
corpus answers *what has happened*; the guard needs to know *what can happen*,
and only the call sites hold that. The fix (union both sources) is now baked into
the drift guard itself, so no future derivation can regress to the corpus alone.

**A comment documenting a gap as precedent extended the gap's life.**
`loop.py:704` read: *"Not validated by validate_event.py … `gate_reached` and
`attempt_outcome` are the existing precedent for driver-local event types outside
the envelope enum and per-type registry."* That sentence converted a defect into
a convention. Every subsequent author who read it learned that unsanctioned
types were the house style, and four more arrived. T01 corrected it; the comment
now reads *"Validated by validate_event.py via fall-through: `arm_predicate_evaluated`
is sanctioned in the driver-local registry"*, and a repo-wide grep for
`precedent` in `loop.py` returns nothing.

**The lesson that justified the gap was describing a schema this repository no
longer ships.** `LEARNINGS [FEAT-2026-0002/G1-CLOSE]` asserted the orchestrator
schema *"rejects driver-emitted events by design (the schema's `source` enum is
the orchestrator protocol)"*. The vendored `event.schema.json` in this tree has
**no `source` enum at all** — `properties.source` carries exactly
`['type', 'description', 'pattern']`, and its description explicitly names *"the
loop's single-repo `driver`"* as a legitimate emitter. The schema anticipated the
driver; it merely lacked its vocabulary. The only thing rejecting driver events
was the `event_type` enum. That entry has been corrected in place — it is the
reason the gap read as intentional for as long as it did, and leaving it standing
would have kept teaching the same wrong thing.

**Half of this feature's own audit trail was unvalidatable until the feature
fixed it.** 12 of the 24 events in this feature's `events.jsonl` are types that
failed envelope validation before T01. The log now validates clean end to end,
including on `correlation_id` — which no closing WU's log will, until
FEAT-2026-0073.

**A close should verify its own premise about blast radius.** This WU instructed
the close to treat the new gate as a downstream-visible change. Checking the
manifests rather than assuming from the file's location showed it ships nowhere;
the actual shipped surface is permissive-only. Had the close copied the WU's
framing, the contract-change list — the one artifact whose whole job is to be
accurate about what consumers see — would have been wrong in the direction of
overstating risk.

## What I'd change

**Author the derivation source, not the derivation verb.** "Re-derive the list
from the corpus" and "re-derive the list from what the driver can emit" read
almost identically and differ by two types and one full re-arm. Where a WU asks
for a set to be computed, the criterion should name every source that can
contribute a member, and say which is authoritative when they disagree.

**Do not put a satisfiability answer in prose when the tree can be asked.**
`PLAN.md`'s satisfiability check answered "zero after T01" for `event_type` and
never ran the validator's other checks — so the 279 `correlation_id` errors were
invisible at plan time and surfaced as a blocked attempt costing $4.48. Running
the actual oracle at plan time, unscoped, would have cost seconds.

**A gate-report defect is more expensive than the failures it hides.** $5.31 —
28% of this gate's spend — bought two attempts that produced no diagnosis and
then triggered the spinning guard *because* they produced no diagnosis. The
guard's inputs were the report's, and the report was blank.

**Criterion 6 inherited a scope its siblings had already shed.** T01 and T02 both
carry an explicit, well-argued `event_type` carve-out with the 279-error figure
spelled out. The close's criterion 6 says "total" with no carve-out, which is why
this feature closes hedged on a criterion whose real subject was settled two WUs
ago. Where a scope decision is made mid-feature, the close's criteria are part of
what has to be re-read.

## Lessons promoted

Four entries appended to `.specfuse/LEARNINGS.md`, plus one **correction in
place** to `[FEAT-2026-0002/G1-CLOSE]`'s `source`-enum claim:

- Corpus-derived registries are derived from a lagging indicator; union the call
  sites.
- A comment that records a gap as precedent converts a defect into a convention.
- A close must verify its own premise about consumer blast radius against the
  manifest, not the file's location.
- A guard test that exercises a helper is not the guard observed failing.

## Gate verdict

**`met_locally`.**

Fifteen of the sixteen acceptance criteria are met, each on a fresh in-session
oracle run with the exit code read directly. Criterion 6 is met in the dimension
the feature owns (`event_type`: 0 errors across 43 files, and this feature's own
log clean on *every* class) and unmet as literally written (`total`: 279).

`met` would be a claim that the corpus validates with zero total errors, and it
does not. The gap is fully diagnosed, separately filed as FEAT-2026-0073, and
unfixable from inside this feature's do-not-touch boundary — but "diagnosed and
out of scope" is not the same as "verified", and the hedged verdict is the honest
one. The upgrade condition is a single named command, recorded above.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Accepted by the operator on:** 2026-08-03T13:53:15+00:00

**Operator's reason (verbatim):**

> items 1-4 are inherent or out of scope

**Standing follow-ups carried forward.** Accepting this hedge ships the feature
with the items below **open**, not discharged. They are reproduced verbatim from
`## What the loop did NOT verify` above; none is resolved by this acceptance, and
none may be treated as closed on the strength of it.


**Four items.** This is not an empty list.

1. **Criterion 6's literal wording: "the total error count … must be zero."**
   Actual: 279, every one a `correlation_id` pattern rejection, zero
   `event_type`. *Why not verified here:* unsatisfiable within this feature's
   scope by explicit prior decision — the fix requires editing
   `specfuse/loop/data/schemas/event.schema.json`, which is this feature's
   central do-not-touch and the premise of the entire driver-local design. T01's
   criterion 9 and T02's criterion 7 were both rescoped to `event_type` for
   exactly this reason after a prior attempt correctly escalated it. *Where it
   is actually verified:* **FEAT-2026-0073**, filed for it. *Exact re-run
   condition to upgrade to `met`:* after FEAT-2026-0073 lands, re-run the
   corpus-wide validator over all `.specfuse/features/*/events.jsonl`; the total
   error count must read 0.

2. **`gate_auto_armed` and `re_arm_rejected` have never been emitted.** They are
   registered and the registry is closed around them, but no real event of
   either type has ever existed to validate. Their inclusion rests on call-site
   derivation, which is sound but is not the same as an observed event. *Where
   it is actually verified:* the first recorded run in which either code path
   fires — `loop.py`'s `gate_events.append` auto-arm branch and the
   `spinning_reproduction_missing` re-arm-rejection branch respectively.

3. **Payload shapes for all nine driver-local types are unguarded by
   construction.** The registry and the drift guard cover **event type names
   only**; `PLAN.md` scopes per-type payload schemas explicitly OUT, and
   `load_per_type_validator` treats their absence as contract-conformant rather
   than a gap. A type passing the guard is not a claim its payload is validated.
   This is stated in the drift guard's own docstring, per
   `LEARNINGS [FEAT-2026-0071/G1-CLOSE]`. *Where it is actually verified:*
   nowhere, until per-type payload schemas are authored — which needs its own
   feature and a failing check behind it.

4. **A live scaffold upgrade of a real target project was not exercised.** That
   `schemas/driver-event.schema.json` reaches a downstream project is asserted by
   the manifest and init-integration tests, which run against temp directories.
   No actual project was upgraded from this session. *Where it is actually
   verified:* `tests/test_init_integration.py` and `tests/test_scaffold_init.py`
   at packaging level; a live `specfuse upgrade` against a real target remains
   unrun.

**Auto-close debt (close-g).** None. Gate 1 is the only gate in this feature, so
there is no predecessor gate that could have auto-closed, and no
`specfuse:autoclose-debt` marker exists anywhere in the feature directory. The
gate ran its full close ceremony.

**Recorded by** `/accept-hedged-close`. This record and the close WU's `verdict:`
field are the only surfaces this skill wrote. `PLAN.md`'s status, `GATE-01.md`'s
status, and the roadmap row were not touched here — they are flipped only by
`fire_terminal_flips`, reached through
`loop.py --recheck-verdict FEAT-2026-0060`, per `[FEAT-2026-0023/G1-CLOSE]`'s
single-owner constraint.

