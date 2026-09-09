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

## Gate 3

Gate 3 changed **what the driver is** while it runs: `main()` materializes a
content-addressed copy of `specfuse/` outside the working tree, keyed on
`HEAD^{tree}`, re-execs into it, and — because the running process is then a
stable snapshot — stops halting the run when a work unit edits the driver.
T08 built that mechanism. T09 and T10 were added after the gate's first close
recorded `not_met`: T09 closed the two definition-of-done bullets that close
found unmet (#3270, #3271), and T10 fixed a livelock the gate hit while T09 was
being retried.

This is the close's **third** attempt. Attempt 1 recorded `not_met` and filed
#3270 and #3271, both real and both since fixed by T09. Attempt 2 recorded `met`
and the judge lowered it to `not_met` on three test failures that were artifacts
of the judge's own environment; § *The five follow-ups attempt 2's judgment
produced* below reproduces that and shows the artifact directly. This attempt
re-measures everything from scratch.

All seven definition-of-done bullets are met on this attempt's evidence.

Three numbers gate 1 and gate 2 both deferred to "the next failure" are no
longer zero. That is the substantive thing this gate produced beyond its own
mechanism, and it happened because gate 3 was the first gate in this feature
that actually failed.

## Measurements

All commands below were run in this close session, on this working tree, exit
codes read directly. This session runs no `git` command; every fact about
history is read from `events.jsonl`, from the pin cache on disk, or from the
process table.

### Definition of done — one command per bullet

| # | `GATE-03.md` bullet | Command run in this session | Exit | State |
|---|---|---|---|---|
| 1 | The driver executes a pinned build, and records which one | `python3 -m unittest tests.test_installed_copy_driver_e2e -q` → `Ran 9 tests in 3.103s`, `OK`; and over `events.jsonl`, `event_type == 'driver_build_pinned'` → **9** events, the last at 2026-09-09T15:19:31Z naming tree `18c1933c…` and its path under `$TMPDIR/specfuse-pins/`; `ps -eo pid,ppid,etime,command` → PID 1411 `python3 -m specfuse.loop.loop --feature FEAT-2026-0109` with child PID 1413 executing `…/specfuse-pins/18c1933ca3f437ad65e994ea6279e79cc69cc779/_run_pinned.py --feature FEAT-2026-0109` | 0 | **met** |
| 2 | A unit editing `specfuse/loop/*.py` does not halt the run | oracle above; **and in production**: `driver_staleness_detected` with `halted: false` → **2** (T09 at 2026-09-09T13:30:52Z, T10 at 13:32:22Z), each carrying `pinned_tree: 4545ce57…` and a `next_pin_tree`, with the same process dispatching T10 straight after T09's squash (T10 completed 90.1s later); `halted: true` after the pin landed → **0** | 0 | **met** |
| 3 | The pin is transparent to the operator's command | `python3 -c "…resume_command_for('FEAT-2026-0109')"` → `python3 -m specfuse.loop.loop --feature FEAT-2026-0109`, exit 0 — and that exact command is PID 1411 in this session's process table with the pinned `_run_pinned.py` as its child; **and the reuse-integrity half that failed at attempt 1**: the reaped pin `021342f2…` fails `_pin_is_complete`, a fresh pin with two files deleted behind its back is rebuilt rather than reused, and a launcher-shaped import inside the reused pin resolves `specfuse.loop.loop` to the pin. Full output below | 0 | **met** (was `not_met`, #3271; closed by T09) |
| 4 | #1040's guarantee survives — a third state, `pinned at a recorded tree` | all three states exercised directly in this session, exit 0 each: in-tree → `None`; **the live pin `18c1933c…`** → `running a recorded pin of specfuse from …/specfuse-pins/18c1933c… (tree 18c1933c…); the working tree at <REPO_ROOT> is now at tree 00fda5bf…`, no "confidently wrong" text; the pipx-installed wheel (an **unidentified** out-of-tree build) still prints the original warning verbatim. Full output below | 0 | **met** |
| 5 | The cost is stated at the moment it is incurred, in words | stdout probe of the real pinned driver subprocess, `RETURNCODE: 0`: the per-unit seam prints `DRIVER EDIT RECORDED (pinned build <tree>)` naming `next_pin_tree` and "no restart is required"; the gate summary prints `DRIVER EDITS RECORDED (gate summary, pinned build <tree>)` and "No restart was required."; **none** of the three pre-T09 strings appears. Case-insensitive `pin` occurrences on that stdout: **11**, against **2** at attempt 1. Full output below | 0 | **met** (was `not_met`, #3270; closed by T09) |
| 6 | A project that never installed the driver is unaffected | oracle above (`ProjectWithoutDriverSourceIsUnaffected.test_no_pin_materialized_no_new_event`), `OK`, exit 0 | 0 | **met** |
| 7 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `GATE-03-CRITERIA.md`, 11 entries, each carrying `oracle` / `kind` / `state` written by this close; `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` → `CLOSING-READY`, exit 0; `python3 -m unittest tests.test_lint_closing_criteria -q` → `OK`, exit 0 | 0 | **met** |

### feature_oracle: PASS

`python3 -m unittest tests.test_installed_copy_driver_e2e -q` → `Ran 9 tests in
3.103s`, `OK`, exit **0**, run fresh in this session with no
`SPECFUSE_LOOP_PINNED_TREE` in the environment (`env | grep -i specfuse` returns
nothing).

### The five follow-ups attempt 2's judgment produced are environment artifacts, not code defects

Issues **#3273–#3277** were filed from attempt 2's judgment. This close was told
they are artifacts of a pin-marker leak into the judge's environment, and told to
verify that claim rather than accept it. Verified, with the two commands the work
unit names, run back to back in this session:

```
$ env SPECFUSE_LOOP_PINNED_TREE=18c1933ca3f437ad65e994ea6279e79cc69cc779 \
      python3 -m unittest tests.test_installed_copy_driver_e2e
Ran 9 tests in 3.137s
FAILED (failures=3)                                          # exit 1
  FAIL: PinnedRunRecordsAndSurvivesDriverEdits.test_the_run_records_the_build_it_executed
  FAIL: ProjectWithoutDriverSourceIsUnaffected.test_no_pin_materialized_no_new_event
  FAIL: UnpinnedRunStillHalts.test_halt_event_and_exit_code_are_unchanged

$ python3 -m unittest tests.test_installed_copy_driver_e2e
Ran 9 tests in 3.332s
OK                                                           # exit 0
```

One variable, nothing else changed, and the three failing test names are exactly
the three defects `#3273`, `#3274` and `#3276` describe. `#3275` cites the
combined command `tests.test_installed_copy_driver_e2e
tests.test_pin_honesty_and_integrity`; run in this session without the marker it
reports `Ran 14 tests in 5.990s`, `OK`, exit 0. `#3277` is the aggregate — "the
gate's `feature_oracle` does not report `OK` — 3 failures" — and is the same
three.

All five trace to one cause: `run_judge_session` spawned the judge without `env=`,
so a judge dispatched from a **pinned** driver inherited the marker and three
pin-conditional tests took their pinned branch. `75543e7` strips the marker there
and at the smoke-import runner, and adds `tests/test_pin_marker_spawn_sites.py`,
which enumerates spawn sites rather than patching the ones anyone remembers — that
enumeration is what found the smoke-import site nobody had reported. Both modules
are green here:

```
$ python3 -m unittest tests.test_pin_marker_spawn_sites tests.test_pin_marker_not_inherited -q
Ran 6 tests in 0.039s
OK                                                           # exit 0
```

**Stated plainly, because the reverse error is equally bad:** `#3273`–`#3277`
describe no defect in this feature's code. They describe the driver's own test
environment, and the environment is fixed. They are not carried into
`FOLLOW-UPS.md` as open work and they are not counted as unmet criteria. The judge
that filed them was reading true observations of a false environment — itself a
fourth instance of this gate's recurring shape, recorded as such in
`## Retrospective`.

**Attempt 1's two findings are separately, genuinely closed** — re-verified below
against `FOLLOW-UPS.md`'s own re-run conditions rather than against their
`Closed by` lines. Their `### ` headings stay byte-identical so the driver's
deduplication keeps resolving them to #3270 and #3271; their presence in the file
is bookkeeping, not open work.

### The two bullets T09 moved, against `FOLLOW-UPS.md`'s re-run conditions

`FOLLOW-UPS.md` wrote an explicit re-run condition for each. Both are quoted
verbatim and answered against a probe run in **this** session — not against the
gate's oracle, which by `GATE-03.md`'s own binding instruction asserts only on the
subprocess exit code and `events.jsonl` and therefore cannot see either defect.
Attempt 1 found #3270 by reading the subprocess's **stdout**; that is the probe
re-run here.

**#3270 — "A pinned run prints the pre-T08 halt text at the point it declines to
halt."** The condition, verbatim: *"Satisfied when the probe above shows a
pin-aware sentence at both the per-unit seam and the gate summary, and
`UnpinnedRunStillHalts` still passes unchanged. Because the gate's oracle is bound
to `events.jsonl` and the exit code, the covering assertion needs a separate test
that reads the subprocess's stdout."*

```
$ python3 - <<'EOF'          # exit 0
import sys; sys.path.insert(0, ".")
from tests import test_installed_copy_driver_e2e as m
C = m.PinnedRunRecordsAndSurvivesDriverEdits
C.setUpClass(); print("RETURNCODE:", C.proc.returncode); print(C.proc.stdout); C.tearDownClass()
EOF
RETURNCODE: 0

--- pre-T09 wording present on the pinned run's stdout? ---
  'STALE DRIVER PROCESS'                      : 0 occurrences
  'stop this driver now and start a new one'  : 0 occurrences
  'A fresh driver process is required'        : 0 occurrences
--- pin-aware wording present? ---
  'DRIVER EDIT RECORDED (pinned build'                : 1
  'DRIVER EDITS RECORDED (gate summary, pinned build' : 1
  'no restart is required'                            : 1
  'No restart was required'                           : 1
  case-insensitive 'pin' occurrences on stdout        : 11    # was 2 at attempt 1,
                                                              # both the feature slug
```

All three clauses hold: pin-aware text at the per-unit seam, pin-aware text at the
gate summary, and `UnpinnedRunStillHalts` green — it is one of the 9 tests in the
oracle run above, and
`tests/test_pin_honesty_and_integrity.py::UnpinnedTextIsByteIdentical` compares the
unpinned strings against HEAD's wording directly. The covering assertion the
condition asked for exists and is green:
`tests/test_pin_honesty_and_integrity.py::PinnedSeamTextIsPinAware`, which reads
the subprocess's stdout rather than the event log.

**#3271 — "A materialized pin can lose its files and still be reported as the
running build."** The condition, verbatim: *"`materialize_pin`'s reuse check
validates the pin's **content**, not only its marker … Satisfied when a test
materializes a pin, deletes `specfuse/loop/__init__.py` (or any other file) behind
its back, calls `materialize_pin` again, and asserts the returned pin is
**complete** — and when the launcher-shaped import inside a reused pin resolves
`specfuse.loop.loop` to the pin, never to the working tree."*

```
$ python3 -c "…build_provenance.materialize_pin / _pin_is_complete…"     # exit 0
fresh pin: $TMPDIR/specfuse-pins/00fda5bfc544ed948701174619464c6b12a8427e
  complete? True    manifest present: True    manifest lines: 131
  after deleting specfuse/loop/__init__.py and build_provenance.py behind its back:
    marker still matches : True        # the check that used to be the only one
    _pin_is_complete     -> False
  materialize_pin() again -> same dir: True   both deleted files restored: True

REAL REAPED PIN 021342f2… (the build events.jsonl records executing 2026-09-08T20:30:25Z):
  files under specfuse/ : 72        # 131 at materialize time
  marker present : True   manifest present: False   _pin_is_complete -> False

$ python3 -c "sys.path.insert(0, '<pin>'); import specfuse.loop.loop as L; …"   # exit 0
RESOLVED: $TMPDIR/specfuse-pins/00fda5bf…/specfuse/loop/loop.py
  resolves to the PIN      : True
  resolves to WORKING TREE : False
```

Both clauses hold. The pin cache's own chronology corroborates when the fix landed:
of the four pins still on disk that this feature recorded executing, `021342f2…`
and `4545ce57…` (materialized before T09's squash) carry no manifest and
`_pin_is_complete` refuses both; `b396c1a6…` and `18c1933c…` (after) carry one and
pass.

**What T09 did not change.** Pins still live in `tempfile.gettempdir()` and
`shutil.copytree` still preserves source mtimes, so a pin is still born looking
days old to an age-based reaper. What changed is that losing files is now loud
instead of silent: a reaped pin is rebuilt, at the cost of one re-copy, instead of
being executed as a hybrid of pin and working tree. The retention question is
recorded under `## What the loop did NOT verify`.

### Fresh oracle re-runs

Every oracle re-run from scratch in this session, exit codes read directly.

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate 3 `feature_oracle` | `python3 -m unittest tests.test_installed_copy_driver_e2e -q` | `Ran 9 tests in 3.103s`, `OK` | 0 |
| Gate 2 `feature_oracle` | `python3 -m unittest tests.test_tiered_verification_e2e -q` | `Ran 5 tests in 4.798s`, `OK` | 0 |
| Gate 1 `feature_oracle` | `python3 -m unittest tests.test_lazy_baseline_e2e -q` | `Ran 8 tests in 3.041s`, `OK` | 0 |
| Full suite | `python3 -m unittest discover -s tests -q` | `Ran 3833 tests in 173.310s`, `OK (skipped=3)` | 0 |
| Smoke test | `bash scripts/smoke-test.sh` | 16 gates, `smoke test: OK` | 0 |
| Lint sweep | `lint_plan.py` over all **77** `.specfuse/features/*/` folders | 77 linted, **0** ERROR findings, 0 non-zero exits | 0 |
| T09's covering tests | `python3 -m unittest tests.test_pin_honesty_and_integrity -q` | `Ran 5 tests`, `OK` | 0 |
| T10's covering tests | `python3 -m unittest tests.test_red_baseline_never_reused -q` | `Ran 6 tests`, `OK` | 0 |
| Marker-strip tests | `python3 -m unittest tests.test_pin_marker_spawn_sites tests.test_pin_marker_not_inherited -q` | `Ran 6 tests in 0.039s`, `OK` | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | `CLOSING-READY` | 0 |

Both the full suite and the smoke test were run **twice** in this session: once
before this close wrote anything, and once after every edit landed — including
`GATE-03-CRITERIA.md`, which is exactly the kind of `.specfuse/` write that
reddened two of this gate's three broad runs. Second run: `Ran 3833 tests in
174.646s`, `OK (skipped=3)`, exit 0; `smoke test: OK`, exit 0. The corpus check
that failed twice before, `tests.test_lint_closing_criteria`, is green with this
close's criteria artifact in place (`Ran 11 tests`, `OK`, exit 0), and the plan
lint sweep still reports 0 ERROR over all 77 folders.

The suite is **3833** tests, up from 3829 at attempt 2: `TestRedBroadRunIsNeverReused`
(2 tests) arrived with the operator fix described below, and
`tests/test_pin_marker_spawn_sites.py` (2 tests) with `75543e7`.

The lint sweep is run through `.specfuse/scripts/lint_plan.py` rather than the
`specfuse` console script deliberately. `specfuse lint` resolves to the pipx wheel,
which prints its own `build_provenance` warning — *"This command is measuring the
INSTALLED build, not your checkout — results can be confidently wrong rather than
failing"* — and that warning is correct: the installed wheel predates this feature.
Running the in-tree script is what the warning instructs. Its live appearance in
this session is also bullet 4's third state, observed rather than asserted.

### The restart count, against the prediction of 1

| Gate | `driver_staleness_detected` `halted: true` | `halted: false` | Dead time to the next event |
|---|---|---|---|
| 1 | 3 | 0 | 138.3s |
| 2 | 4 | 0 | 419.4s |
| 3 | **1** | **2** | **79.5s** |
| **Feature** | **8** | **2** | **637.2s (10.6 min)** |

**Gate 3's halted count is exactly 1, as this unit's body predicted.** The single
halt fired at 2026-09-08T20:29:06Z naming `wu_id: FEAT-2026-0109/T08`,
`driver_paths: [specfuse/loop/build_provenance.py, specfuse/loop/loop.py]` and
`remaining_wu_ids: [FEAT-2026-0109/G3-CLOSE]` — the pre-T08 driver halting on T08's
own squash, with only the close left to dispatch. 79.5 seconds later the restarted
driver emitted this feature's first `driver_build_pinned`. The prediction — "the
pre-T08 halt fires once, and the restarted driver is the first one to pin" — is
confirmed event for event, and it held even though the gate subsequently grew two
units nobody had drafted when the prediction was written and the close was re-armed
twice more.

`GATE-03.md` recorded this feature at **7** restarts before gate 3 ran, tied worst
repo-wide with FEAT-2026-0100. The feature's final count is **8**; swept over all
71 feature event logs in this repository the count is now **50** across 14
features.

**And the branch that retires the halt fired in production — twice.** T09 and T10
both edited `specfuse/loop/loop.py`; both squashes produced
`driver_staleness_detected` with `halted: false`, `pinned_tree:
4545ce57035e7b67408004da0770a16161e92656`, and a `next_pin_tree` naming the build
the edit takes effect in (`b77b5c95…` for T09, `a5930047…` for T10). T10 was then
dispatched **in the same process** immediately after T09's squash and completed
90.1 seconds later. Under the pre-T08 driver those two units would have cost two
halts and two operator restarts; they cost none.

Being precise about what it took to observe that: gate 3 could only produce this
evidence because the gate *failed*. T08 was the last unit before the close, so
nothing followed it. The two units that exercised the non-halting branch exist only
because the close recorded `not_met` and the operator added them.

### Did this close session run from a pinned build? Yes.

The evidence, in order, none of it inferred from silence:

1. **The process table, read in this session.** `ps -eo pid,ppid,etime,command`
   shows PID **1411** running `python3 -m specfuse.loop.loop --feature
   FEAT-2026-0109` and its child PID **1413** running
   `/private/var/folders/…/T/specfuse-pins/18c1933ca3f437ad65e994ea6279e79cc69cc779/_run_pinned.py
   --feature FEAT-2026-0109`. The driver that dispatched this session is executing
   the pin, not the working tree, right now.
2. `driver_build_pinned` at **2026-09-09T15:19:31Z**, payload `{"tree":
   "18c1933ca3f437ad65e994ea6279e79cc69cc779", "path":
   "…/specfuse-pins/18c1933c…/specfuse/loop"}` — the last such event in the log and
   the ninth this feature has emitted.
3. This work unit's frontmatter `started_at: 2026-09-09T15:23:24.019544+00:00` —
   3m52s after that pin, with no intervening `driver_build_pinned`, no
   `driver_staleness_detected` and no restart of any kind between them. The same
   process emitted `broad_run_result` (`ok: true`, `failing: []`) at 15:23:23.852Z,
   167ms before the dispatch.
4. **The pin validates on disk, by the check T09 added.** `.specfuse-pin-tree` reads
   `18c1933ca3f437ad65e994ea6279e79cc69cc779`, equal to its own directory name;
   `.specfuse-pin-manifest` lists **131** files and `_pin_is_complete` returns
   `True`.
5. **And the build it executes is no longer the working tree's.** `18c1933c…` is the
   tree of commit `90f24e6`; two commits have landed since, and `HEAD^{tree}` now
   reads `00fda5bfc544ed948701174619464c6b12a8427e`. Asked from inside the pin,
   `out_of_tree_warning()` says exactly that and does not call itself an error:

   ```
   running a recorded pin of specfuse from …/specfuse-pins/18c1933ca3f437ad65e994ea6279e79cc69cc779
   (tree 18c1933ca3f437ad65e994ea6279e79cc69cc779); the working tree at
   <REPO_ROOT> is now at tree 00fda5bfc544ed948701174619464c6b12a8427e.
   ```

   This is the "pinned run whose working tree has since moved" case, live, in the
   terminal close of the feature that built it.

Note what this session still cannot read: `SPECFUSE_LOOP_PINNED_TREE` is absent from
this agent's environment (`env | grep -i specfuse` → nothing), and that is correct —
`child_env_without_pin_marker` strips it at every spawn boundary, including the
work-unit dispatch at `specfuse/loop/loop.py:3659`, so a dispatched session does not
take pin-conditional branches. **A close cannot ask its own environment which build
dispatched it**, and this attempt exists because attempt 2's judge could. It has to
read the event log, the pin on disk, and the process table.

### The three counts gate 1 and gate 2 each deferred

Gate 1 deferred all three to "the next failure". Gate 2 deferred them again. Gate 3
is the next failure, and all three moved off zero.

**1. `baseline_attribution` firings: 1 — the first in this repository's history, and
it livelocked the gate.**

```
this feature's events.jsonl                          -> 1
swept over all 71 .specfuse/features/*/events.jsonl  -> 1     (the same one)
```

The single firing is at **2026-09-09T11:58:48Z**, gate 3, payload
`{"attributed_to": "FEAT-2026-0109/T09", "failing": [{"gate": "tests",
"failure_signature": "test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings"},
{"gate": "coverage", "failure_signature": "no_gate_marker"}]}`, followed immediately
by `human_escalation` `reason: preexisting_gate_failure`. Attribution did precisely
what T01 built it to do: T09's first attempt failed, the retroactive probe ran
against the post-reset tree, the failure was pre-existing, and T09's attempt count
was not charged.

And then the mechanism ate itself. The tree was fixed. The next attribution, at
**12:12:54Z**, emitted **no `baseline_attribution` event at all** — it reused the
11:58 record and re-escalated a failure that no longer existed, leaving `attempts`
at 0 again. T09 could not consume an attempt, could not surface its own defect, and
could not progress. Only hand-clearing the block broke the loop, and T10 was added
to fix the class.

The root cause is a collision between two things this feature itself shipped. T02
keys the baseline on `HEAD^{tree}` with the `.specfuse` entry dropped — correct for
its stated purpose, since bookkeeping commits write to `.specfuse/` on every gate
entry. But the `code` gate set *reads* `.specfuse/`: the corpus lint walks real
feature folders, as do the roadmap-link, arm-sweep and event-type gates. So a failure
inside `.specfuse/` can be recorded under a key that no `.specfuse/`-side fix can
move. T07's "at most once per tree state per gate" bound then makes it sticky. T10's
fix is to reuse only a **green** record.

*What the 1 establishes:* attribution works on its first firing, in production,
exactly as designed — the failing set was correctly identified as pre-existing and no
attempt was charged. Three gates of "checked instead by
`tests/test_lazy_baseline_e2e.py`" turned out to be right about the happy path.
*What it does not establish, and what a zero would have hidden:* the mechanism's
**second** call is where it breaks, and no unit test in eight modules covered a red
record surviving its own fix. *What it still does not establish at n=1:* any rate,
and nothing at all about the case the escalation was actually designed for — an
operator who **cannot** fix the pre-existing failure quickly. That case has still
never occurred here.

**2. Attempts that genuinely narrowed: 5 across the feature — and gate 3's own pin is
what made the count knowable.**

Gate 2's close established n=1 (T05) and said the answer could only be reconstructed
by re-running `resolve_narrow_test_selection` against the driver as it stood at close
time. The first gate-3 close could not answer it for T08 at all. Both statements
remain true of the *record*: `attempt_outcome` carries `attempt`, `outcome`,
`duration_seconds`, `cost_usd`, token counts, `model`, `effort`, `failure_*`,
`files_touched`, `agent_status`, `agent_blocked_reason`, `re_arm_count` — and nothing
about which tier ran or what it selected.

But gate 3 ships a cache of the driver source keyed by the tree it ran at, so for a
unit dispatched from a pin the question is answerable after the fact by reading the
build itself. Re-read in this session:

```
<pin>/4545ce57…/specfuse/loop/loop.py:4629     CHANGED_FILE_SELECTION_ENABLED = False
     working tree specfuse/loop/loop.py:4694   CHANGED_FILE_SELECTION_ENABLED = False
resolve_narrow_test_selection: byte-identical between pin 4545ce57… and this tree -> True
```

`4545ce57…` is the build that dispatched T09's passing attempt and T10, so today's
computation is valid for that build:

```
T09  produces=[…, tests/test_pin_honesty_and_integrity.py]  -> ['tests.test_pin_honesty_and_integrity']
T10  produces=[…, tests/test_red_baseline_never_reused.py]  -> ['tests.test_red_baseline_never_reused']
```

T09's three attempts and T10's one attempt all ran a genuine narrow selection with no
fallback: **4 in gate 3** on top of gate 2's **1**, for **5** across the feature. T08
remains undeterminable — it was dispatched by the pre-T08, unpinned driver, and there
is no pin of that build to read.

*What the 5 establishes:* the declared-tests rule resolves cleanly for every
implementation unit in this feature, and with the changed-file half off there is no
fallback left to cancel the saving — which is what gate 2's measurement predicted.
*What it does not establish:* anything about narrowing's **safety**; that is the third
number. And the method has a shelf life worth naming: the pin cache is a `$TMPDIR`
cache, `021342f2…` has already lost most of its 131 files, and `loop.py` surviving in
`4545ce57…` is luck. A build you can read only until the OS reaps it is not a record.

**3. Broad runs that went red on narrow-passed work: 3 — and one of them is the first
real evidence in this repository that narrowing let something through.**

This is the number gates 1 and 2 both recorded as 0 and deferred to "the first gate in
which a broad run actually goes red". All three reds are in gate 3. Swept over all 71
feature event logs: **7** broad runs have ever executed in this repository, 4 green
and 3 red, and all 7 are in this feature.

| When | Gate | `ok` | Failing signature |
|---|---|---|---|
| 2026-09-08T17:45:06Z | 2 | true | — |
| 2026-09-08T20:33:47Z | 3 | **false** | `test_driver_edit_halts_before_next_dispatch`; `coverage`/`no_gate_marker` |
| 2026-09-09T11:12:05Z | 3 | true | — |
| 2026-09-09T13:35:58Z | 3 | **false** | `test_skip_uses_recorded_failing_set`; `coverage`/`no_gate_marker` |
| 2026-09-09T13:49:39Z | 3 | true | — |
| 2026-09-09T15:05:22Z | 3 | **false** | `test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings`; `coverage`/`no_gate_marker` |
| 2026-09-09T15:23:23Z | 3 | true | — |

**Red 1 (after T08) was not a narrowing miss.** T08's own verification ran under the
pre-T08, unpinned driver, whose subprocesses have no `SPECFUSE_LOOP_PINNED_TREE` to
inherit; a full-suite run at that attempt would have been green. The defect
(`child_env_without_pin_marker`) became observable only once the pin existed. It is a
datapoint about the broad run's value and about gate 3's "a driver change takes effect
at the next run" property, not about narrowing.

**Red 2 (after T10) is the datapoint the first was not.** T10 passed its own
per-attempt verification at 13:32:22Z with narrow selection
`['tests.test_red_baseline_never_reused']` — its own `produces:` module and nothing
else. 216 seconds later the broad run went red on `test_skip_uses_recorded_failing_set`,
a test **not in that module**: T10 changed the baseline-reuse contract and an existing
test asserting the old contract broke. That test existed and was green before the
squash, so a full-suite run at that attempt would have caught it. The narrow tier
structurally could not.

**Red 3 (after the close's second attempt) was not a narrowing miss either — it was
this close's own artifact.**
`test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings` asserts
that no real feature folder produces a `close-l` finding. Re-arming `G3-CLOSE` reset
`attempts` to 0 while the `GATE-03-CRITERIA.md` that attempt 2 committed still
recorded `attempt: 1` on its broad entries, so the corpus lint refused the tree —
*"close-l: G3-CLOSE#N: broad entry reads state: pass but attempt '1' != current
attempt '0'"*. It is the second occurrence of that exact cause; `ac350cb` cleared the
artifact both times. A hand re-arm resets a close's counters and does not touch its
criteria artifact, and the mismatch is charged to the code.

**And red 3 exposed a fourth instance of this gate's recurring defect.** At 15:13:37Z
the driver raised a *second* `broad_run_gate_failure` escalation with no
`broad_run_result` event between them: `gate_broad_run_check` replayed the red record
from 15:05:22Z without re-running a single gate, for a failure the tree no longer had.
`90f24e6` fixed it — the same fix T10 made for the baseline record, applied to the
cache T10 did not cover — and `TestRedBroadRunIsNeverReused` is its covering test. The
broad run at 15:23:23Z then ran for real and came back `ok: true, failing: []`. That
is the run this close was dispatched behind.

*What the 3 establishes:* the once-per-gate broad run is load-bearing on every shape it
was built for. Red 1 caught something no other surface in the system could see — that
test module's own docstring records the failure as "invisible to `smoke-test.sh`, to
CI, and to any local run, because none of those has the marker set". Red 2 caught
exactly what the driver's own escalation text claims it catches: *"the per-attempt
narrow tier … scopes checks to changed files as a speed optimization — this full-set
run is the safety net that catches what that narrowing missed."* Until 13:35:58Z on
2026-09-09 that sentence was a design claim. It is now a measurement.

*What it does not establish:* a rate. **One** narrowing miss in five genuinely narrowed
attempts is not a safety number, it is an existence proof, and the denominator is far
too small to price the trade. Two of the three reds were not narrowing misses at all,
which is the more honest reading of the count: the broad run's realised value in this
feature was mostly catching things *no* tier would have caught, not things the narrow
tier dropped. It also says nothing about the window between a miss and its catch: red 2
was caught 216 seconds later because T10 happened to be the gate's last unit. A miss by
an early unit in a long gate is carried by every subsequent unit's attempt until the
gate boundary, and nothing here measured that.

*Cost of the three catches:* red 1 halted at 2026-09-08T20:33:47Z and the next run
pinned at 2026-09-09T11:08:31Z — **52,484s (14.6 hours)** of dead time. Red 2 halted at
13:35:58Z, next pin 13:46:00Z — **602s (10.0 min)**. Red 3 halted at 15:05:22Z, next
pin 15:19:31Z — **849s (14.2 min)**. Against the 637.2s the feature's eight driver
restarts cost in total. **Gate 3 removed a tax measured in minutes; the feature then
paid fifteen hours to a different, correct halt.** That is the honest shape of the win:
gate 3 buys the ability to run unattended *between* halts, not the absence of halts.
Both `preexisting_gate_failure` halts and all four `broad_run_gate_failure`
escalations still stop the run for a human.

### Per-criterion state

Recorded in `GATE-03-CRITERIA.md`, 11 entries, one per acceptance criterion of this
work unit, each carrying the oracle that proved it, that oracle's `kind` (`narrow` /
`broad`) and its `state` — written by this close from the runs above and never
inferred. `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` reports
`CLOSING-READY` (exit 0) with no `close-l` finding, and `python3 -m unittest
tests.test_lint_closing_criteria -q` reports `OK` (exit 0) over the whole real feature
corpus including this folder.

## Retrospective

Gate 3 did the thing it was for, and then the feature spent two more units and
$4.81 proving it. The driver materializes a pin, re-execs into it, records what
it executed, says so in words when it declines to halt, refuses a pin that has
lost files, and dispatched two consecutive driver-editing units without a single
restart. This close is the first work unit in this repository dispatched by a
driver that can say which build it is, and it can now read that build off disk.

The gate was one substantive unit because `[FEAT-2026-0019/G1]` said a harness
migration cannot be decomposed. That was right about T08, which passed on
attempt 1 at $4.55 against $6.50 planned. It was also, in retrospect, the reason
the gate had no second unit to exercise its own central branch — and the first
close therefore had to close a gate whose headline property had never fired.

What the gate did not anticipate is that its two failures would both be about
*telling the operator the truth* rather than about the mechanism, and that the
correction would surface a third defect nobody had looked for. T09 fixed the
words and the pin's integrity check. Retrying T09 is what made attribution fire
for the first time in this repository's history, and attribution's first firing
livelocked the gate: a red baseline record, keyed on a tree hash that
deliberately ignores `.specfuse/`, outliving the `.specfuse/`-side fix that
cleared it. Two attempts and 24 minutes of dispatch were spent on a unit whose
attempt counter never moved. T10 fixed that in 90 seconds and $0.47, and then
its own squash broke a test asserting the old contract, which the broad run
caught. Then the close itself failed twice more, for two reasons that were
neither the gate's mechanism nor anyone's code: a judge that inherited the
driver's pin marker and filed five follow-ups against a false environment, and a
re-arm that reset this close's `attempts` counter while leaving its criteria
artifact recording the old one. Six defects across the gate, five of them found
only by running the thing.

The pattern worth naming is that almost every one of them was a **cache trusting
its key instead of its contents, or a state carried across a boundary that
should have reset it**. The pin trusted a marker file and executed a directory
that had lost most of its files. The baseline record trusted a tree hash that by
design excludes the directory the gates read. The broad-run record repeated that
exact mistake in the cache T10's fix did not cover, and replayed a red verdict
for a tree that no longer had the failure — the fourth instance, caught at
15:13:37Z and fixed by `90f24e6`. And on the environment side: the pin marker
survived a process boundary it had no business crossing, and `attempts` was
reset at a boundary the criteria artifact did not know about. Nothing here
failed loudly. Every one produced a confident answer that was wrong, which is
the exact failure mode `build_provenance` exists to prevent and the one #1040
named. A cache is a promise that re-deriving would give the same answer, and
none of these keys could see the thing that had changed.

The generalization the feature earned the hard way: **a fix for a
trusting-the-key cache should be applied to every cache in the same commit, and
the spawn/re-arm boundaries should be enumerated rather than patched one at a
time.** `75543e7` did the enumeration for spawn sites and immediately found a
site nobody had reported; `90f24e6` had to be written because T10 fixed one of
two identical caches. The two remedial units cost $4.81; the four repeat
instances that followed them cost far more than that in halts.

### Contract surface gate 3 changed

Recorded in the same shape gates 1 and 2 used, and folded into the reconciled
enumeration below.

1. **New driver event type `driver_build_pinned`** (T08) — added to
   `specfuse/loop/data/schemas/driver-event.schema.json`, emitted once per
   process before any dispatch when the process is itself a materialized pin,
   carrying `tree` and `path`.
2. **`driver_staleness_detected` gains a non-halting shape** (T08) — the same
   event type with `halted: false` plus `pinned_tree` and `next_pin_tree`. No
   schema addition; the registry constrains the type list, not the payload.
3. **Behavioural default change: a driver-editing unit no longer halts a pinned
   run** (T08). An unpinned run is byte-identical to before
   (`UnpinnedRunStillHalts`).
4. **Two environment variables** (T08). `SPECFUSE_PIN_CACHE_DIR` overrides where
   pins are materialized (operator-facing). `SPECFUSE_LOOP_PINNED_TREE` is the
   driver's own pin marker, set on the re-exec and **stripped from every child
   process** — a gate command must never see it.
5. **A pin cache on disk** (T08, extended by T09) —
   `$TMPDIR/specfuse-pins/<tree-hash>/`, holding a copy of `specfuse/`, a
   generated `_run_pinned.py` launcher, a `.specfuse-pin-tree` marker, and — as
   of T09 — a `.specfuse-pin-manifest` listing every file the copy contained at
   materialize time.
6. **`build_provenance.out_of_tree_warning` gains a third state** (T08) — a
   recorded pin now reports both tree hashes in plain text; only an
   *unidentified* out-of-tree build keeps the "confidently wrong" warning.
7. **The changed-file half of the per-attempt selection is off by default** —
   `CHANGED_FILE_SELECTION_ENABLED = False`, on gate 2's measured evidence
   (+38.4s realised, −43.4% with the half off). T05's code and tests are kept,
   not deleted; the flag is to be flipped in the same change that lands the map.
8. **Dispatched sessions are told to run the narrow tier** —
   `.specfuse/rules/result-contract.md`,
   `.specfuse/rules/verification-discipline.md`,
   `.specfuse/templates/WU.template.md` and the `verification` skill (plus their
   `specfuse/loop/data/` mirrors) now instruct a work-unit session to run its
   type's gate set **minus** `tier: broad`, with `tests` through
   `narrow_command`, and never the full suite. This is the agent-facing half of
   gate 2's driver-side split; it landed in gate 3's window as operator commits
   rather than as a work-unit squash, which is why no gate's close enumerated it
   before the previous close attempt.
9. **The pinned staleness seam and gate summary print their own text** (T09) —
   `format_driver_staleness_warning` and `format_driver_staleness_summary` take
   optional `pinned_tree` / `next_pin_tree`; with them they name the pin, name
   the build the edit takes effect in, and say the process continues against its
   snapshot. Without them the pre-T09 wording is reproduced byte-for-byte.
   Operator-visible output, changed on the pinned path only.
10. **A pin is reused only when its recorded content is still present** (T09) —
    `materialize_pin` validates the manifest, not just the marker, and rebuilds
    a partially reaped pin from scratch.
11. **A red baseline record is never reused; only a green one is a cache**
    (T10) — a `baseline:` record whose `failing` is non-empty always re-probes,
    at any tree state. Behavioural change to `--no-baseline-probe`'s subject
    matter; the key computation, when attribution fires, and the once-per-tree
    -state bound for green records are all unchanged.
12. **A red `broad_run:` record is never reused either** (`90f24e6`, an operator
    commit landed after this close's second attempt) — `gate_broad_run_check`
    reused any record whose tree key matched, red or green, so a red broad run
    recorded against `.specfuse/` content could not be invalidated by the
    `.specfuse/`-side change that fixed it. The same defect as item 11, in the
    cache item 11 did not cover; the gate livelocked on it once, replaying a red
    verdict at 15:13:37Z without re-running a gate. A green record is still
    reused at an unchanged tree, so T06's whole dedup benefit is intact.
    Covering test: `tests/test_red_baseline_never_reused.py::TestRedBroadRunIsNeverReused`.

## Consumer-visible contract changes

The reconciled enumeration across gates 1, 2 and 3, built from gate 1's staged
list (`### Contract surface gate 1 changed`, 3 items), gate 2's staged list
(`### Contract surface gate 2 changed`, 7 items) and gate 3's above (12 items),
with gate 2's item 5 (T07's three reworded claims) folded into item 15 as
documentation-only. **Twelve `added`, six `changed`, five `fixed` — 23 items.**
Neither gate 1's nor gate 2's section was read for anything but its own list,
and neither was edited to produce this. Every item below has a matching
`CHANGELOG.md` `Unreleased` entry carrying `FEAT-2026-0109`, `#3270` or `#3271`;
`parse_changelog` over `Unreleased` reports `{'added': 12, 'changed': 6,
'fixed': 3}` for `FEAT-2026-0109` plus 2 `fixed` traced to `#3270` / `#3271`,
which is the same 23.

**Added**

1. `tier:` key on a `code:` gate entry in `verification.yml` (gate 2 / T04).
   Value `broad` opts a gate out of the per-attempt run. **Absent key means
   "runs in both tiers"**, so a `verification.yml` predating this feature
   behaves byte-identically.
2. `narrow_command:` key on a `code:` gate entry (gate 2 / T04). A template
   carrying `{selected_test_modules}`, run instead of `command` per attempt.
   Orthogonal to `tier:`.
3. `broad_run:` frontmatter block on `GATE-NN.md` (gate 2 / T06), keys `tree` /
   `ran_at` / `ok` / `failing`. A missing or malformed block degrades to
   "never run".
4. `tree:` and `source:` keys on the `baseline:` record (gate 1 / T02, T03).
   Both optional; legacy records still parse.
5. New driver event type `baseline_attribution` (gate 1 / T01).
6. New driver event type `broad_run_result` (gate 2 / T06), plus the new
   `human_escalation` reason value `broad_run_gate_failure`.
7. New driver event type `driver_build_pinned` (gate 3 / T08).
8. `driver_staleness_detected` gains a non-halting shape with `pinned_tree` and
   `next_pin_tree` (gate 3 / T08).
9. `SPECFUSE_PIN_CACHE_DIR` environment variable (gate 3 / T08).
10. `SPECFUSE_LOOP_PINNED_TREE` environment variable — the driver's pin marker,
    stripped from every child process (gate 3 / T08).
11. A pin cache directory `$TMPDIR/specfuse-pins/<tree-hash>/` containing a copy
    of `specfuse/`, a `_run_pinned.py` launcher, a `.specfuse-pin-tree` marker
    and a `.specfuse-pin-manifest` (gate 3 / T08, manifest added by T09).
12. `.specfuse-changed-file-test-map.json` reserved in `.gitignore` (gate 2 /
    T05). Nothing writes it.

**Changed**

13. The gate-entry `code`-set baseline probe no longer runs (gate 1 / T01).
    `--no-baseline-probe` and the `baseline_probe` key keep their names and now
    govern retroactive attribution rather than the entry probe.
14. A work unit that edits `specfuse/loop/*.py` no longer halts a **pinned** run
    (gate 3 / T08). An unpinned run is byte-identical to before.
15. `build_provenance.out_of_tree_warning` gains a third state, `pinned at a
    recorded tree` (gate 3 / T08) — both hashes reported, no alarming text. Only
    an unidentified out-of-tree build keeps the original warning. Documentation
    alignment on the same surface: the attribution bound is stated as "once per
    **tree state** per gate" in `GATE-01.md`, `attribute_failure_to_baseline`'s
    docstring and `PLAN.md` (gate 2 / T07) — wording only, no behaviour moved.
16. `[tool.coverage.run] dynamic_context = "test_function"` in `pyproject.toml`
    (gate 2 / T05). Changes what every `coverage run` in this repo records and
    grows `.coverage` 27×; +9.1% on a full run.
17. The changed-file half of the per-attempt test selection is **off by
    default** (gate 3), `CHANGED_FILE_SELECTION_ENABLED = False`. T05's code and
    tests are retained.
18. A dispatched work-unit session is instructed to run the **narrow tier**, not
    the full suite — `result-contract.md`, `verification-discipline.md`,
    `WU.template.md` and the `verification` skill, with their
    `specfuse/loop/data/` mirrors (gate 3). Consumer-visible to any project
    vendoring the scaffold.

**Fixed**

19. A recorded baseline *failure* outlived the change that fixed it and
    livelocked a gate; a `baseline:` record whose `failing` is non-empty is now
    never reused and always re-probes, while a green record stays a real cache
    (gate 3 / T10). The key computation, the firing condition and the
    once-per-tree-state bound for green records are unchanged.
20. The pin marker no longer leaks into child processes (gate 3). Every gate
    subprocess of a pinned driver used to inherit `SPECFUSE_LOOP_PINNED_TREE`
    and take pin-conditional branches; `child_env_without_pin_marker` strips it
    at each spawn boundary.
21. A pinned run no longer prints the pre-pin "stop this driver now and start a
    new one" text at the point it declines to halt (gate 3 / T09, #3270). Both
    the per-unit seam and the gate-completion summary are pin-aware; the
    unpinned wording, event and exit code 3 are unchanged byte-for-byte.
22. A pin that has lost files is rebuilt rather than reused and reported as the
    running build (gate 3 / T09, #3271). Reuse now requires every file in the
    pin's manifest to still be present.
23. A red `broad_run:` record was replayed instead of re-run, for the same
    reason a red `baseline:` record was (gate 3 / `90f24e6`). Reuse of the
    once-per-gate broad-run record is now restricted to a **green** record; a
    green record at an unchanged tree is still reused, so the dedup that makes
    the broad run affordable is unchanged.

**Breaking**

None. Every key above is additive with an absent-key default that preserves
prior behaviour; the behavioural default changes (13, 14, 17) and the baseline
reuse fix (19) are scoped either to a driver-source checkout, which downstream
projects do not have, or to the driver's own baseline bookkeeping, which no
consumer reads.

## Cost analysis

`PLAN.md` frontmatter still reads `planned_cost_usd: 26.00`. It was **not**
corrected. `GATE-02-REVIEW.md` Q4 flagged it, `GATE-03-REVIEW.md` Q3 flagged it
again and left it to the operator, both prior close attempts recorded it, and
this close does not own `PLAN.md`. The arithmetic follows, reported against the
WU sums rather than against a figure already known to be wrong.

Per-unit, from `events.jsonl` `attempt_outcome` payloads (summed across
attempts, so failed attempts are included), against each WU's own
`planned_cost_usd` frontmatter:

| Unit | Gate | Planned | Actual | Attempts | Duration |
|---|---|---|---|---|---|
| T01 lazy attribution | 1 | $3.50 | $3.79238 | 1 | 2092.1s |
| T02 tree-hash keying | 1 | $2.00 | $1.59976 | 1 | 1394.5s |
| T03 baseline provenance | 1 | $2.00 | $0.78003 | 1 | 667.5s |
| G1-CLOSE-INTERMEDIATE | 1 | $4.50 | $3.11467 | 1 | 942.4s |
| G1-PLAN | 1 | $6.00 | **$12.70105** | **5** | 1812.8s |
| T04 per-attempt tier | 2 | $4.00 | $3.37960 | 1 | 1375.4s |
| T05 changed-file selector | 2 | $4.00 | $4.28166 | 1 | 2357.8s |
| T06 per-gate broad run | 2 | $3.50 | $2.25820 | 1 | 1251.0s |
| T07 attribution tree bound | 2 | $1.50 | $0.87782 | 1 | 676.8s |
| G2-CLOSE-INTERMEDIATE | 2 | $4.50 | $6.66057 | 1 | 2185.8s |
| G2-PLAN | 2 | $6.00 | $6.34852 | 1 | 796.7s |
| T08 installed-copy driver | 3 | $6.50 | $4.54640 | 1 | 2072.9s |
| T09 pin honesty and integrity | 3 | $4.00 | $4.33568 | **3** | 2263.1s |
| T10 red baseline never reused | 3 | $2.50 | $0.47220 | 1 | 90.1s |
| G3-CLOSE (attempts 1 + 2) | 3 | $8.00 | **$29.78817** | **2** | 3385.5s |

Plus **$0.82575** in judge sessions (2 of them: $0.64077 at 11:40:07Z,
$0.18498 at 14:20:55Z), which `attempt_outcome` does not carry. **This close's
own third attempt is not in `events.jsonl` yet**; its planned $8.00 was
consumed by attempt 1 alone.

Per gate, and per feature:

| Scope | Planned | Actual | Delta |
|---|---|---|---|
| Gate 1 (5 units, 9 attempts) | $18.00 | $21.98789 | **+$3.99 (+22.2%)** |
| Gate 2 (6 units, 6 attempts) | $23.50 | $23.80637 | +$0.31 (+1.3%) |
| Gate 3 (4 units, 7 attempts) | $21.00 | $39.14245 | **+$18.14 (+86.4%)** |
| **Feature, WU-sum (15 units, 22 attempts)** | **$62.50** | **$84.93671** | **+$22.44 (+35.9%)** |
| Feature, incl. judge sessions | $62.50 | **$85.76246** | +$23.26 (+37.2%) |
| **Feature, `PLAN.md` figure** | **$26.00** | **$85.76246** | **+$59.76 (+229.9%)** |

**The delta, named.** Against the WU sums the drafts actually declare, the
feature is **$22.44 (+35.9%) over**, or $23.26 (+37.2%) counting the judge, with
this close's third attempt still unpriced. Against `PLAN.md`'s
`planned_cost_usd`, it is **229.9% over** — and that figure is stale, not
exceeded: $26.00 describes gate 1's five units plus a scaffolded gate-3 close,
and was never raised when gate 2's six units, gate 3's two, or the two remedial
units drafted after the first close were added. The plan lint says so unprompted
on every run, and did in this session:

```
WARN: PLAN.md: planned_cost_usd $26.00 differs from sum of WU planned costs
      $62.50 (delta 140%, threshold 10%). Review estimates.
```

It is also what `arm_predicate_evaluated` fired `budget_projection` against at
gate 3's boundary — *"projected spend $92.94 … exceeds 2.0x baseline planned
total $26.00 (cap $52.00)"* — a stop class computed entirely from a number
nobody maintained. **$62.50 is the arithmetic.** Correcting the field is the
operator's call; it is not an acceptance criterion of any work unit and
`PLAN.md` is the driver's.

**Implementation-only, the number that is actually about estimation quality:**

| Gate | Planned | Actual | Delta |
|---|---|---|---|
| 1 (T01–T03) | $7.50 | $6.17217 | −17.7% |
| 2 (T04–T07) | $13.00 | $10.79728 | −16.9% |
| 3 (T08–T10) | $13.00 | $9.35428 | **−28.0%** |
| **All 10 units** | **$33.50** | **$26.32373** | **−$7.18 (−21.4%)** |

FEAT-2026-0101's recalibrated estimates held across all three gates and all ten
implementation units. No re-calibration is indicated for implementation work.

**Every dollar of overrun is in a closing or planning unit, and the gap widened
with each close attempt:**

| Scope | Planned | Actual | Delta |
|---|---|---|---|
| 10 implementation units | $33.50 | $26.32373 | −21.4% |
| 5 closing / planning units | $29.00 | $58.61298 | **+102.1%** |

Two units account for nearly all of it. **G1-PLAN** cost $12.70 against $6.00
across **5** attempts — three `closing_deliverable_missing` guard refusals, a
`deterministic_refusal_repeat` escalation, a re-arm, an `agent_reported_blocked`,
and a second re-arm. **G3-CLOSE** cost $29.79 against $8.00 across two completed
attempts, and the third is running. Of that $29.79, attempt 2's $17.17 bought a
`met` the judge then lowered on evidence that was an artifact of the judge's own
environment — the single most expensive item in this feature, and it was not
spent on the feature's subject matter at all. Nine of the ten implementation
units passed on attempt 1.

**The livelock's price, isolated.** T09's first two attempts cost **$3.09577**
across **1427.7s (23.8 min)** and neither incremented T09's attempt counter —
`attempts` still reads 1 in its frontmatter. That is 71% of T09's total spend,
bought by a red baseline record that could not be invalidated by the fix that
cleared it. It is also, precisely, the cost `PLAN.md` accepted in the abstract
when gate 1 made attribution lazy — "one burned dispatch when the tree is
genuinely pre-broken" — paid for the first time, at twice the stated unit because
the bound made it repeatable. T10 removed the class for $0.47, and `90f24e6`
removed its twin in the broad-run cache for the price of an operator commit.

### Failure-class breakdown

| `failure_class` | Attempts | Units |
|---|---|---|
| `guard_refusal` | 3 | G1-PLAN (`closing_deliverable_missing`, `assert_next_gate_drafted_or_terminal` ×3) |
| `lint` | 2 | T09 (both attributed to a pre-existing failure; neither charged) |
| (none — `blocked`) | 1 | G1-PLAN (`agent_reported_blocked`) |
| — (passed) | 16 | all others |

22 attempts across 15 units. **No implementation unit produced a non-passing
attempt that was charged against it in any gate.** Both of T09's `lint` failures
were attributed to the pre-existing `.specfuse/`-side failure and left its
counter at 0 — which is the livelock, and is why the count of *charged* failures
across ten implementation units is zero while the gate still took three
dispatches to get T09 through.

The two verdicts this close's predecessors recorded are not in this table because
`attempt_outcome` records them as `passed`: attempt 1 passed its guards and was
judged `not_met` (2 findings, unlowered); attempt 2 passed its guards, recorded
`met`, and was judged `not_met` (5 findings, `lowered: true`, `disagreed: true`).
Both `judged` events are in `events.jsonl`.

## What the loop did NOT verify

Each entry names the criterion, why it went unverified here, and where it
actually gets checked.

1. **Whether a pin survives the reaper — only whether it is caught when it does
   not.** *Criterion:* bullet 1's "materializes that package into a
   content-addressed build outside the working tree … and executes from it".
   *Reason:* T09 took the manifest half of `FOLLOW-UPS.md`'s "and/or" and left
   pins in `tempfile.gettempdir()` with `shutil.copytree`'s preserved mtimes, so
   a pin is still born looking days old to an age-based cleaner. Relocating the
   cache and choosing a retention policy is an operator decision this unit's
   escalation trigger explicitly declined to make. *Checked instead by:*
   `tests/test_pin_honesty_and_integrity.py::AReapedPinIsRebuiltNotReused`, and
   in this session by `_pin_is_complete` refusing the real reaped pin
   `021342f2…`. *What is unmeasured:* the re-copy rate in steady state. Every
   pin in this cache is 131 files; if the reaper runs between two runs at the
   same tree, the second pays a full re-copy instead of a reuse, and nothing
   counts that.

2. **Which tier any given attempt ran, from the record.** *Criterion:* implicit
   in gate 2's definition of done and load-bearing for every close that reports
   on it. *Reason:* `attempt_outcome` carries no `tier`, no selection and no
   resolved command. *Checked instead by:* nothing in the record. This close
   recovered it for T09 and T10 by reading `CHANGED_FILE_SELECTION_ENABLED` and
   `resolve_narrow_test_selection` out of the pin that dispatched them — which
   works only for pinned units, only while the pin survives, and not at all for
   T08. *Where it gets checked:* nowhere today. Two fields on the event the
   driver already emits would close it.

3. **The size of the narrowing risk.** *Criterion:* implicit in gate 2's tier
   split. *Reason:* the broad run went red three times, but only one of the
   three (red 2, after T10) was a genuine narrowing miss; the other two caught
   defects no tier would have caught. n=1 numerator, n=5 denominator, one repo,
   one feature. *Checked instead by:* nothing — there is no synthetic test for
   "how often does a unit break a test outside its own module". *Where it gets
   real evidence:* accumulated `broad_run_result` events over many features.
   **Seven** broad runs have ever executed, all seven in this feature.

4. **The window between a narrowing miss and its catch.** *Criterion:* none
   states it, which is the point. *Reason:* T10's miss was caught 216 seconds
   later because T10 was the gate's last unit. A miss by an early unit in a long
   gate is carried by every subsequent unit's attempt until the gate boundary,
   and no unit in this feature was in that position. *Checked instead by:*
   nothing. *Where it gets real evidence:* the first multi-unit gate whose broad
   run goes red on a unit that was not the last one.

5. **`specfuse run --feature X` reaching the pin.** *Criterion:* bullet 3's
   "`specfuse run --feature X` and `python3 -m specfuse.loop.loop --feature X`
   both still work and both reach the pinned execution". *Reason:* the `-m` form
   is verified in production — it is PID 1411 in this session's process table,
   with the pinned `_run_pinned.py` (PID 1413) as its child. The console-script
   form is not: `specfuse lint` run in this session printed `build_provenance`'s
   unidentified-out-of-tree warning, because today's installed wheel predates
   T08. *Checked instead by:*
   reading the installed `specfuse/cli.py` dispatch table, which maps `"run"` to
   `specfuse.loop.loop:main`, the function that calls `_reexec_pinned`. *Where
   it gets real evidence:* the first run from a wheel built after this feature
   merges — gate 3's own "takes effect at the next run" property, one level up.

6. **A downstream project upgrading without editing `verification.yml`.**
   *Criterion:* carried from gate 2 — absent-`tier:` behaviour. *Reason:* this
   repository declares `tier: broad` on nine gates and cannot stand in for a
   project that declares none. *Checked instead by:*
   `test_a_config_with_no_tier_keys_is_byte_identical_to_today`. Unchanged from
   gate 2's item 5 and the previous close attempt's item 7.

7. **Attribution's behaviour on a genuinely pre-broken tree that stays broken.**
   *Criterion:* gate 1's "a pre-existing failure escalates
   `preexisting_gate_failure` … and is not counted against the unit's attempts".
   *Reason:* the one production firing was a `.specfuse/`-side failure that was
   fixed between attempts, which is what exposed the livelock. The case the
   escalation is actually designed for — an operator who cannot fix the
   pre-existing failure quickly — has still never occurred here. *Checked
   instead by:* `tests/test_lazy_baseline_e2e.py` (8 tests) and
   `tests/test_red_baseline_never_reused.py` (6 tests). *Where it gets real
   evidence:* the next red baseline that stays red.

8. **Whether the judge now reads a clean environment on a pinned run.**
   *Criterion:* none states it, which is the defect. *Reason:* `75543e7` strips
   the pin marker at `run_judge_session` and at the smoke-import runner, and
   `tests/test_pin_marker_spawn_sites.py` asserts every non-git `subprocess`
   spawn in `loop.py` passes an explicit env. That is a structural assertion
   over the source, not an observation of a judge session. The judge that runs
   after this close is the first to exercise the fixed path, and it runs *after*
   this close reports — so this close structurally cannot verify it. *Checked
   instead by:* `tests/test_pin_marker_spawn_sites.py` (2 tests) and
   `tests/test_pin_marker_not_inherited.py` (4 tests), plus the one-variable
   reproduction in `## Measurements`. *Where it gets real evidence:* this
   feature's own next judge session.

9. **That a re-armed close cannot again desync from its criteria artifact.**
   *Criterion:* none — it is not a property of this feature at all, which is why
   it kept costing this feature money. *Reason:* re-arming a close resets
   `attempts` and does not touch `GATE-NN-CRITERIA.md`, so the corpus lint's
   `close-l` check refuses the tree; it happened twice here (`53f4996`,
   `ac350cb`), and the second time cost a red broad run and a halt. Nothing in
   this feature's scope owns the re-arm path. *Checked instead by:* nothing —
   both occurrences were repaired by hand. *Where it gets fixed:* the re-arm
   surface (`/unblock-wu` and the driver's own re-arm) clearing or re-stamping
   the criteria artifact alongside the counters. Not filed as a follow-up
   because it is not a failed criterion of this unit; recorded here so the next
   re-arm of any close does not rediscover it.

## Lessons

1. **When a driver picks between two behaviours per attempt, the branch it took
   belongs in that attempt's record — and a snapshot of the code is not a
   substitute for it.** This feature shipped a per-attempt/per-gate tier split
   across two gates and added neither a `tier` field nor the resolved selection
   to `attempt_outcome`. Gate 2's close could answer "did this attempt narrow?"
   only by re-running the predicate against the driver as it stood at close
   time; the first gate-3 close could not answer it for T08 at all. This close
   *could* answer it for T09 and T10 — but only because gate 3 happens to cache
   the driver source by tree hash, so the build that dispatched them is still
   readable on disk. That is a lucky affordance, not a record: the cache lives
   in `$TMPDIR`, one of this feature's own pins has already lost 91 of its 131
   files, and `loop.py` surviving in it is chance. Reconstructing a decision by
   re-executing the code that made it is strictly weaker than writing the
   decision down, because it can only ever answer for the runs whose code you
   still have. **The drafting-time check is one question: name the command the
   close will run to count how often each branch fired.** If the honest answer
   involves re-implementing the predicate, or reading a build out of a temp
   directory, the branch is unrecorded, and one field on an event the driver
   already emits fixes it.

2. **A cache keyed on identity must validate its contents, and a negative
   result is never a cache.** Gate 3 produced **three** instances of the same
   failure within two days, in code written by three different hands on the same
   feature, plus a fourth in the same family on the environment side. The pin
   trusted a marker file naming a tree hash and executed a directory that had
   silently lost most of its 131 files, resolving the program back to the
   working tree while still emitting "I am running build X". The baseline record
   trusted a tree hash that deliberately excludes `.specfuse/` — correct for
   surviving bookkeeping commits — while the gates it summarises *read*
   `.specfuse/`, so a recorded failure could not be invalidated by the fix that
   cleared it, and the gate livelocked: two dispatches, $3.10, 24 minutes, and
   an attempt counter that never moved. The **broad-run** record then repeated
   that mistake verbatim in the one cache the baseline fix did not cover, and
   replayed a red verdict without re-running a gate. And the pin marker itself
   was a value that survived a process boundary it had no business crossing,
   which made a judge lower a correct verdict on five defects that did not
   exist. None of them failed loudly. Every one produced a confident wrong
   answer, which is the exact mode `build_provenance` exists to prevent. Two
   rules, and the second is the one that is easy to miss.
   **(a)** A content-addressed cache's validity check must cover the content,
   not only the marker naming it — a manifest, a file count, or
   re-materialize-on-mismatch — so a partially reaped entry fails loudly instead
   of degrading into a hybrid of cache and source. **(b)** A cache entry
   recording a *failure* must always be re-derived, never reused, whatever its
   key says. A green record is a real cache: nothing has to be re-checked. A red
   record is the single case where re-checking is the whole point, because
   someone is presumably fixing it — so reusing it can only ever be redundant or
   wrong. The general shape of both: a key that cannot see everything the value
   depends on is not an identity, and the cheapest correct fix is to shrink what
   you are willing to cache, not to widen the key. **Corollary this gate paid
   for three times:** when you fix one instance, fix every sibling in the same
   commit and *enumerate* the boundaries rather than patching the ones you
   remember. `90f24e6` exists only because T10 fixed one of two identical
   caches; `75543e7`'s spawn-site enumeration found a leak site nobody had
   reported. The enumeration is cheap and the rediscovery is not.

## Verdict

Advisory only, per `close-discipline.md` §1 — the judge session reads
`## Measurements`, the per-criterion state and the gate diff, and is deliberately
not given this section.

**`met`.** All seven of `GATE-03.md`'s definition-of-done bullets are met on
re-run evidence gathered in this session. Every oracle the feature's acceptance
criteria name was re-run fresh here with its exit code read directly: the full
suite (`Ran 3833 tests`, `OK (skipped=3)`, exit 0), `scripts/smoke-test.sh`
(exit 0), the plan lint over all 77 feature folders (0 ERROR), and all three
gates' `feature_oracle` commands (`OK`, exit 0 each).

Two bullets that a prior attempt recorded as unmet were re-probed with the same
probes that failed them, not with the gate's oracle:

- **Bullet 5** (#3270) — the pinned seam and the gate-completion summary print
  pin-aware text naming the pin's tree and the tree the edit takes effect in;
  none of the three pre-T09 strings appears anywhere on the pinned run's stdout.
- **Bullet 3** (#3271) — `materialize_pin` validates the pin's manifest, not only
  its marker; the reaped pin `021342f2…` fails `_pin_is_complete`, a mutilated
  pin is rebuilt rather than reused, and a launcher-shaped import inside a reused
  pin resolves to the pin rather than the working tree.

Both `FOLLOW-UPS.md` re-run conditions are quoted verbatim and answered in
`## Measurements`.

**The five follow-ups from attempt 2 (#3273–#3277) are environment artifacts and
are recorded as such, with the reproduction.** One variable —
`SPECFUSE_LOOP_PINNED_TREE` — flips `tests.test_installed_copy_driver_e2e`
between `FAILED (failures=3)` and `OK`, and the three failing test names are
exactly the three defects those issues describe. They are not code defects, they
are not open work, and they are not counted as unmet criteria. Recording an
environment artifact as a code defect is as wrong as the reverse, so this close
says which one it is and shows the command.

No criterion is unmet, so no new `FOLLOW-UPS.md` entry is written. The two
existing entries are retained with their `### ` headings byte-identical so the
driver's deduplication still resolves them to #3270 and #3271; both carry
`Closed by` lines, and both were re-verified in this session rather than taken on
their word.

There is no partial credit and nothing is hedged. `specfuse lint --closing`
reports `CLOSING-READY` for this feature — run as `python3
.specfuse/scripts/lint_plan.py <feature_dir> --closing`, exit 0.

**This close ran from a pinned build, and can say which one.** Pin
`18c1933ca3f437ad65e994ea6279e79cc69cc779`, materialized at 2026-09-09T15:19:31Z,
executing as PID 1413 under the operator's `python3 -m specfuse.loop.loop
--feature FEAT-2026-0109` (PID 1411), while the working tree has since moved to
tree `00fda5bfc544ed948701174619464c6b12a8427e`. That is gate 3's whole subject,
answered by the one session positioned to answer it.

**Two things are knowingly left uncorrected, neither a criterion of any unit.**
`PLAN.md`'s `planned_cost_usd` of $26.00 against a WU sum of $62.50 and actual
spend of $85.76 across 22 attempts and 2 judge sessions — the driver owns that
file and the arithmetic is in `## Cost analysis`. And the re-arm path's desync
with `GATE-NN-CRITERIA.md`, which cost this gate a red broad run and a halt but
belongs to the re-arm surface, not to this feature — recorded as item 9 of
`## What the loop did NOT verify`.
