---
feature_id: FEAT-2026-0059
title: Hedged-close ergonomics — classified follow-ups and a verdict-ceiling headline
slug: hedged-close-ergonomics
branch: feat/FEAT-2026-0059-hedged-close-ergonomics
roadmap_goal: Make a hedged close answer the operator's two real questions — why couldn't this be `met`, and what kind of reason is expected — by classifying each follow-up entry at close time and having /accept-hedged-close lead with the verdict ceiling instead of a wall of quotes.
autonomy_default: review
status: active
planned_cost_usd: 14.50
---

# Plan: Hedged-close ergonomics

`/accept-hedged-close` quotes the raw follow-up record and demands a one-line
reason. It never answers the two things the operator is actually asking:
**why couldn't this close `met`**, and **what kind of reason is expected?**

## The friction is measured, not assumed

The roadmap row was filed after the first live run (FEAT-2026-0054, 2026-07-30).
Two more runs since have reproduced it exactly:

- **FEAT-2026-0041** hedged `met_locally` on one entry — a contract-change list needing
  a human signature. The operator had to read four paragraphs to learn that accepting
  *was* the only move.
- **FEAT-2026-0042** hedged `partially_met` on three entries of three *different*
  kinds: a pull request that never appeared (a real gap, re-runnable), a guard tested
  on a reset marker (re-runnable), and fix correctness (**never** assertable). The
  operator asked, verbatim, *"why did it not complete with met?"* — which is the
  question this feature exists to answer before it is asked.

## A fourth `kind`, added to the row's three

The row proposes `acceptance-discharged` / `externally-verifiable-later` /
`routed-finding`. **This plan adds `inherent`.**

FEAT-2026-0042's close already invented the category in prose, because the contract
had no slot for it — its third row reads *"Fix correctness — **Inherent.** Not
deferred, not scheduled, not a gap. **Never.** Mitigated structurally; asserted
nowhere. This row exists so no future reader mistakes it for outstanding work."*
Shipping three values would force the next close to invent it again, in different
words, and a reader would have no mechanical way to tell "nobody has done this yet"
from "this can never be done".

The four, and what each answers about the verdict ceiling:

| `kind` | meaning | can a re-run upgrade it? |
| --- | --- | --- |
| `acceptance-discharged` | needs a human signature | no — but accepting *is* the discharge |
| `externally-verifiable-later` | needs a real run or environment | **yes**, at the named condition |
| `routed-finding` | now owned elsewhere | no — tracked on another surface |
| `inherent` | not assertable, ever | **never** |

The ceiling follows mechanically: if **any** entry is `externally-verifiable-later`,
rework exists and the operator has a real choice. If none is, `met` is unreachable by
any in-repo work and the only question is whether to accept now.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: grep -rn "acceptance-discharged\|externally-verifiable\|routed-finding"
             .specfuse/rules/ specfuse/loop/
         grep -n "hedged\|met_locally" specfuse/loop/closing_requirements.py

Verdict: NO classification exists anywhere. close-discipline.md §2 requires three
         fields per entry (criterion verbatim, why unverifiable, exact re-run
         condition) and nothing more.

Gap:     the §2 record is NOT lint-enforced at all. closing_requirements.py holds
         nine `close` requirements and none covers it, so a hedged close can ship
         a malformed record — or none — and only a human reading the retrospective
         would notice.

Reuse:   closing_requirements.Requirement is the registry shape for the new check
         (`id`, `wu_type`, `phase`), and lint_closing.py already dispatches on it —
         `_check_verdict_well_formed` reads `ctx.wfm["verdict"]` against
         VERDICT_VALUES and is the closest existing analogue.

         `/accept-hedged-close`'s step 2 already locates and quotes the record; this
         feature changes what it does with it, not how it finds it.
```

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

The trap here is a lint that cannot be green on this tree.

Two hedged records already exist, in FEAT-2026-0041's and FEAT-2026-0042's
retrospectives, and **neither carries `kind:`** — they predate it. A lint requiring
`kind:` on every §2 record found anywhere would be red on arrival and unfixable
without rewriting closed features' history.

So the check is scoped to **the close WU currently being linted**, not to a corpus
sweep: it fires when *this* close writes a hedged verdict, which is the moment the
contract applies. Historical records are untouched and unread. That keeps the
criterion satisfiable on day one — the shape that cost FEAT-2026-0060 two blocked
attempts and $4.48 when it demanded zero validator errors corpus-wide while
forbidding the only file that could deliver them.

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value, threshold, or severity is flipped. A new required
field is added to a record that is currently unlinted, so nothing that passes today
begins failing — except a close that writes a hedged verdict *after* this ships,
which is the intended behaviour and is what T01's own tests exercise.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced.

## Scope boundary — explicitly OUT

- **Changing what hedges.** `verdict_permits_terminal_flips` decides which verdicts
  withhold the terminal flips and is working correctly. This feature changes how a
  hedge is *explained*, never when one happens.
- **Retro-classifying the two existing hedged records.** FEAT-2026-0041 and
  FEAT-2026-0042 are closed and merged. Rewriting their retrospectives would edit
  history for no reader, and the §2 record is a record of what that close knew at the
  time.
- **Auto-authoring the operator's reason.** `operator-escalation.md`'s never-author
  rule is binding. The classification scaffolds the prompt; the words stay the
  human's. A skill that pre-fills a plausible reason is worse than a blank line,
  because it invites accepting a sentence the operator did not think.
- **A fifth kind.** Four cover every entry across the three hedged closes observed. A
  new one is added when a real close needs it, not speculatively.

## The trap that will otherwise be rediscovered

**`kind` must be written by the close WU, not inferred by the skill.** The close has
the context — it knows why a criterion went unmet, because it just tried to meet it.
The skill sees only prose. A skill that guesses the classification from wording will
be confidently wrong on exactly the ambiguous entries where the operator most needs
it right, and its guess would carry the authority of the tool rather than the
uncertainty of a heuristic.

## Release note

The operator has stated that a release follows this feature and FEAT-2026-0064.
T01 changes a rule contract that ships in the scaffold, so its consumer-visible
enumeration in the close matters more than usual — it is the raw material 0064's
CHANGELOG will consume.

## Gates

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0059/T01
        file: WU-01-kind-contract-and-lint.md
        depends_on: []
      - id: FEAT-2026-0059/T02
        file: WU-02-verdict-ceiling-headline.md
        depends_on: [FEAT-2026-0059/T01]
      - id: FEAT-2026-0059/T03
        file: WU-03-routed-finding-tracking.md
        depends_on: [FEAT-2026-0059/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0059/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0059/T01
          - FEAT-2026-0059/T02
          - FEAT-2026-0059/T03
```
