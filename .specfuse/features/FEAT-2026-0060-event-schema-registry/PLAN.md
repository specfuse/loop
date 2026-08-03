---
feature_id: FEAT-2026-0060
title: Driver-local event schema registry — sanction the driver's own event types
slug: event-schema-registry
branch: feat/FEAT-2026-0060-event-schema-registry
roadmap_goal: Give the loop driver a registry that sanctions the event types it actually emits, so validate_event.py passes over a real driver-produced events.jsonl, and add a standing check so the next unsanctioned type is caught in CI rather than accumulating unnoticed.
autonomy_default: review
status: done
planned_cost_usd: 13.00
---

# Plan: Driver-local event schema registry

The loop driver writes every event it emits to `events.jsonl` with
`source: "driver"`. The envelope schema those events are nominally validated
against — `specfuse/loop/data/schemas/event.schema.json` — carries a closed
28-entry `event_type` enum that does not contain most of what the driver emits.
The gap is invisible because `build_event` / `flush_events` never invoke the
validator: `validate_event.py` is a standalone CLI nobody runs over the driver's
own output.

## The measured state, which is worse than the roadmap recorded

The roadmap row names three unsanctioned types. A sweep of every `events.jsonl`
in the repository finds **seven**, and they account for a third of all events
ever emitted:

```
OK   task_started                335
OK   task_completed              304
GAP  attempt_outcome             237
GAP  gate_reached                 77
OK   human_escalation             33
GAP  auto_close_decision          19
GAP  arm_predicate_evaluated       5
GAP  plan_next_draft_lint          4
GAP  re_arm_dispatched             3
GAP  unsandboxed_dispatch          2

347 of 1019 events (34%) fail envelope validation
```

Running the validator over a single real feature log confirms it:
`validate_event --file .specfuse/features/FEAT-2026-0062-lifetime-cost-reads/events.jsonl`
reports `7 validation error(s) across 13 event(s)`.

**Four of the seven arrived after the roadmap row was filed naming three.** That
is the argument for the standing check: this gap does not sit still.

## Two findings that shaped the design

**The vendored schema anticipates the driver; it just lacks its vocabulary.**
The `source` property's description reads *"the loop's single-repo `driver` …
is the loop execution surface's sole emitter"*, and there is **no `source`
enum**. So `LEARNINGS [FEAT-2026-0002/G1-CLOSE]`'s claim that the orchestrator
schema "rejects driver-emitted events by design (the schema's `source` enum is
the orchestrator protocol)" no longer holds against the vendored copy — the only
thing rejecting driver events is the `event_type` enum. That lesson describes a
schema version this repository no longer ships.

**Three driver types are already sanctioned.** `task_started`,
`task_completed`, and `human_escalation` all validate. The driver is partially
inside the contract, which is why nobody noticed it was mostly outside.

## The decisions this feature settles

**A driver-local registry, not an edit to the vendored file.** The vendored
schema's `$id` is `https://specfuse.dev/orchestrator/schemas/event.schema.json`
and its `$comment` is a changelog of another repository's work units. This
repository does not own that file. Editing it here would be reverted or silently
diverged by the next vendor sync — a worse failure than today's, because it
would look fixed. Five of the seven types (`gate_reached`,
`auto_close_decision`, `arm_predicate_evaluated`, `re_arm_dispatched`,
`unsandboxed_dispatch`) describe loop-driver mechanics the orchestrator has no
concept of, so the split matches reality rather than forking a shared contract.

**Fall-through, not duplication.** The driver-local registry sanctions only what
the vendored one does not. `human_escalation`, `task_started`, and
`task_completed` keep resolving against the vendored enum, so there is no second
definition to drift. This mirrors a contract `validate_event.py` already has one
level down: `load_per_type_validator` treats per-type payload schemas as
additive — *"an event type without a schema file … validates against the
top-level envelope alone."*

**A drift guard and a real-log gate, not runtime validation.** Validating inside
`build_event` was rejected. Events are buffered and flushed at *outcome* time, so
a raise there would destroy the record of the work unit that just ran — turning a
schema nit into lost audit data at the worst possible moment. Instead the check
moves to CI, where it is cheap: a test asserting every emittable type is
registered, and a gate running the validator over this repository's own event
logs. The real-log gate is the one that matters — its absence is why 34% of
events failed silently for the driver's entire history.

## Scope boundary

**IN.** The driver-local registry sanctioning the seven types; fall-through
resolution in `validate_event.py`; the drift guard; the `verification.yml`
real-log gate.

**OUT — per-type payload schemas for the seven.** The goal is the validator
passing over a real log, and envelope conformance achieves that.
`load_per_type_validator` treats payload schemas as additive by design, so their
absence is contract-conformant rather than a gap. Authoring seven payload schemas
is real work with no failing check behind it; it can follow once the envelope is
sound.

**OUT — editing `specfuse/loop/data/schemas/event.schema.json`**, and
upstreaming anything to the orchestrator repository. Both are the point of
choosing a driver-local registry.

**OUT — runtime validation in `build_event`.** Declined above, on audit-log
durability grounds.

**OUT — `source` values other than `driver`.** All 1019 corpus events carry
`source: "driver"`; no other emitter writes to a loop feature's event log.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  `grep -rn "driver.schema\|driver_events\|DRIVER_SCHEMA\|driver-local" specfuse/ .specfuse/scripts/ tests/`
  and `grep -rn "EVENT_TYPES\|_EVENT_TYPE\|event_type_registry" specfuse/ tests/`
- **Verdict:** `no existing mechanism, building new`

The first returns exactly one hit, and it is a comment **admitting the gap**
rather than a mechanism — `loop.py:704`, inside `build_arm_predicate_event`:

> *"Not validated by validate_event.py — see the WU's Verification note;
> `gate_reached` and `attempt_outcome` are the existing precedent for
> driver-local event types outside the envelope enum and per-type registry."*

The gap was known, written down, and treated as precedent to follow rather than
a defect to fix. The second grep returns nothing: no event-type registry exists
anywhere in the package.

**Two seams are reused rather than built.** `_resolve_schema_root()` already
supports a `$SPECFUSE_SCHEMA_ROOT` override plus an `importlib.resources`
default, so the resolution point exists and needs extending, not inventing. And
the drift guard copies a shape this repository has built twice —
`tests/test_label_registry_covers_consumers.py` (FEAT-2026-0071) and
`tests/test_bats_suites_gated.py` (FEAT-2026-0072). T02 follows their shape
without importing from them; two guards over unrelated surfaces sharing a helper
would couple them for no gain.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature adds a blocking gate, so the check applies.

- **What does the rule report on an input already in its intended final state?**
  **Zero — but only after T01 lands.**

This is the sharp part. The real-log gate reports **7 errors on the tree as it
stands** and must report **0** after the registry exists. A gate that fires on
the current tree is unsatisfiable until the tree is corrected, so **T02 depends
on T01** and must not wire the gate into `verification.yml` before the registry
sanctions the seven types. The drift guard has the same ordering: it reports
seven unregistered types today and zero once T01 lands.

## Task graph

```yaml
# Single terminal gate: 2 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0060/T01
        file: WU-01-driver-event-registry.md
        depends_on: []
      - id: FEAT-2026-0060/T02
        file: WU-02-drift-guard-and-gate.md
        depends_on: [FEAT-2026-0060/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0060/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0060/T01
          - FEAT-2026-0060/T02
```

T02 depends on T01 for the satisfiability reason above, not merely for tidiness:
wiring a red gate into `verification.yml` would fail every subsequent WU in this
gate, including its own close.

## Notes

- **The seven-type list is a measurement, not a constant to trust.** It was taken
  from the corpus on 2026-08-02 and four types had already appeared since the
  roadmap row was written. T01 must re-derive the list from the corpus rather
  than copying it from this document, and record any difference.
- **`autonomy_default: review` is structural.** `specfuse/loop/` is a
  `JUDGE_PATHS` prefix (`arm_eval.py:57`), so every gate fires `judge_editing`
  and `auto` is unreachable regardless of this field.
- No bootstrap problem: because validation stays out of the emit path, a work
  unit that changes event emission does not validate through the code it is
  changing. Had Q2 gone the other way, it would have.
