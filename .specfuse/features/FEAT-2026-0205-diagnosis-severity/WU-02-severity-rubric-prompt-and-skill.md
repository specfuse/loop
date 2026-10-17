---
id: FEAT-2026-0205/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/monitor/diagnosis.py
  - specfuse/agent/diagnose_invoke.py
  - plugins/specfuse/skills/diagnose-issue/SKILL.md
  - .specfuse/skills/diagnose-issue/SKILL.md
  - tests/test_diagnosis_severity_rubric.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T19:08:02.845066+00:00
duration_seconds: 32.566
cost_usd: 0.196815
input_tokens: 16
output_tokens: 3480
---

# T02 — one severity rubric, used by the headless prompt and /diagnose-issue

**Objective.** Both diagnosis entry points ask for a severity against the same rubric,
defined once in code.

**Context.** `FEAT-2026-0205/T02`. Add `SEVERITY_RUBRIC` to
`specfuse/monitor/diagnosis.py`: one line per value in
`agent_policy.SEVERITY_VALUES`, judged from the finding's evidence —
`critical`: users cannot complete a core action, or data is lost or corrupted, now;
`high`: a user-facing request or a message flow fails repeatedly, or a scheduled job
has stopped; `medium`: a failure with a workaround, or limited to a few requests or
instances; `low`: noise (e.g. a client abort on a request that succeeded) or no
user-visible effect. `diagnose_invoke`'s prompt (replacing T01's placeholder) includes
the rubric verbatim and asks for an optional `severity` field. Both SKILL.md copies of
`/diagnose-issue` gain a step to set `Diagnosis.severity` from the same rubric,
referencing `diagnosis.SEVERITY_RUBRIC` rather than restating it; the copies stay
byte-identical (`scripts/sync-scaffold.sh`).

**Acceptance criteria.**

1. `tests/test_diagnosis_severity_rubric.py::TestRubric::test_one_line_per_value`
   fails on HEAD and passes after: `SEVERITY_RUBRIC` has exactly one entry per
   `SEVERITY_VALUES` member.
2. `test_prompt_carries_the_rubric`: the prompt `diagnose_invoke.build_invocation`
   returns contains every rubric line verbatim and names the `severity` field as
   optional.
3. Both SKILL.md copies name `SEVERITY_RUBRIC` and are byte-identical, and
   `bash scripts/sync-scaffold.sh` leaves `git status --porcelain` unchanged.

**Do not touch.** The marker format (T01). Autofix (T03).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_diagnose_issue_skill tests.test_agent_provider_findings_diagnose -b`.

**Escalation triggers.** If the skill-copy sync check fails for reasons outside these
two files, stop and escalate rather than editing other skills.
