---
id: FEAT-2026-0040/G1-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.6.0
started_at: 2026-07-28T19:50:12.237471+00:00
duration_seconds: 884.28
cost_usd: 6.68748
input_tokens: 103
output_tokens: 66991
---

# Draft gate 2 — the Azure adapters and the cron-dialect contract

**Objective.** Draft gate 2's substantive work units into `PLAN.md`, and write
`GATE-02-REVIEW.md` for the human review-and-arm checkpoint.

**Context.** Correlation ID `FEAT-2026-0040/G1-PLAN`. Depends on
`G1-CLOSE-INTERMEDIATE`, whose retrospective and lessons are this unit's primary
input — gate 2 is drafted from what gate 1 actually learned, not from what gate 1
predicted.

**The review artifact is named for the gate being armed, not the gate being closed.**
`assert_gate_review_exists` requires **`GATE-02-REVIEW.md`**. `close-discipline.md`
§4 records this as the single most expensive guard in the system — $53.11 of measured
waste across 15 refusals — because the intuitive name is wrong. A gate-1 `plan-next`
writes `GATE-02-REVIEW.md`.

**What gate 2 is for.** The Azure adapter pair against the protocols T01 defined:
a Service Bus DLQ peek broker adapter, and App Insights KQL telemetry adapters for
the telemetry-keyed check types. Plus the cron-dialect contract, moved here at
drafting because it is schema work and the heartbeat adapter is what consumes it.

**Three things gate 2 must carry, decided at drafting and not re-openable by this
unit:**

1. **The cron dialect is declared, never inferred.** Heartbeat targets declare their
   dialect explicitly; the validator enforces the enum **and** the expression's arity
   against it. Inference by field count was considered and rejected by the operator
   on the grounds that it degrades silently when a new dialect appears. This widens
   0069's deliberate "target coordinate contents are opaque" position — say so in the
   drafted WU rather than letting it look accidental.
2. **The validator change is a severity flip, so §4's runtime probe is mandatory at
   arming.** Apply the change locally, run the exact command the WU's tests gate will
   run over every shipped YAML surface, and paste the finding list into
   `GATE-02-REVIEW.md`. That list is the enumerated migration surface. Arming without
   it is what makes an implementation WU spin on a defect one local run would have
   shown.
3. **Expand → migrate → contract, and the migrate criterion must be a sweep.**
   `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` lost $5.26 to a migrate criterion scoped
   to a *sample* ("a component with the new field exists and validates") where the
   flip needed a *sweep* ("no non-conforming instance remains anywhere"). Flip-first
   is not merely risky but unsatisfiable: the shipped example is validated by a code
   gate, so tightening the validator before migrating turns the gate red on a correct
   tree, and under the preflight baseline probe a red base gate halts the run before
   any unit dispatches.

**And one thing gate 2 must be honest about.** This repo cannot be the oracle for the
adapters — `verification.yml` records it "is a CLI tool with no deployable components
and will never carry a real monitoring.yml." Adapters will be verified against
stubbed transports in-loop, and against the downstream .NET backend only by an
operator run. Gate 2's close must name that in `## What the loop did NOT verify`
rather than claiming what a stub proved.

**Acceptance criteria.**

1. `GATE-02-REVIEW.md` exists in the feature directory and is non-empty. The filename
   is literal — named for the gate being armed.
2. `PLAN.md`'s gate 2 `work_units` list is no longer empty and contains at least one
   entry at `status: draft`.
3. Every drafted gate-2 WU file exists, is `status: draft`, and carries the five
   mandatory body sections.
4. A drafted WU covers the Service Bus DLQ peek broker adapter against T01's
   `BrokerAdapter` protocol.
5. A drafted WU covers the App Insights telemetry adapters against T01's
   `TelemetryAdapter` protocol.
6. A drafted WU covers the cron-dialect contract, and its body states that the
   dialect is declared rather than inferred and that this widens 0069's
   contents-opaque position.
7. The cron-dialect WU's migrate criterion is a **sweep** — asserting no
   non-conforming instance remains across every shipped YAML surface — not a sample.
8. `GATE-02-REVIEW.md` records the §4 runtime-probe requirement for the validator
   change, and states that the probe's finding list must be pasted in before arming.
9. Every drafted WU carries a `planned_cost_usd`, and `GATE-02.md` carries a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest.
10. `PLAN.md`'s `planned_cost_usd` is re-baselined to include gate 2's drafted units,
    and the delta against the previous figure is stated in `GATE-02-REVIEW.md`.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0040-failure-artifact-harvester`
    exits zero.

**Do not touch.** Source files owned by T01–T03. `RETROSPECTIVE.md` — the previous
unit wrote it; this one reads it. Gate 3's `close` placeholder, beyond leaving it in
place as the terminal entry. `PLAN.md`'s `status` field. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus criterion 11's lint run over the
whole feature folder. Note that drafted WUs are prose: their quality is checked by
the human at the arming checkpoint, which is what `GATE-02-REVIEW.md` exists to
support — criteria 4–8 are the structural floor, not a substitute for that review.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: gate
1's retrospective reports a finding that invalidates the drafted gate-2 shape — for
example that T01's protocols cannot express a Service Bus peek without a provider
type leaking into the core, which would make criterion 4 unsatisfiable as written;
or the §4 probe cannot be described because the validator change's surface is not yet
knowable. A gate-2 draft built on a premise gate 1 disproved is worse than no draft.
