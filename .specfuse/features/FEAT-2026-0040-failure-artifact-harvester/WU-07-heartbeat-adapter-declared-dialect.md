---
id: FEAT-2026-0040/T07
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/monitor/schedule.py
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_schedule_dialect.py
  - tests/test_heartbeat_adapter.py
model: sonnet
effort: high
gate_set: code
driver_version: 0.6.0
started_at: 2026-07-28T22:16:30.973038+00:00
duration_seconds: 1111.82
cost_usd: 4.368643
input_tokens: 124
output_tokens: 58389
---

# Did it fire? — the heartbeat adapter, against a declared dialect

**Objective.** Answer "should this schedule have fired, and did it?" per heartbeat
target: a neutral schedule evaluator that reads the **declared** dialect T04 shipped,
and the App Insights heartbeat adapter that uses it to emit one artifact per silent
schedule.

**Context.** Correlation ID `FEAT-2026-0040/T07`. Gate 2; depends on
`FEAT-2026-0040/T04` (the dialect must exist in the schema and in the shipped
examples before anything reads it) and on `FEAT-2026-0040/T06` (the telemetry
transport, the seam call, and the module this adapter joins). This is the unit the
whole cron-dialect decision was made for.

**The dialect is read, never inferred — including here.** T04 makes the schema carry
it; this unit is where inferring would have been tempting, because the expression is
right there and its field count is one `split()` away. Do not. The rejected design
degrades silently exactly when a new dialect appears, and an adapter that guesses
undoes the schema work in one line. If this unit ever receives a target whose
expression arity disagrees with its declared dialect, it **refuses** — a loud failure,
never a best guess at what the operator meant. T04's validator makes that unreachable
through the lint path; criterion 5 makes it unreachable through every other path too.

**The dialect must be load-bearing, and that is testable.** The same expression string
under two dialects yields two different schedules — `0 2 * * *` read as `standard-5`
means 02:00 daily, and a six-field expression's leading field is seconds, not minutes.
Criterion 4 asserts a *difference*, because a dialect that changes no computed result
is decoration, and a test that only checks "it parsed" would pass on an
implementation that ignored the field entirely.

**Keep the evaluator neutral and out of `providers/`.** `specfuse/monitor/schedule.py`
takes an expression, a dialect, an IANA zone, and a reference time, and returns the
expected firing times. No provider, no telemetry, no `FailureArtifact`. T01 kept
schedule semantics out of `artifact.py` so the model stayed neutral; the same
reasoning puts the arithmetic in its own module rather than inside a vendor adapter,
where the next provider would have to reimplement it.

**Zero runtime dependencies — that constraint bites hardest here.** No `croniter`, no
`dateutil`. The stdlib gives you `zoneinfo` and `datetime`, and that is the budget.
Scope the evaluator to what the schema's own examples need: `*`, `*/n`, comma lists,
`a-b` ranges, and literals, over both arities. Anything beyond that — `L`, `W`, `#`,
named months and weekdays — is **out of scope for this unit** and must be rejected
explicitly with a clear message rather than silently mis-parsed. A parser that
half-accepts an expression it does not understand is the same failure class as
inferring the dialect.

**Time is an argument, never a read of the clock.** Every function takes the reference
time as a parameter. A schedule evaluator that calls `datetime.now()` internally is
untestable at the boundaries that matter — DST transitions, month ends, the minute
after a fire — and those boundaries are precisely where a monitoring tool files a
false issue at 3am.

**What the artifact carries.** One artifact per silent schedule, built through
`FailureArtifact.from_target` so the heartbeat coordinate — the target's `name` —
round-trips into `target_coordinates`. T02's fingerprint incorporates it, which is what
keeps a single silent timer among several individually visible instead of averaged away
into one host-wide heartbeat finding.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_schedule_dialect.py::TestDialectIsLoadBearing::test_same_expression_under_two_dialects_differs`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/monitor/schedule.py` defines a function that, given a cron expression, a
   dialect from T04's enum, an IANA timezone name, and a reference `datetime`, returns
   the most recent expected firing time at or before that reference. It names no
   provider and imports nothing from `specfuse/monitor/providers/`.
3. The evaluator supports `*`, `*/n`, comma lists, `a-b` ranges, and literal values in
   every field of both arities, and **rejects** any other syntax with an explicit
   error naming the unsupported token. A test asserts the rejection for at least
   `L`, `W`, and `#` — a negative observation, since a silently mis-parsed expression
   is the failure this unit exists to prevent.
4. **The dialect is load-bearing.** One six-field expression is evaluated as
   `seconds-first-6` and its five-field truncation as `standard-5`, against the same
   reference time, and the two results **differ**. A test whose two dialects yield the
   same answer proves nothing about which field was read.
5. **Arity disagreement refuses.** Evaluating a 5-field expression declared
   `seconds-first-6`, or a 6-field expression declared `standard-5`, raises with a
   message naming both the declared dialect and the observed field count. No fallback,
   no inference from the count.
6. Timezone handling is real: an expression evaluated under two different IANA zones
   for the same reference instant yields two different expected firing times, and a
   test covers a reference time inside a DST transition in a zone that has one,
   asserting the computed instant rather than only that no exception was raised.
7. `specfuse/monitor/providers/azure_app_insights.py` gains a heartbeat adapter whose
   `fetch_failures()` returns an iterable of `FailureArtifact` — structurally a
   `TelemetryAdapter` — resolving its binding through
   `resolve_telemetry(component, environment)` **with the component**, as T06's
   adapters do.
8. **Cardinality the failure needs.** The stub carries **at least 2 heartbeat targets
   on one component with different dialects**, one of which has reported in within its
   window and one of which has not. The adapter yields **exactly one** artifact — for
   the silent schedule — and its `target_coordinates` carries that target's `name`.
   `fingerprint_artifact` over artifacts from two different silent targets on the same
   component returns two different digests.
9. A schedule whose last observed heartbeat is at or after its most recent expected
   firing time produces **no** artifact. The false-positive direction is the one that
   destroys trust in a monitoring tool, and it is asserted rather than assumed.
10. Every artifact returned passes through T03's `redact_artifact` before leaving the
    adapter, proven by a planted synthetic value that does not survive. Use a value
    that is not a real credential and not a denylisted token.
11. `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/schedule.py
    specfuse/monitor/artifact.py specfuse/monitor/adapters.py
    specfuse/monitor/fingerprint.py specfuse/monitor/redaction.py` returns no match,
    and `grep -rn "datetime.now\|time.time" specfuse/monitor/schedule.py` returns no
    match — the reference time is always an argument.
12. `python3 -m unittest tests.test_schedule_dialect tests.test_heartbeat_adapter -v`
    exits zero after this WU's edits, and the `code` gate set passes in full — `tests`,
    `lint`, `security`, `coverage` (≥90%), `leak-scan`, `monitoring-example-lint`, and
    the five `bats` suites.

**Do not touch.** `specfuse/loop/lint_monitoring.py`, the dialect enum, and the
monitoring examples — T04 owns the schema, and a dialect added here would put the
adapter and the validator into disagreement, which is the one shape the declared-dialect
decision exists to prevent. `specfuse/monitor/artifact.py`, `fingerprint.py`,
`redaction.py`, `adapters.py` — T01–T03's, consumed here. T06's three adapters in the
same module: extend the file, do not rewrite them. `escalation.py` — gate 3's.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 12, the rejection assertions in
criteria 3 and 5, the difference assertions in criteria 4 and 6 — a schedule evaluator
verified only by "it returned something" is not verified — and the two greps in
criterion 11. Report which sandbox each gate ran under; the `bats` suites fail under
the session's default sandbox for reasons unrelated to this unit.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: T04 has
not landed the `dialect` field, since reading a field the schema does not carry is
guessing by another name; the supported-syntax subset in criterion 3 cannot express an
expression already present in the shipped examples, which means the subset was scoped
wrong and the fix is a plan decision rather than a parser patch; `zoneinfo` has no
timezone database available in the run environment, which makes criterion 6
unverifiable here and needs recording rather than working around; or satisfying
criterion 6's DST case would require pinning a specific tzdata version, which is a
dependency decision this unit may not take alone.
