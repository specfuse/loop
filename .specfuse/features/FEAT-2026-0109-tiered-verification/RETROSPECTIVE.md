## Gate 1

Gate 1 made the baseline probe lazy: no `code`-set execution at gate entry, and
retroactive attribution against the post-reset tree when a unit's verification
first fails. Three implementation units (T01 tracer bullet, T02 tree-hash
keying, T03 provenance) landed, each on attempt 1, with three driver restarts
between them.

This is a **non-terminal** close. It measures; it declares no feature-level
verdict.

## Measurements

All commands below were run fresh in this close session, from the working tree
at gate 1's head, under `.venv`. The test suite is run unsandboxed — the
sandbox falsely reds roughly a dozen git/network tests in this repo, so a
sandboxed run would not be a measurement of the code.

### Definition of done — one command per bullet

| # | `GATE-01.md` bullet | Command run in this session | Exit |
|---|---|---|---|
| 1 | The gate-entry probe does not run on the green path | `python3 -m unittest tests.test_lazy_baseline_e2e.LazyBaselineIntegration.test_green_gate_entry_runs_no_gate_set -q` | 0 |
| 2a | A unit's first verification failure triggers attribution against the post-reset tree | `python3 -m unittest tests.test_lazy_baseline_e2e.LazyBaselineIntegration.test_first_failure_triggers_attribution -q` | 0 |
| 2b | A pre-existing failure escalates `preexisting_gate_failure` and is **not** counted against attempts | `python3 -m unittest tests.test_lazy_baseline_e2e.LazyBaselineIntegration.test_preexisting_failure_does_not_consume_an_attempt -q` | 0 |
| 2c | A genuine failure counts normally and the unit retries | `python3 -m unittest tests.test_lazy_baseline_e2e.LazyBaselineIntegration.test_genuine_failure_counts_normally -q` | 0 |
| 3 | Attribution runs at most once per gate | `python3 -m unittest tests.test_lazy_baseline_e2e.AttributionDedup.test_attribution_runs_at_most_once_per_gate -q` | 0 |
| 4 | The probe that does still run is keyed on the tree hash, not the HEAD sha | `python3 -m unittest tests.test_baseline_tree_hash_key -q` (Ran 4, OK) | 0 |
| 5 | The baseline record says how it was determined (`entry_probe` / `attributed:<wu_id>` / absent) | `python3 -m unittest tests.test_baseline_provenance -q` (Ran 4, OK) | 0 |
| 6 | `--no-baseline-probe` and the `baseline_probe` key still mean what they mean today | `python3 -m unittest tests.test_baseline_probe tests.test_baseline_persistence -q` (Ran 24, OK) | 0 |
| 6b | — same, driven end-to-end through `loop.run()` | `python3 -m unittest tests.test_lazy_baseline_e2e.LazyBaselineIntegration.test_no_baseline_probe_flag_still_honoured -q` | 0 |
| 7 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing` | 0 |

Bullet 7 is satisfied **vacuously, and that is stated rather than implied**:
gate 1 carries no `GATE-01-CRITERIA.md`, so `close-intermediate-f`
(`check_criteria_state_well_formed`, `applies_when: criteria_artifact_present`)
does not fire and the narrow/broad contract has nothing to constrain. §5 is
conditional on the artifact existing — this gate proved the requirement
inapplicable, not that the contract holds.

Bullet 1 is worth naming precisely, because it is the one bullet whose evidence
could most easily have been hollow. `test_green_gate_entry_runs_no_gate_set`
does not mock `probe_baseline`; it injects a recording `_run_gate_set` that
raises on any invocation and drives the real `loop.run()` through a green gate,
then asserts the recorder was never called. The structural corroboration:
`gate_baseline_check` now has exactly **one** call site in `loop.py` (line
4741, inside `attribute_failure_to_baseline`), reached only from the
attempt-failure path at `loop.py:8779`. There is no gate-entry call site left
to run.

### Fresh oracle re-runs

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_lazy_baseline_e2e -q` | Ran 6 tests, `OK` | 0 |
| Full suite | `python3 -m unittest discover -s tests -q` | Ran 3788 tests in 146.099s, `OK (skipped=3)` | 0 |
| Smoke test | `bash scripts/smoke-test.sh` | `smoke test: OK` | 0 |
| Lint sweep | `lint_plan.py` over all 77 `.specfuse/features/*/` folders | 77 folders linted, **0** with an ERROR finding | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | pass | 0 |

### feature_oracle: PASS

### The saving — `code`-set wall clock on a green gate entry

Measured on **this tree**, so the before and after are commensurable — the same
16-gate `code` set, the same machine, the same checkout. The "before" number is
not inherited from the FEAT-2026-0101 run; it was produced here by calling
`probe_baseline(feature_dir, cfg)` directly, which is byte-for-byte the work the
old gate-entry path performed:

| | Gates executed | Wall clock | Result |
|---|---|---|---|
| **Before** (entry probe, this tree) | 16 of 16 | **169.4s** | `failing: []` |
| **After** (lazy probe, green entry) | 0 of 16 | **0.0s** | no record written |
| **Reduction** | | **169.4s → 0.0s = 100%** | |

The reduction is 100% by construction, not by optimisation: on a green gate
entry the `code` set is not executed at all, so there is no residual to
measure. The interesting number is therefore not the percentage but the
absolute, and the absolute agrees with the recorded baseline: `PLAN.md` § Notes
records roughly 3 minutes per entry across five probes on the FEAT-2026-0101
run, each returning `failing: []`; 169.4s is 2.82 minutes. The recorded before
and the measured before describe the same cost.

**Realised on this gate specifically.** Four gate entries occurred:

- **1 entry under the old behaviour** — the driver probed at
  `2026-09-08T11:26:09Z` and wrote `GATE-01.md`'s `baseline:` block, three
  minutes before T01 was dispatched at `11:29:24Z`. T01 had not landed yet.
- **3 entries under the new behaviour** — the three restarts after T01, T02 and
  T03 each tripped `driver_staleness_detected`. None probed.

The proof that those three did not probe is the record itself: `GATE-01.md`'s
`baseline:` block still reads `sha: cc8b2613…`, `probed_at: 11:26:09Z`, with no
`tree:` and no `source:` key — exactly the legacy shape the pre-T01 driver
wrote, untouched since. Any probe on any of the three restarts would have
rewritten it through `write_gate_baseline` and stamped both fields.

The counterfactual is exact rather than estimated, because the record's shape
determines it. With `tree` absent, `gate_baseline_check` falls back to
`baseline.sha == head_sha`; HEAD is now `03a5fba`, not `cc8b261`, so the old
entry path would have re-probed on **all three** restarts, not skipped any:

> **3 × 169.4s = 508.2s ≈ 8.5 minutes of wall clock not spent on this gate.**

### The cost — attribution, and the accepted wasted dispatch

| Measurement | Value |
|---|---|
| Times attribution fired during gate 1 | **0** |
| `baseline_attribution` events in `events.jsonl` | **0** |
| Non-passing attempts in gate 1 | **0** (3 of 3 units passed on attempt 1) |
| Wasted dispatches on a pre-broken tree | **0** — did not occur |
| Cost of the accepted trade, as realised | **$0.00** |

**Attribution fired zero times in this gate, so the happy path was measured and
the failure path was not.** Nothing observed in gate 1's own execution
establishes that the retroactive probe correctly attributes a real failure,
that a pre-existing failure escalates instead of burning an attempt, or that the
once-per-gate bound holds under real dispatch. Those properties are covered by
`tests/test_lazy_baseline_e2e.py`'s six tests — which drive the real
`loop.run()` path against injected failures — and by nothing else. The 8.5
minutes above is a measured saving; the safety of taking it is a tested claim,
not an observed one.

Symmetrically, the cost `PLAN.md` accepts — one dispatch burned discovering a
pre-broken tree, roughly $1–4 and 15–25 minutes — **was not incurred**, because
the tree was never pre-broken. Reporting the saving as though the cost side had
been survived would be reporting half the trade; it was not paid, and it was
also not tested against reality.

## Retrospective

**Did the lazy probe ever attribute a failure to the wrong side?** No — and the
question could not be answered by this gate. Zero failures occurred, so
attribution never ran, so it never had the opportunity to mis-attribute. The
only evidence bearing on mis-attribution is
`test_preexisting_failure_does_not_consume_an_attempt` and
`test_genuine_failure_counts_normally`, which assert the two directions
separately against a stubbed `probe_baseline`. This gate contributes no
production evidence either way, and the answer above should not be read as one.

**Did the once-per-gate bound hold?** Vacuously. Attribution ran zero times, so
the bound was never tested at runtime. Its mechanism is worth stating anyway,
because it is not a counter: `attribute_failure_to_baseline` delegates to
`gate_baseline_check`, and the bound falls out of that function's existing
tree/sha dedup — a second failing unit at the same `head_before` finds the
record the first failure wrote and returns it without probing. The bound is
therefore only as tight as the dedup key. If two units fail at *different*
`head_before` shas within one gate, the record is stale by the dedup's own
rules and attribution runs again; "at most once per gate" is really "at most
once per tree state per gate." `AttributionDedup.test_attribution_runs_at_most_once_per_gate`
covers the same-sha case, which is the common one. The differing-sha case is
listed below as unverified.

**The half of gate 1 that got no production exercise.** T02 (tree-hash keying)
and T03 (provenance) both harden the probe *that still runs* — and on a green
gate, after T01, no probe runs. The live `GATE-01.md` record consequently sat
in its legacy pre-T02/T03 shape through all three restarts: no `tree:` key to
exercise the new comparison, no `source:` key to read. Both units are correct
and unit-tested; neither had anything to do in its own gate. This is not a
defect in either unit — T02's keying is what makes the *attribution* probe
survive a bookkeeping commit, which matters precisely on the failure path — but
it does mean gate 1 shipped three units and produced production evidence for
one.

### Contract surface gate 1 changed (input for the terminal close to enumerate)

Recorded here so the gate 3 close does not have to re-derive it; this section is
deliberately **not** the `close-discipline.md` §3 enumeration, which is the
terminal close's obligation:

- `baseline:` record gains `tree:` (T02) and `source:` (T03) keys — additive;
  `read_gate_baseline` treats both as optional and legacy records still parse.
- New driver event type `baseline_attribution`
  (`specfuse/loop/data/schemas/driver-event.schema.json`, T01).
- Behavioural default change: the gate-entry `code`-set probe no longer runs.
  `--no-baseline-probe` and the `baseline_probe` verification.yml key retain
  their meanings, now governing attribution rather than the entry probe.

## Cost analysis

`planned_cost_usd` for gate 1 is **$18.00** (`PLAN.baseline.json`, gate 1's five
units: T01 $3.50 + T02 $2.00 + T03 $2.00 + this close $4.50 + G1-PLAN $6.00).

Reconciled against `events.jsonl` (`attempt_outcome` / `task_completed`
payloads):

| Unit | Planned | Actual | Attempts | Duration |
|---|---|---|---|---|
| T01 lazy attribution | $3.50 | $3.79238 | 1 | 2092.1s |
| T02 tree-hash keying | $2.00 | $1.59976 | 1 | 1394.5s |
| T03 baseline provenance | $2.00 | $0.78003 | 1 | 667.5s |
| **Implementation subtotal** | **$7.50** | **$6.17217** | 3 | 4154.1s (69.2 min) |
| G1-CLOSE-INTERMEDIATE (this unit) | $4.50 | not yet in `events.jsonl` | — | — |
| G1-PLAN | $6.00 | not yet dispatched | — | — |

**The delta.** Against the three units that have actually run: **$6.17 actual
vs $7.50 planned, a delta of −$1.33 (−17.7%)** — under budget, with no unit
exceeding its estimate except T01 by $0.29 (+8.4%). Against the full $18.00
gate-1 envelope, **$11.83 remains unspent**, but that is not a saving: two of
the five units (this close, and G1-PLAN) have not completed, and their $10.50 of
planned cost is still outstanding. The honest reading of the gate-1 budget is
therefore *the implementation half came in 17.7% under*, not *the gate came in
66% under*. FEAT-2026-0101's recalibrated estimates continue to hold; no
re-calibration is indicated.

**Restart count: 3.** Three `driver_staleness_detected` events, all with
`halted: true` and `reason: driver_restart_required`, one after each of T01,
T02 and T03 — every unit in this gate edited `specfuse/loop/loop.py`, which is
the driver the run itself executes. The restarts carry no per-unit dollar cost
in `events.jsonl` (they halt between dispatches, not inside one), but they are
the reason gate 1 took four gate entries instead of one, and therefore the
reason the 8.5-minute saving above is 3 × the per-entry figure rather than
0 × it. This is exactly the tax gate 3 exists to remove; gate 1's own run is a
four-datapoint measurement of it.

### Failure-class breakdown

(no non-passing attempts in scope)

## What the loop did NOT verify

Each entry names the criterion, why it went unverified here, and where it
actually gets checked.

1. **The failure path, end to end, in production.** *Criterion:* "A unit's first
   verification failure triggers attribution … a pre-existing failure escalates
   `preexisting_gate_failure` … and is not counted against the unit's attempts."
   *Reason:* attribution fired zero times — all three units passed on attempt 1,
   so no failure ever reached `loop.py:8779`. *Checked instead by:*
   `tests/test_lazy_baseline_e2e.py::LazyBaselineIntegration`
   (`test_first_failure_triggers_attribution`,
   `test_preexisting_failure_does_not_consume_an_attempt`,
   `test_genuine_failure_counts_normally`), which drive the real `loop.run()`
   with an injected failing `verify`. *Where it gets real evidence:* the first
   gate on any feature in which a unit's verification actually fails — gate 2 or
   gate 3 of this feature if one does, otherwise the next feature that goes red.
   Nothing needs to be built for this; it needs a failure to occur.

2. **The CI fast path.** *Criterion:* none — `PLAN.md` § Scope boundary scopes
   it out deliberately. *Reason:* it cannot be the general answer here. Every
   probe sha on the FEAT-2026-0101 run was local-only (0 of 4 known to CI),
   because the probe runs at HEAD and at HEAD-after-`--prepare`, and a
   bookkeeping commit or a squash is never pushed — the restart case, the
   expensive one, has no CI result by construction. Environment compounds it:
   CI is Linux plus a Windows job, the driver here runs macOS, and the probe
   must predict whether *this* machine's gate run will be green, because that
   run is the unit's exit oracle. *Checked instead by:* nothing, by design.
   *Where it would get checked:* T03's `source:` provenance field is the stated
   precondition if it is ever revisited — a CI-sourced record would be
   distinguishable from a locally probed one only because that field now exists.
   Gate 1 makes it largely moot regardless: the cost it would have removed is
   the cost gate 1 removed.

3. **The tree-hash key and the provenance field, against the live record.**
   *Criteria:* "The probe that does still run is keyed on the tree hash" and
   "The baseline record says how it was determined." *Reason:* no probe ran
   after T01 landed, so `write_gate_baseline` was never called on this gate and
   `GATE-01.md`'s record still carries neither `tree:` nor `source:`. Both units
   shipped into a path this gate never took. *Checked instead by:*
   `tests/test_baseline_tree_hash_key.py` (4 tests, including the
   bookkeeping-commit-preserves-the-record case that motivated T02) and
   `tests/test_baseline_provenance.py` (4 tests, including the legacy-record
   fallback). *Where it gets real evidence:* the first attribution probe on any
   gate — the same trigger as (1).

4. **The once-per-gate bound when two units fail at different shas.**
   *Criterion:* "Attribution runs at most once per gate. A second failing unit
   does not re-probe if the gate already has a fresh attribution record for this
   tree." *Reason:* zero failures, and the covering test exercises the same-sha
   case only. The bound is implemented as `gate_baseline_check`'s tree/sha
   dedup, so its real guarantee is "at most once per tree state per gate"; two
   failures separated by a landed unit would legitimately re-probe. *Checked
   instead by:* `AttributionDedup.test_attribution_runs_at_most_once_per_gate`
   for the same-sha case; the differing-sha case has no test. *Where it gets
   checked:* nowhere today — it is a known gap, and gate 2's `plan-next` is the
   right place to decide whether the wording or the mechanism should move, since
   gate 2 is where the per-attempt tier makes multi-unit failure within one gate
   more likely.

5. **The wasted-dispatch cost `PLAN.md` accepts.** *Criterion:* not a
   definition-of-done bullet — an accepted cost. *Reason:* the tree was never
   pre-broken during gate 1, so the one-dispatch penalty was never paid and its
   real magnitude ($1–4 and 15–25 minutes, per `PLAN.md`) remains an estimate.
   *Checked instead by:* nothing. *Where it gets checked:* the first
   `preexisting_gate_failure` escalation reached through the attribution path;
   the `baseline_attribution` event T01 added carries the `attributed_to` unit,
   so the dispatch's cost is recoverable from that unit's `attempt_outcome`
   without new instrumentation.

## Lessons

1. **A gate whose feature is "stop doing X when nothing is wrong" measures its
   saving on the happy path and its safety nowhere.** Gate 1 removed 100% of the
   green-entry probe cost (169.4s → 0.0s, 8.5 minutes realised across three
   restarts) and fired attribution exactly zero times, because every unit
   passed. That is the *expected* shape — a feature betting that failures are
   rare, validated on a run with no failures — and it means the close must state
   which half it measured rather than let a large saving imply the whole trade
   was observed. The generalizable move: when a gate's definition of done splits
   into a common path and a rare path, count the rare path's firings as a
   first-class measurement, and say "zero" plainly when it is zero.

2. **A unit that hardens the path its sibling unit removes from the common case
   gets no production evidence in its own gate.** T02 (tree-hash keying) and T03
   (provenance) both act on the probe that still runs; T01 deleted the entry
   probe, which is the only probe a green gate has. The live `GATE-01.md` record
   sat in its legacy pre-T02/T03 shape through all three restarts, so the entire
   gate-1 saving is attributable to T01 alone and neither sibling was exercised
   outside its unit tests. Worth catching at drafting time: when a gate contains
   both a "stop doing X" unit and a "make X better" unit, the second one's
   evidence lives in the first one's *exception* path, and the gate should say so
   up front rather than discover it at close.
