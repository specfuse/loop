---
id: FEAT-2026-0025/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.60
produces: .specfuse/skills/pick-feature/SKILL.md
oracle_env: macos_local
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Wire pick-feature to load the LEARNINGS slice via learnings_query

**Objective.** Change `/pick-feature`'s "read the durable lessons" step so it loads
only the LEARNINGS entries relevant to the candidate features under comparison (via
the gate-1 `learnings_query` CLI), honoring the `load-whole` fallback, instead of
reading the whole ~1700-line `.specfuse/LEARNINGS.md`.

**Context.** This is `FEAT-2026-0025/T04` → gate 2. Gate 1 shipped
`.specfuse/scripts/learnings_query.py`, a stdlib CLI:
`python3 .specfuse/scripts/learnings_query.py "<query>" [--top N] [--threshold K] [--file PATH]`.
It prints the top-N ranked `raw` bullets, or the single sentinel line
`LEARNINGS-LOAD-WHOLE` when the file has fewer than `--threshold` (default 40)
entries. `pick-feature/SKILL.md` §1 ("Read the roadmap and the durable lessons")
currently reads `.specfuse/LEARNINGS.md` **whole** (the bullet at the
`- **`.specfuse/LEARNINGS.md`**` line). This WU rewrites that one bullet to slice.

**Relevance-risk note (read `GATE-02-REVIEW.md`).** pick-feature is unlike
draft-feature: it does not plan *one* feature, it ranks 2–3 candidates. There is no
single feature query. Assemble the query from the **concatenated roadmap goals +
slugs of the planned candidate rows under comparison**, and use a generous `--top`
(≥ 15) so a lesson relevant to a lower-ranked candidate is not dropped. Because the
comparison is diffuse, this is the consumer where slicing most risks dropping a
needed lesson — the instruction must say so and keep the sentinel fallback.

Query assembly is **consumer-side and prose** (PLAN decision; no `build_query`
helper). This is `type: implementation` because it does substantive gate work (not a
closing-sequence WU), but the change is prose-only — it edits a markdown skill file,
adds no Python and no new symbol. Reference the binding rules in `.specfuse/rules/`
and the verification skill rather than restating them.

**Red-test exempt:** prose skill-file edit — no code path and no unit test exists for
markdown skill instructions (§12 pure-data / prose carve-out). The machine-checkable
substitute is the grep assertions in AC2–AC4, which fail on HEAD and pass after.

**Acceptance criteria.**

1. The three grep assertions (AC2–AC4) fail against `pick-feature/SKILL.md` on HEAD
   and pass after this WU's edit — the red→green substitute for the exempt code test.
2. `grep -q "learnings_query" .specfuse/skills/pick-feature/SKILL.md` exits 0 — the
   step names the real CLI with a `--top` bound of at least 15.
3. `grep -q "LEARNINGS-LOAD-WHOLE" .specfuse/skills/pick-feature/SKILL.md` exits 0 —
   the instruction falls back to reading the whole file on the sentinel.
4. The rewritten bullet states the query is the concatenated goals/slugs of the
   candidate rows being compared (not a single feature), and explicitly flags that a
   large or heterogeneous comparison set should prefer the whole-file read. The
   default whole-file read is removed (it survives only in the sentinel-fallback and
   the large-set branch).
5. No other section of the skill is changed; the edit is confined to §1's LEARNINGS
   bullet. `git diff --stat` touches only `pick-feature/SKILL.md`.

**Do not touch.** `.specfuse/scripts/learnings_query.py` (gate-1 primitive — call it,
do not modify it), `.specfuse/LEARNINGS.md` content, `draft-feature/SKILL.md` (T03's
file), other WUs' files, `.git/`, secrets, generated dirs. The driver owns all git.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set the driver runs for `type: implementation`
(`tests`, `coverage` ≥ 90%, `lint`, `security`). This WU changes no Python, so those
gates run against unchanged gate-1 code and still pass; the real oracle is the
unit-specific greps in AC2–AC4 against `.specfuse/skills/pick-feature/SKILL.md`, plus
a smoke check that the named command runs:
`python3 .specfuse/scripts/learnings_query.py "roadmap candidate goals" --top 15`
exits 0. Confirm the leak-scan / structural hooks still pass (prose scan — keep real
org names/paths out of the edited bullet).

**Escalation triggers.** If `pick-feature/SKILL.md` no longer contains a whole-file
LEARNINGS load in §1 (surface moved or already wired), emit `status: blocked` naming
the drift. If the gate-1 CLI is absent or does not emit `LEARNINGS-LOAD-WHOLE`, emit
`status: blocked`. Blocked is respectable (`result-contract.md` rule 4).
