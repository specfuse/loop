<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Gate 2 review — wire the planning consumers (drafted by G1-PLAN)

Weighted toward doubt. This is the human's arm/reject checkpoint (autonomy
`review`). Read the **Scope correction** first — it changes the WU count from the
"four consumers" the roadmap_goal assumed.

## What gate 2 delivers (drafted)

| WU | File | Consumer | Type | Cost |
|----|------|----------|------|------|
| T03 | `WU-03-wire-draft-feature.md` | `draft-feature` §1 | implementation† | $0.60 |
| T04 | `WU-04-wire-pick-feature.md`  | `pick-feature` §1  | implementation† | $0.60 |
| G2-CLOSE | `WU-92-gate-2-close.md` | — | close | $0.75 |

† `type: implementation`, not `docs`: the lint closing-sequence check counts `docs`
as closing work (`_CLOSING_TYPES`), so a substantive `docs` WU makes the gate-2
sequence read as `[docs, docs, close]` and fails lint. `implementation` is the only
substantive, non-closing type. The edits are prose-only (markdown skill files), so
each carries an explicit §12 **Red-test exempt** line; their `code` gate set runs
against unchanged gate-1 Python (still passes) and the real oracle is grep assertions.

Both substantive WUs rewrite exactly one bullet (the whole-file `.specfuse/LEARNINGS.md`
read) in the named skill's §1, replacing it with a call to the gate-1 CLI
`python3 .specfuse/scripts/learnings_query.py "<query>" --top N` that honors the
`LEARNINGS-LOAD-WHOLE` sentinel fallback.

## Decisions + rationale

### 1. Scope correction: two real consumers, not four

`roadmap_goal` and `GATE-02.md`'s DoD name four consumers — `draft-feature`,
`pick-feature`, `plan-next`, `authoring-work-units`. Reading the actual files
(evidence, not assumption):

- **`draft-feature/SKILL.md` §1** — reads `.specfuse/LEARNINGS.md` **whole**
  (grounding-context bullet). Real load-whole consumer. **Wired (T03).**
- **`pick-feature/SKILL.md` §1** — reads `.specfuse/LEARNINGS.md` **whole**
  (durable-lessons bullet). Real load-whole consumer. **Wired (T04).**
- **`authoring-work-units/SKILL.md`** — does **not** load LEARNINGS at runtime. It
  is a *static distillation* of LEARNINGS ("This skill distills `.specfuse/LEARNINGS.md`",
  §"pipeline: runs → retrospective → lessons → LEARNINGS.md → this skill"). The
  lessons are baked into the skill prose at authoring time; there is nothing to
  slice at planning time. **Out of scope** — wiring it would be a no-op against an
  invented surface.
- **`plan-next`** — has **no durable skill file** (`.specfuse/skills/plan-next/`
  does not exist). It is a driver-dispatched WU type; each plan-next WU's "what to
  read" is authored in that WU's own objective (this very WU, G1-PLAN, read the
  retro + consumer skills, *not* LEARNINGS whole). There is no single surface to
  edit. **Out of scope** — deferred; see open risk R4.

Per `.specfuse/rules/result-contract.md` and this WU's escalation trigger, drafting
WUs against surfaces that do not load LEARNINGS whole would be drafting against
invented surfaces. The honest move is to wire the two that do and document the two
that do not — which is what this review is for. **The escalation trigger fired
partially** (2 of 4 mechanisms unlocatable-as-load-whole) but not wholly, so this is
a scope note, not a `blocked`.

### 2. Query-assembly location: consumer-side prose, no `build_query` helper

The forward-arc left this open ("includes `build_query(feature_dir)` if gate 1's
retro shows it belongs consumer-side"). **The gate-1 retro is an auto-close stub —
it makes no recommendation.** Deciding from evidence instead:

- A `build_query(feature_dir)` that reads `PLAN.md` frontmatter fits **neither**
  wired consumer. `draft-feature` runs *before* the feature's `PLAN.md` exists (it
  is the thing that writes PLAN); `pick-feature` ranks 2–3 candidates, so there is
  no single feature dir to read.
- The gate-1 CLI already takes a **raw query string**. Both consumers are
  interactive prose skills executed by Claude, not Python callers — they shell out
  and pass a query built from context they already hold (the feature idea + slug;
  the candidate rows' goals).

So: **no Python helper.** Query assembly is a prose instruction in each skill, built
from that consumer's available inputs. This matches PLAN.md's own decision line
("assembled on the consumer side, gate 2"). Consequence: gate 2 ships **zero new
code** — two `docs` WUs. That is the correct shape here, not an under-scope.

### 3. Threshold in practice

`DEFAULT_LOAD_WHOLE_THRESHOLD = 40`. The real `.specfuse/LEARNINGS.md` parses to
**95 entries** today (`should_load_whole` → `False`), so slicing engages now and the
feature earns its value immediately. Small / early-stage repos (< 40 entries) hit the
sentinel and keep the whole-file read — exactly the intended guard. Both WUs keep the
default `--threshold` (no override), so the guard travels to any repo that copies the
scaffold.

## Open risks (weighted toward doubt)

- **R1 — relevance drop (the core doubt).** BM25 is keyword-lexical. A lesson phrased
  in vocabulary that does not overlap the query (synonyms, a lesson stated
  abstractly) can rank below `--top` and be silently dropped — the planner never
  sees it and cannot know it was there. This is *the* risk the whole feature trades
  against context cost. Mitigation in the drafts: generous `--top`, sentinel
  fallback below threshold. **Not mitigated:** there is no unit test that proves the
  slice contains the lessons a real planning session needed — that can only be
  judged by real sessions. G2-CLOSE's `## What the loop did NOT verify` must name
  this (its AC5 already does).
- **R2 — pick-feature is the weakest fit.** It ranks multiple candidates, so a
  single query is a compromise; a lesson relevant to a lower-ranked candidate is the
  most likely R1 casualty. T04 counters with concatenated-candidate queries + `--top
  ≥ 15` + an explicit "prefer whole-file for large/heterogeneous sets" branch, but
  the human should decide at arm time whether pick-feature should slice at all or
  keep loading whole (it is the cheaper-to-leave-alone consumer — it runs rarely and
  the roadmap is short).
- **R3 — draft-feature query timing.** The query is built pre-PLAN from the idea +
  provisional slug, which is thinner context than a full feature. Early-draft slices
  may be lower-precision than plan-next-time slices would be. Acceptable (draft is
  exploratory) but noted.
- **R4 — plan-next left unwired.** plan-next is arguably the *ideal* slice consumer
  (a concrete active feature with a real PLAN.md and touched paths), but it has no
  durable file to edit. Wiring it would mean editing `draft-feature`'s plan-next
  authoring guidance and/or `WU.template.md` to instruct future plan-next WUs to
  slice — a broader, more speculative change than "rewrite one bullet." Deferred out
  of this gate deliberately; a follow-up roadmap item is the honest home for it.
- **R5 — no code oracle for prose edits.** Both WUs are markdown. The oracle is grep
  assertions (`learnings_query`, `LEARNINGS-LOAD-WHOLE` present) plus a smoke-run of
  the named command. That proves the *instruction is wired and the command is real*;
  it does not prove the instruction *reads well* to a cold session — a reviewer-eye
  check the human does at arm time.

## Verification story per WU

- **T03 (draft-feature).** `doc` gate set + three greps against
  `draft-feature/SKILL.md` (CLI named with `--top`; sentinel handled; whole-file read
  removed from default path) + smoke run
  `learnings_query.py "orders validation" --top 5` exits 0 + `git diff --stat` shows
  only that file. Red-test exempt (§12: prose, no code oracle) — greps fail on HEAD
  (CLI not referenced today), pass after.
- **T04 (pick-feature).** Same shape against `pick-feature/SKILL.md`, with `--top ≥
  15` and the multi-candidate query instruction; smoke run
  `learnings_query.py "roadmap candidate goals" --top 15` exits 0.
- **G2-CLOSE.** `plannext`/close gates + hollow-pass guards (`## Cost analysis`,
  `## What the loop did NOT verify`, closing-deliverable presence,
  `assert_terminal_flips_fired` on `verdict: met`). Must name R1 (relevance quality
  unverifiable by unit test) in `## What the loop did NOT verify`, and must set
  `verdict: met` only if T03/T04 actually shipped the wiring.

## Arm-time checklist for the human

1. Accept the **2-of-4 scope correction**, or push back (e.g. "wire plan-next too" →
   promote R4 to a WU / follow-up feature).
2. Decide **pick-feature (T04)**: slice, or leave it loading whole? It is the
   riskiest (R2) and cheapest-to-skip consumer.
3. Confirm **no `build_query` helper** is the intended call (query stays prose).
4. If accepting: flip T03/T04 `status: draft → pending`, flip G1 `awaiting_review`
   per the driver, resume the loop.
