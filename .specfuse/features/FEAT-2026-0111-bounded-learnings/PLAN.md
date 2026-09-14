---
feature_id: FEAT-2026-0111
title: Bounded LEARNINGS on the dispatch path
slug: bounded-learnings
branch: feat/FEAT-2026-0111-bounded-learnings
roadmap_goal: The rules worth following reach every dispatched session, inside a word budget a lint enforces, chosen by a human with computed weights as evidence.
autonomy_default: review        # edits the driver and the scaffold's binding block
status: active
planned_cost_usd: 28.00
---

# Plan: Bounded LEARNINGS on the dispatch path

`.specfuse/LEARNINGS.md` is append-only by contract:
`assert_learnings_appended_or_noop` makes at least one added line the success
signal of every close, with `"nothing generalizes"` as the only exit. That is
an unbounded growth rule attached to a file no dispatched work unit reads.

Measured in this repository on 2026-09-14: **233 entries, 4,371 lines, roughly
80,000 tokens.** Of 133 distinct entry ids, **51 (38%) have never been cited by
any other feature** — self-citation excluded. The consumer that prompted #3272
measured 219 entries / 5,497 lines / ~167k tokens with 91 of 219 never cited,
so the shape reproduces across repositories rather than being local mess.

The two planning skills slice the file; every implementation dispatch ignores
it. This feature puts the part worth reading in front of the sessions that do
the work, inside a budget that is enforced rather than aspirational.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Commands run:**
  - `ls .specfuse/rules-local/`
  - `sed -n '218,245p' specfuse/loop/scaffold.py`
  - `wc -w .specfuse/rules/{result-contract,never-touch,security-boundaries}.md`
  - `grep -rn "2500" specfuse/loop/ .specfuse/scripts/`
- **Verdict:** `the slot and the budget both exist; neither is enforced and nothing fills the slot`.

  `.specfuse/rules-local/` already exists and the binding block already
  documents it — "Project-authored rules live in `.specfuse/rules-local/`
  (never touched by `specfuse upgrade`). Add one
  `@.specfuse/rules-local/<rule>.md` line per rule below." The consumer's
  hand-curated distilled file is that documented pattern, not a new one. So
  reaching the dispatch path is a file plus one `@` line.

  The 2,500-word cap lives in a comment at `scaffold.py:227`, set by
  FEAT-2026-0084/T01 because "every dispatch pays for this block, and a
  7,213-word set was read past rather than read". **No lint enforces it, and
  the block is at 2,574 words today** with `rules-local/` empty — 74 over,
  unnoticed. Same shape FEAT-2026-0104 found with the `replan` event: the
  consumer was built and the producer never was.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature makes the 2,500-word cap blocking, so §2 applies directly.

- **What does the rule report on an input already in its intended final state?**
  Today, on `main`, it reports **failure**: 2,574 words against a 2,500 cap,
  before this feature adds anything.
- That is the point rather than a defect — the predicate is meant to fire on
  the current tree, and T01 exists to establish whether it can be satisfied at
  all. But it means the lint may not be introduced as blocking until the trim
  lands. **T01 reports headroom; T04 lands the allocation; the lint becomes
  blocking only when the tree can pass it.** A severity flip shipped against a
  tree that fails it is the unsatisfiable-predicate defect §2 exists to stop.

## What is being selected, and by whom

The weights rank; they do not decide.

`reach` counts citations in planning documents, and planning agents cite what
they read in `LEARNINGS.md` — an entry is cited partly because it is already
visible. It also favours old entries: the top five here (20–22 citing features)
all come from FEAT-2026-0014 through 0069. So `reach` measures what planning
has looked at, not what changed behaviour, and it is demoted to a tiebreaker
with that bias stated in the output.

`failure_signature` attempt-cost from `events.jsonl` is the primary weight: it
is the closest available proxy for "following this rule avoids expensive
failures", and it is causal in a way a citation count is not.

**Neither measures whether a rule improves the next session's work.** Nothing
in the tree does, and establishing it would need a before/after on failure
rates that would dwarf this feature. So the distilled set ships through a
**human accept step** — a ranked proposal against the budget, accepted, edited
or rejected per entry — the same propose-and-confirm posture `/arm-gate`,
`/pick-feature` and `/learnings-curate` already use. #3272's consumer curated
its 47 lines by hand and reported the weights *corrected* that judgment rather
than replacing it: six high-value entries a by-hand cut had dropped, two
zero-weight singletons it had kept.

One filter is worth applying and cannot be computed: **a lesson already
enforced by a guard, a lint or a registry entry does not belong in a dispatch
prompt** — the machine enforces it and the words are pure cost. Only 7 of 234
entries literally name such a guard, and most that became guards never name
the enforcer, so this surfaces as a review prompt at the accept step rather
than as a weight.

## The loud uncertainty

**Where the trim comes from is unknown.** All three binding rules are
contracts; `result-contract.md` is the agent↔driver interface. If T01 reports
that nothing can defensibly go, this feature cannot put anything on the
dispatch path without raising a cap that was set on measured evidence — a
different decision than the one this plan was accepted on. T01 is ordered
first so that answer arrives before four units are built on top of it, and its
escalation trigger says to report the headroom and block rather than trim a
binding contract to make room.

## On the estimates

Driver-touching units are priced at $5–6 rather than the $3.50 default. This
is a correction, not padding: FEAT-2026-0106's T01 came in at $9.13 against
$3.50 and its T03 at $6.13 — both units already flagged as risky and priced at
the default anyway, which is what put that gate off-plan.

It matters mechanically here. FEAT-2026-0106 shipped conditional reflection
that only fires on an **on-plan** gate, and it has never fired, because its own
gate went off-plan on cost. Honest estimates are what make this run a test of
that feature rather than another blind one.

## Scope boundary — deliberately out

- **#3272 suggestion #5**, stopping `close-b` from rewarding volume. It changes
  what every close must do to satisfy a guard, and deserves its own evidence.
- **`LEARNINGS.md`'s own append contract.** Unchanged: closes still append or
  say nothing generalizes. This feature bounds what is *loaded*, not what is
  *written*.
- **Automated curation with no accept step.**
- **`GATE-NN-CRITERIA.md` carry-forward** (#3313), the other live ceremony
  lever, which is a different mechanism.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0111/T01
        file: WU-01-budget-lint-tracer-bullet.md
        depends_on: []
      - id: FEAT-2026-0111/T02
        file: WU-02-weights.md
        depends_on: [FEAT-2026-0111/T01]
      - id: FEAT-2026-0111/T03
        file: WU-03-accept-step.md
        depends_on: [FEAT-2026-0111/T02]
      - id: FEAT-2026-0111/T04
        file: WU-04-budget-allocation.md
        depends_on: [FEAT-2026-0111/T01]
      - id: FEAT-2026-0111/T05
        file: WU-05-document-the-budget.md
        depends_on: [FEAT-2026-0111/T03, FEAT-2026-0111/T04]
      # --- closing sequence: 1-WU close (terminal gate, <=8 substantive WUs) ---
      - id: FEAT-2026-0111/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0111/T01
          - FEAT-2026-0111/T02
          - FEAT-2026-0111/T03
          - FEAT-2026-0111/T04
          - FEAT-2026-0111/T05
```

## Notes

- Five substantive work units is under `docs/methodology.md` §6's
  ceremony-proportionality threshold, so this is a single gate with a single
  terminal `close`.
- Dependencies live here, not in WU frontmatter.
