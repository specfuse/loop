---
feature_id: FEAT-2026-0070
title: Terminal-flip contract — hedged-verdict acceptance, row-status breadth, auto-close debt
slug: terminal-flip-contract
branch: feat/FEAT-2026-0070-terminal-flip-contract
roadmap_goal: Make a correctly-closed feature reach `done` through the driver from every legitimate starting state — row `planned` or `active`, verdict `met` or operator-accepted `met_locally` — so terminal state is never hand-edited, and make an auto-closed gate's skipped deferred-verification walk a visible debt rather than a silent saving.
autonomy_default: review
status: active
planned_cost_usd: 32.00
---

# Plan: Terminal-flip contract

Three issues, one symptom: **a correctly-closed feature whose recorded state lies.**

- **#226** — the roadmap row says `planned`. An `autonomy: auto` feature self-dispatches
  from a `planned` row, but `fire_terminal_flips` only handles `active → done`, so the
  row never flips and the `roadmap_row_not_done` invariant escalates on a correct close.
- **#243** — the roadmap row says `active`. A close writing `verdict: met_locally` leaves
  every WU `done`, the gate `awaiting_review`, and PLAN + roadmap `active`, with **no
  supported path to `done`**. For some features `met_locally` is the ceiling by
  construction, not by accident.
- **#241** — the retrospective says nothing. An auto-closed gate skips the
  per-criterion deferred-verification walk, and nothing downstream is obliged to
  reconcile it.

The first two are the same two functions and are gate 1. The third is a different
module and a different kind of defect — a skipped *deliverable* rather than a withheld
*flip* — and is gate 2, drafted by `plan-next` once the flip contract has settled.

## Scope boundary

**IN — gate 1.** Broaden the row-flip precondition (#226); a driver-side primitive that
re-evaluates a completed close WU's verdict and fires the flips when it now permits
them; an `/accept-hedged-close` operator path built on that primitive (#243 candidate 1);
and the pre-registered `lint_plan` verdict-exempt fix from
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`.

**IN — gate 2.** Auto-close's skipped deferred-verification enumeration (#241),
sketched below.

**OUT — held at drafting, deliberately.** #243's candidate 2, *a roadmap status between
`active` and `done`* (`done_hedged` or similar). A new status value is a contract every
downstream project, every skill, and `lint_plan`'s row parser reads; `done` carrying an
open-follow-up count gets most of the benefit without a new enum member. Revisit only if
the acceptance path proves insufficient in practice.

**OUT — prevention, not repair.** #243's candidate 3, *pre-declaring the ceiling at draft
time* — a feature whose definition of done is an operator experience declaring
`met_locally` as its planned ceiling in `PLAN.md`. Real value, but it is a
`/draft-feature` interview change and it does not help the features already sitting in
the dead end. If gate 1 lands cleanly this is the natural follow-up feature.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rniE "accept_hedged|accept-hedged|override.*verdict|force.*flip|recheck" specfuse .specfuse/skills .specfuse/rules
    -> 2 hits, both `_override_active` in loop.py — the RE-ARM override
       (`re_arm_override`), an unrelated mechanism
ls .specfuse/skills/
    -> 21 skills; none flips terminal feature state. `wrap-feature` explicitly
       refuses non-`done` features and says "do not attempt manual reconciliation"
grep -n "def fire_terminal_flips|def verdict_permits_terminal_flips" specfuse/loop/loop.py
    -> loop.py:3128, loop.py:134 — the two functions gate 1 changes
```

**Verdict: no existing mechanism, building new — but the new work must REUSE, not
replace, `fire_terminal_flips`.** This is the binding constraint on the whole gate, from
`.specfuse/LEARNINGS.md`:

> `[FEAT-2026-0023/G1-CLOSE]` **Terminal-state flips must have exactly ONE driver-side
> owner called identically by every close path.** #49 existed because two paths diverged:
> the dispatched-close path relied on the close WU's *agent* to flip `PLAN.md`, while the
> agent-less auto-close path ran no agent and `fire_terminal_flips` never touched PLAN.

An `/accept-hedged-close` skill that writes the three surfaces itself would rebuild that
divergence exactly. T03 therefore calls T02's primitive; it does not write terminal
state. **A WU that hand-writes a terminal surface has failed this feature's central
constraint even if every gate passes.**

## Escalation-predicate satisfiability (mandatory — §2)

Gate 1 raises no severity. It **broadens** two preconditions (a row status, a verdict
gate) and adds an operator path — every change makes the driver accept more, not less.
Existing correct closes are unaffected: `active → done` on `verdict: met` continues to
fire exactly as today, and T01/T02 add tests asserting that.

The one place a *new* refusal appears is T04's `lint_plan` exempt-set fix, and it makes
the linter **stricter** on `in_progress`/`in_review` close WUs. What does it report on a
tree already in its intended final state? **Zero** — a close WU is only `in_progress`
mid-dispatch, and every committed close WU in this repo is `done`. The satisfiability
probe belongs in T04's acceptance criteria rather than here, because it must be run
against the tree at execution time.

**Gate 2 does raise a severity** — #241's option 3 is a post-pass invariant that
escalates when a terminal close ignores an auto-closed predecessor's debt. That question
is `plan-next`'s to answer at gate-1 close, with the probe run at arming per
`GATE-01.md`'s arming discipline. Recorded here so it is not rediscovered.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0070/T01
        file: WU-01-row-flip-breadth.md
        depends_on: []
      - id: FEAT-2026-0070/T02
        file: WU-02-verdict-recheck-primitive.md
        depends_on: []
      - id: FEAT-2026-0070/T03
        file: WU-03-accept-hedged-close-skill.md
        depends_on: [FEAT-2026-0070/T02]
      - id: FEAT-2026-0070/T04
        file: WU-04-lint-verdict-exempt-set.md
        depends_on: []
      # --- non-terminal gate: close-intermediate then plan-next ---
      - id: FEAT-2026-0070/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0070/T01
          - FEAT-2026-0070/T02
          - FEAT-2026-0070/T03
          - FEAT-2026-0070/T04
      - id: FEAT-2026-0070/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]

  - gate: 2
    file: GATE-02.md
    work_units:
      # Drafted by G1-PLAN. T05 is a precursor extraction; T06 writes the debt
      # enumeration + marker; T07 reads the marker; T08 predicts T07's refusal
      # at arm time. See GATE-02-REVIEW.md for the arming evidence.
      - id: FEAT-2026-0070/T05
        file: WU-05-shared-wu-section-slicers.md
        depends_on: []
      - id: FEAT-2026-0070/T06
        file: WU-06-autoclose-debt-enumeration.md
        depends_on: [FEAT-2026-0070/T05]
      - id: FEAT-2026-0070/T07
        file: WU-07-autoclose-debt-invariant.md
        depends_on: [FEAT-2026-0070/T06]
      - id: FEAT-2026-0070/T08
        file: WU-08-arm-time-debt-prediction.md
        depends_on: [FEAT-2026-0070/T07]
      - id: FEAT-2026-0070/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on:
          - FEAT-2026-0070/T05
          - FEAT-2026-0070/T06
          - FEAT-2026-0070/T07
          - FEAT-2026-0070/T08
```

## Gate 2 sketch (for `plan-next`, not binding)

Definition of done: an auto-closed gate leaves a concrete deferred-verification worklist,
and a terminal close that ignores it is visible rather than silent.

- **Auto-close writes the enumeration itself** (#241 option 1). Mechanical — it already
  knows the gate's WUs, so it can list each one's acceptance criteria under a
  `deferred: unknown — not enumerated (auto-closed)` heading. No agent dispatch, so it
  does not reintroduce the cost auto-close exists to avoid.
- **A post-pass invariant** (#241 option 3): if any non-terminal gate auto-closed and the
  terminal close's `## What the loop did NOT verify` never mentions it, escalate. This is
  the severity flip §2 flags above.
- The framing, from `[FEAT-2026-0039/G2-CLOSE]`: *an auto-closed gate's skipped ceremony
  is a **debt entry, not a saving**.* That feature's gate 1 auto-closed at $0.00 against a
  $5.00 estimate and simply moved the walk into the terminal close — where it cost *more*,
  because the session doing it had not written those WUs.

## Notes

- **Multi-gate (4 planned substantive WUs in gate 1, plus gate 2's)** — full ceremony per
  `docs/methodology.md §6`. Gate 1 is non-terminal; gate 2 pre-declares its terminal close.
- **T02 before T03 is not a preference.** T02 is the single driver-side owner of the
  flips; T03 is a skill that invokes it. A skill that writes terminal state itself is
  `[FEAT-2026-0023/G1-CLOSE]` violated verbatim, and that rule cost issue #49 to learn.
- **T02 also closes a gap none of the three issues report.** FEAT-2026-0069 discharged its
  follow-ups post-close and honestly upgraded `verdict: met_locally → met` — and
  re-running the driver **still** did not fire the flips, because `fire_terminal_flips`
  runs at close-WU-*outcome* time and that WU was already `done`. Three surfaces were
  hand-flipped, which is precisely what this feature exists to stop. Recorded on #243 as
  a second defect.
- **T04's real defect is diagnostics, not strictness.** `lint_plan.py:626`'s exempt set
  omits `in_progress`/`in_review`, so a close WU that fails to write its verdict fails
  plan-lint *mid-dispatch* with a message about the WU rather than about the missing
  verdict. Same family as #265 and #272: the driver enforcing a contract whose violation
  it does not explain.
- **Cost note.** $32.00 against the per-type floors set by #266: gate 1 at $20.50
  (T01 $2.50, T02 $3.50, T03 $2.50, T04 $1.50, `close-intermediate` $4.50, `plan-next`
  $6.00), gate 2 sketched at ~$11.50. Implementation estimates sit above the observed
  $1.33 median because all four touch driver internals with existing guard tests.
- **Gate 2 drafted at exactly $11.50** by `G1-PLAN` (T05 $1.00, T06 $2.00, T07 $2.25,
  T08 $1.25, `close` $5.00), so the WU sum now reconciles to $32.00 and the cost-delta
  WARN below is retired. The match is arithmetic, not evidence: gate 1's *actual* is
  running a different shape — the substantive half came in **53.5% under** plan while the
  `close-intermediate` came in **41.6% over** ($6.37 against $4.50). `GATE-02-REVIEW.md`
  § *Cost reconciliation* carries the split, and `G2-CLOSE` reconciles actuals against
  this as-drafted $32.00 rather than re-baselining onto it.
- **~~Expected lint cost-delta WARN until gate 1 closes~~** — retired at `G1-PLAN`, which
  drafted gate 2's substantive WUs. The as-drafted figure stands unadjusted.
