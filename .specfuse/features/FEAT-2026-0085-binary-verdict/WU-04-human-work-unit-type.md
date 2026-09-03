---
id: FEAT-2026-0085/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
model: opus
effort: high
oracle_env: macos_local
produces_driver_helper: halt_for_human_unit
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/lint_plan.py
  - plugins/specfuse/skills/unblock-wu/SKILL.md
  - tests/test_human_work_unit.py
gate_set: code
driver_version: 0.14.0
started_at: 2026-09-03T10:53:37.987519+00:00
duration_seconds: 1713.68
cost_usd: 11.092705
input_tokens: 266
output_tokens: 53713
---

# A `type: human` work unit the driver halts on, so a human step is recorded before the close

**Objective.** Sixteen hedged features needed a person to reply, click, sign,
or run something interactively, and recorded that as a softened verdict after
the fact. Add a work-unit type the driver never dispatches: when a `human`
unit is ready, the driver prints the operator brief and halts; the operator
performs the step, marks it `done` with `evidence:`, and the run resumes.

**Context.** FEAT-2026-0085/T04; read `PLAN.md`. `DISPATCHABLE` is
`loop.py:326`; `MODEL_BY_TYPE` and the gate-set map at `:289-326` must not
map `human` (no model, no gate set). In `run()`, before dispatch: if
`wu.type == "human"` and status is pending, call `halt_for_human_unit`: emit
`human_escalation` with reason `human_step_required` and a `blocked_human`
frontmatter flip, print the six-part brief from
`.specfuse/rules/operator-escalation.md` using the unit's Objective as "what
decision is needed", and return exit 1. On resume, a `human` unit whose
status is `done` and whose frontmatter `evidence:` is non-empty is treated as
done with `attempts: 0`; the close quotes the evidence. `/unblock-wu` gains
`--done --evidence "<text>"` for `human` units (skill is canonical under
`plugins/specfuse/skills/`; sync). `lint_plan`: `human` joins the known types;
a `done` human unit without `evidence` is ERROR; a `human` unit needs only
Objective, Context, and Acceptance criteria sections (no Verification, no
Escalation triggers). `evaluate_auto_close` needs no change: the
`blocked_human` event already disables auto-close for the gate. Red test
first.

**Acceptance criteria.**

- `tests/test_human_work_unit.py::test_ready_human_unit_halts_without_dispatch` fails on HEAD and passes after: on a fixture with a pending `human` unit, `run()` exits 1, no `claude` process is spawned (patched dispatcher asserts not called), `events.jsonl` carries `human_escalation` with reason `human_step_required`, and stdout carries the brief's six headings.
- `tests/test_human_work_unit.py::test_done_human_unit_with_evidence_lets_next_unit_dispatch`: after the fixture's human unit is flipped `done` with `evidence: replied on issue #12`, `ready()` returns the next unit and it dispatches.
- `tests/test_human_work_unit.py::test_lint_rejects_done_human_without_evidence` and `::test_lint_accepts_human_unit_with_three_sections`.
- `python3 -c "from specfuse.loop.loop import halt_for_human_unit, DISPATCHABLE; assert 'human' not in __import__('specfuse.loop.loop', fromlist=['MODEL_BY_TYPE']).MODEL_BY_TYPE"` exits 0.
- `python3 -m specfuse.loop.lint_plan` over every folder under `.specfuse/features/` reports the same ERROR count as on HEAD.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `arm_eval.py`'s `human_only` veto (unchanged, separate
concept); `gate_eval.py`; verdict guards (T01); stubs (T02); `escalation.py`
(T03); rules and docs (T05); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if the brief cannot be printed
from the unit's own sections without inventing text for one of the six parts;
name the part. Emit `status: blocked` if `halt_for_human_unit` is absent from
the files you edited.
