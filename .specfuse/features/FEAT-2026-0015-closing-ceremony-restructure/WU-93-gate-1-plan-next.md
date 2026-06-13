---
id: FEAT-2026-0015/G1-PLAN
type: plan-next
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
---

# Gate 1 plan-next: detail Gate 2's WUs

**Objective.** Detail Gate 2's substantive + closing work units as
`draft` entries in PLAN.md's gates graph + corresponding `WU-*.md`
files. Write `GATE-01-REVIEW.md` summarizing what Gate 1 delivered
and what Gate 2 must achieve.

**Context.** Correlation ID `FEAT-2026-0015/G1-PLAN`. Read this
feature's `RETROSPECTIVE.md`, `LEARNINGS.md` (updates from G1-LESSONS),
PLAN.md's `roadmap_goal` + roadmap detail section for FEAT-2026-0015,
and the existing Gate 1 WU specs to ensure Gate 2 builds on what
landed. Reference binding rules under `.specfuse/rules/`.

**Acceptance criteria.**

1. `GATE-01-REVIEW.md` exists at this feature folder, summarizing:
   - What Gate 1 delivered (new types, lint shapes, templates, skill
     update).
   - What Gate 2 MUST deliver per PLAN.md `roadmap_goal` and the
     roadmap detail's "Verdict coupling / Oracle env / State-flip /
     Planned-cost / Hollow-pass guard" sections.
   - Verdict on whether Gate 2 should retain all proposed scope or
     defer any item to a follow-up feature. Per
     `[FEAT-2026-0003/G4-LESSONS]`: let work drive WU count; don't
     pad for symmetry. Per `[FEAT-2026-0010/G1-PLAN]`: explicit
     Cross-repo contracts table if Gate 2 will reference values
     authored elsewhere.
2. PLAN.md's `gates[1].work_units` is populated with the drafted
   Gate 2 WUs in dependency order. Likely shape (subject to G1-PLAN's
   own judgment):
   - T04 `WU-04-verdict-coupling.md` (driver enforcement of
     `verdict:` frontmatter field).
   - T05 `WU-05-oracle-env-parity.md` (frontmatter field + lint).
   - T06 `WU-06-state-flip-consolidation.md` (move terminal flips
     from /wrap-feature into `close` WU; shrink /wrap-feature).
   - T07 `WU-07-hollow-pass-guard.md` (type-keyed assertion table
     in driver).
   - T08 `WU-08-planned-cost-capture.md` (WU + PLAN frontmatter
     field + close-WU `## Cost analysis` AC + lint warning).
   - G2-CLOSE `WU-94-gate-2-close.md` (type `close`, NEW contract).
3. Each Gate 2 WU file is written with `status: draft`,
   `attempts: 0`, `planned_cost_usd` per the PLAN.md cost table.
   Bodies follow the five-section structure
   (`Objective` / `Context` / `Acceptance criteria` /
   `Do not touch` / `Verification` / `Escalation triggers`) and
   apply `/authoring-work-units` rules — especially §10
   helper-duplication pre-flight.
4. The NEW closing-shape contract is exercised by G2-CLOSE: it uses
   `type: close` (NOT the legacy 4-WU sequence). G2-CLOSE's AC list
   includes ALL of: produce `RETROSPECTIVE.md` Gate 2 section, append
   LEARNINGS, reconcile docs, write feature-arc verdict,
   `## Cost analysis` section (per T08's contract), execute terminal
   state-flips (per T06's consolidation: PLAN → done conditional on
   verdict, gate → passed, roadmap row → done, auto-archive call).
5. Recursive close audit per `[FEAT-2026-0008/G1-CLOSE]`: G2-CLOSE's
   AC includes running the new hollow-pass guard (T07) against its
   OWN deliverables. If the guard fires, G2-CLOSE emits
   `status: blocked`.

**Do not touch.** Source code (`loop.py`, `lint_plan.py`), templates,
production skills (T03 already updated `/draft-feature`; G1-DOCS may
have touched others), other features' WU files, secrets, `.git/`.
The agent writes Gate 2 WU files + `GATE-01-REVIEW.md` + updates the
`gates[1].work_units` block in this feature's `PLAN.md`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml` (`lint_plan.py` on this feature) —
structural validity preserved. Drafted Gate 2 WUs must pass lint.

**Escalation triggers.**

1. **Scope creep / hollow-pad.** If proposed Gate 2 WUs exceed 6
   substantive units, emit `status: blocked` and ask the operator
   to triage. Per LEARNINGS, big gates correlate with high failure
   surface.
2. **Cross-repo contracts missing.** If any Gate 2 WU references
   load-bearing strings (frontmatter field names, lint warnings,
   driver constants), G1-PLAN must enumerate them in
   `GATE-01-REVIEW.md`'s `## Cross-repo contracts` table per
   `[FEAT-2026-0003/G3-LESSONS]`. If unable to enumerate, emit
   `status: blocked`.
3. **Legacy contract drift.** If G1-PLAN's draft of G2-CLOSE
   fall back to the 4-WU shape "to be safe", emit `status: blocked`
   — the recursive dogfood is the load-bearing test that the new
   contract works end-to-end.
