---
id: FEAT-2026-0113/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/agent/triage_invoke.py
  - tests/test_triage_severity_classify.py
---

# T05 — the classification session assesses severity, and fails closed without one

**Objective.** `build_invocation` carries the repository's own severity rubric into
the one classification session, and the result reader returns a severity only when
the session named a readable one.

**Context.** `specfuse/agent/triage_invoke.py` builds the prompt for the single
headless classification session per issue and reads its answer back through
`specfuse.loop.triage.parse_marker`. Severity folds in **here** rather than in a
second session: one dispatched session per issue is the constraint `PLAN.md`'s
gate-2 sketch sets, and a second one would double the per-issue cost of triage.

The rubric is T03's reader — the operator's own `severity:*` label descriptions —
not a definition specfuse ships. That is what makes the classification a technical
judgment against *this* repository's declared meaning rather than an imported one.

`classify_result` keeps its `(category, confidence)` return type and its caller in
`specfuse/agent/providers/triage.py:255`; severity is reached through a new
fields-returning reader, mirroring the `parse_marker` / `parse_marker_fields`
split gate 1 landed for the same reason.

**Acceptance criteria.**

1. `tests/test_triage_severity_classify.py::SeverityPrompt::test_prompt_unchanged_when_rubric_is_empty`
   fails on HEAD before this unit runs and passes after: given an empty rubric, the
   prompt string is byte-identical to the one built today, asserted by string
   equality.
2. Given a non-empty rubric, the prompt names each severity value beside that
   repository's own label description, and asks for the marker in the three-field
   form `render_marker` now emits.
3. `classify_result` returns `(category, confidence)` unchanged for every input it
   handles today; the new fields reader is additive and returns the severity the
   session named only when that value is a key of the rubric it was given.
4. An absent `severity=` field, an empty value, a value outside the given rubric,
   and a marker whose `confidence` is not `high` each yield **no** severity —
   asserted case by case. Nothing is defaulted or inferred, so the issue keeps
   failing closed under a `min_severity` floor exactly as it does today.

**Do not touch.** `specfuse/loop/triage.py` (T04) and `specfuse/loop/labels.py`
(T03). `specfuse/agent/providers/triage.py` (T06) — this unit changes what the
invocation builder offers, and T06 is what calls it with a rubric.
`CATEGORIES` / `CONFIDENCES`, and `agent_policy.py`'s `SEVERITY_VALUES` /
`SEVERITY_ORDER`, which this unit reads through T03's rubric and does not extend.
`rules.bugs.min_severity` and `rules.bugs.severity_aliases` — where the floor sits
stays the operator's.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_agent_provider_triage tests.test_triage_skill_contract tests.test_agent_invoke_usage -b`,
and a symbol check for the new fields reader
(`python3 -c "from specfuse.agent.triage_invoke import <reader>"`). If it is
absent from the files you edited, emit `status: blocked`.

**Escalation triggers.** If carrying the rubric into the prompt appears to need a
second dispatched session, stop — one session per issue is this gate's
constraint, and a second is a re-scope, not an implementation detail. If a
repository defines a `severity:*` label whose description is empty, do not
substitute a specfuse-authored definition for it: that entry is undefined, and if
that leaves an otherwise-defining repository with nothing to classify against,
escalate rather than shipping a default rubric.
