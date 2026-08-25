---
feature_id: FEAT-2026-0081
title: Feature-ID collision prevention and cheap renumbering
slug: feature-id-collision-prevention
branch: feat/FEAT-2026-0081-feature-id-collision-prevention
roadmap_goal: Make a feature-ID collision cheap to prevent and cheap to recover from — narrow the race window by re-running the next-ID scan immediately before the feature folder is written, catch a collision at the next lint rather than at merge, and make renumbering a command instead of a careful manual sweep.
autonomy_default: auto
status: planned
planned_cost_usd: 29.00
---

# Plan: Feature-ID collision prevention and cheap renumbering

Two features were drafted three minutes apart in different worktrees of the same
repo and both took `FEAT-2026-0093`. One merged. The other was renumbered *after
its gate had closed* — folder, `PLAN.md` frontmatter, every WU `id`,
retrospective, staged lessons, criteria file, generated docs, two roadmap rows,
the archive anchor, the branch, and a closed-and-reopened PR, by hand, where
getting it wrong is silent.

The next-ID scan cannot close that window on its own: it is a point-in-time read,
and the colliding PR was created *after* the draft ran, so no query shape would
have caught it. #1644 investigated the scan's GitHub query and found it sound;
the contamination defect it surfaced instead was fixed separately as #1872,
leaving the race itself — and the cost of recovering from it — unaddressed. This
feature is what #1644 was closed in favour of.

Three independent lines, each shippable alone: **narrow** the window, **catch**
the collision at lint, **recover** with a command instead of a sweep.

## Scope boundary

**IN, gate 1 (prevention).** The four-source next-ID scan extracted from skill
prose into a tested helper; the ID→slug collision check as a new ERROR in the
repo-scoped roadmap linter; and `/draft-feature` calling the scan twice — once to
propose, once immediately before it writes the folder.

**IN, gate 2 (recovery), drafted by gate 1's `plan-next`.** A renumbering command
shipped as a flat console script, and the rule about which files keep the old ID.

**The keep-the-old-ID rule, decided here rather than left for gate 2 to
rediscover.** `events.jsonl` and `PLAN.baseline.json` **keep the old correlation
ID** under any renumbering. The run really did execute under that ID; rewriting a
log to match a later rename falsifies history to tidy a name. The renumbered
feature's retrospective carries a note so a future reader correlating events
knows what to expect. Written into this PLAN because gate 2 is drafted later by
an agent, and this is precisely the kind of rule that gets reasoned away at
drafting time by someone optimising for internal consistency.

**OUT, deliberately.**

- **`specfuse renumber` as an umbrella subcommand.** `DELEGATED_COMMANDS` is a
  hardcoded dict in the *umbrella* package's `cli.py`; this repo ships flat
  console scripts the umbrella delegates to. `specfuse-renumber` works standalone
  from this repo on day one. The one-line delegation entry is a **cross-repo
  follow-up** for specfuse/specfuse, not a work unit here, because this repo
  cannot land it.
- **GitHub as a source for the lint check.** A network call inside a `code`-set
  gate makes the gate flaky, and FEAT-2026-0034's own lesson is that a gate red
  for reasons a reader dismisses gets ignored. GitHub stays a source for the
  *scan* (T01), which already reads it and already degrades to a WARN when it is
  unreachable.
- **Repairing existing violations.** There are none — see the probe below. If a
  future probe finds some, the honest move is to ship the check as WARN and file
  the cleanup separately, not to weaken the rule.
- **Row ordering, status vocabulary, and detail-content rules.** FEAT-2026-0034
  drew that boundary for the roadmap linter and it holds here.

## Correction to the roadmap row, found while drafting

The roadmap states the lint check "also resolves the title-only-claim ambiguity
above mechanically," citing `FEAT-2026-0098` — an ID appearing only in merged PR
#1843's title, with no roadmap row and no folder, whose work actually landed as
`FEAT-2026-0078`. **It does not.** No in-tree check reaches an ID that exists
only in a PR title. That case belongs to the scan (T01, which reads GitHub
issue/PR titles and bodies), not to the linter. Recorded here rather than
inherited silently, per `[FEAT-2026-0034/G1-CLOSE/re-verify-the-producer-not-the-audit]`:
a defect described in a roadmap row is a dated observation, not a current fact.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rniE "renumber|next_id|next-id" specfuse/ --include='*.py'
  -> 0 hits

grep -rn "_check_uniqueness" specfuse/loop/lint_roadmap.py
  -> :207

grep -n "next.*ID|four-source" .specfuse/skills/roadmap-add/SKILL.md
  -> the four-source scan is PROSE ONLY; no Python implements it

grep -n "add_parser|DELEGATED_COMMANDS" <umbrella>/specfuse/cli.py
  -> :96 (hardcoded dict), :1041 (registration loop)
```

**Verdict, per line — one extends, one builds new, one is cross-repo.**

- **Lint check: found `specfuse/loop/lint_roadmap.py`, extending it.**
  FEAT-2026-0034 shipped it as a repo-scoped sibling to `lint_plan.py`, already
  wired into `verification.yml`'s `code` set as `roadmap-link-gate`. It already
  carries `_check_uniqueness` (`lint_roadmap.py:207`) — but that check is over
  **anchors**, and its own finding text says so: *"anchor '<id>' is defined twice
  in <file>"*. It catches an ID defined twice. It cannot see an ID claimed by two
  different **slugs**, which is the collision this feature is about. New check,
  existing home, existing gate wiring.
  **Why not `lint_plan.py`:** it is feature-scoped and structurally cannot
  compare two features. 0034 recorded that reasoning when it chose to build a
  sibling rather than add a second mode to a single-job tool; the same reasoning
  puts cross-feature ID identity here.
- **Next-ID scan: no existing mechanism in code, building new.** The four-source
  scan exists only as prose in `roadmap-add/SKILL.md`, so every caller re-derives
  it by reading markdown, and its correctness has already cost one investigation
  (#1644). T01 extracts it; the skill then calls it rather than describing it.
- **Renumbering: no existing mechanism, building new** — and see the scope
  boundary for why the umbrella-facing half is out.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

Gate 1 raises a new check to ERROR in a gate every feature in this repo runs, so
both the §2 question and §4's runtime-probe requirement bind.

> **What does the rule report on a tree already in its intended final state?**

**Zero — probed, not asserted.** Two probes run at draft time against this repo:

```
roadmap rows scanned: 78
  ids appearing on >1 row:            none
  ids with >1 distinct slug in-row:   none

IDs across roadmap.md + roadmap-archive.md + folder names + PLAN.md frontmatter: 68
  IDs whose slug DISAGREES across sources: 0
```

The predicate is satisfiable and the ERROR is armable on day one: no cleanup work
unit is needed, and T02's gate can go green on arrival rather than being a
cleanup task wearing a check's clothes. **T02 re-runs both probes as its first
act** — this record is a draft-time measurement, and `[FEAT-2026-0034/G1-CLOSE/re-verify-the-producer-not-the-audit]`
is explicit that a close may not restate a dated observation as a current fact.
If the re-run comes back dirty, ship the check as WARN and file the cleanup; do
not weaken the rule to fit the tree.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0081/T01
        file: WU-01-next-id-helper.md
        depends_on: []
      - id: FEAT-2026-0081/T02
        file: WU-02-id-slug-collision-lint.md
        depends_on: []
      - id: FEAT-2026-0081/T03
        file: WU-03-draft-feature-rescan.md
        depends_on: [FEAT-2026-0081/T01]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0081/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0081/T01
          - FEAT-2026-0081/T02
          - FEAT-2026-0081/T03
      - id: FEAT-2026-0081/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0081/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # --- terminal close, pre-declared so lint reads gate 1 as non-terminal ---
      # G1-PLAN inserts gate 2's substantive WUs ABOVE this entry and sets its
      # real depends_on when it drafts the gate.
      - id: FEAT-2026-0081/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: []
```

## Notes

- **Gate cut: prevention, then recovery.** The dependency runs one way — knowing
  which surfaces carry an ID is an *output* of T02's four-source check, and that
  list is exactly the input gate 2's renumber sweep needs. Drafting the sweep now
  would mean guessing it. `plan-next` drafts gate 2 against the shipped fact
  instead.
- **T01 and T02 are independent** (no edge between them): one touches a new
  helper module, the other touches `lint_roadmap.py`. T03 depends on T01 because
  it calls the helper T01 extracts.
- **`autonomy_default: auto` is the operator's explicit choice**, made against a
  recommendation of `review`. Recorded here so a later reader does not read it as
  an oversight. The blast radius to keep in mind: T02 flips a check to ERROR in a
  gate every feature in this repo runs, so a false positive there reds the gate
  for work that has nothing to do with this feature. The `human_only: true`
  per-WU veto exists for exactly this shape and was deliberately **not** applied
  — see GATE-01.md's arming discipline for the one-line change if that judgement
  is revisited.
- **Rebase hazard against FEAT-2026-0082.** `agent-policy.yml:47` already records
  0081 as queued behind 0082 because both touch `/draft-feature`. T03 edits that
  skill's step 6; 0082 rewires how the skill is invoked. Land in queue order, or
  expect a conflict in one file.
- **`specfuse-next-id` and `specfuse-renumber` are flat console scripts** in this
  repo's `[project.scripts]`, alongside `specfuse-loop` / `specfuse-lint` /
  `specfuse-stats`. That is the pattern the umbrella delegates to, and it is the
  only half of the CLI surface this repo owns.
- Costs use `planning-discipline.md` §5 floors for every closing WU
  (`close-intermediate` $4.50, `plan-next` $6.00, `close` $5.00). `planned_cost_usd`
  is $29.00 — gate 1's five units ($24.00) plus gate 2's pre-declared terminal
  close ($5.00), which is a real graph entry and so counts in the WU sum the lint
  reconciles against. Gate 1's budget is its own units plus one re-attempt of the
  largest.
- **`auto` changes where lessons are written.** Under `autonomy_default: auto`,
  `assert_learnings_staged_under_auto` forbids a dispatched session from writing
  `.specfuse/LEARNINGS.md` directly — lessons stage to `LEARNINGS-pending.md` for
  a human to fold in. Both closing WUs name the staging file, not the real one; a
  criterion naming `LEARNINGS.md` here is refused *after* dispatch, costing a full
  re-attempt. This is a consequence of the autonomy choice, recorded so it is not
  read as an inconsistency with features that write `LEARNINGS.md` directly.
