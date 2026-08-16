---
feature_id: FEAT-2026-0058
title: Feature decision registry + override lint
slug: decision-registry
branch: feat/FEAT-2026-0058-decision-registry
roadmap_goal: A feature's decisions live in one canonical registry that artifacts cite by ID, so transcription drift and silent overrides become lintable instead of vigilance-dependent.
autonomy_default: auto
status: planned
planned_cost_usd: 18.00
---

# Plan: Feature decision registry

FEAT-2026-0066 hit three drift defects from decisions transcribed as prose
between PLAN, GATE, and WU files: a four-row operator contract table transcribed
as three rows — the dropped 404 row shipped as a defect and cost a gate — a
false premise propagated into three files that T11 had to repair in all three,
and an ADR silently overriding a ratified operator decision, surfaced two gates
later as a close blocker. That WU's own note: *"there is no override registry in
`.specfuse/` today."* Vigilant prose is the entire current defense against all
three shapes.

This feature gives a feature's decisions one home. `DECISIONS.md` holds the
decision; every other artifact cites it by ID. A gate cannot arm while a
citation dangles, while an artifact restates a decision instead of citing it, or
while an override sits unsigned.

## Decisions taken at draft time

**D1 — the lint checks reference integrity and non-restatement; it does not
attempt contradiction detection.** Detecting that an artifact's prose
*contradicts* a registry entry is a semantic judgment on free text: a lint
claiming it would either fire on every paraphrase or fire on nothing.
`[FEAT-2026-0071/G1-CLOSE]` names shipping a partial guard described as a total
one as the failure mode — "a partial structural guard described as a total one
is how the unguarded fields stop being reviewed."

So the guard is two mechanical checks. **Reference integrity**: every decision
ID cited by an artifact exists in the registry. **Non-restatement**: an artifact
reproducing a decision's statement text, rather than citing its ID, is an error.

The second is the load-bearing one, and it attacks the cause rather than the
symptom: if artifacts may only *cite*, there is no second copy to drift. This is
the same move that resolved the roadmap-archive split — FEAT-2026-0079 gave one
algorithm one owner instead of keeping two copies in sync.

**Semantic agreement between a cited decision and the work done under it stays
unguarded by construction.** The close must say so; see `WU-90`.

**D2 — ERROR severity, earned by measurement, with the repair landing ahead of
the feature.** Both sibling checks in this repo are WARN for the same reason:
`check_closing_guard_literals` because 22% of existing closing WUs would fail
it, and the `auto` lessons-destination check (#2173) because 9 of 14 historical
`auto` closing WUs would. An ERROR unsatisfiable on a populated tree is the
failure `[FEAT-2026-0015/G2-CLOSE]` records.

Measured here, 2026-08-15: **66 feature folders, 6 carrying decisions-prose, and
only 2 live** (not `done`/`abandoned`) — FEAT-2026-0011, which is `blocked` and
expected to move to the authoring repository, and FEAT-2026-0050, drafted the
same day. `done` features are sealed and exempt, the same exemption both sibling
checks already apply. So an ERROR is satisfiable on this tree **today**, by
measurement rather than by hope.

Sequencing condition, from
`[FEAT-2026-0034/G1-CLOSE/hand-check-the-invariants-before-automating-them]`:
FEAT-2026-0050's D1–D3 prose is converted to a `DECISIONS.md` in **its own PR,
landing before this feature's gate runs**. A feature that both repairs and
checks cannot demonstrate its checker ever fires.

**D3 — an override carries provenance, not just a status flip.**
`[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]` records the cost of the alternative:
when an operator override mutates the very field that recorded the pre-override
state, the record becomes byte-identical to one that was never overridden, and
the distinction survives only in prose that nothing parses. So a decision moving
to `ratified` from `overridden-pending-signoff` carries `overridden_from`,
`signed_off_by`, and `signed_off_at` — "ratified from the start" and "overridden
then signed off by a named human on a date" stay distinguishable to a query.

**D4 — the close ceremony's contract-change enumeration is OUT of scope.** The
roadmap goal names it, and it is deliberately deferred: it would wire
`closing_requirements.py` — a surface every closing WU in this repository
depends on — to a format with one day of real use. It becomes its own roadmap
row once the format has survived a feature. The 0050 repair (D2) is what will
show whether the format holds.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

This feature designs an enforcement gate, so the search is required.

```
grep -rn "DECISIONS.md\|decision registry\|override registry" --include="*.py" --include="*.md" specfuse/ .specfuse/rules/ plugins/
grep -rln "Decisions taken at draft time" .specfuse/features/*/PLAN.md
grep -n "CONSUMER_VISIBLE_HEADING" specfuse/loop/closing_requirements.py
```

**Verdict — no registry exists; one incumbent convention does.**

- No `DECISIONS.md`, no decision registry, and no override registry anywhere in
  the tree. The FEAT-2026-0066 WU's own note confirms it.
- The incumbent is a `## Decisions taken at draft time` **prose section**, in 6
  of 66 PLAN files. That is the surface this feature replaces, and D2's
  measurement of it is what makes ERROR severity affordable.
- `closing_requirements.py` already owns `CONSUMER_VISIBLE_HEADING` — the close
  ceremony's contract-change enumeration. It is left alone per D4; this feature
  adds no second reader of it.
- The lint lands in `lint_plan.py` beside `check_produces_shape` and
  `check_closing_guard_literals`, reusing the walk those already perform rather
  than adding a second pass over the feature folder.

## Escalation-predicate satisfiability

Every escalation trigger in this feature's work units is falsifiable inside the
session that would fire it, with no external environment:

- **T02** — "the non-restatement matcher cannot separate a citation from a
  restatement without firing on legitimate quotation": checked by running the
  matcher over this repository's six decisions-prose PLANs, which exist in the
  tree.
- **T03** — "the override provenance fields cannot be validated without knowing
  who signs off": checked against `DECISIONS.md`'s own schema from T01, in the
  same tree.

Neither depends on a deployed component, a credential, or a network round-trip.

## Scope boundary — explicitly OUT

- **Contradiction detection.** D1. The guard is citations and restatement.
- **The close ceremony's contract-change enumeration.** D4 — a separate roadmap
  row, after the format has survived a feature.
- **Migrating features other than FEAT-2026-0050.** `done` and `abandoned`
  folders are sealed history; FEAT-2026-0011 is expected to leave this
  repository. Neither is rewritten.
- **Deciding anything on the operator's behalf.** The registry records a
  decision and who ratified it; nothing in this feature ratifies, overrides, or
  signs off automatically.

## Gates

One gate, three substantive work units, one terminal close — the ceremony
proportionality rule for a feature at or under four substantive units. The close
consumer that would have justified a second gate is out of scope by D4.

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0058/T01
        file: WU-01-decisions-format.md
        depends_on: []
      - id: FEAT-2026-0058/T02
        file: WU-02-citation-lint.md
        depends_on: [FEAT-2026-0058/T01]
      - id: FEAT-2026-0058/T03
        file: WU-03-override-signoff-lint.md
        depends_on: [FEAT-2026-0058/T01]
      # --- closing sequence: terminal gate, single close ---
      - id: FEAT-2026-0058/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0058/T01
          - FEAT-2026-0058/T02
          - FEAT-2026-0058/T03
```

## Notes

- T02 and T03 both depend on T01 and on nothing else: one reads the registry's
  citations, the other its override fields. They are independent of each other
  and could run in either order.
- **This feature's own `DECISIONS.md`** is written by T01 as the first consumer
  of its own format — D1–D4 above move into it. A registry format whose first
  real use is the feature that defines it is the cheapest possible dogfood, and
  it means this PLAN's decision prose is itself migrated rather than left as the
  seventh copy of the pattern being retired.
- `planned_cost_usd` $18.00: T01 $4.00, T02 $5.00, T03 $4.00, close $5.00. The
  close sits at the documented floor rather than above it — unlike
  FEAT-2026-0050's `plan-next`, this is a single terminal close on a
  three-unit gate with no next gate to draft.
