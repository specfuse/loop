---
id: FEAT-2026-0049/T09
type: implementation
status: draft
attempts: 0
planned_cost_usd: 6.50
produces:
  - specfuse/agent/monitoring_read.py
  - tests/test_agent_findings_seam.py
---

# T09 — the findings seam: two kinds, their ranking, and the monitoring reader

**Context.** `FEAT-2026-0049/T09`. Gate 2's T05 opened the selector's kind
vocabulary from two to four and shipped the provider registry and the spend
ledger. This unit does the same narrow job for the findings pair, and nothing
else: the two providers that follow (T10, T11) then only add their own module and
their registry line.

Two facts from the shipped code the work is written against:

> `_select_next` (`specfuse/agent/run.py:190-245`) ranks `KIND_ESCALATION_ANSWER`
> at `(-1, 0)`, `KIND_BUG` at `(0, 0)` when `rules.bugs.preempt` is true and
> `(2, 0)` otherwise, `KIND_FEATURE` at `(1, <queue index>)`, and `KIND_TRIAGE`
> at `(3, 0)`. Every other kind lands in `unresolved` and is escalated with
> `unknown item kind`. A provider advertising a kind this function does not rank
> is never executed.
>
> `run_autofix(..., monitoring_config, component)`
> (`specfuse/monitor/autofix_run.py:164`) requires the parsed monitoring config
> **and** the component name as separate arguments; `autofix.decide` reads the
> component's `autofix` dial out of it. Nothing in `specfuse/agent/` reads a
> monitoring config today, and `main()` has no flag naming one.

**The ranking decision is made here, not per provider** — the same reasoning T05
recorded for its own four kinds: priority is policy, and a per-provider guess is
how it stops being policy. Both kinds are added in one edit even though only one
provider lands in this unit; a half-populated vocabulary is a worse intermediate
state than a complete one, and the ranking is only reviewable as a whole.

- **`KIND_FINDING_AUTOFIX` ranks at the bug tier**, honouring `rules.bugs.preempt`
  exactly as `KIND_BUG` does. It is the same class of work by construction:
  `autofix_invoke.build_invocation` (`specfuse/monitor/autofix_invoke.py:41`)
  launches `/fix-bug`, so a fired autofix *is* a bug-lane run reached by a
  different route. Ranking it anywhere else would mean the same work has two
  priorities depending on who noticed it. This is **OQ-1** in
  `GATE-03-REVIEW.md`; it is drafted this way and one criterion changes if the
  operator decides otherwise.
- **`KIND_FINDING_DIAGNOSE` ranks ahead of triage**, at tier 3 with `KIND_TRIAGE`
  moved from `(3, 0)` to `(3, 1)`. Both classes prepare work rather than close
  it, so both stay behind everything that acts. Diagnosis goes first because it
  is the only preparatory class that can unlock acting work *within the same
  run* — T11's provider reads issue comments live at `advertise()` time, so a
  diagnosis posted at iteration 3 is visible at iteration 4. Triage cannot do
  that. Moving `KIND_TRIAGE`'s sub-rank changes its position relative to no
  existing kind; it replaces an ordering that would otherwise depend on provider
  registration order, which is not a policy.

**The monitoring reader.** Both providers need to answer "which component is this
finding about, and what has the operator said about it?" — and neither can get it
from the snapshot, because `state._read_issues` requests only
`number,title,labels,body` and the component is prose inside the body. Build it
once here as `specfuse/agent/monitoring_read.py`:

- load a monitoring config from a path, returning `None` (not raising) when the
  file is absent — an absent `.specfuse/monitoring.yml` is a correct, valid final
  state, in `.specfuse/monitoring.yml.example`'s own words, and the agent must
  read it as "nothing to do here", never as an error;
- resolve a finding issue's component from the `**Component:** <name>` line
  `specfuse.monitor.issues._render_body` writes (`issues.py:137`);
- read one component's `diagnose` dial from the config's `components:` list.

Parse the config with `specfuse.loop._miniyaml.parse`, the same reader
`autofix_run.main` uses (`autofix_run.py:230-231`). Do **not** write a second
`autofix`-dial reader: T11 hands the raw config to `run_autofix`, which reaches
`autofix._read_dial` itself, and a second copy is the drift §8 exists to prevent.

**Acceptance criteria.**

1. `tests/test_agent_findings_seam.py::TestFindingKinds::test_finding_items_are_selected_not_escalated`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_findings_seam.TestFindingKinds.test_finding_items_are_selected_not_escalated`.
2. `specfuse/agent/run.py` exposes `KIND_FINDING_DIAGNOSE` and
   `KIND_FINDING_AUTOFIX`, and `_select_next` ranks both as described above.
   Criterion 1's test asserts a test-double provider advertising each kind is
   executed rather than escalated with `unknown item kind`.
3. The same test passes after this WU's edits.
4. **Gate 1's and gate 2's ranking is unchanged.** A test constructs items of all
   six kinds and asserts the resulting execution order is:
   escalation-answer, then bugs and features exactly as `rules.bugs.preempt`
   already orders them with findings-autofix alongside bugs, then
   findings-diagnose, then triage. `rules.bugs.preempt` keeps its `False` safe
   default and its existing tier values.
5. `specfuse/agent/monitoring_read.py` exposes the three readers described above.
   A test asserts an absent config path yields `None` rather than raising, and a
   second asserts the component name is read from a finding-issue body rendered
   in `issues.py`'s real format rather than from a shape invented by the test.
6. `main()` accepts `--monitoring-config`, defaulting to
   `.specfuse/monitoring.yml`, and threads it to `default_providers(...)`. A test
   asserts the default path is used when the flag is absent. The three existing
   providers' construction is unchanged.
7. The module performs no writes: no issue comment, no label, no file. A test
   asserts the injected runner receives no `gh` call at all from
   `monitoring_read`.

**Do not touch.** `specfuse/monitor/` entirely — `autofix.py`, `autofix_run.py`,
`autofix_state.py`, `diagnose_cli.py`, `diagnosis.py`, and `issues.py` are read
for their contracts and driven, never edited; a needed change there is a plan
change to escalate. `specfuse/loop/` entirely, `_miniyaml.py` included — it is
imported as-is. `specfuse/agent/state.py`, `specfuse/agent/budget.py`, and the
three gate-2 providers under `specfuse/agent/providers/`. `specfuse/agent/run.py`
is edited **only** for the two constants, `_select_next`'s ranking, the
`--monitoring-config` flag, and threading that value into `default_providers`.
The sibling gate-3 WU files (`WU-10`, `WU-11`) and the modules they will create.
The driver owns all git; this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.run import KIND_FINDING_DIAGNOSE, KIND_FINDING_AUTOFIX; print(KIND_FINDING_DIAGNOSE, KIND_FINDING_AUTOFIX)"`
and
`python3 -c "import specfuse.agent.monitoring_read as m; print(m)"`.

**Escalation triggers.** If ranking findings-autofix at the bug tier turns out to
require a new `agent-policy.yml` key — a `rules.findings.*` dial of any shape —
stop and say so rather than minting one: that is the same boundary T05's
escalation trigger drew, and OQ-1 exists to let the operator answer it first. If
the monitoring reader cannot resolve a component without duplicating
`autofix._read_dial`'s private component-keying, stop and name the duplication
rather than shipping it. If reading the `diagnose` dial reveals that no shipped
code consumes it and you conclude the dial is therefore free to reinterpret,
stop: OQ-2 is exactly that question and it is the operator's.
