---
gate: 1
status: open
cost_budget_usd: 30.00
---

# Gate 1 — Collision prevention: one scan in code, one new ERROR, one late re-check

Definition of done: the four-source next-ID scan exists as a tested function
instead of skill prose; a `feature_id` claimed by two different slugs across
`roadmap.md`, `roadmap-archive.md`, feature folder names, or `PLAN.md`
frontmatter is an ERROR that fails `roadmap-link-gate`; and `/draft-feature`
re-runs the scan immediately before it writes a feature folder, so an ID claimed
between step 1 and the write is caught rather than collided with.

## Arming discipline

- **The §2/§4 probe is already run and recorded in PLAN.md** — 78 roadmap rows
  with no duplicate ID, 68 IDs across four sources with zero slug disagreement.
  The ERROR is armable with no cleanup work unit. **T02 re-runs both probes as
  its first act**: the PLAN's numbers are a draft-time measurement, and
  `[FEAT-2026-0034/G1-CLOSE/re-verify-the-producer-not-the-audit]` is explicit
  that a dated observation may not be restated as a current fact. A dirty re-run
  means ship the check as WARN and file the cleanup — never weaken the rule to
  fit the tree.
- **T02's blast radius is the whole repo, not this feature.**
  `roadmap-link-gate` runs in the `code` set for every work unit of every
  feature. A false positive there reds gates for work with no connection to this
  one. That is the reason `review` was recommended for this feature.
- **`autonomy_default: auto` is the operator's explicit decision**, made against
  that recommendation. It stands. If it is revisited, the per-WU lever is one
  line — add `human_only: true` to `WU-02-id-slug-collision-lint.md`'s
  frontmatter, which subtracts autonomy for that unit alone without changing the
  feature default. The WU template describes exactly this case: *"the planner's
  self-flag on a draft it knows needs a human, e.g. right after writing a
  defaults flip."*
- **T01 and T02 carry no dependency edge** and may run in either order. T03
  depends on T01's helper existing.
- **Land in queue order relative to FEAT-2026-0082.** Both touch
  `/draft-feature`; `agent-policy.yml:47` already records 0081 as sitting behind
  0082 for that reason. T03 is the file that conflicts.

## What gate 2 inherits from this gate

`G1-PLAN` drafts gate 2 (the renumbering command) and must carry two things
forward from here, because neither is recoverable from the diff alone:

1. **The list of ID-bearing surfaces T02's check enumerates.** That list is the
   renumber sweep's work list. Deriving it a second time by inspection is how a
   manual renumber misses a file.
2. **The keep-the-old-ID rule, unchanged.** `events.jsonl` and
   `PLAN.baseline.json` keep the old correlation ID. It is stated in PLAN.md's
   scope boundary with its reasoning; carry it into gate 2's WUs verbatim rather
   than re-deriving it.
