---
id: FEAT-2026-0025/T03
type: implementation
status: draft
attempts: 0
planned_cost_usd: 0.60
produces: .specfuse/skills/draft-feature/SKILL.md
oracle_env: macos_local
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Wire draft-feature to load the LEARNINGS slice via learnings_query

**Objective.** Change `/draft-feature`'s grounding-context step so it loads only the
LEARNINGS entries relevant to the feature being drafted (via the gate-1
`learnings_query` CLI), honoring the `load-whole` fallback, instead of reading the
whole ~1700-line `.specfuse/LEARNINGS.md`.

**Context.** This is `FEAT-2026-0025/T02` → gate 2. Gate 1 shipped
`.specfuse/scripts/learnings_query.py`, a stdlib CLI:
`python3 .specfuse/scripts/learnings_query.py "<query>" [--top N] [--threshold K] [--file PATH]`.
It prints either the top-N ranked `raw` bullets, or the single sentinel line
`LEARNINGS-LOAD-WHOLE` when the file has fewer than `--threshold` (default 40)
entries. `draft-feature/SKILL.md` §1 ("Read the grounding context") currently reads
`.specfuse/LEARNINGS.md` **whole** (the bullet at the `- **`.specfuse/LEARNINGS.md`**`
line). This WU rewrites that one bullet to slice instead.

Query assembly is **consumer-side and prose** (PLAN decision; no `build_query`
helper — see `GATE-02-REVIEW.md`). draft-feature runs *before* the feature's
`PLAN.md` exists, so the query is built from the one-line feature idea the user gave
plus the provisional slug (and any surfaces already named in the idea) — not from a
PLAN file.

This is `type: implementation` because it does substantive gate work (not a
closing-sequence WU), but the change is prose-only — it edits a markdown skill file,
adds no Python and no new symbol. Reference the binding rules in `.specfuse/rules/`
(`result-contract.md`, `never-touch.md`, `security-boundaries.md`,
`correlation-ids.md`) and the verification skill rather than restating them.

**Red-test exempt:** prose skill-file edit — no code path and no unit test exists for
markdown skill instructions (§12 pure-data / prose carve-out). The machine-checkable
substitute is the grep assertions in AC2–AC4, which fail on HEAD (the CLI is not
referenced in the skill today) and pass after this edit.

**Acceptance criteria.**

1. The three grep assertions (AC2–AC4) fail against `draft-feature/SKILL.md` on HEAD
   and pass after this WU's edit — the red→green substitute for the exempt code test.
2. `grep -q "learnings_query" .specfuse/skills/draft-feature/SKILL.md` exits 0 — the
   §1 grounding-context step names the real CLI
   `python3 .specfuse/scripts/learnings_query.py "<query>"` with a `--top` bound.
3. `grep -q "LEARNINGS-LOAD-WHOLE" .specfuse/skills/draft-feature/SKILL.md` exits 0 —
   the instruction tells the skill that when the CLI prints the `LEARNINGS-LOAD-WHOLE`
   sentinel it must fall back to reading the whole `.specfuse/LEARNINGS.md` (small /
   early-stage repos are unaffected).
4. The rewritten bullet states the query is assembled from the feature idea + slug
   (the context available before `PLAN.md` exists), so a cold session can build the
   query without inventing inputs. The whole-file read is removed from the default
   path (it survives only inside the sentinel-fallback branch).
5. No other section of the skill is changed; the edit is confined to §1's LEARNINGS
   bullet (and, if needed, a one-line note in §2 recon). `git diff --stat` touches
   only `draft-feature/SKILL.md`.

**Do not touch.** `.specfuse/scripts/learnings_query.py` (gate-1 primitive — call it,
do not modify it), `.specfuse/LEARNINGS.md` content, `pick-feature/SKILL.md` (T04's
file), other WUs' files, `.git/`, secrets, generated dirs. The driver owns all git.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set the driver runs for `type: implementation`
(`tests`, `coverage` ≥ 90%, `lint`, `security`). This WU changes no Python, so those
gates run against the unchanged gate-1 code and still pass; the real oracle for this
WU is the unit-specific greps in AC2–AC4 run against
`.specfuse/skills/draft-feature/SKILL.md`, plus a smoke check that the command the
skill now names actually runs:
`python3 .specfuse/scripts/learnings_query.py "orders validation" --top 5` exits 0.
Confirm the leak-scan / structural hooks still pass (this repo's pre-commit scans
prose — keep real org names/paths out of the edited bullet).

**Escalation triggers.** If `draft-feature/SKILL.md` no longer contains a
whole-file LEARNINGS load in §1 (surface moved or already wired), emit
`status: blocked` naming the drift rather than inventing a bullet to rewrite. If the
gate-1 CLI is absent or does not emit `LEARNINGS-LOAD-WHOLE`, emit `status: blocked`
— there is nothing coherent to wire. Blocked is respectable
(`result-contract.md` rule 4).
