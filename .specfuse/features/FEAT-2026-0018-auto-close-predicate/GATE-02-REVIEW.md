# Gate-2 review — drafted by G1-PLAN

This document is the operator's pre-arm review for gate 2 of
`FEAT-2026-0018-auto-close-predicate`. Flip each gate-2 WU from
`status: draft` → `pending` only after working the Open
verifications + Cross-repo contracts sections.

## Gate-1 summary

Gate 1 shipped the deterministic predicate as three substantive WUs
plus the close-intermediate ceremony: `gate_eval.py` (T01, the
pure module + dataclass + 7-check algorithm), the unit-test corpus
(T02, 15 fixtures + ≥ 90% coverage), and the backtest CLI +
calibration regression (T03, validates predicate against
FEAT-2026-0013/0014/0015/0017 historical data).

Gate 1 substantive spend: $9.51 actual vs $4.10 planned (2.32×
over). Driver of overrun: spec density priced as
`implementation/high` $1.50 defaults when the actual work was
test-scaffolding-at-scale (T02: 92k output tokens, 15 named
classes, 12 fixture dirs) and fixture-as-context calibration (T03:
5.3M cache-read tokens across 4 historical feature folders). The
overrun was honest, not chasing a bad design; it surfaced a
planner-side estimation gap promoted to LEARNINGS this gate.

**Predicate self-check** (T03's CLI run on this very feature, gate
1 — first live exercise of the recursive-dogfood property):

```
FEAT-2026-0018  predicate=v1
  G01  auto=False
    reasons:
      - per_wu_cost_overrun: T01 actual=$2.85 planned=$1.80 ratio=1.59x
      - per_wu_cost_overrun: T02 actual=$4.18 planned=$1.50 ratio=2.79x
      - per_wu_hard_overrun: T02 actual=$4.18 planned=$1.50 ratio=2.79x
      - per_wu_cost_overrun: T03 actual=$2.47 planned=$0.80 ratio=3.09x
      - per_wu_hard_overrun: T03 actual=$2.47 planned=$0.80 ratio=3.09x
    metrics:
      gate_total_cost: $12.04
      gate_budget: $14.00
```

Meta-confirmation: the predicate this feature ships correctly
identifies its own gate 1 as off-plan. Close-intermediate ceremony
was warranted on gate 1; the OLD close path (still in effect for
gate 1, since T04+ wiring hasn't landed) ran as intended.

## Gate-2 substantive WUs

### T04 — Driver integration at terminal gate boundary ($2.50, xhigh)

Wires `gate_eval.evaluate_auto_close` into `loop.py` at the
terminal-flip block (`loop.py:2005` — `set_gate(awaiting_review)`
site). On `auto=True`: writes a stub `RETROSPECTIVE.md`, marks the
close WU `auto_close: true` + `verdict: met` + `status: done`,
appends an `auto_close_decision` event, and lets
`fire_terminal_flips` + `verify_post_pass_invariants` run
unchanged. The `verdict: met` flag is the load-bearing detail:
FEAT-2026-0017's `assert_terminal_flips_fired` short-circuits when
`verdict != "met"`, so setting it ensures the wiring-race guard
STILL covers the auto path. On `auto=False`: zero side effects;
caller falls through to today's close-WU dispatch.

### T05 — Driver integration at intermediate gate boundary ($2.20, xhigh)

Same pattern at the intermediate close-WU dispatch site. Implements
option A (per PLAN.md): skip the `close-intermediate` WU dispatch
but DO dispatch the gate's `plan-next` WU so the next gate gets
drafted. APPENDS (never overwrites) a `## Gate N — auto-closed`
section to `RETROSPECTIVE.md` (intermediate gates accumulate one
section per gate close). Reuses T04's `mark_close_wu_auto_closed`
unchanged. Idempotent under re-arm: appending detects an existing
section and no-ops. Depends on T04 because the predicate-call
pattern + frontmatter writer + event-emission helpers all live in
T04.

### T06 — `--force-full-close` flag + PLAN.md override ($0.80, medium)

The operator escape hatch. Two surfaces: a CLI flag
`--force-full-close <feature-id>` on `loop.py`, and a PLAN.md
frontmatter `auto_close_disabled: true` (whose plumbing already
exists in `gate_eval.py:292` from T01). Both bypass predicate
consultation entirely — the existing close path runs unmodified.
Logs an `auto_close_decision` event with `override: true` for the
audit trail even though no auto-close decision was made. Depends on
T05 because the override must hook both T04 and T05's call sites.

## Open verifications

Operator should check / resolve each before flipping the gate-2
WUs from `draft` → `pending`.

1. **Driver wiring-site precise location.** T04 specifies the
   edit location as `loop.py:2005–2056` (the terminal-flip block
   that begins with `backend.set_gate(gate, "awaiting_review")`
   and ends with the `verify_post_pass_invariants` early-return).
   Confirmed accurate at draft time (G1-PLAN verified
   `grep -n 'set_gate.*awaiting_review' loop.py` → line 2005).
   `loop.py` evolves; re-verify the line range when arming T04.
   Update T04's body if it has drifted.

2. **Stub `RETROSPECTIVE.md` content shape.** T04 writes a stub
   section shaped:
   ```
   ## Gate {N} — auto-closed (predicate=v1)

   On-plan close; full retrospective ceremony skipped per ...
   - feature_id, predicate_version, gate_total_cost, gate_budget,
     reasons
   ```
   `assert_retrospective_exists` (loop.py:1232) accepts any non-
   empty file — stub satisfies trivially.
   `assert_retrospective_gate_section` (loop.py:1353) requires
   `^#{1,3} Gate {N}\b` — stub's `## Gate {N} — auto-closed`
   matches.
   `assert_cost_analysis_section_when_met` requires
   `^##+ Cost analysis` ONLY when `wu.verdict == "met"` on a
   close-type WU. T04 sets `verdict: met` on the auto-closed
   close WU. Does the stub need a `## Cost analysis` header to
   satisfy this guard? **Operator must decide**: either add a
   minimal `## Cost analysis\n\nAuto-closed; no actual close-WU
   cost.` block to the stub (recommended), OR re-scope T04's
   AC3 to set `verdict: pending` / not set `verdict` at all and
   accept that `assert_terminal_flips_fired` short-circuits to
   `True, ""` on the auto path (which would silently bypass the
   FEAT-2026-0017 guard — exact regression T04 was meant to
   prevent). The recommended path (add `## Cost analysis` to the
   stub) keeps the guard live; flag T04's AC2 for that addition
   before arming.

3. **WU lifecycle for auto-skipped close WUs.** T04 + T05 mark
   the auto-closed close WUs `status: done` + `auto_close: true`
   + `auto_close_reasons: [...]`. No new lifecycle status is
   added. This affects every consumer of the WU status field:
   - `lint_plan.py` — passes `status: done`; verify no rule
     rejects the `auto_close: true` extra frontmatter key.
   - `/gate-status` skill — already reads `done`; will the
     `auto_close` flag's absence change its summary?
   - `/wrap-feature` skill — should it surface auto-closed
     gates differently?
   - The driver's own bookkeeping (the squash + event log) —
     verify no double-squash, no missing trailer.
   Operator: run `/gate-status` + `/wrap-feature` against a
   fixture feature with `auto_close: true` flagged WUs once T04
   lands to confirm shape.

4. **Plan-next dispatched on intermediate auto-close.** PLAN.md
   commits to option A: when an intermediate gate auto-closes,
   `plan-next` still dispatches (the gate-N+1 substantives
   still need a planner). Gate-1 retrospective evidence: the
   `close-intermediate` cost is structurally cheap (~$0.50
   targeted vs the planner's $1.20 default per FEAT-2026-0015);
   the saved cost on auto-skip is small relative to the
   risk-of-no-next-gate. Option A is still the right call.
   Re-confirm: gate 2 retrospective (when written) should
   re-evaluate against actual T05 behavior. If gate 2 reveals
   that `plan-next` is ALSO often unnecessary on intermediate
   auto-close (e.g. drafts already exist from upstream
   features), revisit.

5. **`args` plumbing for T06.** T06 needs the argparse `args`
   namespace at T04 + T05's call sites inside the dispatch
   loop. Confirm at arm time whether `args` is already
   accessible (likely via a `nonlocal` / outer-scope closure
   in `run_loop()` or similar) or whether plumbing requires a
   new helper. Documented as T06 escalation #3; surface here so
   the operator can pre-emptively decide if a `T06H` hygiene WU
   is needed.

6. **`validate-event.py` schema admits `auto_close_decision`.**
   T04 AC7 will patch `validate-event.py`'s known-event-type
   table if `auto_close_decision` is rejected. Confirm at arm
   time whether the script enforces a known-types table and how
   intrusive the edit is.

## Cross-repo contracts

Per `[FEAT-2026-0003/G3-LESSONS]` (verify cross-surface contract
values against authoritative source). For this gate, all surfaces
are internal to the loop's single repo, so "cross-repo" reduces to
"cross-WU values invented at draft time that future code/tooling
will join on". Each row must be operator-checked before arming.

| Invented value | Authoritative source | Used in | Checked |
|---|---|---|---|
| frontmatter key `auto_close` (bool) | this feature's PLAN.md § "Scope OUT" | T04 AC3, T05 AC1, T06 AC2 | [ ] |
| frontmatter key `auto_close_reasons` (list[str]) | this feature's PLAN.md § "Scope OUT" | T04 AC3, T05 AC1 | [ ] |
| PLAN.md frontmatter `auto_close_disabled` (bool) | `gate_eval.py:292` (already shipped in T01) | T06 AC2 | [x] |
| event type `auto_close_decision` (string) | invented this gate; no prior precedent | T04 AC1, T05 AC1, T06 AC3 | [ ] |
| event field `gate_type: "intermediate"\|"terminal"` | invented this gate | T05 AC1 | [ ] |
| event field `override: true` on bypass | invented this gate | T06 AC3 | [ ] |
| CLI flag `--force-full-close <feature-id>` (positional-arg value = feature id) | this feature's PLAN.md § "Predicate v1" closing paragraph | T06 AC1 | [ ] |
| stub RETROSPECTIVE.md heading `## Gate {N} — auto-closed (predicate=v1)` | invented this gate; constraint: must match `assert_retrospective_gate_section`'s `^#{1,3} Gate {N}\b` | T04 AC2, T05 AC2 | [ ] |
| commit-message suffix `auto-closed (predicate=v1)` | invented; mirrors `chore(loop): {wu_id} ...\n\nFeature: {feature_id}` convention | T04 AC4, T05 AC3 | [ ] |

Each unchecked row is a value an arming operator should grep the
codebase + LEARNINGS for, to confirm it doesn't collide with an
existing convention. The single checked row (`auto_close_disabled`)
is already live in `gate_eval.py` per T01 and is included for
completeness.

## Predicate-version note

This review is written against `predicate=v1`. Predicate constants
(`PER_WU_COST_RATIO_CEILING = 1.5`, `PER_WU_HARD_OVERRUN_RATIO =
2.0`, `PLAN_NEXT_COST_RATIO_CEILING = 1.5`) are hardcoded in
`gate_eval.py`. The `predicate_version` string threads through
every `auto_close_decision` event T04/T05/T06 emit so future
predicate revisions (v2+) remain auditable retroactively.
