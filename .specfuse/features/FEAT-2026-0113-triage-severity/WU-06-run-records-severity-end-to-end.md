---
id: FEAT-2026-0113/T06
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/agent/providers/triage.py
  - tests/test_triage_severity_end_to_end.py
---

# T06 — a run records severity, and a repository without the labels sees no change

**Objective.** `TriageProvider.execute` reads the rubric once per run, threads it
through classification into the decision, and the gate's `feature_oracle` goes
green on both halves of the milestone.

**Context.** This is the unit that turns gate 2's `feature_oracle` green
(`/authoring-work-units` §14). It is **not** a tracer bullet and may not stub
anything: T03, T04 and T05 land every layer it wires, each separately tested, and
a stub here would be the hollow pass §9 exists to catch.

`GATE-02.md` left the drafting agent to say whether the end-to-end proof belongs
at `apply_triage` or one level up. It belongs here: `apply_triage` never reads a
label rubric, so it cannot observe the opt-out half of the milestone at all.
`TriageProvider.execute` (`specfuse/agent/providers/triage.py:208`) is the one
place a run both reads the repository's labels and applies a decision.

`PLAN.md`'s **Record precedence** is what criterion 1 asserts at run level: marker
carrying `severity=` written first, `severity:<value>` label projected second.

**Acceptance criteria.**

1. `tests/test_triage_severity_end_to_end.py::SeverityEndToEnd::test_severity_recorded_when_labels_are_defined`
   fails on HEAD before this unit runs and passes after: with an injected runner
   whose label listing returns described `severity:*` labels and whose
   classification answer names a severity, the run issues the
   `gh issue edit --body` call carrying `severity=` **before** the
   `--add-label severity:<value>` call.
2. `test_no_severity_when_repository_defines_none`: with an injected runner whose
   label listing returns no `severity:*` label, the full `gh` argv sequence the run
   issues — apart from that one read-only listing call — equals the sequence
   today's code issues for the same inputs. This equality is the opt-out contract;
   it is asserted, not described.
3. The rubric is read once per `execute` run, not once per issue: a run over three
   untriaged issues issues exactly one label listing.
4. A failing label listing, or an absent `gh` binary, leaves the run classifying
   and writing exactly as it does today — no severity, no raise — which is T03's
   fail-soft `{}` observed at run level.

**Do not touch.** `specfuse/loop/labels.py` (T03), `specfuse/loop/triage.py`
(T04), `specfuse/agent/triage_invoke.py` (T05). The escalation payloads and the
`_is_agent_escalation` skip in `providers/triage.py` — this unit adds severity to
the decision path and changes no routing. `AgentSnapshot.triage_auto` and the
low-confidence-under-auto downgrade, which stays `apply_triage`'s. Gate 3's
backfill: an issue already carrying a severity-less marker is out of scope here
and stays skipped exactly as today.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session, the
gate's `feature_oracle` as declared in `GATE-02.md`, and
`python3 -m unittest tests.test_agent_provider_triage tests.test_triage_skips_agent_escalations tests.test_agent_policy_triage_dial -b`.

**Escalation triggers.** If criterion 2's argv equality cannot be made to hold —
if any write differs for a repository that defines no `severity:*` label — stop
and escalate. That equality is the opt-out contract and the reason no `severity:*`
entry is added to `LABEL_REGISTRY`; weakening the criterion to "behaves
equivalently" is not a move this unit has. If wiring the rubric through requires
editing a module T03–T05 own, stop rather than reaching across the boundary.
