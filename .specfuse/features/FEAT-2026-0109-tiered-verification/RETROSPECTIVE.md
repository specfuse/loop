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

## Gate 2

Gate 2 split verification into two tiers: a narrow set per attempt, and the
full `code` set once per gate before the close. Four implementation units
landed — T04 (the tier and the declared-tests selection), T05 (the
changed-file selector), T06 (the once-per-gate broad run and its halt), T07
(the attribution bound's wording) — each on attempt 1, with four driver
restarts between them.

This is a **non-terminal** close. It measures; it declares no feature-level
verdict.

The headline is not the one the gate was drafted expecting. **Every
definition-of-done bullet is demonstrated below, and the gate as actually run
cost 38.4s MORE wall clock than the same gate would have cost with no tier at
all.** The mechanism works; the wiring that would let it pay is missing, and
the measurement below is what says so.

## Measurements

All commands below were run fresh in this close session, from the working tree
at gate 2's head, under `.venv`, unsandboxed — the sandbox falsely reds roughly
a dozen git/network tests in this repo, so a sandboxed run is not a measurement
of the code. This is the same tree, machine and checkout `GATE-02.md`'s
recorded before was measured on; the commensurability check is below.

### Definition of done — one command per bullet

| # | `GATE-02.md` bullet | Command run in this session | Exit |
|---|---|---|---|
| 1 | A gate declaration in `verification.yml` carries a tier; an entry declaring nothing runs in both tiers | `python3 -m unittest tests.test_tiered_verification_e2e.TieredVerificationIntegration.test_untiered_gate_still_runs_every_attempt -q` (Ran 1, OK) | 0 |
| 2 | A per-attempt verification runs only the narrow tier — asserted by absence from the run, on the real dispatch path | `python3 -m unittest tests.test_tiered_verification_e2e.TieredVerificationIntegration.test_per_attempt_run_executes_only_the_narrow_tier -q` (Ran 1, OK) | 0 |
| 3 | The `tests` gate narrows rather than disappears — one entry, two commands | `python3 -m unittest tests.test_tiered_verification_e2e.TieredVerificationIntegration.test_declared_test_paths_are_selected -q` (Ran 1, OK) | 0 |
| 4 | The selection rule is declared, fail-safe, and auditable | `python3 -m unittest tests.test_tiered_verification_e2e.TieredVerificationIntegration.test_selection_falls_back_to_the_full_command_when_empty -q` (Ran 1, OK) + `python3 -m unittest tests.test_changed_file_test_selection -q` (Ran 5, OK) | 0 |
| 5 | The broad set runs exactly once per gate, before the closing sequence dispatches, and a red broad run halts the gate | `python3 -m unittest tests.test_gate_broad_run.TestBroadSetRunsBeforeClose -q` (Ran 1, OK) + `... TestRedBroadRunHalts -q` (Ran 2, OK) | 0 |
| 6 | The broad run is recorded on the gate and keyed on the tree | `python3 -m unittest tests.test_gate_broad_run.TestBroadRunDedup -q` (Ran 2, OK) | 0 |
| 7 | The once-per-gate attribution bound says what the mechanism actually does | `python3 -m unittest tests.test_lazy_baseline_e2e.AttributionDedup -q` (Ran 3, OK) | 0 |
| 8 | Absent-key and flag behaviour preserved: a config with no tier declarations behaves byte-identically to today | `python3 -m unittest tests.test_tiered_verification_e2e.TieredVerificationIntegration.test_a_config_with_no_tier_keys_is_byte_identical_to_today -q` (Ran 1, OK) | 0 |
| 9 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing` | 0 |

Three bullets carry structural corroboration beyond their test, because each is
the kind of claim a test alone can satisfy hollowly.

**Bullet 2 — the narrow tier is a real filter on the live config.**
`resolve_gate_tiers(load_verification()["code"], "narrow")` over this repo's own
`.specfuse/verification.yml`, run in this session, returns **7 of 16** gates:
`tests`, `lint`, `agent-policy-example-lint`, `event-type-gate`,
`roadmap-link-gate`, `arm-sweep-gate`, `monitoring-example-lint`. The nine it
drops are `security`, `coverage`, `leak-scan`, `leak-scan-hook`,
`sync-scaffold-bats`, `sync-scaffold-symlinks-bats`, `init-sh-shim-bats`,
`init-skills-bats`, `hookspath-conflict-bats` — each of which declares
`tier: broad` explicitly. No gate was demoted by omission.

**Bullet 3 — one entry, two commands, observed on the live `tests` gate.** For
work unit T06, `resolve_narrow_command(tests_gate, wu, {})` returns
`python3 -m unittest tests.test_gate_broad_run -v -b` while `tests_gate["command"]`
remains `coverage run --source=specfuse -m unittest discover -s tests -v -b`,
and the broad run below executed that second command whole. One gate entry
produced both.

**Bullet 6 — the tree-keyed skip was observed live, not only tested.**
`gate_broad_run_check(GATE-02.md, feature_dir, cfg)` called in this session
against the record the driver wrote at `2026-09-08T17:45:06Z` returned
`(ok=True, failing=[], ran=False)` in **0.020s**, and `GATE-02.md` was
byte-identical afterwards. The same call at a moved tree costs 194.4s (measured
below). That is the restart tax the tree key removes, observed rather than
inferred.

### Fresh oracle re-runs

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_tiered_verification_e2e -q` | Ran 5 tests in 4.260s, `OK` | 0 |
| Full suite | `python3 -m unittest discover -s tests -q` | Ran 3806 tests in 147.935s, `OK (skipped=3)` | 0 |
| Smoke test | `bash scripts/smoke-test.sh` | `smoke test: OK` | 0 |
| Lint sweep | `lint_plan.py` over all 77 `.specfuse/features/*/` folders | 77 folders linted, **0** with an ERROR finding | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | pass | 0 |
| Broad set, end to end | `run_gate_broad_set(feature_dir)` — the full 16-gate `code` set | `ok=True`, `failing=[]`, 194.4s | 0 |

### feature_oracle: PASS

**Commensurability with `GATE-02.md`'s recorded before.** The full unittest
suite alone measures **147.935s / 3806 tests** here against gate 1's recorded
**146.099s / 3788 tests** — +1.3% wall clock for +18 tests. The trees compare;
the numbers below are not an incommensurable comparison.

### The saving — narrow tier per attempt, against 169.4s

Gate 2 ran **4 attempts** (T04, T05, T06, T07 — one each, all `passed`). Which
tier each attempt took is determined by which driver binary ran it, and that is
recorded: every unit in this gate edited `specfuse/loop/loop.py` and therefore
emitted `driver_staleness_detected` with `halted: true,
reason: driver_restart_required`, so each attempt ran the driver the *previous*
unit had landed.

| Attempt | Driver that ran it | Tier path taken | Wall clock |
|---|---|---|---|
| T04 | pre-T04 (no tier) | full `code` set, unfiltered | **169.4s** (`GATE-02.md`'s recorded before) |
| T05 | T04 only | narrow, declared-tests selection | **5.3s** |
| T06 | T04 + T05 | narrow, **fell back to the full command** | **172.9s** |
| T07 | T04 + T05 | narrow, **fell back to the full command** | **174.0s** |
| — | — | once-per-gate broad run | **194.4s** |

The four narrow-tier figures were produced by calling `verify(wu, feature_dir,
gate_file=GATE-02.md)` in this session for each unit, with
`attempt_changed_source_lines` returning that attempt's own changed source
paths taken verbatim from its `attempt_outcome.files_touched` in
`events.jsonl` — the same input the live driver computed. The broad figure is
`run_gate_broad_set(feature_dir)`, which is byte-for-byte the work the driver's
broad run performs.

**The gate total, and the counterfactual.**

| | Arithmetic | Total |
|---|---|---|
| **As actually run** | 169.4 + 5.3 + 172.9 + 174.0 + 194.4 (broad) | **716.0s** |
| **Counterfactual, no tier** | 169.4 × 4 attempts, no broad run | **677.6s** |
| **Realised** | | **+38.4s (+5.7%) — the tier cost more than it saved** |

Two further arithmetics, because the counterfactual above is not the whole
story and reporting only it would misattribute the loss:

| Scenario | Arithmetic | Total | vs 677.6s |
|---|---|---|---|
| Had the changed-file half not forced a fallback (T04's declared-tests rule alone, all attempts after T04) | 169.4 + 5.3 + 6.9 + 7.8 + 194.4 | **383.8s** | **−293.8s (−43.4%)** |
| Steady state — all 4 attempts under a working narrow tier | 10.2 + 5.3 + 6.9 + 7.8 + 194.4 | **224.6s** | **−453.0s (−66.9%)** |

The declared-tests narrow tier measures **5.3s–10.2s per attempt (mean 7.6s
over 4 units)** against 169.4s — `GATE-02-REVIEW.md` predicted "roughly 6s" and
that prediction holds. The mechanism is not what failed.

### Why the gate lost wall clock: the fallback fired on 2 of 3 tiered attempts

`resolve_narrow_test_selection` returns `None` — "run the gate's full command"
— when the changed-file half cannot resolve while there is something for it to
resolve. Run in this session for each gate-2 unit against its own
`files_touched`:

| Unit | Declared modules | Changed source paths | Changed-file half | Final selection | Command resolved |
|---|---|---|---|---|---|
| T04 | `tests.test_tiered_verification_e2e` | `specfuse/loop/loop.py`, `specfuse/loop/data/verification.yml.example` | `None` | `None` | full `coverage run … discover -s tests` |
| T05 | `tests.test_changed_file_test_selection` | `specfuse/loop/loop.py` | `None` | `None` | full |
| T06 | `tests.test_gate_broad_run` | `specfuse/loop/loop.py`, `specfuse/loop/data/schemas/driver-event.schema.json` | `None` | `None` | full |
| T07 | `tests.test_lazy_baseline_e2e` | `specfuse/loop/loop.py` | `None` | `None` | full |

The changed-file half resolves to `None` for all four **because the map it
reads does not exist and nothing in the repository ever creates it.**
`read_changed_file_test_map()` returns `None` in this session;
`CHANGED_FILE_TEST_MAP_PATH.is_file()` is `False`. A repo-wide grep for
`write_changed_file_test_map` returns **one hit — its own `def` line at
`specfuse/loop/loop.py:4505`**. It has no caller in `specfuse/`, in
`.specfuse/scripts/`, or in `tests/`. T05's builder (`build_changed_file_test_map`)
is exercised by `tests/test_changed_file_test_selection.py`; the production
wiring that would persist its output after the broad run's `coverage run` was
never landed.

This is not a fail-open — the fail-safe worked exactly as designed and ran
*more*, never less. It is a fail-safe that fires on every attempt, which turns
the narrow tier into the broad tier plus a second broad run.

### The number that says whether narrowing lost anything

> **Broad runs that went red on work every narrow tier had passed: 0.**

`broad_run_result` events in `events.jsonl`: **1**, with `ok: true` and
`failing: []`. `human_escalation` events with
`reason: broad_run_gate_failure`: **0**. The one broad run this gate performed
went green.

**What that zero establishes:** on this gate, the per-attempt narrowing that
actually ran let no regression through to the backstop. **What it does not
establish:** anything about narrowing, because on 2 of the 3 tiered attempts
the "narrow" tier ran the full suite. The only attempt that genuinely narrowed
was T05's, at n=1. A zero over one genuinely-narrowed attempt is not evidence
that narrowing is safe; it is the absence of an opportunity to find out. The
liveness half of the gate's oracle — that the broad set *does* run, once,
before the close, and that a red one halts — is proven; the safety half is
proven only in `tests/test_gate_broad_run.py::TestRedBroadRunHalts`, which
drives an injected red broad run through the real dispatch path.

### Fallback and skip counts

| Count | Value |
|---|---|
| Attempts in gate 2 | 4 (all `passed`, all on attempt 1) |
| Attempts that ran under a tier-aware driver | 3 (T05, T06, T07) |
| Attempts that ran a narrowed selection | **1** (T05) |
| Attempts that fell back to the full command — reason: **map absent** (`read_changed_file_test_map()` is `None`, no writer exists) | **2** (T06, T07) |
| Attempts that fell back — reason: empty selection (no `produces:` path under `tests/`) | **0** — all four units declare a test path |
| Attempts that fell back — reason: unmapped path with a map present | **0** — unreachable, there is never a map |
| Attempts that fell back — reason: stale map | **0** — same |
| Times the changed-file map resolved anything at all | **0** |
| Broad runs executed | **1** (`ran=True`, `ok=True`) |
| Broad runs skipped at an unchanged tree, during the gate's own execution | **0** — only one dispatch reached the broad-run guard |
| Broad runs skipped at an unchanged tree, observed live in this close session | **1** (`ran=False`, 0.020s, `GATE-02.md` unmodified) |
| Attribution firings (`baseline_attribution` events) | **0** — as in gate 1 |

Zero skips during the gate's execution is not the tree key failing; it is the
guard having been reached exactly once. Gate 2's four driver restarts all
happened *before* the closing sequence, so none of them re-entered the
broad-run guard. The skip is nonetheless real — it was observed directly, above.

### The cost T05 charged for the map it never built

| Measurement | With `dynamic_context = "test_function"` | Without | Delta |
|---|---|---|---|
| Suite under `coverage run` | 165.900s | 151.995s | **+13.9s (+9.1%)** per broad run |
| `.coverage` data file | 2,109,440 B | 77,824 B | **27.1×** |

Measured by running `coverage run --source=specfuse -m unittest discover -s tests -q`
under this repo's `pyproject.toml` and again under a temporary rcfile carrying
only `[run] source = specfuse`. WU-05's escalation trigger asked for exactly
this and set the threshold at "roughly half" — +9.1% is well under it, so
enabling contexts was the right call *given a map*. Without one it is pure
cost. (The no-context run reports one failure,
`test_a_changed_line_selects_the_tests_that_executed_it`, which builds a map
from an inner coverage run and needs the ambient `dynamic_context` — an
artefact of the isolation measurement, not a repository defect. The same test
passes under the project config, in the 3806-test `OK` run above.)

This also explains the broad run's 194.4s against `GATE-02.md`'s 169.4s: +13.9s
of dynamic-context tax, +1.8s of suite growth (3788 → 3806 tests), and ~9s of
unattributed run-to-run variance across a three-minute run.

## Retrospective

**Did the narrow tier ever let a regression reach the broad run?** No — zero
broad runs went red. But the honest reading is that the question was barely
asked. Three attempts ran under a tier-aware driver and only one of them
actually narrowed; the other two ran the full suite under the fail-safe. The
gate produced one datapoint on the safety question, and one datapoint is not a
measurement of a rare event. This is the same shape gate 1's lesson 1 named,
one tier down: gate 1 measured a saving on a path where the safety mechanism
never fired, and gate 2 was drafted to fix that by making failure cheaper and
more likely. It did not, because all four units passed on attempt 1 again.

**Did the changed-file selector earn its cost over the declared-tests rule
alone?** **No — as landed it is net negative, and the sign is not close.**
`GATE-02-REVIEW.md` Q1 asked exactly this and recommended building it for
attribution precision rather than speed, with the honest caveat that "in a
project's first gate the changed-file half does not narrow anything." What
landed is worse than that caveat: the map is never built at all, so the half
never narrows in *any* gate, and because an unresolvable changed-file half
forces the full command rather than degrading to the declared set, it
**cancelled the working half** for every attempt that touches `specfuse/` —
which, in this repo, is every driver-editing attempt. Measured: 6.9s becomes
172.9s. On top of that it charges +13.9s per broad run and a 27× larger
coverage data file for a map nothing reads.

The design decision that turns a missing map into a regression rather than a
no-op is worth naming precisely, because it is defensible in isolation.
`resolve_narrow_test_selection` returns `None` when the changed-file half is
unresolvable *and there was something for it to resolve* — T05's own docstring
argues that "a changed source file this feature cannot vouch for is exactly the
case the fail-safe design exists to catch." That is a coherent reading of
`GATE-02.md`'s "fails safe, never open". The alternative reading — degrade to
the declared set, which is still strictly more than nothing and is what T04
alone would have run — is equally safe against the hollow-pass failure and
costs 166s less per attempt. Neither reading is wrong; the gate never chose
between them, because the choice only becomes visible once the map is missing
in production, and no acceptance criterion in the gate could observe that.

**What the gate's own oracle could not see.** `GATE-02.md` warned that "a
feature about running less verification, whose oracle only checked a selector
function, would be its own hollow pass," and required the oracle to assert on
observable effects of the real dispatch path. It does — `test_per_attempt_run_executes_only_the_narrow_tier`
drives `loop.run()` and asserts on which gate commands executed. It still could
not catch this, because it asserts on T04's tier filtering, and T05's map has
no bearing on which *gates* run — only on which *command* the `tests` gate
runs. The oracle asked "did the broad gates stay out of the attempt?" and the
answer was yes on every attempt. The question it never asked is "did the
attempt actually run less than the whole suite?", which is the question the
feature is about.

### Contract surface gate 2 changed (input for the terminal close to enumerate)

Recorded here so the gate 3 close does not have to re-derive it; this section
is deliberately **not** the `close-discipline.md` §3 enumeration, which is the
terminal close's obligation.

1. **`tier:` key on a `code:` gate entry in `verification.yml`** (T04) —
   additive. Values: `broad`. Absent key means "runs in both tiers", so a
   `verification.yml` predating this feature behaves byte-identically
   (`test_a_config_with_no_tier_keys_is_byte_identical_to_today`). Documented in
   the shipped `specfuse/loop/data/verification.yml.example` and in this repo's
   own `.specfuse/verification.yml`.
2. **`narrow_command:` key on a `code:` gate entry** (T04) — additive, and
   orthogonal to `tier:`. A template carrying `{selected_test_modules}`, run
   instead of `command` per attempt. Also documented in the shipped example.
   Not named in this WU's list but consumer-visible on the same surface.
3. **New driver event type `broad_run_result`** (T06) — added to
   `specfuse/loop/data/schemas/driver-event.schema.json`, emitted whenever the
   once-per-gate broad pass actually runs and never on a dedup skip, carrying
   `gate`, `tree`, `ok`, `failing`. A red broad run additionally raises the
   already-sanctioned `human_escalation` with the **new reason value**
   `broad_run_gate_failure`.
4. **`broad_run:` frontmatter block on `GATE-NN.md`** (T06) — additive, keys
   `tree` / `ran_at` / `ok` / `failing`. Read by `read_gate_broad_run`, which
   degrades a missing or malformed block to "never run" rather than failing, so
   gate files predating this feature parse unchanged.
5. **T07's three reworded claims** — the same overclaim corrected on three
   surfaces outside this gate's units, each verified by grep in this session:
   `GATE-01.md:23` ("Attribution runs at most once per **tree state** per
   gate"), `specfuse/loop/loop.py:5338` (`attribute_failure_to_baseline`'s
   docstring, same wording), and `PLAN.md:164` § Notes ("Bounded to one
   dispatch per **tree state** per gate"). Documentation only; no behaviour
   moved, per `GATE-02-REVIEW.md` § "The differing-sha gap".
6. **`[tool.coverage.run] dynamic_context = "test_function"` in
   `pyproject.toml`** (T05) — changes what every `coverage run` in this repo
   records, and with it the size of `.coverage` (27×). Consumer-visible to
   anyone running coverage locally or in CI.
7. **`.specfuse-changed-file-test-map.json` added to `.gitignore`** (T05) — a
   derived-data path reserved by name. Nothing writes it today (see
   `## What the loop did NOT verify`).

## Cost analysis

Gate 2 has **no baseline entry**: `PLAN.baseline.json` was frozen at gate 1 and
records `{"gate": 2, "work_units": []}`. Its planned costs are the ones
`G1-PLAN` wrote into the WU frontmatter — T04 $4.00, T05 $4.00, T06 $3.50,
T07 $1.50, this close $4.50, `G2-PLAN` $6.00, for a gate envelope of **$23.50**.

Reconciled against `events.jsonl` (`attempt_outcome` payloads):

| Unit | Planned | Actual | Attempts | Duration |
|---|---|---|---|---|
| T04 per-attempt tier | $4.00 | $3.37960 | 1 | 1375.4s |
| T05 changed-file selector | $4.00 | $4.28166 | 1 | 2357.8s |
| T06 per-gate broad run | $3.50 | $2.25820 | 1 | 1251.0s |
| T07 attribution tree bound | $1.50 | $0.87782 | 1 | 676.8s |
| **Implementation subtotal** | **$13.00** | **$10.79728** | 4 | 5661.0s (94.4 min) |
| G2-CLOSE-INTERMEDIATE (this unit) | $4.50 | not yet in `events.jsonl` | — | — |
| G2-PLAN | $6.00 | not yet dispatched | — | — |

**The delta.** Against the four units that have run: **$10.80 actual vs $13.00
planned, a delta of −$2.20 (−16.9%)** — under budget, and remarkably close to
gate 1's implementation delta of −17.7%. Only T05 overran, by $0.28 (+7.0%);
T06 came in 35.5% under and T07 41.5% under. FEAT-2026-0101's recalibrated
estimates continue to hold across two gates now; no re-calibration is
indicated. Against the full $23.50 gate-2 envelope, $12.70 is outstanding for
the two closing units, not saved.

**Feature-level, and the number that needs an operator.** Feature spend to date
is **$32.79** ($21.99 gate 1 over 9 attempts, $10.80 gate 2 over 4), against a
`PLAN.md` `planned_cost_usd` of **$26.00** — which still describes gate 1's five
units plus the scaffolded gate-3 close and was never raised when gate 2's six
units were drafted. `GATE-02-REVIEW.md` Q4 flagged this at arm time and left the
number for the operator; it is still unresolved, and gate 1's
`arm_predicate_evaluated` already fired `budget_projection` on it ("projected
spend $53.49 … exceeds 2.0x baseline planned total $26.00"). It will fire again
at gate 2's boundary. This is a stale plan figure, not an overrun: measured
against the WU-sum the drafts actually declare, both gates came in ~17% under.

**Restart count: 4.** Four `driver_staleness_detected` events, all `halted: true`
with `reason: driver_restart_required`, one after each of T04, T05, T06 and T07
— every unit in this gate edited `specfuse/loop/loop.py`. Gate 1 paid three;
gate 2 paid four. This is the tax gate 3 exists to remove, and gate 2 is also
where it became load-bearing rather than merely annoying: the restarts are the
reason T05's attempt ran a T04-only driver and T06/T07's ran a T04+T05 driver,
which is what makes the per-attempt tier path differ across the gate at all.

### Failure-class breakdown

(no non-passing attempts in gate 2 — all four units passed on attempt 1)

## What the loop did NOT verify

Each entry names the criterion, why it went unverified here, and where it
actually gets checked.

1. **The changed-file map, in production, at all.** *Criterion:* "The selection
   rule is declared, fail-safe, and auditable. The per-attempt test selection is
   the union of the unit's own declared test paths and whatever the changed-file
   rule resolves." *Reason:* the union's second term was `None` on every attempt
   because no map exists and no code creates one —
   `write_changed_file_test_map` has exactly one occurrence in the repository,
   its own definition. Only the fallback branch of the rule ever executed.
   *Checked instead by:* `tests/test_changed_file_test_selection.py` (5 tests),
   which construct a map in a temporary directory from a real inner coverage run
   and assert selection, union, and all three unresolvable cases. Every one of
   those tests passes, and none of them can observe that nothing calls the
   writer. *Where it gets real evidence:* nowhere, until the writer is wired
   into the once-per-gate broad run — after `coverage run` has produced fresh
   contexts and before the next gate's first attempt. That wiring is the natural
   first item for `G2-PLAN` to weigh against gate 3's atomicity constraint, and
   is recorded here rather than acted on because source is outside this close's
   scope.

2. **Whether the narrow tier is safe.** *Criterion:* "The broad set runs exactly
   once per gate … a gate whose broad run is red does not reach its close. This
   is the criterion that makes the narrowing safe rather than merely cheap."
   *Reason:* the broad run ran once and went green, and the only attempt that
   genuinely narrowed was T05's. There was one opportunity for narrowing to lose
   something and it did not, which is n=1 on a rare event. *Checked instead by:*
   `tests/test_gate_broad_run.py::TestRedBroadRunHalts` (2 tests) — a red broad
   run halts the gate before the close and counts against no unit — and
   `TestBroadSetRunsBeforeClose`. *Where it gets real evidence:* the first gate
   in which a broad run actually goes red on narrow-passed work. Nothing needs
   building; it needs a regression to occur.

3. **The retroactive attribution path, again.** *Criterion:* carried over from
   gate 1's definition of done. *Reason:* `baseline_attribution` events in
   `events.jsonl`: **0**, across both gates now. All seven implementation units
   in this feature have passed on attempt 1, so no failure has ever reached the
   attribution call site. `GATE-02.md` drafted the gate's oracle specifically to
   "drive a narrow-tier attempt that fails and observe attribution fire" —
   the oracle does drive that, in `tests/test_lazy_baseline_e2e.py`; production
   still has not. *Checked instead by:* `tests.test_lazy_baseline_e2e`
   (9 tests, including T07's new differing-tree re-probe case). *Where it gets
   real evidence:* the same trigger as gate 1's item 1 — the next attempt that
   goes red anywhere.

4. **The broad run's tree-keyed skip on a real driver restart.** *Criterion:*
   "The broad run is recorded on the gate and keyed on the tree … so a driver
   restart at an unchanged tree does not re-run 169.4s of gates it already ran."
   *Reason:* gate 2's four restarts all occurred before the closing sequence, so
   none re-entered the broad-run guard; the guard ran once and executed. *Checked
   instead by:* `tests/test_gate_broad_run.py::TestBroadRunDedup` (unchanged tree
   skips, moved tree re-runs) — and, in this session, by calling
   `gate_broad_run_check` directly against the live record, which returned
   `ran=False` in 0.020s. That is a genuine observation of the skip, but not of a
   *restart* taking it. *Where it gets real evidence:* the first gate whose close
   is re-dispatched after a halt — likely gate 3's, since gate 3 is about
   restarts.

5. **A gate that declares no `tier:` anywhere, end to end.** *Criterion:*
   "Absent-key and flag behaviour is preserved: a `verification.yml` with no tier
   declarations anywhere behaves byte-identically to today." *Reason:* this
   repo's own `verification.yml` declares `tier: broad` on nine gates, so the
   absent-key configuration was never the one under test on a real dispatch.
   *Checked instead by:*
   `test_a_config_with_no_tier_keys_is_byte_identical_to_today` and
   `test_untiered_gate_still_runs_every_attempt`, both driving `loop.run()`.
   *Where it gets real evidence:* the first downstream project that upgrades
   without editing its `verification.yml` — which is the population this default
   exists to protect, and which this repo cannot stand in for.

## Lessons

1. **A helper with no caller passes every test it has, and a fail-safe that
   fires on every attempt is a regression wearing a safety jacket.** T05 shipped
   `build_changed_file_test_map`, `read_changed_file_test_map`, `is_map_stale`
   and `select_tests_for_changed_files`, all tested, all green — and
   `write_changed_file_test_map`, which nothing calls. Its five acceptance
   criteria were all satisfiable against a map built inside the test, so none of
   them could observe that production never builds one. The damage is not that
   the new half does nothing: it is that an unresolvable changed-file half
   forces the *full* command rather than degrading to the declared set, so the
   half that did work was cancelled by the half that did not — 6.9s per attempt
   became 172.9s, and the gate as run cost 38.4s more than having no tier at
   all. Two generalizable moves. **(a)** A unit that adds a producer/consumer
   pair needs one acceptance criterion asserting the producer is *reachable from
   the real entry point* — a call-site assertion, or an end-to-end criterion
   that fails when the artifact is absent — not only that both halves work when
   handed to each other. `grep -c '<producer_name>'` returning 1 is the cheapest
   possible version of that check and it would have caught this at close time in
   the producing unit, not two units later. **(b)** When a fail-safe fallback is
   introduced, its acceptance criteria must state the *expected firing rate* in
   production, not only that it fires correctly. "Falls back when the map is
   missing" is satisfied identically by a mechanism that falls back once and one
   that falls back always; only the rate distinguishes a safety net from a
   bypass.

2. **When two units split one mechanism across a "do not touch" boundary, the
   seam between them is nobody's acceptance criterion.** T05's body said the map
   "must be written by the broad run … and not by an attempt", and its **Do not
   touch** list said "T06's broad-run bookkeeping". T06 landed 21 minutes later
   and its body said "T04's tier resolution and T05's selector are untouched."
   Both units obeyed their boundaries exactly; the one edit that had to cross
   the boundary — calling T05's writer from T06's broad run — belonged to
   neither, and no criterion in either unit could fail for its absence. The
   gate's own `feature_oracle` could not catch it either: it asserts on which
   *gates* execute per attempt, which T05 does not change, rather than on
   whether an attempt ran less than the whole suite, which is the thing the
   feature is for. Drafting-time move: when unit A produces data that only unit
   B's code path can persist, the wiring is a named deliverable of the *later*
   unit's `produces:` and one of its acceptance criteria — or the two units are
   one unit. Reviewing move: for each pair of units in a gate whose bodies name
   each other in **Do not touch**, ask what edit sits between them and which
   unit's criteria would go red if it never happened.
