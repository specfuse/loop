---
id: FEAT-2026-0084/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
produces:
  - .specfuse/templates/WU.template.md
  - plugins/specfuse/skills/authoring-work-units/SKILL.md
  - tests/test_wu_template_renders_lintable.py
gate_set: code
driver_version: 0.14.0
started_at: 2026-09-02T16:02:49.075290+00:00
duration_seconds: 2153.807
cost_usd: 10.692664
input_tokens: 176
output_tokens: 91534
---

# Shrink the work-unit template to 70 lines and the authoring skill to 200

**Objective.** A work unit should be 30-45 lines: objective, 2-5 acceptance
criteria each paired with its check, `produces:`, do-not-touch as deltas, one or
two escalation triggers. Make the template and the authoring skill prescribe
that shape instead of the current 94-line median.

**Context.** FEAT-2026-0084/T02; read `PLAN.md`. `WU.template.md` is 199 lines,
120 of them frontmatter field notes; move those notes to `docs/methodology.md`
§2 as one line per field and leave a pointer. `authoring-work-units/SKILL.md`
is 571 lines and 13 rules while its description says eight. Keep §2 (criteria
scoped to the footprint), §6 (sizing), §12 (red test first), §13 (`produces:`);
fold §9 and §10 into one rule; move §11 (operator scripts) into
`verification-discipline.md`; reduce the rest to one-line pointers with their
citation. Skills are canonical under `plugins/specfuse/skills/`, synced by
`scripts/sync-scaffold.sh`. The five bold sections stay: `lint_plan` requires
them, and 327 existing bodies use the `**Section.**` preamble form
(LEARNINGS `[FEAT-2026-0055/G1-CLOSE]`). This feature's own WU files are the
worked example of the target shape.

**Acceptance criteria.**

- `tests/test_wu_template_renders_lintable.py::test_rendered_template_passes_lint` exists and fails on HEAD (the test file does not exist yet); after this WU it passes. It renders `WU.template.md` into a temp feature folder with a minimal PLAN.md and runs `lint_plan` on it (LEARNINGS `[FEAT-2026-0015/G1]`).
- `wc -l .specfuse/templates/WU.template.md` reports at most 70; `wc -l plugins/specfuse/skills/authoring-work-units/SKILL.md` reports at most 200.
- The skill's frontmatter `description` states the actual rule count.
- `grep -c "^\*\*\(Context\|Acceptance criteria\|Do not touch\|Verification\|Escalation triggers\)\.\*\*" .specfuse/templates/WU.template.md` reports 5.
- `specfuse lint` exits 0 on every folder under `.specfuse/features/` that exits 0 on HEAD (run it before and after; the set of passing folders is unchanged).
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain specfuse/loop/data .specfuse/skills` empty; `tests/test_skills_vendored_in_sync.py` and `tests/test_scaffold_data_in_sync.py` pass.

**Do not touch.** `.specfuse/rules/*.md` except the `verification-discipline.md`
paragraph receiving §11 (T01 owns the rest); `lint_plan.py` (T03, T04);
`PLAN.template.md`, `GATE.template.md`; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if any existing feature folder
that lints clean on HEAD stops linting clean, or if a section the linter
requires cannot fit the 70-line ceiling. Do not relax the linter to make room.
