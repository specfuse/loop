---
id: FEAT-2026-0247/T03
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 2.00
produces:
  - plugins/specfuse/skills/roadmap-add/SKILL.md
  - plugins/specfuse/skills/draft-feature/SKILL.md
  - .specfuse/skills/roadmap-add/SKILL.md
  - .specfuse/skills/draft-feature/SKILL.md
  - tests/test_roadmap_add_skill.py
  - tests/test_keyed_feature_ids_end_to_end.py
---

# T03 — `/roadmap-add` and `/draft-feature` allocate through `ids next`

**Objective.** The two allocating skills hand out keyed IDs when a key is set, and count
keyed IDs when computing the next ordinal, without the agent re-deriving the ordinal in
prose.

**Context.** `FEAT-2026-0247/T03`. This unit **edits** the oracle module T01 created.
Today `roadmap-add`'s "Next-ID algorithm" has the agent scan four sources for
`FEAT-<YYYY>-<NNNN>`; a keyed sequence is invisible to it. Rewrite the local part to call
`python3 -m specfuse.loop.ids next` (sources a and b), and keep in prose only what the
command cannot do: source (d), the GitHub issue/PR scan with its plausibility bound,
which may raise the ordinal, and the collision check over all four sources. Every
pattern the prose names accepts both forms. The row, anchor and heading formats in
"String formats" gain the keyed example. `draft-feature` step 1 points at the same
command.

Skills are canonical under `plugins/specfuse/skills/`; edit there, then run
`bash scripts/sync-scaffold.sh` and confirm `.specfuse/skills/` matches
(`tests/test_skills_vendored_in_sync.py`).

Un-skip the oracle's clause-4 class (asserts the shipped skill text names
`specfuse.loop.ids next` and a keyed example).

**Acceptance criteria.**

1. `tests/test_roadmap_add_skill.py`: its `FEAT_RE`, `FEAT_ROW_RE` and `PLAN_FEAT_RE`
   import from `ids`; a new test asserts the skill names `specfuse.loop.ids next` and
   that its row/anchor examples parse with `ids.parse` in both forms. Fails before,
   passes after.
2. `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes after the sync.
3. The skill still states the #771/#1872 rules (source (c) advisory, implausible source
   (d) ordinals excluded) in substance.

**Do not touch.** Other skills that only *mention* the ID shape (pick-feature,
block-feature, abandon-feature, …): their prose works for both forms. Code.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If the sync script reverts the edit, the edit was made in the
wrong tree (see the sync direction above); fix it there rather than editing
`.specfuse/skills/` directly.
