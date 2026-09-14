---
id: FEAT-2026-0111/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces_driver_helper:
  - score_learnings_entries
produces:
  - tests/test_learnings_weights.py
---

# Rank entries by what failures cost, not by how often they were cited

**Objective.** Compute a weight per `LEARNINGS.md` entry: `failure_signature`
attempt-cost as the primary signal, citation reach as a tiebreaker, with the
tiebreaker's bias stated in the output.

**Context.** FEAT-2026-0111/T02. #3272 proposes three computable weights.
Their order matters and the issue does not fix it, so PLAN.md does: `reach`
counts citations in planning documents, and planning agents cite what they
read in `LEARNINGS.md`, so an entry is cited partly because it is already
visible. It also favours age — this repo's top five (20–22 citing features)
are all from FEAT-2026-0014 through 0069. `failure_signature` attempt-cost
from `events.jsonl` is causal where a citation count is not: it is what the
failure this entry describes actually cost.

Measured baseline for this repo, 2026-09-14: 233 entries, 133 distinct ids, 51
(38%) never cited by another feature.

**Acceptance criteria.**

- `python3 -m unittest tests.test_learnings_weights -v -b` fails on HEAD
  before this unit's edits and passes after.
- Reach is computed **excluding self-citation**: an entry citing itself from
  its own feature's files scores zero reach. A naive substring count over
  `.specfuse/features/**` reports 90 of 92 entries as cited; excluding the
  owning feature reports 82 of 133. The test asserts the exclusion directly,
  because the difference is the whole signal.
- Every scored entry carries its inputs, not just its score — the cost figure,
  the reach count, and the `failure_signature` it matched — so a human at T03's
  accept step can disagree with the ranking on evidence.
- The output states that reach is a tiebreaker and names its age bias, in the
  artifact itself rather than only in documentation.

**Do not touch.** `LEARNINGS.md` — this unit reads and scores, it does not
curate or rewrite. The binding block (T01's and T04's). The sibling WU files.

**Verification.** Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_learnings_weights tests.test_binding_block_budget -v -b`
and the symbol check (§9):
`python3 -c "from specfuse.loop.loop import score_learnings_entries"`.

**Escalation triggers.** Stop with `status: blocked` if `failure_signature`
cannot be mapped onto entries for a meaningful share of the corpus — a primary
weight that resolves for a handful of entries is not a primary weight, and
which signal leads is then a decision for a human rather than a fallback this
session picks.
