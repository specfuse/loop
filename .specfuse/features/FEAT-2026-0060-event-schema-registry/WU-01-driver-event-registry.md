---
id: FEAT-2026-0060/T01
type: implementation
status: done
attempts: 2
re_arm_count: 3
re_arm_override: true
re_arm_history:
  -
    timestamp: 2026-08-03T00:12:33+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 5.308758
    prior_duration_seconds: 1350.329
    reason: "reporting defect made both attempts undiagnosable; fixed in #322, retrying clean"
  -
    timestamp: 2026-08-03T00:43:43+00:00
    prior_status: blocked_human
    prior_attempts: 1
    prior_cost_usd: 4.478344
    prior_duration_seconds: 772.327
    reason: "agent correctly escalated an unsatisfiable criterion 9 (zero total validator errors vs the vendored-schema Do-not-touch); criterion 9 rescoped to event_type, correlation_id gap filed as FEAT-2026-0073"
  -
    timestamp: 2026-08-03T11:27:50+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 3.922447
    prior_duration_seconds: 800.344
    reason: "registry shipped incomplete — criterion 3 derived the type list from the corpus only, which cannot see gate_auto_armed and re_arm_rejected (emitted in code, never fired in a recorded run); T02 found both and blocked. Criterion 3 widened to union build_event call sites with the corpus; operator raised the gate budget to $28.00 to fund the completion"
planned_cost_usd: 4.50
produces:
  - specfuse/loop/data/schemas/driver-event.schema.json
  - specfuse/loop/validate_event.py
  - tests/test_validate_event_driver_types.py
produces_driver_helper:
  - load_validator
oracle_env: macos_local
escalation_reason: spinning_signature_repeat
escalation_failure_class: tests
escalation_failure_signature: $ python3 -m unittest discover -s tests -v
duration_seconds: 1358.683
cost_usd: 2.593786
input_tokens: 4073
output_tokens: 22300
cumulative_cost_usd: 4.478344
cumulative_duration_seconds: 772.327
cumulative_input_tokens: 156
cumulative_output_tokens: 41202
cumulative_attempts: 3
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T00:48:21.920822+00:00
folded_through_re_arm: 3
---

# A driver-owned registry, resolved by fall-through

**Objective.** Sanction the event types the loop driver actually emits in a
schema this repository owns, and make `validate_event.py` resolve a
`source: "driver"` event against the vendored envelope first and the driver-local
registry second — so a real `events.jsonl` validates without the vendored file
being touched.

**Context.** Correlation ID `FEAT-2026-0060/T01`. Read `PLAN.md` first: it
records the measured seven-type list, why a driver-local registry was chosen over
editing the vendored schema, and why fall-through beats duplication. Do not
reopen those decisions.

The gap is already documented in the driver as precedent to follow rather than a
defect — `loop.py:704` says of `arm_predicate_evaluated`: *"Not validated by
validate_event.py … `gate_reached` and `attempt_outcome` are the existing
precedent for driver-local event types outside the envelope enum and per-type
registry."* That comment becomes false when this WU lands, and updating it is
part of the work.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## Re-derive the list; do not copy it

`PLAN.md` records seven unsanctioned types measured on 2026-08-02. **Four of them
appeared after the roadmap row was written naming three**, so the list is a
moving measurement, not a constant. Re-derive it as the first step — from **both**
sources, unioned:

```
(a) every build_event(...) call site in specfuse/loop/*.py  — what the driver CAN emit
(b) every .specfuse/features/*/events.jsonl                 — what the driver HAS emitted
then subtract the vendored envelope enum
```

**Source (a) is not optional, and it is the one a prior attempt missed.** An
earlier version of this criterion said "re-derive from the corpus", so that
attempt produced a registry of **seven** types and shipped it — but the corpus is
a *lagging* indicator. `gate_auto_armed` (`loop.py:6043`) and `re_arm_rejected`
(`loop.py:5332`) are emitted by real code paths that have never fired in any
recorded run, so no corpus sweep can see them. T02 derived from call sites,
found both missing, and correctly blocked rather than editing this WU's registry
itself. Both belong in the registry.

Note that some `build_event` calls span lines, so a single-line grep undercounts
— `re_arm_rejected` is one of them. Read the call sites, don't pattern-match a
tidy one-liner.

If the union differs from the seven in `PLAN.md`, the union is right and
`PLAN.md` is stale — register what you find and record the difference in the
result.

## Fall-through, stated precisely

`task_started`, `task_completed`, and `human_escalation` are **already in the
vendored enum**. They must keep validating against it and must **not** be
duplicated into the driver-local registry — a second definition is a second
thing to drift. The resolution order is: vendored envelope first; only if the
event's `event_type` is absent there, try the driver-local registry.

This mirrors a contract `validate_event.py` already has one level down —
`load_per_type_validator` returns `None` for an unknown type so it *"validates
against the top-level envelope alone."* Match that spirit: additive, absent means
fall back, never a hard failure on a missing file.

**The vendored schema is do-not-touch.** Its `$id` points at another repository
and its `$comment` is that repository's changelog. Editing it is the failure mode
this design exists to avoid; a diff to that file means this WU did the wrong
thing.

**Acceptance criteria.**

1. `tests/test_validate_event_driver_types.py::TestDriverEventTypes::test_real_driver_log_validates`
   exists and **fails on HEAD before this WU runs** — running the validator over
   `.specfuse/features/FEAT-2026-0062-lifetime-cost-reads/events.jsonl` reports
   `7 validation error(s) across 13 event(s)` today.
2. That test passes after this WU's edits: the same real log validates with zero
   errors.
3. The unsanctioned-type list is re-derived from **the union of `build_event`
   call sites and the corpus** per the section above, and the derived list is
   quoted in the result alongside `PLAN.md`'s seven, with any difference named.
   The result must state explicitly that `gate_auto_armed` and
   `re_arm_rejected` are present in the registry, since a corpus-only derivation
   demonstrably omits them.
4. Every derived type is sanctioned in
   `specfuse/loop/data/schemas/driver-event.schema.json`, a file this repository
   owns — with an `$id` that does **not** claim the orchestrator namespace.
5. `git diff --exit-code specfuse/loop/data/schemas/event.schema.json` shows
   **no change** to the vendored envelope. Quote the command and its exit code in
   the result.
6. A test asserts the three already-sanctioned types (`task_started`,
   `task_completed`, `human_escalation`) still validate, and a separate test
   asserts none of them appears in the driver-local registry — fall-through, not
   duplication.
7. A test asserts an event with an `event_type` in **neither** registry still
   fails validation. The point of the registry is that it is closed; a
   fall-through that accepts anything unknown is worse than the status quo.
8. A test asserts a missing or unreadable driver-local registry file degrades to
   vendored-only validation rather than raising — matching
   `load_per_type_validator`'s additive contract.
9. The validator is run over **every** `.specfuse/features/*/events.jsonl` in the
   repository and the **`event_type` error count** is recorded in the result. It
   must be **zero**; if any file still fails on `event_type`, name the file and
   the type.

   **Scoped to `event_type` deliberately — read this before widening it.** The
   original wording demanded zero *total* validator errors, which this WU cannot
   deliver: **279 `correlation_id` errors across 36 files** remain, because the
   vendored envelope's pattern
   `^(FEAT|INIT)-\d{4}-\d{4}(/F\d{2})?(/T\d{2})?$` rejects the
   closing-sequence (`G<n>-CLOSE`, `G<n>-PLAN`, …) and hygiene (`TNNH`) ID shapes
   that `.specfuse/rules/correlation-ids.md` documents as valid. Fixing that means
   editing the vendored schema this WU is forbidden to touch. That gap is filed as
   [FEAT-2026-0073](../../roadmap.md#feat-2026-0073) and is **not this WU's work**.
   The contradiction between the old criterion 9 and criterion 5 was authored, not
   discovered — a prior attempt correctly escalated on it rather than proceeding.

10. The `correlation_id` error count is **also** recorded in the result, as a
    known and separately-filed gap rather than a failure of this WU. Report the
    number; do not attempt to reduce it.
11. The stale comment at `loop.py:704` is corrected — it currently cites the gap
    as precedent, and after this WU that is no longer true.
12. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/data/schemas/event.schema.json` — the vendored
envelope, per criterion 5; if it seems to need changing, that is a design
question, not an implementation one. `specfuse/loop/data/schemas/events/*` — the
four vendored per-type payload schemas. `build_event` / `flush_events` — runtime
validation was explicitly declined in `PLAN.md`. `.specfuse/verification.yml` —
T02 wires the gate, and wiring it before this WU lands makes the gate set red.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run
in criteria 1–2 and the corpus-wide validation in criterion 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the red test in criterion 1 passes on HEAD, meaning the real log already
validates and this WU's premise is wrong; the re-derived list in criterion 3
contains a type whose correct home is genuinely the vendored schema rather than
the driver-local one — that is a cross-repo decision, not this WU's call;
resolving a driver event against two registries cannot be done without changing
`validate_line`'s contract in a way that affects orchestrator-sourced events,
which would widen the blast radius past what `PLAN.md` scoped; or criterion 9's
**`event_type`** count cannot reach zero — note that a non-zero `correlation_id`
count is expected and is NOT a reason to block, see criterion 10. If
`specfuse/loop/data/schemas/driver-event.schema.json` is absent from the files
you edited, emit `status: blocked` — do not claim complete.
