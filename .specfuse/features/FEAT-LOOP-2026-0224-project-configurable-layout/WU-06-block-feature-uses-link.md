---
id: FEAT-LOOP-2026-0224/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - plugins/specfuse/skills/block-feature/SKILL.md
  - .specfuse/skills/block-feature/SKILL.md
  - tests/test_block_feature_layout.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.29.1
started_at: 2026-10-28T00:53:00.456950+00:00
duration_seconds: 80.486
cost_usd: 0.249828
input_tokens: 16
output_tokens: 5810
---

# T06 — `block-feature` renders decision links through the layout

**Objective.** `/block-feature` stops hand-building `../docs/adr/…` links and stops
calling every decision blocker "an ADR": it asks `layout get decisions.style` and
renders each decision link with `python3 -m specfuse.loop.layout link`.

**Context.** Edit the canonical `plugins/specfuse/skills/block-feature/SKILL.md`, then
copy to `.specfuse/skills/block-feature/SKILL.md` (canonical direction: `plugins/` →
`.specfuse/`, memory `skills_canonical_plugins_dir`). Changes: the description and
§ at lines 19, 72–91 classify a decision blocker by `decisions.style` — `adr`: a path,
as today; `entries`: an id (plus `--domain` when the `link` template has
`{domain}`); the rendered link comes from the `layout link` command, and the skill
states that command verbatim. The "Do not require the ADR file to exist" rule stays
(PLAN scope: out). Wording says "decision record" where it means either style and
"ADR" only inside the `adr` branch.

`tests/test_block_feature_layout.py`: extract every fenced command in the skill that
starts `python3 -m specfuse.loop.layout`, run it (with placeholders filled from a
fixture) in a no-layout and an entries-layout temp repo, assert exit 0 and that the
no-layout output equals the skill's own ADR example string.

**Acceptance criteria.**

1. `tests/test_block_feature_layout.py` fails on HEAD (no such command in the skill)
   and passes after, and `grep -n "\.\./docs/adr" plugins/specfuse/skills/block-feature/SKILL.md` matches
   only the rendered ADR example, not instructions to build the path by hand.
2. `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes.

**Do not touch.** Other skills (T07). `layout.py`.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_skills_vendored_in_sync -b`.

**Escalation triggers.** If the skill sync test requires a sync script run that also
regenerates symlinks under `.claude/skills/`, run it and declare only paths it
actually changed (`[FEAT-LOOP-2026-0045/G1-CLOSE]`).
