---
feature_id: FEAT-2026-0073
title: Envelope correlation_id accepts the ID shapes the methodology documents
slug: correlation-id-envelope
branch: feat/FEAT-2026-0073-correlation-id-envelope
roadmap_goal: Make the event envelope accept the correlation-ID shapes correlation-ids.md documents — closing-sequence G<n>-<NAME> and hygiene TNNH — so the driver's event log validates end to end rather than in the event_type dimension alone.
autonomy_default: review
status: done
planned_cost_usd: 12.50
---

# Plan: Envelope `correlation_id` accepts the IDs the methodology documents

The vendored envelope constrains `correlation_id` to
`^(FEAT|INIT)-\d{4}-\d{4}(/F\d{2})?(/T\d{2})?$` — a substantive work unit and nothing
else. `.specfuse/rules/correlation-ids.md` documents two further valid shapes: closing
units use `G<n>-<NAME>`, hygiene units use `TNNH[N…]`. So **every event a closing work
unit has ever emitted fails validation**, and has since closing units were given their
own ID shape.

## The decision the roadmap left open, and the evidence that settles it

The row named two options and said the `event_type` answer may not transfer.

**Chosen: a driver-local override, following FEAT-2026-0060's precedent.**

The deciding evidence is in the vendored file itself. Its `$id` is
`https://specfuse.dev/orchestrator/schemas/event.schema.json` — another repository owns
it — and its `$comment` is that repository's changelog, which **already records a prior
upstream widening of this exact field** ("correlation_id pattern widened from
`^FEAT-\d{4}-\d{4}(/T\d{2})?$` to … as part of the reframe migration"). That is a file
with live upstream history. Editing it here forks it, and the next vendor sync reverts
the fix silently — reinstating 285 failures with no signal that anything regressed.

The counter-argument in the roadmap row is real and is **not** dismissed: ID *format* is
more plausibly a shared protocol concern than event vocabulary is, and a local widening
risks the two diverging in a way that breaks a consumer reading both logs. The answer is
not to make an unowned edit but to record the upstream need explicitly — the close files
it — so the local override is a documented bridge rather than a silent fork.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

FEAT-2026-0060 built precisely this mechanism one feature ago, and it must be reused
rather than duplicated:

```
specfuse/loop/data/schemas/driver-event.schema.json   the driver-local registry
validate_event.load_driver_event_types()              reads it, degrades to empty set
validate_event.load_validator()                       fall-through on a DEEP COPY, so
                                                      the vendored schema on disk is
                                                      never touched
```

This feature extends that registry with the correlation-ID shapes and widens the pattern
through the same deep-copy path. It does not invent a second override mechanism, and it
does not write to the vendored file.

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

T02's criterion is "the validator reports zero errors corpus-wide," which is
satisfiable **only if `correlation_id` is the sole remaining error class.** Measured
before drafting, at the tree this feature starts from:

```
285 errors across 38 feature folders
by kind: {'correlation_id': 285, 'other': 0}
shapes : G<n>-CLOSE 98, G<n>-PLAN 87, G<n>-CLOSE-INTERMEDIATE 28,
         G<n>-DOCS 23, G<n>-RETRO 22, G<n>-LESSONS 20
```

Every failure is `correlation_id`, and every shape is a `G<n>-<NAME>` closing unit — all
of them forms `correlation-ids.md` already documents. So zero-errors is reachable. This
is the check FEAT-2026-0060 did not do: it measured `event_type` failures only, declared
satisfiability on that basis, and authored a criterion demanding zero *total* errors
while forbidding the only file that could deliver them. One blocked attempt, $4.48.

The count grows with every feature that closes (279 when the row was filed, 282, now
285), so T01 and T02 will measure a different number than this. **That is expected and
is not a block** — the shape distribution is what matters, not the total.

## Runtime probe for a default/severity flip (§4)

Not applicable. No default, threshold, or severity is flipped. A pattern is widened to
accept inputs the methodology already calls valid; nothing that validates today stops
validating. The widening is strictly additive, which T01 asserts directly.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced.

## Scope boundary — explicitly OUT

- **Editing the vendored `event.schema.json`.** Reasoned above. The deep-copy
  fall-through exists so this is unnecessary.
- **Fixing the upstream orchestrator schema.** Out of this repository's reach. The close
  files the upstream need so the local override is a recorded bridge, not a silent fork.
- **Rewriting historical correlation IDs.** The 285 failing events are correct as
  emitted; the schema is what disagrees with the documented contract. Nothing rewrites
  history.
- **Widening any other envelope field.** `correlation_id` only.

## The trap that will otherwise be rediscovered

**`correlation-ids.md` and the schema must end up stating the same contract**, because
the entire defect is that they do not. A change that widens the pattern without
reconciling the rules file leaves the same class of disagreement in place, just shifted.
T01 owns both surfaces for that reason.

## Gates

```yaml
# Single terminal gate: 2 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0073/T01
        file: WU-01-correlation-id-override.md
        depends_on: []
      - id: FEAT-2026-0073/T02
        file: WU-02-widen-the-gate.md
        depends_on: [FEAT-2026-0073/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0073/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0073/T01
          - FEAT-2026-0073/T02
```
