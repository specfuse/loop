---
id: FEAT-2026-0007/G2-PLAN
type: plan-next
model: claude-opus-4-7
effort: high
status: draft
attempts: 0
---

# Plan the next gate (or write the terminal feature-arc verdict)

**Objective.** Decide whether the feature is complete (the four levers of
`roadmap_goal` have all shipped and been observed in real telemetry) or
whether a Gate 3 is warranted. If complete, write the terminal feature-arc
verdict and propose status changes to `roadmap.md`. If Gate 3 is warranted,
draft its work units (as `draft`), wire them into `PLAN.md`'s graph, and
write `GATE-03-REVIEW.md` for the human.

**Context.** Read, in this order:

1. `PLAN.md` — `roadmap_goal` and Gate 2's `work_units` (now `done`).
2. `RETROSPECTIVE.md` — both Gate 1 and Gate 2 sections.
3. `.specfuse/LEARNINGS.md` — both feature gates' promoted entries.
4. The post-Gate-2 events.jsonl — actual budget vs spend, observed cache
   hit rates, model-default behavior under real dispatch.

The terminal-vs-extend decision is governed by LEARNINGS
`[FEAT-2026-0003/G4-LESSONS]`: three tests must all pass to extend with a
gate — bounded scope (hours not weeks), contiguous proof on this branch,
disciplined trigger on live concrete evidence. If any test fails, the
correct move is to write the terminal verdict and open a new feature
later if needed.

The four levers of `roadmap_goal` are: per-WU model alias (T01), effort
tier (T02), terseness directive (T03), per-gate budget (T07). All landed
in code by end of Gate 2 (assuming T08H corrects the T04 gap). The
feature's natural terminus is Gate 2.

**Acceptance criteria.**
1. **Decision branch.** Either:
   (a) **Terminal.** Write the terminal feature-arc verdict appended to
       `RETROSPECTIVE.md` (a `# Feature-arc verdict` section): what shipped
       vs `roadmap_goal`, what telemetry confirmed, what was deferred,
       which `Scope OUT` items remain unresolved and what feature might
       address them next. Update `.specfuse/roadmap.md` row to mark this
       feature `done`. Do **not** draft a Gate 3.
   (b) **Extend.** Draft Gate 3's substantive WUs (as `draft`, with all
       five mandatory sections, `type`, `model`, `effort`), update
       `PLAN.md`'s graph to add Gate 3 with its `work_units` list and
       `depends_on` edges, append Gate 3's own closing sequence with
       WU-98 through WU-101 (next 90+-range numbers), and write
       `GATE-03-REVIEW.md`. The escalation evidence in
       `RETROSPECTIVE.md` must satisfy all three
       `[FEAT-2026-0003/G4-LESSONS]` tests — quote them in the review
       artifact.
2. Whichever branch you take, the rationale is written in the review/verdict
   artifact and references the specific retrospective entries that drove
   the choice.
3. `lint_plan.py` exits 0 on the feature folder after your edits (the
   verification gate runs this, but run it yourself first).

**Do not touch.** Any non-draft WU; any current/prior gate's status; source
code (code changes belong to a Gate 3 substantive WU if you draft one);
secrets; `.git/`. You write at most: the terminal verdict in
`RETROSPECTIVE.md` (branch a) OR Gate 3 draft WU files + `PLAN.md` graph +
`GATE-03-REVIEW.md` (branch b); roadmap.md row in either branch.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`
(`lint_plan.py` on this feature). Also confirm the terminal-vs-extend
artifact exists per AC 1.

**Escalation triggers.**
1. **Gate-extension discipline.** If the temptation to extend is driven by
   "we could improve X" speculation rather than concrete failed-telemetry
   evidence, write the terminal verdict instead and note the deferred
   improvement as a candidate future feature in the verdict's "what was
   deferred" paragraph. Per `[FEAT-2026-0003/G4-LESSONS]`, weak evidence
   corrodes the "feature ends" contract.
2. **Roadmap-goal change.** If Gate 2's run revealed that the `roadmap_goal`
   itself was wrong (e.g. cost did not actually drop, or the levers
   compound differently than predicted), flag it LOUDLY in the artifact
   you produce — do not silently rewrite the goal. Goal changes are a
   human decision.
3. **T08H still missed something.** If post-Gate-2 reading reveals T08H
   *also* declared `complete` without landing all required symbols
   (Gate 2's retrospective AC 2 smoke check should have caught this, but
   verify), the terminal verdict must name this as a methodology-level
   correctness gap and recommend the next feature to address it.
