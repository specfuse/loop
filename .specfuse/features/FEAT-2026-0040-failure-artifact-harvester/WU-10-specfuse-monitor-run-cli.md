---
id: FEAT-2026-0040/T10
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - specfuse/monitor/cli.py
  - tests/test_monitor_cli.py
  - pyproject.toml
model: sonnet
effort: high
gate_set: code
---

# One polling cycle, end to end — the `specfuse-monitor run` CLI

**Objective.** Ship `specfuse-monitor run [--component X] [--env Y] [--dry-run]`:
read `.specfuse/monitoring.yml`, enumerate every check and target, dispatch each to
its provider adapter, fingerprint and redact what comes back, and hand the findings
to `T09`'s issue lifecycle — or, under `--dry-run`, print them and touch nothing.

**Context.** Correlation ID `FEAT-2026-0040/T10`. Gate 3, depends on `T08` (the last
adapter, so the CLI can enumerate all six check types rather than five) and `T09`
(the sink it writes to). This is the unit that makes the feature a *tool* instead of
a library: gates 1 and 2 built parts that have never been run together, and the first
time an enumeration bug shows up is the first time something enumerates.

**The schema already decided how dispatch works, and this unit must not re-decide
it.** `.specfuse/monitoring.yml.example` states it in its own comments:
`environments.<name>.telemetry.provider` and `.broker.provider` are **opaque
strings this layer does not interpret — FEAT-2026-0040's harvester CLI reads it and
dispatches to a provider-specific adapter. Adding a new provider never requires a
change here or in the validator.** So the CLI carries a registry keyed on that
opaque string, and an unknown provider is a clear error naming the string and the
registered keys — never a crash and never a silent skip.

**Telemetry resolves through the seam, not around it.** `T01` shipped
`resolve_telemetry(component, environment)` precisely so that
[#262](https://github.com/specfuse/loop/issues/262) — one telemetry binding per
environment, correct for the motivating project and wrong in general — can be fixed
later by adding a resolver rather than reshaping every adapter. The CLI is the
component that decides *which* component's telemetry each adapter gets, so it is the
one place where reaching into `environment["telemetry"]` directly would quietly undo
that decision. Criterion 6 is a grep, because no test catches a shortcut that
produces the right answer today.

**State is derivable or safely losable.** The roadmap's state principle, and it
bounds this unit: **issues are the fingerprint registry** (`T09` owns that), and
watermarks are a **best-effort per-host cache with a lookback-window fallback**. A
missing, unreadable, or corrupt watermark file must degrade to the lookback window
and keep going — never fail the run, never re-file everything as new. Idempotency
comes from fingerprint dedupe, not from the watermark, which is why losing the cache
is survivable at all.

## Flag-scope table (`planning-discipline.md` §3)

`--dry-run` is a behaviour flag and its headline claim is **"a dry run touches
nothing outside this process."** §3 requires that claim be crossed against the paths
it is supposed to gate, because a claim the table does not support is a scope
mismatch that surfaces as a defect gates later — and here the defect would be a
monitoring tool filing issues during a rehearsal.

| Code path | Gated by `--dry-run`? | Why |
|---|---|---|
| config load + schema validation | **no** | Reading `.specfuse/monitoring.yml` is the thing a dry run is *for*; a dry run that skipped validation would rehearse nothing |
| adapter construction | **no** | Constructing an adapter is inert — the transports are injected and no I/O happens until `fetch_failures()` |
| `fetch_failures()` — the read against telemetry/broker | **no** | Deliberate. All environment access in this feature is read-only (`PLAN.md`'s scope boundary), so the reads are safe, and a dry run that does not read has nothing to print. **Stated explicitly so `--dry-run` is not mistaken for `--offline`.** |
| fingerprint + redaction | **no** | Pure functions over artifacts; the dry-run output must show exactly what would be filed, redaction included |
| watermark **write** | **yes** | A dry run that advances the watermark makes the next real run skip findings nobody ever saw |
| `T09` find-or-create / update / annotate — every `gh` invocation | **yes** | The claim itself. Criterion 8 asserts a recorded call set that is empty, not merely short |
| run-summary output | **no** | Both modes print; the dry run prints the findings themselves as well |

**No other flag is introduced.** `--component` and `--env` are selectors, not
behaviour flags: they narrow which components and which environment are enumerated
and change no code path's behaviour on the ones selected. Recorded as assessed
rather than omitted.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**In-loop evidence.** This unit produces **real in-loop evidence for its dry-run
path and its enumeration**, which is most of it: a fixture `monitoring.yml` plus stub
transports exercises config load, target enumeration, provider dispatch, the seam,
fingerprinting, redaction, watermark fallback, and the run summary, all decidable
here. **The write path is stub-evidence only**, because it terminates in `T09`, whose
`gh` surface returns auth errors inside `claude -p`
(`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`). Deferred criterion **D-10**, carried into
`G3-CLOSE`: *"`specfuse-monitor run` against a real repository and a real environment
files the issues the dry run predicted."* Its verification proxy is the same
operator-journal artifact `T09`'s D-9 uses — one operator run, recorded in the
feature folder's operator journal, with the dry-run output and the resulting issue
list side by side.

**Acceptance criteria.**

1. `tests/test_monitor_cli.py::TestRunCycle::test_two_targets_on_one_component_yield_two_findings`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/cli.py` defines a `main()` accepting `run` with
   `--component`, `--env`, and `--dry-run`, and `pyproject.toml`'s
   `[project.scripts]` gains `specfuse-monitor = "specfuse.monitor.cli:main"`
   alongside the four existing entry points. `python3 -c "from specfuse.monitor.cli
   import main"` exits zero on a clean checkout with no cloud SDK installed — the
   package's zero-runtime-dependency property holds through the CLI.
3. **Enumeration follows the 0069 axis.** Over a fixture config, the run enumerates
   `check["targets"]` when present and the component otherwise, and produces one
   finding per *target*, not per check. A component with two `dlq` targets yields
   **two** findings whose fingerprints differ — the binding constraint, asserted at
   the level where it is finally observable end to end.
4. **All six check types dispatch.** The fixture exercises `dlq`, `error-logs`,
   `http-5xx`, `invariant`, `heartbeat`, and `queue-stalled`, and each reaches its
   adapter. A check type present in the schema with no registered adapter is a clear
   error naming the type — **negative observation**, not an inference from the happy
   path, because a silently-skipped check type is invisible exactly when it matters.
5. **Provider dispatch is registry-driven and opaque.** An unknown
   `telemetry.provider` / `broker.provider` string produces an error naming the
   string and the registered keys, and adding a registry entry requires no change to
   `lint_monitoring.py` or to the schema. A test asserts the unknown-provider error
   rather than a traceback.
6. **The seam is used, not bypassed.**
   `grep -n 'environment\["telemetry"\]\|environment.get("telemetry")'
   specfuse/monitor/cli.py` returns no match, and a test asserts
   `resolve_telemetry` is called **with the component name** for each component
   enumerated.
7. **Selectors select.** `--component` restricts the run to one component and
   `--env` to one environment; a name matching nothing is an error naming the
   available values, not an empty successful run. An empty successful run is
   indistinguishable from "everything is healthy," which is the worst possible way
   for a monitoring tool to be wrong.
8. **`--dry-run` touches nothing, proven by an empty recorded call set.** With a
   stub runner threaded through `T09`, a dry run over a fixture that produces
   findings records **zero** `gh` invocations of any kind, and the watermark file's
   contents are byte-identical before and after. Both halves asserted; the table
   above is the claim and this is its test.
9. **Watermarks degrade, never fail.** A missing watermark file, an unreadable one,
   and a corrupt one each fall back to the lookback window and complete the run
   with a summary line naming the fallback. **Negative observation** on all three;
   a watermark that raises turns a transient cache problem into an outage of the
   thing that detects outages.
10. **The run summary is the operator's evidence.** It reports, per component:
    findings emitted, issues created vs. updated vs. throttled (or "would be", under
    `--dry-run`), targets skipped with their reasons — including `T08`'s recorded
    `stall_after`-absent skips — and any watermark fallback. A test asserts the
    skip reasons reach the summary: a target silently doing nothing is the defect
    `T08` criterion 8 recorded the skip for.
11. **Redaction survives the CLI.** A fixture artifact carrying a planted synthetic
    secret produces dry-run output in which no occurrence of that value appears.
    Use a synthetic value that is not a real credential and not a denylisted token;
    see `security-boundaries.md`.
12. **No provider identifier reaches the core**, the CLI included:
    `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/cli.py
    specfuse/monitor/artifact.py specfuse/monitor/adapters.py
    specfuse/monitor/fingerprint.py specfuse/monitor/redaction.py
    specfuse/monitor/schedule.py specfuse/monitor/issues.py` returns no match. The
    registry maps opaque strings to lazily-imported provider modules; the string
    lives in the config, not in the source.
13. `python3 -m unittest tests.test_monitor_cli -v` exits zero after this WU's
    edits, `python3 -m unittest tests.test_monitor_issue_lifecycle
    tests.test_queue_stalled_adapter tests.test_service_bus_dlq_adapter
    tests.test_app_insights_adapters tests.test_heartbeat_adapter` still exits zero,
    and the `code` gate set passes in full — `tests`, `lint`, `security`, `coverage`
    (≥90%), `leak-scan`, `monitoring-example-lint`, and the `bats` suites.

**Do not touch.** Everything under `specfuse/monitor/` except `cli.py` — `T01`–`T03`,
`T06`–`T08` own the modules and `T09` owns `issues.py`; this unit **composes** them.
If one cannot express what a polling cycle needs, that is an escalation, not an edit.
`specfuse/loop/lint_monitoring.py` and both `monitoring.yml.example` copies — the
schema is settled and the CLI reads it as-is; a config the CLI needs but the
validator rejects is an escalation. `specfuse/loop/escalation.py`. The GitHub Actions
workflow surface and the runner dial — `T11` owns them. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 13, the two greps in criteria
6 and 12, and the negative observations in criteria 4, 8, 9, and 11 — criterion 8 in
particular is the flag-scope table's oracle and `verification-discipline.md` §3
requires it be observed rather than asserted. Note the `bats` `mktemp` sandbox effect
recorded in `[FEAT-2026-0072/G1-CLOSE]`: report which sandbox each gate ran under
rather than reporting a manufactured regression. **Report the D-10 deferral
explicitly in the RESULT block.**

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
schema cannot express which adapter a check should dispatch to without a change to
`lint_monitoring.py` — that is a schema question and a cross-gate contract, not this
unit's to settle; `resolve_telemetry`'s signature cannot carry per-component
resolution as the CLI needs it, which would mean #262's seam did not do its job and
is worth reporting before it is worked around; the run cannot be exercised end to
end without a live environment, which would mean the stub boundary was drawn in the
wrong place; or enumerating `check["targets"]` produces a finding that cannot be
fingerprinted without a field no WU shipped — the escalation `G2-PLAN` named, and a
blocked report rather than a widened model.
