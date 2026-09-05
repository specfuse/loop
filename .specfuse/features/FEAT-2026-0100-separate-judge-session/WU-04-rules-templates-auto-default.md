---
id: FEAT-2026-0100/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
produces:
  - .specfuse/rules/close-discipline.md
  - .specfuse/templates/PLAN.template.md
  - docs/methodology.md
  - plugins/specfuse/skills/draft-feature/SKILL.md
---

# The rules say who writes the verdict, and a drafted feature defaults to `auto`

**Objective.** Move the verdict's authorship in prose to match the
mechanism: the close writes measurements and the retrospective; the judge
writes the verdict. Then make `autonomy_default: auto` the default a drafted
feature carries, since the judge is what makes an auto-armed close
trustworthy.

**Context.** FEAT-2026-0100/T04; read `PLAN.md`. Edit: `close-discipline.md`
§1 (fresh oracle re-runs stay; add that the verdict is the judge's and a
close body must not name it); `docs/methodology.md` §3 (the judge, the
`judged` event, `judge_disabled`, what the judge reads) and §9 (auto is the
recommended default; the arm predicate unchanged); `PLAN.template.md`
`autonomy_default: auto`; `plugins/specfuse/skills/draft-feature/SKILL.md`
step 3's autonomy decision recommends `auto` and names the judge as the
reason, and the `judge_disabled` question is asked only when a criterion
cannot be judged from evidence. Also the close section of `WU.template.md`
as 0084/T02 left it: one line, "do not write the verdict; measure". Sync
scripts for rules, docs and skills. Red-test exempt: prose; the render-and-
lint test from 0084/T02 covers the template.

**Acceptance criteria.**

- `grep -c "judge" .specfuse/rules/close-discipline.md` reports at least 2 and `grep -c "judge" docs/methodology.md` at least 3.
- `grep -n "^autonomy_default:" .specfuse/templates/PLAN.template.md` reads `auto`.
- `grep -c "auto" plugins/specfuse/skills/draft-feature/SKILL.md` increased and the autonomy decision's recommendation line names the judge.
- `tests/test_wu_template_renders_lintable.py` passes unchanged.
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain specfuse/loop/data .specfuse/skills` empty; `tests/test_scaffold_data_in_sync.py` and `tests/test_skills_vendored_in_sync.py` pass.

**Do not touch.** `specfuse/loop/*.py` (T01-T03, T05); `arm_eval.py` and its
docs section on stop classes; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if a rule test asserts a
sentence this unit must remove; name the test and the sentence.
