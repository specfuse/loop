---
id: FEAT-2026-0049/T07
type: implementation
status: done
attempts: 1
planned_cost_usd: 7.00
produces:
  - specfuse/agent/providers/triage.py
  - specfuse/agent/triage_invoke.py
  - tests/test_agent_provider_triage.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.11.0
started_at: 2026-08-11T03:25:10.865186+00:00
duration_seconds: 892.693
cost_usd: 1.674008
input_tokens: 3684
output_tokens: 19007
---

# T07 — the triage provider

**Context.** The triage action class over two shipped functions, both consumed
unmodified:

> `specfuse.loop.triage.list_untriaged(runner, repo, limit) -> list` — open
> issues whose body carries no triage marker, each row flagged
> `already_structured` when it carries a harvester finding marker instead.
>
> `specfuse.loop.triage.apply_triage(runner, repo, decisions, *, auto) -> list`
> — marker first, label best-effort, idempotent on an already-marked body. With
> `auto=True` a decision whose confidence is not `"high"` is recorded as
> `question` (route `needs-human`) rather than applied as proposed.

**The gap this unit fills, and why it is bigger than "call the function".**
`apply_triage` *records* a decision; nothing in the repo *makes* one. Categorising
free text is judgment, and the only existing surface for it is the interactive,
operator-confirmed `/triage-issues` skill. So this unit also needs a headless
classification step. Build it as `specfuse/agent/triage_invoke.py`, modelled on
the shipped precedent `specfuse/monitor/autofix_invoke.py` — a
`build_invocation(...) -> (argv, prompt)` plus a result classifier, with this
module executing the argv and the invoker running nothing itself. That split is
what makes the provider testable without a network or a model.

`rules.triage.auto` is already resolved into the snapshot as
`AgentSnapshot.triage_auto` (`state.py:127`, via `agent_policy.resolve_triage_auto`).
Pass it straight through to `apply_triage(auto=...)`. Do **not** re-implement the
low-confidence downgrade in the provider: `apply_triage` owns it, and a second
copy is a contract that drifts.

The category vocabulary (`triage.CATEGORIES`), the routes (`route_for`), the
labels (`label_for`), and the marker format (`render_marker` / `parse_marker`)
all live in `specfuse/loop/triage.py`. Read them from there — §8: never re-spell
a cross-module contract value in a new module.

**Acceptance criteria.**

1. `tests/test_agent_provider_triage.py::TestTriageProvider::test_low_confidence_under_auto_becomes_question`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_triage.TestTriageProvider.test_low_confidence_under_auto_becomes_question`.
2. `specfuse/agent/providers/triage.py` implements T05's protocol over
   `list_untriaged` and `apply_triage`, and `specfuse/agent/triage_invoke.py`
   builds and classifies the headless classification session. Neither
   `specfuse/loop/triage.py` nor any other `specfuse/loop/` file is edited.
3. The same test passes after this WU's edits.
4. The provider passes `auto=snapshot.triage_auto` to `apply_triage` and contains
   no confidence-downgrade logic of its own; the `question` recategorisation in
   criterion 1's test is produced by `apply_triage`, asserted through the
   `gh issue edit` body the injected runner receives.
5. A classifier result naming a category outside `triage.CATEGORIES` never
   reaches `apply_triage` — which would raise `ValueError` — and the item is
   escalated with the offending value named in the detail. A test asserts no
   `gh issue edit` is issued for that item.
6. A row `list_untriaged` flags `already_structured` (a harvester finding) is not
   re-categorised. A test asserts it is not advertised.
7. The provider is registered in `default_providers()`, advertises
   `kind="triage"` (T05's constant), and performs no git mutation of its own.

**Do not touch.** `specfuse/loop/` entirely, and `specfuse/loop/triage.py` in
particular — it is driven, not edited; a needed change there is a plan change.
`specfuse/monitor/` — including `autofix_invoke.py`, which is read as a shape
precedent and neither imported-for-reuse-by-editing nor modified.
`specfuse/agent/state.py` and `specfuse/agent/budget.py`. `specfuse/agent/run.py`
**except** the one-line registration in `default_providers()`. The sibling gate-2
WU files (`WU-05`, `WU-06`, `WU-08`) and their modules. The driver owns all git;
this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.providers.triage import TriageProvider; print(TriageProvider)"`
and
`python3 -c "from specfuse.agent.triage_invoke import build_invocation, classify_result; print(build_invocation, classify_result)"`.

**Escalation triggers.** If the headless classification step cannot be built
without changing `apply_triage`'s decision shape — its required `number` / `body`
/ `category` keys, or the `auto` semantics — stop and name the change rather than
editing the driven surface. If the classifier's output cannot be validated
against `triage.CATEGORIES` before the call (criterion 5) without duplicating the
category list into this package, stop: the duplicate is the failure §8 names, and
the fix is to import the list, not to copy it. If drafting reveals that a triaged
issue needs to be re-advertised to the bugs provider *within the same run* — a
cross-provider handoff nothing in T05's protocol expresses — stop and say so;
that is a selection design question, not a triage detail.
