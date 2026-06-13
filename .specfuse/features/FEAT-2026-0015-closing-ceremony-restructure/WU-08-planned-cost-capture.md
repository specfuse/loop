---
id: FEAT-2026-0015/T08
type: implementation
model: claude-sonnet-4-6
effort: medium
status: draft
attempts: 0
planned_cost_usd: 0.80
---

# Planned-cost capture: WU + PLAN frontmatter, close `## Cost analysis` AC, lint warning

**Objective.** Formalize `planned_cost_usd` as an optional WU
frontmatter field and an optional PLAN.md frontmatter field; emit
lint WARN when either is missing on a new (post-T08) feature;
require `## Cost analysis` section as part of the `close` WU
contract; document the field in templates.

**Context.** This is `FEAT-2026-0015/T08`. Independent of T04–T07
on the code axis (touches `lint_plan.py` + templates only);
G2-CLOSE depends on T08 because the close ceremony's `## Cost
analysis` AC consumes the field.

This feature has dogfooded `planned_cost_usd` informally — both
PLAN.md and the WU files (T01–T08, G2-CLOSE) carry the field
already. T08 makes it lint-aware and template-documented.

The field is OPTIONAL for already-merged features (grandfather)
and WARN-only on new features (per LEARNINGS
`[FEAT-2026-0005/G1-LESSONS]` discipline: never break existing
fixtures with a new required field).

Lint behavior:

- WU file missing `planned_cost_usd`: WARN-only, non-blocking,
  exit code 0.
- PLAN.md missing `planned_cost_usd`: WARN-only.
- PLAN.md `planned_cost_usd` differs from Σ of WU planned costs
  by > 10%: WARN-only with the delta named.
- PLAN.md `planned_cost_usd` matches Σ exactly (within $0.01):
  silent pass.

Grandfather check: WARN only when the feature is "post-T08."
Operational definition: skip the WARN when the WU's frontmatter
`status` is `done` AND the PLAN.md `status` is `done` (the
feature is sealed; backfilling planned_cost on history is
pointless). Active or draft WUs get the WARN.

Reference binding rules under `.specfuse/rules/`. Driver owns git.

**Acceptance criteria.**

1. `WU.template.md` documents `planned_cost_usd: <float>` as an
   optional frontmatter field, with prose explaining: per-WU
   estimate at draft time, used by the close WU's `## Cost
   analysis` section, lint warns when missing on active/draft
   WUs. Cite PLAN.md `roadmap_goal` § "Planned-cost capture."
2. `PLAN.template.md` documents `planned_cost_usd: <float>` as
   an optional frontmatter field; lint warns when missing or
   when it differs from Σ of WU planned costs by > 10%.
3. `lint_plan.py` walks WU files for the active feature:
   - Reads `planned_cost_usd` from each WU's frontmatter.
   - For each missing-on-active-or-draft WU: emit
     `WARN: <wu_file>: missing 'planned_cost_usd' frontmatter (optional but recommended for cost-variance calibration). See PLAN.md roadmap_goal § Planned-cost capture.`
   - Sealed WUs (status=`done` AND PLAN.md status=`done`)
     skipped silently.
4. `lint_plan.py` computes Σ over WU `planned_cost_usd` for the
   active feature (treating missing values as 0). Compares
   against PLAN.md's `planned_cost_usd`:
   - PLAN.md missing the field: WARN as above for WU case.
   - PLAN.md present and delta > 10%: emit
     `WARN: <feature_dir>/PLAN.md: planned_cost_usd $X.XX differs from sum of WU planned costs $Y.YY (delta Z%, threshold 10%). Review estimates.`
   - PLAN.md present and delta ≤ 10%: silent.
5. `close`-type WU specs MUST declare a `## Cost analysis`
   section as one of their acceptance criteria. T08 adds this
   to:
   - The `/draft-feature` skill's `close`-WU body template
     (when emitting a new feature, the AC list for a `close`
     WU includes a bullet referencing `## Cost analysis`).
   - This is a TEMPLATE/SKILL change, NOT a `loop.py` change.
     The hollow-pass guard for `## Cost analysis` lives in
     T07's `assert_cost_analysis_section_when_met`, which is
     already in scope there.
6. New unit tests in `tests/test_planned_cost_lint.py`:
   - `test_lint_warns_on_active_wu_missing_planned_cost`
   - `test_lint_skips_warn_on_sealed_wu_missing_planned_cost`
   - `test_lint_warns_on_plan_missing_planned_cost`
   - `test_lint_warns_on_plan_wu_sum_delta_over_10pct`
   - `test_lint_silent_when_plan_wu_sum_within_10pct`
   - `test_lint_warns_when_plan_has_field_but_wus_dont`
   - `test_lint_exit_code_zero_for_all_planned_cost_warns`
     (warn-only; never blocks).
7. Symbol-existence:
   `python3 -c "from lint_plan import check_planned_cost"`
   exits 0 (the WU-walker and PLAN.md-summer factored into
   one helper named `check_planned_cost`).
8. Existing test suite stays green:
   `python3 -m unittest discover tests` exits 0.
9. Lint regression on this feature's own files:
   `python3 .specfuse/scripts/lint_plan.py
   .specfuse/features/FEAT-2026-0015-closing-ceremony-restructure`
   exits 0. Acceptable: WARNs on this feature's WUs (they
   already carry `planned_cost_usd`, so the per-WU WARN
   should not fire; the PLAN-vs-WU-sum WARN should not fire
   either — Σ is $12.00 and PLAN.md states $12.00).

**Do not touch.** Exactly 4 files change:
- `.specfuse/scripts/lint_plan.py` (helper + WU walker + PLAN
  field check + WARN emission).
- `.specfuse/templates/WU.template.md` (frontmatter note).
- `.specfuse/templates/PLAN.template.md` (frontmatter note).
- `.specfuse/skills/draft-feature/SKILL.md` (close-WU
  template-body addition: AC bullet referencing `## Cost
  analysis`).
- `tests/test_planned_cost_lint.py` (new file).

Wait — that's 5. The template AND skill counts as 2 changes
PLUS lint_plan.py and the new test = 4 files modified + 1 new
file. State this explicitly in the RESULT block.

No edits to: `loop.py` (no driver change; T07 owns the
hollow-pass guard for `## Cost analysis`), other features' WU
files, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Plus AC7 symbol-existence. Plus AC9 lint-regression check.

**Escalation triggers.**

1. **Completeness.** If `check_planned_cost` is absent from
   `lint_plan.py` after your edits, emit `status: blocked`.
2. **§10 helper-duplication pre-flight.** Run
   `grep -rn "planned_cost_usd" .specfuse/ tests/`
   and enumerate every site. This feature's WUs (T01–T08) and
   PLAN.md already carry the field; that's expected (the
   dogfood seed). What MUST NOT exist is a pre-existing
   `check_planned_cost`-style helper in `lint_plan.py`. If
   found, name it and emit `status: blocked`.
3. **Warn-only invariant.** If your test surface accidentally
   asserts that lint EXITS NON-ZERO on a planned-cost gap,
   STOP — that breaks the grandfather contract. The
   exit code is unaffected. If you cannot keep it exit-0
   while flagging the WARN, emit `status: blocked` with the
   specific assertion gap named.
4. **Cost-sum precision.** Floating-point arithmetic on
   per-WU costs ($0.50 + $0.80 + ...) can drift. Use
   `round(sum, 2)` or `Decimal` to avoid spurious "delta
   0.0001%" WARNs. If your implementation cannot keep this
   clean without a decimal-arithmetic refactor, emit
   `status: blocked` with the precision issue named.
