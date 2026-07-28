# Gate-2 review — drafted by `FEAT-2026-0040/G1-PLAN`

The operator's pre-arm document for gate 2 of `FEAT-2026-0040-failure-artifact-harvester`.
Flip each gate-2 WU `status: draft` → `pending` only after **running the §4 probe** and
working the **Open questions** section at the bottom.

> **Filename note.** This file is `GATE-02-REVIEW.md`, not `GATE-01-REVIEW.md`. The
> driver's `assert_gate_review_exists` computes the expected filename from the **next**
> gate — the one this document arms — so a gate-1 `plan-next` writes `GATE-02-REVIEW.md`.
> `close-discipline.md` §4 records this as the single most expensive guard in the system:
> $53.11 of measured waste across 15 refusals, because the intuitive name is wrong.

---

## 1. What gate 1 shipped

Gate 1 established that a failure can be **modelled, fingerprinted, and redacted**
without any provider being reachable from the core. Three substantive WUs, all `done`,
all first attempt:

| WU | shipped | planned → actual |
|---|---|---|
| `T01` | `FailureArtifact` + `TelemetryAdapter`/`BrokerAdapter` protocols + the `resolve_telemetry(component, environment)` seam — `specfuse/monitor/artifact.py`, `adapters.py` | $4.00 → **$1.15** |
| `T02` | `fingerprint_artifact` over a canonically-ordered SHA-256 payload that incorporates `target_coordinates` — `specfuse/monitor/fingerprint.py` | $3.00 → **$0.85** |
| `T03` | `redact_artifact`, its own pattern set (not `leak_scan`'s), the `<redacted:sha8>` convention — `specfuse/monitor/redaction.py` | $2.50 → **$0.65** |
| `G1-CLOSE-INTERMEDIATE` | **auto-closed on-plan**, `attempts: 0`, full ceremony skipped | $4.50 → **$0.00** |

**The shape gate 2 is authored against**, from the shipped source:

```python
# specfuse/monitor/adapters.py
class TelemetryAdapter(Protocol):
    def fetch_failures(self) -> Iterable[FailureArtifact]: ...

class BrokerAdapter(Protocol):
    def fetch_failures(self) -> Iterable[FailureArtifact]: ...

def resolve_telemetry(component: str, environment: Mapping[str, object]) -> object: ...
```

Two consequences for gate 2's drafting, both checked rather than assumed:

- `fetch_failures()` takes **no arguments**, so every adapter is configured at
  construction. That is what makes constructor-injected transports natural and keeps the
  package's zero-runtime-dependency property intact — the drafted WUs lean on it.
- Neither protocol names a provider, so `WU-91`'s escalation trigger ("T01's protocols
  cannot express a Service Bus peek without a provider type leaking into the core") does
  **not** fire. Criterion 4 is satisfiable as written.

`artifact.py` also already carries `_TARGET_COORDINATE_FIELDS` and
`_TARGETLESS_CHECK_TYPES`, and `from_target` **raises** for `error-logs`, `http-5xx`,
and `invariant`. Gate 2's telemetry WU builds those three artifacts directly and asserts
the raise — the position is enforced, not documented.

**What gate 1 deliberately did not prove.** Nothing produces a `FailureArtifact` yet.
Every module is exercised by hand-built artifacts. That is gate 2.

---

## 2. What changed from `PLAN.md`'s gate-2 sketch, and why

The sketch named three elements: the Service Bus DLQ peek adapter, the App Insights KQL
telemetry adapters, and the cron-dialect contract. All three are drafted; none is
deferred. One WU exists that the sketch did not name.

| sketch element | drafted as | change from the sketch |
|---|---|---|
| Service Bus DLQ peek broker adapter | `T05` | Unchanged in scope. Sharpened in two places the sketch left open: the transport is **injected at construction** (the package has zero runtime dependencies and the `code` gate set has no install step), and "peek" is asserted by a **recorded-call negative observation** rather than by code review. |
| App Insights KQL telemetry adapters | `T06` **+** `T07` | **Split.** `T06` covers `error-logs`, `http-5xx`, and `invariant`; `T07` covers `heartbeat`. |
| the cron-dialect contract | `T04` | Unchanged in intent. The enum, the arity table, and the four validator rules are written out rather than left to the implementing session, because the enum's *names* are a schema position and not an implementation detail. |
| — | **`T07` (split out)** | Not a separate element in the sketch. `[FEAT-2026-0069]` split its `T07` out of `T06` for exactly this reason: bundling them "would have let `T06`'s red→green proof pass on the `dlq` half while the heartbeat half stayed silently unimplemented." Here the asymmetry is larger — three of the four telemetry check types are a query and a row-to-artifact mapping; the fourth needs a cron evaluator, timezone arithmetic, and a dialect the other three never read. |

**The `queue-stalled` gap, stated rather than left to be discovered.** The schema carries
six check types. Gate 2 ships adapters for five of them: `dlq` (`T05`), `error-logs`,
`http-5xx`, `invariant` (`T06`), and `heartbeat` (`T07`). **`queue-stalled` has no
adapter in any drafted WU.** `PLAN.md`'s scope boundary names "the Azure adapter pair
(Service Bus DLQ peek, App Insights KQL)" and `queue-stalled` is neither: it reads a
broker coordinate (queue depth / age of oldest message), not a dead-letter queue and not
a telemetry query — which is the whole reason 0069 added it as a distinct type. It is a
small addition to `T05`'s transport and a large one to its acceptance criteria. See
**Open question 3**.

---

## 3. The candidate migration surface — static enumeration, **not** the probe

Run at drafting time so the §4 probe starts from a list rather than from zero. Command,
over the whole tree excluding `.git/` and `.specfuse/features/`:

```
grep -rn "cron:" --include='*.yml' --include='*.yaml' --include='*.md' --include='*.py' \
  --include='*.example' .
grep -rn '"cron"' --include='*.py' .
```

| hit | what it is | disposition under `T04` |
|---|---|---|
| `.specfuse/monitoring.yml.example:154,157` | 2 heartbeat targets on the `acme-functions-host` component | **migrate** — each gains a `dialect` |
| `specfuse/loop/data/monitoring.yml.example:154,157` | byte-identical packaged seed | **migrate** — `cmp` must still exit 0 (`T04` AC7) |
| `tests/test_lint_monitoring.py:474` | `test_heartbeat_target_cron_and_timezone_contents_are_opaque` asserts `cron: "this is not a cron expression at all"` **validates clean** | **contradicts the flip.** 7 fields, no dialect. `T04` AC7a splits it: the timezone half stays, the cron half is re-aimed at what remains opaque |
| `tests/test_lint_monitoring.py:461` | `test_heartbeat_target_missing_name_is_rejected` — a target with `cron` and no `name`, expecting **exactly 1** finding | **breaks on count.** After the flip that target yields two findings (missing `name`, missing `dialect`). The assertion is `assertEqual(len(findings), 1)` |
| `tests/test_derive_monitoring_discovery.py:962` | `assertEqual(set(target), {"name", "cron", "timezone"})` on every generated heartbeat target | **breaks on exact set.** `T04` AC7b makes it a four-element set — kept exact deliberately |
| `tests/test_derive_monitoring_discovery.py:127,181,255,503,510,559,805-814` | the discovery reference implementation: `schedules` records, `suggest_checks`' heartbeat fan-out, `_render_target_value`'s cron quoting, and four fixtures | **migrate** — `T04` AC6. A generator emitting non-conforming targets re-breaks the tree on the next `/derive-monitoring` run |
| `tests/test_monitoring_example.py:142` | `crons = {t.get("cron") for t in targets}` — asserts distinct cron values | **no change expected** — adding a sibling key does not change the cron set. Listed so its absence from the diff is deliberate rather than overlooked |
| `.specfuse/monitoring.overrides.yml.example:57` | a `heartbeat` check with **no** targets | **no change** — cron-less heartbeats stay valid; this is the case that keeps the predicate satisfiable |
| `plugins/.../derive-monitoring/SKILL.md:203,219,261`, `PROMPT.md` | heartbeat blocks carrying **no** `cron` | **prose only** — `T04` AC12, edited canonically then synced |

**Nine surfaces, of which four are test assertions that break rather than YAML that
migrates.** That ratio is the reason §4 is mandatory: a WU armed on "two example files"
would rediscover the other seven attempt by attempt.

---

## 4. Runtime probe (`planning-discipline.md` §4) — MANDATORY, **NOT YET RUN**

`T04` flips heartbeat-target validation from "coordinate contents are opaque" to
"arity is checked against a declared dialect." That is a **severity flip**, and §4 says a
gate whose WUs flip a default or a severity may **not** be armed on "mechanical, nothing
design-open." §3 above is static inspection — a starting point, explicitly **not** a
substitute. `[FEAT-2026-0049/F4]`: a gate armed without the probe spun three times
(~$14) on a defect one local run exposed in seconds, and the first two diagnoses were
made against a *subset*, missing failures the full suite showed.

**The operator runs this before flipping any gate-2 WU to `pending`, and pastes the
finding list into §4.3 below.** Arming without it is what makes `T04` spin.

### 4.1 The probe

Apply the validator change locally — the four rules in `T04`'s contract table, in
`specfuse/loop/lint_monitoring.py`'s `_check_targets` — and run, in two passes:

```
# Pass 1 — validator tightened, tree UNMIGRATED.
#          This enumerates what the migrate step must fix.
python3 -m unittest discover -s tests -v
python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example

# Pass 2 — the two example files and the discovery reference impl migrated too.
#          This enumerates the residual test-assertion surface.
python3 -m unittest discover -s tests -v
python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
```

Then revert the probe and confirm the revert: `python3 -m unittest discover -s tests`
returns to green before the run starts.

**Run the full oracle, not a subset.** `python3 -m unittest discover -s tests -v` is the
`tests` gate's exact command. `lint_monitoring.py .specfuse/monitoring.yml.example` is
the `monitoring-example-lint` gate's exact command and the one that halts the run: under
FEAT-2026-0051's preflight baseline probe, a red base gate stops the driver before any
unit dispatches.

### 4.2 What the probe is expected to show

Recorded as a **prediction**, so the run can falsify it. A probe whose output matches a
prediction nobody wrote down teaches nothing.

- **Pass 1:** `monitoring-example-lint` red with 2 findings (the two heartbeat targets in
  the example), plus `test_monitoring_fenced_blocks`, `test_monitoring_example`,
  `test_derive_monitoring_discovery`, and 2 cases in `test_lint_monitoring` red.
- **Pass 2:** `monitoring-example-lint` green; the residue is `test_lint_monitoring`'s
  two contradicting assertions and `test_derive_monitoring_discovery:962`'s exact-set
  assertion — the surface `T04` AC7a/AC7b already name.
- **The cascade is expected to be bounded to four test files.** If it is not, `T04`'s
  first escalation trigger fires and the gate is larger than one WU can hold.

### 4.3 Probe findings — **paste the verbatim failure list here before arming**

**Baseline first** (probe NOT applied), so every line below is attributable:

```
Ran 1695 tests in 60.223s
OK (skipped=3)
OK — monitoring config is structurally valid (or absent).
```

**PASS 1 — validator tightened, tree UNMIGRATED.**

```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
FAIL — 2 finding(s):
  - component 'acme-functions-host': checks[1]: targets[0]: heartbeat target with 'cron' must carry 'dialect'
  - component 'acme-functions-host': checks[1]: targets[1]: heartbeat target with 'cron' must carry 'dialect'

$ python3 -m unittest discover -s tests -v
FAIL: test_heartbeat_target_cron_and_timezone_contents_are_opaque   tests/test_lint_monitoring.py
FAIL: test_heartbeat_target_missing_name_is_rejected                tests/test_lint_monitoring.py
FAIL: test_shipped_example_validates_clean                          tests/test_monitoring_example.py
FAIL: test_single_deployable_with_n_triggers_yields_one_component_with_n_targets
                                                                    tests/test_derive_monitoring_discovery.py
FAIL: test_shim_resolves_package_from_source_outside_repo           tests/test_monitoring_seed.py
FAILED (failures=5, skipped=3)
```

**PASS 2 — both example copies migrated (`dialect: standard-5`; both crons are 5-field).**

```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).

$ python3 -m unittest discover -s tests -v
FAIL: test_heartbeat_target_cron_and_timezone_contents_are_opaque   tests/test_lint_monitoring.py
FAIL: test_heartbeat_target_missing_name_is_rejected                tests/test_lint_monitoring.py
FAIL: test_single_deployable_with_n_triggers_yields_one_component_with_n_targets
                                                                    tests/test_derive_monitoring_discovery.py
FAILED (failures=3, skipped=3)
```

**Revert confirmed:** tree clean, `1695 tests OK (skipped=3)`, monitoring lint green.

### 4.4 The prediction was falsified in three ways — read before arming `T04`

§4.2 was written so the run could falsify it. It did.

1. **`test_monitoring_fenced_blocks` was predicted red and stayed green.** Harmless, but
   it means the predicted set was reasoned about rather than observed.
2. **`tests/test_monitoring_seed.py::test_shim_resolves_package_from_source_outside_repo`
   was not predicted and went red in pass 1.** It clears once the example is migrated, so
   it is migration-surface, not residual — but a session working only from §4.2 would have
   met an unexpected failure.
3. **The migration surface is two files, not one — and this is the finding that matters.**
   Migrating `.specfuse/monitoring.yml.example` alone leaves
   `test_package_data_matches_canonical` red, because the example ships **twice**:
   `.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example`,
   held byte-identical by the scaffold-sync guard. `T04`'s migrate step must touch both,
   and its sweep criterion must be written so migrating one and not the other fails.
   `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` lost $5.26 to exactly this shape — a migrate
   criterion scoped to a sample where the flip needed a sweep.

**The cascade is bounded to four test files**, as §4.2 predicted in count — but the set
differs by one in each direction, and the two-copy migration surface was invisible to
static inspection. `T04`'s enumerated surface is the pass-2 residual: two contradicting
assertions in `tests/test_lint_monitoring.py` and one exact-set assertion in
`tests/test_derive_monitoring_discovery.py`, plus the `suggest_checks` reference
implementation that must emit `dialect`.

**Probe environment note.** Run unsandboxed. Under the command sandbox, three tests in
`tests/test_autosync_no_cwd_leak.py` error with `Couldn't get agent socket?` — the temp
repos inherit a global commit-signing config whose agent the sandbox blocks. Nothing to
do with this gate, but it contaminates a sandboxed baseline and is worth a follow-up so
those tests set `commit.gpgsign=false` on their fixtures.

**This gate is not armed until the two blocks above are filled.** The pasted list
becomes `T04`'s enumerated test surface, and `T04`'s escalation triggers reference it by
name: a session that observes a migration surface materially different from what is
pasted here is to report that, not absorb it.

---

## 5. Cost

### 5.1 Per-WU estimates for gate 2

| WU | type | planned | reasoning |
|---|---|---|---|
| `T04` | implementation | **$4.50** | The largest substantive unit. A validator change plus a migration across nine surfaces plus a discovery reference-impl change plus docs and a skill sync. Four of the nine surfaces are test assertions that must be re-aimed rather than mechanically updated. |
| `T05` | implementation | **$4.00** | A new provider package, a stub transport with 2×2 cardinality, a recorded-call negative observation, and signature normalization. |
| `T06` | implementation | **$4.00** | Three adapters, the seam assertion, the `invariant` fingerprint contract with a 3-row/2-value fixture, and the no-query-from-observed-data assertion. |
| `T07` | implementation | **$4.00** | A cron evaluator with no third-party dependency, across two arities, with timezone and DST assertions. Smaller surface than `T04` but the least mechanical. |
| `G2-CLOSE-INTERMEDIATE` | close-intermediate | **$4.50** | `planning-discipline.md` §5 floor. Load-bearing (`auto_close_disabled: true`): a breaking schema change to acknowledge and gate 1's auto-close debt to reconcile. |
| `G2-PLAN` | plan-next | **$6.00** | §5 floor. |
| | | **$27.00** | |

`GATE-02.md` carries `cost_budget_usd: 33.00` — the $27.00 sum plus one re-attempt of
the largest WU ($6.00), per §5's corollary. That padding is defensive, not a prediction
that a retry is normal.

### 5.2 `PLAN.md` re-baseline and the delta

| | |
|---|---|
| previous `planned_cost_usd` | **$25.00** — gate 1's five units plus gate 3's close placeholder |
| gate 2's six drafted units | **+$27.00** |
| **new `planned_cost_usd`** | **$52.00** |
| **delta** | **+$27.00 (+108%)** |

The doubling is expected and is not a re-plan: $25.00 was explicitly the *drafted* work
only (`PLAN.md`'s own note), and gate 2 was empty. Gate 3's substantive units are still
unpriced, so $52.00 will rise again when `G2-PLAN` drafts them.

### 5.3 The calibration signal, and why gate 2's estimates were **not** scaled down

Gate 1's substantive WUs cost **$2.65 against $9.50 planned — 72% under**, three for
three, every one first attempt. The temptation is to scale gate 2 down by the same
factor, which would price these six units near $10.00.

Deliberately not done, for two reasons. Three observations from one gate is not a
distribution — `planning-discipline.md` §5's own provenance note is that its first two
revisions each generalised a floor from a single feature and both were wrong. And gate
1's units were unusually clean: new modules, no existing tree to migrate, no severity
flip, no cross-file assertions to re-aim. `T04` is none of those things. What gate 1's
underrun does support is trimming `T05`/`T06`/`T07` — see **Open question 1**; that is
the operator's call at arming, not this document's.

---

## 6. Open questions for the operator — work these before arming

1. **Trim the adapter estimates?** Gate 1's three units came in 72% under. `T05`, `T06`,
   and `T07` are new-module work of a similar shape (the migration risk is concentrated
   in `T04`), so $4.00 each may be as generous as gate 1's were. Against trimming:
   `[FEAT-2026-0069/G2-CLOSE]` records the opposite lesson — the expensive planning WU
   bought the cheap gate, and pricing a gate at its optimistic figure is how a budget
   halt lands mid-gate. **Recommendation: leave them.** The budget is a halt threshold,
   not a spend target, and under-running it costs nothing.
2. **Are `standard-5` and `seconds-first-6` the right enum names?** They are
   vendor-neutral by design — the schema "names a symptom, never a vendor" — and the
   arity is in the name so the enum-to-arity mapping is readable without opening the
   validator. If you prefer different spellings, change them **here**, before `T04` is
   armed: renaming an enum after it ships is a second breaking change to the same field.
3. **Does `queue-stalled` get an adapter in gate 2, or gate 3?** §2 records the gap.
   Adding it to `T05` is a modest transport addition and a real acceptance-criteria
   addition (queue depth and age-of-oldest are dials, and the threshold's units are
   currently opaque in the schema). Leaving it for gate 3 means the feature's CLI ships
   able to enumerate a check type it cannot harvest. **Recommendation: gate 3**, drafted
   by `G2-PLAN` alongside the CLI, so gate 2 stays the adapter-shape gate. Either way,
   decide now — discovering it at gate 3's drafting makes it look like an oversight.
4. **Is an operator run against the downstream .NET backend scheduled?** Gate 2's
   adapters are verified against stubs only. That is by construction, not a shortcut —
   but nothing in this repo will ever upgrade it, so if no operator run is planned, the
   feature's terminal verdict is `met_locally` and should be expected as such rather
   than discovered at gate 3's close.

---

### 6.1 Operator decisions — recorded at arming

All four answered "yes to all", i.e. accept the recommendation on 1 and 3, affirm 2 and 4.

1. **Adapter estimates stay at $4.00.** Not trimmed on gate 1's 72% under-run. A budget
   is a halt threshold, not a spend target, and under-running costs nothing while a
   budget halt lands mid-gate.
2. **`standard-5` and `seconds-first-6` are confirmed** as the enum spellings. Locked
   before `T04` is armed — renaming after ship is a second breaking change to the same
   field.
3. **`queue-stalled` gets its adapter in gate 3**, drafted by `G2-PLAN` alongside the
   CLI. Gate 2 stays the adapter-shape gate. Recorded now so it does not read as an
   oversight at gate 3's drafting.
4. **An operator run against the downstream .NET backend IS planned.** This changes what
   the feature's terminal verdict may claim: gate 3's close is no longer `met_locally` by
   construction. It may reach `met` once that run is observed and recorded. Gate 2's
   close must still report its adapters as stub-verified — the run has not happened yet —
   but `G3-CLOSE` should carry the run as the named condition that upgrades the verdict,
   not as a permanent deferral.

---

## 7. What gate 2 will **not** verify — known now, and the close must say so

`verification.yml` records that this repo "is a CLI tool with no deployable components
and will never carry a real monitoring.yml." So:

- **No live Service Bus namespace is reached.** `T05` proves the adapter's shape, its
  coordinate handling, its redaction boundary, its fingerprint behaviour, and that it
  issues no settlement call. It proves nothing about the real peek API's paging,
  throttling, or dead-letter metadata field names.
- **No live App Insights workspace is reached.** `T06` and `T07` prove the row-to-artifact
  mapping against canned rows. They prove nothing about whether a real KQL result carries
  the columns the queries name.
- **No DST transition is observed in production.** `T07` asserts computed instants against
  the stdlib's tz database; whether the deployed schedule agrees is an operator
  observation.

`G2-CLOSE-INTERMEDIATE` criterion 3 requires these named in `## What the loop did NOT
verify` in these terms. A close that reports "all adapters verified" on stub evidence is
the failure this section exists to prevent.

Separately, `G2-CLOSE-INTERMEDIATE` criterion 4 reconciles gate 1's **auto-close debt**:
`RETROSPECTIVE.md` carries a `specfuse:autoclose-debt gate=1` marker for T01–T03's 32
criteria, which gate 1's auto-close never enumerated. Gate 1 was scoped so that list can
legitimately be empty — but "legitimately empty" and "never looked at" are different
claims, and only the reconciliation distinguishes them.
