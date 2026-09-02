---
id: FEAT-2026-0084/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: lint_gate_proportionality
produces:
  - docs/methodology.md
  - specfuse/loop/lint_plan.py
  - tests/test_lint_gate_proportionality.py
---

# Raise the single-gate threshold from 4 to 8 substantive units, and warn when a small feature has more than one gate

**Objective.** A feature whose planned substantive count is at most 8 drafts as
one gate with one terminal `close`. Today the threshold is 4. Every extra gate
costs a human arm (53% of all idle time follows a gate boundary) and the hedge
rate climbs from 37% at one gate to 64% at five.

**Context.** FEAT-2026-0084/T04; read `PLAN.md`. The threshold has one home,
`docs/methodology.md` §6 "Ceremony proportionality", and one reference,
`plugins/specfuse/skills/draft-feature/SKILL.md` step 4 (line 190). No lint
enforces it (`grep -rn proportional specfuse/loop/lint_plan.py` is empty). Add
`lint_gate_proportionality`: WARN when the PLAN's planned substantive count
(types `implementation`, `qa_authoring`, `qa_execution`, `qa_curation`) is at
most 8 and the gates list has more than one entry with work units. Docs are
vendored to `specfuse/loop/data/docs/` by `scripts/sync-scaffold.sh`.

**Acceptance criteria.**

- `tests/test_lint_gate_proportionality.py::test_small_feature_two_gates_warns` fails on HEAD and passes after: a PLAN with 6 substantive units across two gates yields one WARN naming the count and the threshold.
- `tests/test_lint_gate_proportionality.py::test_small_feature_one_gate_clean` and `::test_nine_units_two_gates_clean` yield nothing.
- `grep -c "is \*\*8\*\*" docs/methodology.md` reports at least 1 and `grep -c "≤ 4" docs/methodology.md plugins/specfuse/skills/draft-feature/SKILL.md` reports 0.
- `python3 -m specfuse.loop.lint_plan` over every folder under `.specfuse/features/` reports the same ERROR count as on HEAD (this rule is WARN-only).
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain specfuse/loop/data .specfuse/skills` empty.

**Do not touch.** T03's `lint_ac_observable` and its tests; the `evaluate_auto_close`
predicate; `.specfuse/rules/`; `WU.template.md`; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
`python3 -c "from specfuse.loop.lint_plan import lint_gate_proportionality"`
exits 0.

**Escalation triggers.** Emit `status: blocked` if the threshold turns out to
live in a third place the greps above did not find (a constant in `loop.py` or
`gate_eval.py`); name it, do not change it here.
