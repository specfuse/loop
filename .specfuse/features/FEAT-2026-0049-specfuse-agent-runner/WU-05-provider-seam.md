---
id: FEAT-2026-0049/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 10.00
produces:
  - specfuse/agent/run.py
  - specfuse/agent/providers/__init__.py
  - tests/test_agent_seam.py
---

# T05 — the loop is provider-ready: kind vocabulary, registry, spend ledger

**Context.** Gate 1 shipped the conductor with an *empty* provider registry, and
two consequences of that only become visible now that real providers are being
added. Both are this unit's subject; no provider ships here.

1. **The selector's kind vocabulary is closed at two.** `_select_next`
   (`specfuse/agent/run.py:190-213`) ranks `KIND_BUG` and `KIND_FEATURE` and
   sends *everything else* to `unresolved`, which the loop parks with an
   escalation (`unknown item kind {kind!r}`). Gate 2's providers advertise kinds
   that do not exist in that vocabulary, so without this unit every gate-2 item
   escalates instead of executing.
2. **The token cap is inert.** `RunBudget.record_tokens`
   (`specfuse/agent/budget.py:88`) has no caller anywhere —
   `grep -rn "record_tokens" specfuse/ tests/` returns only its definition — and
   `ActionOutcome` (`run.py:92-98`) carries only `status` and `detail`, so a
   provider has no way to report what it spent. `--max-tokens` is accepted on the
   CLI and compares a counter that never leaves zero. Gate 1 could not surface
   this: with zero providers, nothing spends. Gate 2 is the gate where the agent
   starts invoking headless sessions that cost real money, so the cap has to
   become real *before* the providers land, not after.

Also here because it is the same seam: `main()` builds `run_agent(...)` without a
`providers=` argument (`run.py:347-354`), so the registry is unreachable from the
CLI. This unit adds the one named registry function each later provider WU
appends itself to.

**The selection order, decided here rather than guessed per-provider.** Priority
is policy, not intelligence (PLAN.md, T04). The total order this unit implements:

| Kind | Rank | Why |
|---|---|---|
| `escalation-answer` | first, always | An operator's answer may cancel or redirect work already queued; acting before reading it spends money on a decision that has already been overruled. GATE-02.md's definition of done says answered escalations are acted on first. |
| `bug` | unchanged — `0` when `rules.bugs.preempt`, else `2` | Gate 1's behaviour, preserved exactly. |
| `feature` | unchanged — `1`, ordered within tier by `queue:` position | Gate 1's behaviour, preserved exactly. |
| `triage` | last | Classification is *preparation*, not action: it creates work for a later run rather than closing any. Under a cap the agent should spend its remaining items acting on work it already knows about. |
| anything else | not ranked — parked with an escalation | Gate 1's behaviour, preserved exactly. |

If the operator wants triage to run first, that is a policy dial, not a code
change — say so and stop rather than inventing a new `agent-policy.yml` key here.

**Acceptance criteria.**

1. `tests/test_agent_seam.py::TestKindVocabulary::test_triage_item_is_selected_not_escalated`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_seam.TestKindVocabulary.test_triage_item_is_selected_not_escalated`.
2. `specfuse/agent/run.py` exposes `KIND_TRIAGE` and `KIND_ESCALATION_ANSWER`,
   and `_select_next` ranks them per the order table above.
3. The same test passes after this WU's edits.
4. **Gate 1's ranking is unchanged.** With only bug- and feature-kind items
   advertised, the selected order is identical to gate 1's under both
   `rules.bugs.preempt: true` and `false`, and an item whose `kind` is outside
   the vocabulary is still parked with an escalation rather than guessed into a
   position. One test per branch.
5. `ActionOutcome` carries a spend field defaulting to zero, and `run_agent`
   passes a completed item's reported spend to `budget.record_tokens` before the
   next boundary check. A provider that reports nothing leaves the total at zero.
   `--max-tokens`'s default stays `None` (unbounded) — this unit makes an
   existing cap effective, it does not introduce or flip one.
6. `RunSummary` and the printed run summary name total reported spend alongside
   the counts already there.
7. `specfuse/agent/run.py` exposes `default_providers(...)` returning the
   registry, `main()` passes it to `run_agent`, and `run_agent`'s `providers=`
   default stays `()` so tests keep injecting doubles. The registry returns `()`
   in this unit — the seam ships here, the providers ship in T06–T08 — and
   `specfuse/agent/providers/__init__.py` is created as its future home.
8. **An escalated outcome can reach the human inbox, not only stdout.**
   `ActionOutcome` gains an optional structured escalation payload carrying the
   six parts `specfuse.loop.escalation.emit_escalation` requires
   (`done_so_far`, `issue_summary`, `decision_needed`, `why_not_auto`,
   `options`, `recommendation`), and `run_agent` calls `emit_escalation` —
   imported and used unmodified, with the injected runner passed through — for
   every escalated outcome that supplies one. `emit_escalation` is idempotent on
   `correlation_id`, so a re-run of the same item files no duplicate; a test
   asserts that by invoking twice.
9. **An escalation with no payload is reported as summary-only, in words.** When
   an escalated outcome supplies no payload, no issue is filed and the run
   summary says so for that item — `escalated (summary only, no issue filed)` or
   equivalent — so "escalated" never silently means "printed to a terminal
   nobody was watching". A test asserts both halves: no `gh issue create` reaches
   the runner, and the summary line names the item as unfiled.

**A note on `produces:`.** `specfuse/agent/run.py` is listed there even though
T04 already delivered it, so `specfuse lint` emits a
`check_produces_satisfiability` WARN on this WU. That is expected and is the
linter's own offered resolution — the edit is incremental (the kind constants and
their tiers in `_select_next`, the spend field on `ActionOutcome` and its call to
`record_tokens`, `default_providers()`, and the summary line), and dropping the
path would leave this unit's main deliverable outside the driver's presence gate.

**Do not touch.** `specfuse/monitor/` entirely. `specfuse/loop/` is **read and
imported, never edited** — criterion 8 imports `emit_escalation` from
`specfuse/loop/escalation.py` and calls it unmodified; changing anything under
`specfuse/loop/` is out of bounds and is an escalation, not a fix. Note that a
squash touching `specfuse/loop/` would also halt the driver for a restart, which
is a second reason the import must stay an import.
`specfuse/agent/state.py` and `specfuse/agent/budget.py`: T02's
snapshot and T03's budget are consumed, not edited; `record_tokens` already
exists with the right shape, so wiring it needs no change to `budget.py`. Do not
weaken, rewrite, or delete any existing test in `tests/test_agent_run.py`,
`tests/test_agent_budget.py`, or `tests/test_agent_state.py` — gate 1's tests are
the regression oracle for criterion 4 and must pass unmodified. The sibling
gate-2 WU files (`WU-06`…`WU-08`) and their provider modules. The driver owns all
git; this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.run import KIND_TRIAGE, KIND_ESCALATION_ANSWER, default_providers; print(default_providers)"`
and `python3 -c "import specfuse.agent.providers"`. Plus, for criterion 8:
`python3 -c "import specfuse.agent.run as r, inspect; assert 'emit_escalation' in inspect.getsource(r); print('wired')"`.

**Escalation triggers.** If preserving gate 1's ordering (criterion 4) turns out
to require editing `budget.py` or `state.py`, stop and say which one and why —
that is a gate-1 design defect surfacing, not a licence to widen this unit's
boundary. If expressing the order table needs a new `agent-policy.yml` key, name
the key and stop: policy schema changes are a plan change, not a WU detail. If
`run_agent` cannot record spend without a provider reporting it — that is,
if the only honest number is one the provider does not have — say so and stop
rather than inventing an estimate; a fabricated token count is worse than an
inert cap, because it makes the cap look real.

For criterion 8 specifically: **do not compose the six escalation parts inside
`run_agent`.** `validate_escalation_body` requires two numbered options, and a
loop that has only an item ID and a reason string cannot produce two real ones —
it would be inventing choices nobody identified, which is the same failure as
authoring the operator's own justification. The payload comes from the provider
that knows the situation, or no issue is filed and criterion 9's summary-only
path reports that honestly. If wiring `emit_escalation` appears to require the
loop to author any of the six parts, stop and say which part and why.
