---
gate: 2
status: open
cost_budget_usd: 33.00
---

# Gate 2 — the Azure adapters produce artifacts, and a schedule declares its dialect

## Definition of done

- A `heartbeat` target declares its cron **dialect**, and the validator enforces both
  the enum and the expression's arity against it. No shipped surface carries a
  non-conforming instance, proven by a tree-wide sweep rather than a sampled example.
- A Service Bus **DLQ peek** adapter satisfies T01's `BrokerAdapter` protocol,
  produces one redacted `FailureArtifact` per dead-lettered message, and carries the
  target's `subscription` and `function` coordinates so two targets on one component
  never collapse into one fingerprint.
- **App Insights KQL** adapters satisfy T01's `TelemetryAdapter` protocol for
  `error-logs`, `http-5xx`, and `invariant`, resolving telemetry **through the
  per-component seam** rather than reaching into the environment binding.
- A heartbeat adapter answers "should this have fired?" from the **declared** dialect,
  and the dialect is demonstrably load-bearing: the same expression under two dialects
  yields two different schedules.
- No provider type is reachable from the core. Provider code lives under
  `specfuse/monitor/providers/` and the dependency arrow never points back.
- `RETROSPECTIVE.md` carries a `## Gate 2` section; the deferred list names what only
  a stub proved; gate 3 is drafted and `GATE-03-REVIEW.md` written.

Every clause is decidable **by this gate**, per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`.
Note what is deliberately *not* claimed: nothing here asserts an adapter works against
a live Azure environment. That is unverifiable in this repo by construction —
`verification.yml` records it "is a CLI tool with no deployable components and will
never carry a real monitoring.yml" — so it is a named deferred item in the close, not a
clause in the definition of done.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4) — MANDATORY here, and not yet
  discharged.** T04's cron-dialect change tightens heartbeat-target validation: a tree
  that lints clean today can lint dirty after it. Before arming, apply the change
  locally, run the exact command the WU's tests gate will run over every shipped YAML
  surface, and paste the finding list into `GATE-02-REVIEW.md`. That list is the
  enumerated migration surface, and T04's escalation triggers reference it. The
  candidate surface `G1-PLAN` found by static inspection is recorded in
  `GATE-02-REVIEW.md` §4 — it is a starting point for the probe, explicitly **not** a
  substitute for running it.
- **Escalation-predicate satisfiability (§2) — answered.** What does the tightened
  rule report on an input already in its intended final state? **Zero.** `dialect` is
  required only on a heartbeat target that carries a `cron`; a cron-less heartbeat
  target stays valid and `cron` itself stays optional, so the rule fires on no correct
  input. The one way to make the predicate unsatisfiable is to land the contract step
  before the migrate step, which is why they live in one WU in a fixed order.
- **Flag-scope table (§3) — not applicable.** No behaviour flag is introduced or
  flipped. `dialect` is a schema field with a validation rule, not a gate on code
  paths; there is no "which paths does the flag affect" question to table. Recorded as
  assessed rather than omitted.
- **Migrate before contract, and the migrate criterion must be a sweep.**
  `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` lost $5.26 to a criterion scoped to a sample
  where the flip needed "no non-conforming instance remains anywhere." Flip-first is
  unsatisfiable under the preflight baseline probe: `.specfuse/monitoring.yml.example`
  is validated by the `monitoring-example-lint` code gate, so a tightened validator
  against an unmigrated tree turns a base gate red and halts the run before any unit
  dispatches. T04 criterion 4 is the sweep; criterion 5 is what stops it passing
  vacuously.
- **Adapters are verified against stubs, and the close must say so.** T05–T07 reach no
  live Service Bus namespace and no live App Insights workspace. Arming this gate means
  accepting that its adapter evidence is structural — shape, coordinates, redaction
  boundary, fingerprint behaviour — and that the transport-level oracle is an operator
  run against the downstream .NET backend.

## Reflection notes

<Written by the human at review time.>
