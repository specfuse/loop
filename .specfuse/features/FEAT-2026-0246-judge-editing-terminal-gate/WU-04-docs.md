---
id: FEAT-2026-0246/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - plugins/specfuse/skills/draft-feature/SKILL.md
  - .specfuse/skills/draft-feature/SKILL.md
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - docs/concepts/autonomy-stop-classes.md
  - specfuse/loop/data/docs/concepts/autonomy-stop-classes.md
  - tests/test_judge_editing_terminal_docs.py
  - tests/test_terminal_judge_editing_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T12:04:10.576389+00:00
duration_seconds: 117.853
cost_usd: 0.290164
input_tokens: 24
output_tokens: 6601
---

# T04 — the docs describe the terminal stop, and stop recommending `review` for it

**Objective.** Replace the wording #3544 shipped, which recommends `review` as the
only checkpoint for a terminal-gate judge edit. `review` adds no terminal checkpoint
(PLAN decision 1); the new stop does, at every autonomy level.

**Context.** `FEAT-2026-0246/T04`. Surfaces, every copy (skills are canonical in
`plugins/specfuse/skills/`, mirrored to `.specfuse/skills/`; docs mirrored to
`specfuse/loop/data/docs/`):

- `draft-feature` SKILL.md, the autonomy-decision paragraph: keep "recommend `auto`";
  replace the `judge_editing` caveat with: the terminal gate's own judge-surface edits
  now halt before the close at every autonomy level, cleared by
  `judge_edit_acknowledged` plus `/unblock-wu`; recommend `review` only when a wrong
  arm is expensive to undo.
- `methodology.md` §9: replace the "does **not** cover the terminal gate … Choose
  `review`" sentences with the terminal stop. Keep the "`review` and `supervised` are,
  today, the same behavior" sentence (PLAN decision 9).
- `autonomy-stop-classes.md` class 2: replace the "Does not cover the terminal gate"
  paragraph with a "Terminal gate" paragraph — the check, its seat before the close,
  that it is not one of the eight arm classes, the acknowledgement field, the
  universal-path reach into consumer repos (PLAN decision 5), and the declared-paths
  limit.

`tests/test_judge_editing_terminal_docs.py` currently asserts the #3544 wording. Its
assertions are **replaced deliberately**, not weakened: every copy names the terminal
stop and `judge_edit_acknowledged`, and no copy says `review` is the checkpoint for a
terminal-gate judge edit. Un-skip `DocsNoLongerRecommendReview` in the oracle module
and point it at the same assertions.

**Acceptance criteria.**

1. `tests/test_judge_editing_terminal_docs.py` with the new assertions fails on HEAD's
   copies and passes after; `tests/test_terminal_judge_editing_end_to_end.py::DocsNoLongerRecommendReview`
   passes.
2. Each pair of copies is byte-identical:
   `cmp plugins/specfuse/skills/draft-feature/SKILL.md .specfuse/skills/draft-feature/SKILL.md`,
   `cmp docs/methodology.md specfuse/loop/data/docs/methodology.md`,
   `cmp docs/concepts/autonomy-stop-classes.md specfuse/loop/data/docs/concepts/autonomy-stop-classes.md`.
3. `grep -rn "the only checkpoint the change gets" docs plugins .specfuse/skills specfuse/loop/data`
   returns nothing.

**Do not touch.** Source under `specfuse/loop/*.py`. `CHANGELOG.md` (the close writes
it).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If another surface outside the three named still repeats the
#3544 `review` advice (`grep -rn "#3542" docs plugins specfuse/loop/data`), list it
in the RESULT and fix it only when it is a copy of a named surface.
