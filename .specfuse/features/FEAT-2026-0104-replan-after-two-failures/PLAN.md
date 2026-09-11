---
feature_id: FEAT-2026-0104
title: Re-plan after two failures instead of a third identical attempt
slug: replan-after-two-failures
branch: feat/FEAT-2026-0104-replan-after-two-failures
roadmap_goal: After two failed attempts on a unit the driver re-plans it rather than re-running the same prompt, and a blocked_human escalation offers a re-plan of the remaining gate as its default option.
autonomy_default: review        # this feature edits the driver; the judge_editing stop
                                # class vetoes an auto-arm regardless, so `review` states
                                # up front what would otherwise surface at the gate boundary
status: done
planned_cost_usd: 43.50   # revised at G1-PLAN; see "The estimate was revised once"
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

## Gate 1 was reverted once — what the first attempt taught

Gate 1's first run dispatched T01-T04, all passed first try, all committed.
The gate then halted at T05's entry with a red baseline. The work was
reverted to this plan's baseline commit and gate 1 re-run against the
criteria below, which are rewritten as a result.

Three defects, none of which any unit's acceptance criteria could fail on:

1. **The unit loop did not terminate.** The re-plan branch rewound the attempt
   counter to 0, so the ceiling-relative trigger re-fired at the same point on
   every fresh budget. `test_bookkeeping_commit_crash_run` hung, and because
   it sorts early the rest of the suite never ran — the hang masked the other
   two defects for the whole gate.
2. **The planning turn was a string append.** `run_replan_turn` returned
   `wu.body.strip() + marker`: no session dispatched, nothing narrowed. The
   roadmap goal's "dispatches a planning turn" was not implemented, and every
   criterion still passed.
3. **A re-planned unit that passed was stranded.** The reload replaced the
   unit object without reconciling it with the list `ready()` iterates, so a
   unit that had passed and committed was reported `never became ready`.

The common cause is criteria, not agents. Each unit was asked to prove its own
part worked and none was asked to prove the composition still did. Two
structural changes follow from that, and both are in the criteria below:

- **Termination and end-to-end survival are acceptance criteria**, not
  implications of one. T02 must prove the loop ends; T01 must prove a
  re-planned unit still reaches `done` through the gate's own bookkeeping.
- **The narrow per-attempt tier cannot verify these units.** They edit the
  central dispatch loop, which 44 test modules drive through `loop.run()`, so
  their blast radius is the whole suite while `produces:` names only their own
  new module. T01-T04 each carry the full suite in **Verification**:
  `python3 -m unittest discover -s tests -b`, OK on 3901 tests in ~151s on a
  clean tree. That is the check that would have caught all three at attempt 1.

The four test modules the first attempt wrote are kept out of tree as the
contract the rewrite must meet, not restored: they assert against symbols that
no longer exist.

## The estimate was revised once — $30.00 → $39.50 at G1-PLAN

`planned_cost_usd: 43.50` was set before gate 2 had any work units, and it
decomposed exactly as 14.50 (T01–T05) + 4.50 (G1-CLOSE-INTERMEDIATE) + 6.00
(G1-PLAN) + 5.00 (G2-CLOSE) — leaving **nothing** for gate 2's substantive
work. `RETROSPECTIVE.md` § "Cost analysis" flagged that hole and asked
`G1-PLAN` to either fit gate 2 into the ~$5.74 remaining or revise the figure
deliberately. Revised, deliberately: gate 2's four substantive units are
3.50 + 3.00 + 1.50 + 1.50 = **9.50**, so the feature's plan is 14.50 + 4.50 +
6.00 + 9.50 + 5.00 = **39.50**.

Fitting gate 2 into $5.74 was the alternative and was rejected: at
`planning-discipline.md` §5's floors a terminal `close` alone is $5.00, so
the whole of gate 2's implementation would have had to cost under a dollar.
That is not a smaller gate, it is a fictional one.

Neither gate carries a `cost_budget_usd`. Gate 1 was drafted without one and
adding the brake to gate 2 alone would make the two gates behave differently
for a reason unrelated to their content; the feature-level estimate above is
the number to hold this gate against.

## Gate 2 was widened once, on measured evidence

Gate 2 closed twice and was reopened to add T10. The reason is not the judge's
second finding — that one is circular and is tracked as a judge defect in
#3307, having asked for terminal-flip state only a `met` verdict can produce.

It is a probe. Every proof this feature had stubbed the `claude -p` boundary,
so a throwaway feature was run against a real one to see the trigger fire. It
never fired: two differently-rigged units both **blocked honestly** rather than
spinning, the second because the session found a real repository constraint the
probe's own work unit contradicted. That is worth recording on its own —
well-specified units escalate with a reason instead of spinning, which bounds
how much of the 2.09 human-waits number a re-plan trigger can move.

What the probe did produce is a real `agent_reported_blocked` escalation, and
its payload carried `reason`, `attempts`, `attempts_usage`, `blocked_reason`
and no `message`. `format_spinout_escalation_brief` is called from exactly one
site. Measured across 636 `human_escalation` events in the corpus, the brief
reaches about 19% of real escalations; the most common reason of all,
`agent_reported_blocked` at 22.2%, gets none of it.

`GATE-02-REVIEW.md` predicted this at arming — "that narrowing is the draft's
reading, not the plan's words" — and named `agent_reported_blocked` as the row
most likely wrong. It was armed anyway. T10 closes the gap the review called.

## Scope boundary — deliberately out

- Splitting a unit into new units, and any mid-gate mutation of `gate.refs`.
- Changing `MAX_ATTEMPTS`' default of 3.
- Parallel dispatch of the ready frontier — that is FEAT-2026-0105.
- Executing a re-plan from gate 2's brief. This was drafted as an open
  question — it depended on how gate 1 behaved on real spins — and `G1-PLAN`
  settled it as **recommend only** on gate-1 evidence. The reasoning and the
  four citations are in `GATE-02.md` § "The question gate 1 left open";
  executing is now deliberately out of scope rather than undecided.

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
      - id: FEAT-2026-0104/T06
        file: WU-06-spinout-brief-tracer-bullet.md
        depends_on: []
      - id: FEAT-2026-0104/T07
        file: WU-07-replan-option-recommend-only.md
        depends_on: [FEAT-2026-0104/T06]
      - id: FEAT-2026-0104/T08
        file: WU-08-replan-note-collision.md
        depends_on: [FEAT-2026-0104/T06]
      - id: FEAT-2026-0104/T09
        file: WU-09-document-the-brief.md
        depends_on: [FEAT-2026-0104/T07, FEAT-2026-0104/T08]
      - id: FEAT-2026-0104/T10
        file: WU-10-brief-every-unit-escalation.md
        depends_on: [FEAT-2026-0104/T09]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0104/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on:
          - FEAT-2026-0104/T06
          - FEAT-2026-0104/T07
          - FEAT-2026-0104/T08
          - FEAT-2026-0104/T09
          - FEAT-2026-0104/T10
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never
  needs to know its own dependencies — they are satisfied by the time the
  driver hands it the file.
- WU file numbers track the correlation sub-ID where it exists
  (`WU-04` ↔ `/T04`). Closing units use the reserved 90+ range so they sort
  last.
