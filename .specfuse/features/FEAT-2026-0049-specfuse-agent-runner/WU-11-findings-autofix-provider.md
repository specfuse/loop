---
id: FEAT-2026-0049/T11
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.50
produces:
  - specfuse/agent/providers/findings_autofix.py
  - tests/test_agent_provider_findings_autofix.py
---

# T11 — the findings-autofix provider

**Context.** `FEAT-2026-0049/T11`. The second findings action class, over one
shipped function consumed unmodified:

> `specfuse.monitor.autofix_run.run_autofix(*, runner, invoker, repo,
> finding_issue_number, monitoring_config, component) -> AutofixRunResult`
> (`autofix_run.py:164`) — *"Decide, record, fire, and label — for one diagnosed
> finding issue."* It reads the finding's fingerprint marker and its most recent
> diagnosis comment, calls `autofix.decide`, and on `FIRE` records the attempt
> **before** invoking, fires through the injected invoker, and applies
> `AUTOFIX_FAILED_LABEL` on `refused` / `could_not_proceed`. `DECLINE` and
> `ROUTE_TO_HUMAN` do nothing further. `AutofixRunResult.outcome` is `None`
> whenever nothing fired, *"so a caller can tell 'nothing ran' from 'something
> ran and produced an outcome' without inferring it from side effects."*

**This unit is a caller, and that is the whole point.** `autofix_run`'s module
docstring records that it shipped without one on purpose — *"`run_autofix` is its
own entry point"* — and PLAN.md's existing-mechanism search names this feature as
that caller. So the provider is thin by design. Everything that could tempt it to
add judgment is already owned upstream:

- **The decision** is `autofix.decide`'s. The provider does not read the
  confidence threshold, the `fix_scope` routing, the fingerprint rate limit, or
  the daily cap, and holds no copy of any of them.
- **The invoker** is `specfuse.monitor.autofix_invoke`, passed straight through as
  `run_autofix`'s `invoker=` argument — the same module `autofix_run.main` passes
  (`autofix_run.py:235`). Do not build a second one; T09/T10's invoker pattern
  exists because *those* surfaces had no shipped invoker, and this one does.
- **The safety floor** is inside the prompt `autofix_invoke.build_invocation`
  already writes. The provider adds nothing to it.

**What the provider genuinely owns.** Selection, the config pair, and the outcome
mapping. `advertise` returns one `kind="finding-autofix"` item per open snapshot
issue carrying `issues.FINDING_LABEL` that **already has** a diagnosis comment —
the mirror of T10's filter, read the same way, through `diagnosis.parse` over a
live `gh issue view N --json body,comments`. The `(monitoring_config, component)`
pair comes from T09's `specfuse/agent/monitoring_read.py`; a finding whose
component is not in the config, or any finding when no config is present, is not
advertised, because `decide` would decline it as `unreadable_input` and spending
an item slot to be told that is not selection.

**Outcome mapping**, from `AutofixRunResult` to `ActionOutcome`:

| `decision` / `outcome` | `ActionOutcome` | why |
|---|---|---|
| `FIRE` → `completed` | completed | the fix ran and finished |
| `FIRE` → `refused` / `could_not_proceed` | escalated, **no payload** | `run_autofix` already applied `AUTOFIX_FAILED_LABEL`; a needs-human issue on top would be a second inbox entry for one event |
| `ROUTE_TO_HUMAN` | escalated, **with payload** | the decision's own name says a human is wanted, and nothing upstream files one |
| `DECLINE` | completed | a decline is the predicate working — dial off, rate limit, low confidence — not a failure to report |

The `DECLINE`-as-completed row is the one worth arguing with at arming: it means
a run against a repo with `autofix: "off"` everywhere reports items completed
having changed nothing. The alternative — escalating every decline — turns the
safety dial into an alarm, which is how a correct refusal starts reading as a
malfunction. `ActionOutcome.detail` carries `decide`'s own `reason` string
(`autofix.REASON_*`) either way, so the run summary says which it was.

**Acceptance criteria.**

1. `tests/test_agent_provider_findings_autofix.py::TestFindingsAutofixProvider::test_decline_does_not_invoke_fix_bug`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_findings_autofix.TestFindingsAutofixProvider.test_decline_does_not_invoke_fix_bug`.
2. `specfuse/agent/providers/findings_autofix.py` implements T05's protocol over
   `run_autofix`, passing `specfuse.monitor.autofix_invoke` as the `invoker` and
   T09's reader's output as `monitoring_config` / `component`. No file under
   `specfuse/monitor/` is edited.
3. The same test passes after this WU's edits.
4. **The provider re-decides nothing.** A test asserts the module contains no
   reference to `CONFIDENCE_THRESHOLD`, `FIX_SCOPES`, `DAILY_CAP`, or a
   fingerprint comparison of its own, and that every branch of the outcome table
   above is driven only by `AutofixRunResult`'s `decision` and `outcome` fields.
5. **Each row of the outcome table has a test**, each asserting the observable
   difference through the injected runner: `refused` files no escalation issue
   and adds no second label beyond the one `run_autofix` applied;
   `ROUTE_TO_HUMAN` files exactly one escalation whose body names the finding
   issue; `DECLINE` issues no `gh` write at all and reports `decide`'s reason in
   the detail.
6. **Undiagnosed findings and unresolvable components are not advertised.** Two
   tests, mirroring T10's criterion 6: an issue with no diagnosis comment is not
   advertised; a finding whose component is absent from the config, and every
   finding when no monitoring config is present, is not advertised either.
7. The provider is registered in `default_providers()`, advertises T09's
   `KIND_FINDING_AUTOFIX`, and performs no git mutation of its own — it invokes;
   it does not commit, branch, push, or merge.

**Do not touch.** `specfuse/monitor/` entirely — `autofix_run.py`, `autofix.py`,
`autofix_state.py`, `autofix_invoke.py`, `diagnosis.py`, and `issues.py` are
imported and driven, never edited; a needed change there is a plan change to
escalate, and `autofix_run`'s record-before-invoke ordering in particular is a
correctness property of that module, not a detail to reproduce here.
`specfuse/loop/` entirely. `specfuse/agent/state.py`,
`specfuse/agent/budget.py`, `specfuse/agent/monitoring_read.py` (T09's, consumed
as-is), `specfuse/agent/diagnose_invoke.py` and
`specfuse/agent/providers/findings_diagnose.py` (T10's), and the three gate-2
providers. `specfuse/agent/run.py` **except** the one-line registration in
`default_providers()`. The sibling gate-3 WU files (`WU-09`, `WU-10`). The driver
owns all git; this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus a §9
symbol check:
`python3 -c "from specfuse.agent.providers.findings_autofix import FindingsAutofixProvider; print(FindingsAutofixProvider)"`.

**This unit's target surface cannot be exercised against this repository, and the
criteria above are written to that limit.** `run_autofix` requires a
`monitoring_config` with named components; this repo is a CLI tool with no
deployable components and will never carry a real `monitoring.yml`
(`.specfuse/verification.yml`, `monitoring-example-lint`). Every criterion above
is therefore met with an injected `runner` and a fixture config — the same oracle
`tests/test_autofix_run.py` already holds `run_autofix` itself to
(`_monitoring_config(dial)` at `:44`). What that leaves unproven is named in
`GATE-03-REVIEW.md` § "What cannot be proven here, precisely"; do not attempt to
close that gap by inventing a `.specfuse/monitoring.yml` for this repo.

**Escalation triggers.** If mapping `AutofixRunResult` to `ActionOutcome`
requires reading a field `run_autofix` does not return — most likely the PR number
or branch a fired fix produced — stop and name it rather than shelling out to
find it; a return-shape change to `autofix_run` is a plan change. If a fired
autofix turns out to need the spend figure for T05's ledger and the headless
session's cost is not recoverable from what the invoker returns, stop and say so
rather than reporting a spend of zero as if it were measured. If writing
criterion 5's `ROUTE_TO_HUMAN` test reveals that `emit_escalation`'s two-option
minimum cannot be satisfied honestly for a routed finding — there being only one
sensible action — stop: inventing a second option to satisfy a validator is how
an escalation stops being a decision.
