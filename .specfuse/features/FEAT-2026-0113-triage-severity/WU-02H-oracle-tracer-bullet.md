---
id: FEAT-2026-0113/T02H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces:
  - tests/test_triage_severity_end_to_end.py
---

# T02H — tracer bullet: the gate oracle exists and runs green

**Objective.** Create `tests/test_triage_severity_end_to_end.py` so gate 2's
`feature_oracle` runs green on the thinnest end-to-end path, before any unit that
must be verified against it.

**Context.** Inserted after T03 and T04 both escalated `spinning_signature_repeat`
with the identical signature on all four attempts:

```
ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest...)
ModuleNotFoundError: No module named 'tests.test_triage_severity_end_to_end'
```

That module is T06's `produces:` file and is in both units' Do-not-touch lists, so
neither could create it and neither could pass. The cause is a collision between
how this gate was drafted and how the driver verifies: `GATE-02-REVIEW.md` states
"the gate's `feature_oracle` is red until T06 lands", while `loop.py`'s verify
path states "the `feature_oracle` append below is untiered — it runs on every
attempt regardless, by FEAT-2026-0101's contract." Both cannot hold. The
methodology's answer is the walking skeleton: the gate's first implementation unit
wires the thinnest path end to end and turns the oracle green, so every later unit
has a real oracle to run against.

**This unit is the gate's tracer bullet, and the only one.** Stubs are permitted
here and nowhere else in gate 2 — T03, T04, T05 and T06 each ship a complete,
separately-tested layer, and a stub in any of them is the hollow pass the guard
exists to catch.

**What "thinnest path" means here.** The oracle's subject is
`TriageProvider.execute` (`specfuse/agent/providers/triage.py:208`) — the one
place a run both reads a repository's labels and applies a decision. Severity does
not exist on that path yet, and this unit does not add it. What it wires is the
**harness**: an injected runner, a triage decision driven through `execute`, and
assertions on the `gh` argv sequence that run actually issues today. T06 extends
this module with the severity assertions its own criteria name; it does not
rewrite the harness.

Pinning today's run-level write sequence is not filler — it is the baseline every
later criterion in this gate compares against, including T06's non-interference
assertion.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_triage_severity_end_to_end -v -b` — gate 2's
   `feature_oracle` verbatim — exits non-zero on HEAD before this unit runs
   (`ModuleNotFoundError`) and exits **zero** after it.
2. The module drives `TriageProvider.execute` end to end with an injected runner,
   never a live `gh` call and never a network read, following the double shape
   already used in `tests/test_agent_provider_triage.py`.
3. It asserts the `gh` argv sequence a run issues **today** for one untriaged
   issue: the marker written by `gh issue edit --body`, then the category label by
   `--add-label`, in that order. Order is asserted, not merely presence — this is
   the same precedence claim `PLAN.md`'s **Record precedence** section makes, and
   T06's criterion 1 extends it to severity.
4. No severity assertion appears in this unit. Severity is not on the path yet,
   and a test asserting a behaviour no unit has built is a hollow pass whichever
   way it is written.
5. The full `tests` gate passes: this module is additive and edits no existing
   test.

**Do not touch.** Every source file under `specfuse/` — this unit adds a test and
changes no behaviour. `specfuse/loop/labels.py` (T03), `specfuse/loop/triage.py`
(T04), `specfuse/agent/triage_invoke.py` (T05),
`specfuse/agent/providers/triage.py` (T06). `GATE-02.md`'s `feature_oracle` line,
which this unit satisfies rather than edits. Gate 1's units and
`GATE-01-CRITERIA.md`, which are sealed history.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` module. Plus, in this unit's session, the
gate's `feature_oracle` exactly as `GATE-02.md` declares it, and
`python3 -m unittest tests.test_agent_provider_triage -b`.

**Escalation triggers.** If the thinnest end-to-end path cannot be made green
without changing a source file under `specfuse/`, stop — that means the oracle's
subject is wrong and the gate boundary needs re-cutting, not a widened unit. If
making it green appears to require asserting severity behaviour that no unit has
built, stop: that is criterion 4 failing, and a green oracle bought that way is
worth less than a red one.
