---
feature_id: FEAT-2026-0104
title: Re-plan after two failures instead of a third identical attempt
slug: replan-after-two-failures
branch: feat/FEAT-2026-0104-replan-after-two-failures
roadmap_goal: After two failed attempts on a unit the driver re-plans it rather than re-running the same prompt, and a blocked_human escalation offers a re-plan of the remaining gate as its default option.
autonomy_default: review        # this feature edits the driver; the judge_editing stop
                                # class vetoes an auto-arm regardless, so `review` states
                                # up front what would otherwise surface at the gate boundary
status: active
planned_cost_usd: 30.00
---

# Plan: Re-plan after two failures instead of a third identical attempt

Retrying a failing work unit three times with the same prompt is the pattern
the field warns against, and the corpus agrees: FEAT-2026-0082/T04 took six
dispatches and two carve-outs, and one consumer feature spent $2.82
re-deriving a precondition its own plan had already predicted. Spinning is a
unit-shape problem, not a retry-count problem — the third attempt fails for
the reason the second did, and the only thing that changes between them is
the bill.

The measurement that pulled this feature forward is narrower than that.
Re-measured on 2026-09-10 across the deduped corpus, cut by the driver
version that ran each attempt, human waits per feature moved from 1.16 on
drivers up to 0.14.x to 2.09 on 0.15.0 and later. Every other headline
metric held flat or improved. Escalations are what a spinning unit turns
into once it exhausts its attempts, so the way to move that number is to
stop producing units that reach the wall — not to make the wall friendlier.

This file owns the **shape** of the feature: the gate order, which work units
belong to each gate, and the dependency edges between them. It does **not**
own status — each WU file owns its own status, and each GATE file owns its
gate's status. Detail only as far as the next gate; plan-next drafts the gate
after that from the retrospective and lessons.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -rn '"replan"' --include=*.py specfuse tests`
  - `grep -rn "replan" docs/*.md`
  - `python3 -c "import json; print(json.load(open('specfuse/loop/data/schemas/driver-event.schema.json'))['event_types'])"`
- **Verdict:** `found the consumer, building only the emitter`.

  `specfuse/loop/gate_eval.py:197` already reads `event_type: "replan"` as
  check 2 of the auto-close predicate — a replan on any of a gate's work
  units disables auto-close for that gate. The behaviour is documented at
  `docs/methodology.md:187` ("**No replan** — no `replan` event in
  `events.jsonl` for this gate's WUs") and fixtured by
  FEAT-2026-0018/T02's `TestReplanEvent`. Nothing in the codebase emits the
  event, and no feature's `events.jsonl` in the corpus contains one.

  So the auto-close interaction this feature would otherwise have to design
  is already built, tested and documented; the missing half is the trigger
  that fires it. The one gap on the emit side: `replan` is **not** in the
  driver event-type registry (`driver-event.schema.json`, 15 types), so
  emitting it today fails the repo's own `event-type-gate`. T04 closes that.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to
blocking, and asserts no "zero issues" close predicate. It adds a dispatch
decision and one event type.

## Decisions taken at drafting

- **Both halves ship, split across two gates.** The roadmap goal names a
  re-plan trigger and a re-plan option in the escalation brief. They share a
  concept but touch different code and have different oracles, so the trigger
  is gate 1 and the brief is gate 2.
- **In-place re-scope, not a split.** The re-plan turn rewrites the failing
  unit's own body and resets its attempts; it does not author new units or
  rewire `depends_on`. Splitting would mutate `gate.refs` mid-flight, and
  everything keyed to a gate's declared unit set — the planned-cost tally,
  the auto-close per-WU ratio checks, the dispatch-order staleness summary —
  moves under it. Deferred until re-plan has behaved on real spins.
- **Ceiling-relative trigger, `iterate_on_failure` exempt.** Re-plan replaces
  the last permitted attempt rather than firing on a hard count of two. At
  the default `MAX_ATTEMPTS = 3` that is "after two failures" exactly as the
  roadmap states it, and a unit that declared its own ceiling keeps it —
  `resolve_max_attempts`' whole premise is that the unit's author knows that
  unit's oracle. Units declaring `iterate_on_failure` are exempt outright:
  they fail on purpose against a convergent validator, and reading that as
  spinning would be a defect.

## The constraint gate 1 is built around

`units = [load_wu(feature_dir, ref) for ref in gate.refs]` (`loop.py:9202`)
runs **once per gate, before** the `while True:` dispatch loop, and `load_wu`
is never called again inside it. The running gate holds a snapshot of both
the graph and every unit's body, so a re-planned unit is invisible to the
gate that re-planned it until the driver restarts. Establishing a reload
point for one unit is therefore not a detail of the feature — it is the
thinnest end-to-end path, and T01 is the tracer bullet that wires it.

## Scope boundary — deliberately out

- Splitting a unit into new units, and any mid-gate mutation of `gate.refs`.
- Changing `MAX_ATTEMPTS`' default of 3.
- Parallel dispatch of the ready frontier — that is FEAT-2026-0105.
- Whether gate 2's brief can *execute* a re-plan on the operator's yes, or
  only recommend it. That depends on how gate 1 behaves on real spins, and
  gate 1's `plan-next` will have the evidence this draft does not.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0104/T01
        file: WU-01-replan-tracer-bullet.md
        depends_on: []
      - id: FEAT-2026-0104/T02
        file: WU-02-trigger-predicate.md
        depends_on: [FEAT-2026-0104/T01]
      - id: FEAT-2026-0104/T03
        file: WU-03-planning-turn-contract.md
        depends_on: [FEAT-2026-0104/T01]
      - id: FEAT-2026-0104/T04
        file: WU-04-emit-replan-event.md
        depends_on: [FEAT-2026-0104/T02, FEAT-2026-0104/T03]
      - id: FEAT-2026-0104/T05
        file: WU-05-document-the-trigger.md
        depends_on: [FEAT-2026-0104/T04]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0104/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0104/T01
          - FEAT-2026-0104/T02
          - FEAT-2026-0104/T03
          - FEAT-2026-0104/T04
          - FEAT-2026-0104/T05
      - id: FEAT-2026-0104/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0104/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # --- closing sequence: 1-WU close (terminal gate) ---
      # Scaffolded now so lint reads gate 1 as non-terminal.
      # G1-PLAN fills in gate 2's substantive WUs above this entry.
      - id: FEAT-2026-0104/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: []   # G1-PLAN will set real depends_on when it drafts gate 2
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never
  needs to know its own dependencies — they are satisfied by the time the
  driver hands it the file.
- WU file numbers track the correlation sub-ID where it exists
  (`WU-04` ↔ `/T04`). Closing units use the reserved 90+ range so they sort
  last.
