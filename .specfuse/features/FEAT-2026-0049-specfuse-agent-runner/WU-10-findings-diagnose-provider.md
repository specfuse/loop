---
id: FEAT-2026-0049/T10
type: implementation
status: pending
attempts: 0
planned_cost_usd: 7.50
produces:
  - specfuse/agent/providers/findings_diagnose.py
  - specfuse/agent/diagnose_invoke.py
  - tests/test_agent_provider_findings_diagnose.py
---

# T10 — the findings-diagnose provider

**Context.** `FEAT-2026-0049/T10`. The first findings action class, over one
shipped function consumed unmodified:

> `specfuse.monitor.diagnose_cli.render_headless(raw) -> str`
> (`diagnose_cli.py:88`) parses analysis-step JSON into a `Diagnosis` and renders
> it through `diagnosis.render`. Its module docstring is explicit about its
> boundaries: *"This module produces a comment body; it does not post one, and
> shells out to nothing and reaches no network of its own — posting is the
> caller's job."* `parse_analysis` raises `AnalysisParseError` on invalid JSON, a
> missing required field, a non-numeric `confidence`, or a `fix_scope` outside
> `diagnosis.FIX_SCOPES` — it never returns a `Diagnosis` with a defaulted
> field, because *"a defaulted `fix_scope` would silently route real work past
> FEAT-2026-0042's gate."*

**The gap this unit fills, and why it is two halves rather than one.**
`render_headless` sits in the middle of the path: it needs analysis JSON as
input and produces a comment body as output, and neither end exists. So this unit
builds both:

- **The analysis half** — `specfuse/agent/diagnose_invoke.py`, modelled on the
  shipped precedent `specfuse/monitor/autofix_invoke.py` and on
  `specfuse/agent/triage_invoke.py`, which T07 built to the same shape for the
  same reason. `build_invocation(...) -> (argv, prompt)` plus a result reader;
  this module runs nothing itself, the provider executes the argv. The prompt
  asks for exactly the five fields `diagnose_cli._REQUIRED_FIELDS` names, as one
  JSON object, and nothing else. The interactive `/diagnose-issue` skill is the
  reference for *what* a good diagnosis contains; read it, do not re-derive the
  field list from it — the field list is `diagnose_cli`'s.
- **The posting half** — one `gh issue comment`, in the shape
  `specfuse/agent/providers/answers.py:207` already uses in this package.

**Selection.** `advertise` returns one `kind="finding-diagnose"` item per open
snapshot issue carrying `specfuse.monitor.issues.FINDING_LABEL`
(`monitoring-finding`, `issues.py:54`) that has **no diagnosis comment yet**.
The snapshot cannot answer the second half — `state._read_issues` requests only
`number,title,labels,body` — so this provider reads comments itself with
`gh issue view N --json body,comments`, the same read
`autofix_run._read_finding_issue` performs (`autofix_run.py:106-121`) and the
same softening of "the selector reads a value, not a call" that T08 accepted and
`GATE-02-REVIEW.md` recorded as a risk. Detect an existing diagnosis with
`specfuse.monitor.diagnosis.parse`, not with a marker string spelled here.

**The `diagnose` dial.** `.specfuse/monitoring.yml`'s components each carry
`diagnose: manual | auto` (`lint_monitoring.py:43`, `REQUIRED_COMPONENT_FIELDS`
at `:60`). The linter validates the value and **no shipped code reads it** — this
provider is its first consumer. Drafted conservatively: a component whose dial is
not `auto` is not advertised, and an absent monitoring config advertises nothing
at all. This is **OQ-2** in `GATE-03-REVIEW.md`; criterion 6 changes if the
operator decides the agent should diagnose every finding regardless.

**Acceptance criteria.**

1. `tests/test_agent_provider_findings_diagnose.py::TestFindingsDiagnoseProvider::test_undiagnosed_finding_gets_one_diagnosis_comment`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_findings_diagnose.TestFindingsDiagnoseProvider.test_undiagnosed_finding_gets_one_diagnosis_comment`.
2. `specfuse/agent/providers/findings_diagnose.py` implements T05's protocol over
   `render_headless`, and `specfuse/agent/diagnose_invoke.py` builds and reads the
   headless analysis session. No file under `specfuse/monitor/` is edited.
3. The same test passes after this WU's edits.
4. **The rendered body is `diagnosis.render`'s, unaltered.** Criterion 1's test
   asserts the `--body`/`--body-file` argument the injected runner receives is
   byte-identical to `render_headless(<the analysis JSON the fake session
   returned>)`. The provider holds no heading template and no marker string of
   its own.
5. **An unparseable analysis posts nothing.** A session whose output raises
   `AnalysisParseError` — malformed JSON, a missing field, or a `fix_scope`
   outside `FIX_SCOPES` — escalates with the parse error's own message in the
   detail, and a test asserts no `gh issue comment` is issued for that item. The
   provider does not retry, does not default a field, and does not post a partial
   body.
6. **Already-diagnosed and dial-off findings are not advertised.** Two tests: an
   issue whose comments already carry a diagnosis `diagnosis.parse` reads is not
   advertised; a finding whose component's `diagnose` dial is not `auto`, and
   every finding when no monitoring config is present, is not advertised either.
7. The provider is registered in `default_providers()`, advertises T09's
   `KIND_FINDING_DIAGNOSE`, and performs no git mutation and no label write of
   its own — a diagnosis is a comment.

**Do not touch.** `specfuse/monitor/` entirely. `diagnose_cli.py`, `diagnosis.py`,
and `issues.py` are imported and driven, never edited; `autofix_invoke.py` is read
as a shape precedent and neither modified nor imported for reuse. `specfuse/loop/`
entirely. `specfuse/agent/state.py`, `specfuse/agent/budget.py`,
`specfuse/agent/monitoring_read.py` (T09's, consumed as-is), and the three gate-2
providers. `specfuse/agent/run.py` **except** the one-line registration in
`default_providers()`. The sibling gate-3 WU files (`WU-09`, `WU-11`). The driver
owns all git; this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.providers.findings_diagnose import FindingsDiagnoseProvider; print(FindingsDiagnoseProvider)"`
and
`python3 -c "from specfuse.agent.diagnose_invoke import build_invocation; print(build_invocation)"`.

**Escalation triggers.** If the five analysis fields cannot be obtained without
changing `diagnose_cli._REQUIRED_FIELDS` or relaxing `parse_analysis`'s
`fix_scope` check, stop and name the change: that check is FEAT-2026-0042's gate
and loosening it here would route real work past it. If detecting an existing
diagnosis requires spelling the `<!-- specfuse:diagnosis ... -->` marker in this
package rather than calling `diagnosis.parse`, stop — that is the duplication §8
names. If the comment read needed to decide "already diagnosed" turns out to cost
one `gh` call per finding per loop iteration and you judge that unacceptable,
stop and say so rather than caching state the agent has no database for; a
snapshot change is a gate-1 surface change and out of bounds here.
