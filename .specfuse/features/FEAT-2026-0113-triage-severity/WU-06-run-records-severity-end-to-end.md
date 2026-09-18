---
id: FEAT-2026-0113/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/agent/providers/triage.py
  - tests/test_triage_severity_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.20.1
started_at: 2026-09-18T02:38:49.341086+00:00
duration_seconds: 163.178
cost_usd: 0.822717
input_tokens: 40
output_tokens: 14943
---

# T06 — a run records severity, and never disturbs a repository's own severity labels

**Objective.** `TriageProvider.execute` reads the rubric once per run, provisions
the four labels only where the repository declares no severity scheme of its own,
threads the rubric through classification into the decision, and turns the gate's
`feature_oracle` green on both repository shapes.

**Context.** This is the unit that turns gate 2's `feature_oracle` green
(`/authoring-work-units` §14). It is **not** a tracer bullet and may not stub
anything: T03, T04 and T05 land every layer it wires, each separately tested, and
a stub here would be the hollow pass §9 exists to catch.

`GATE-02.md` left the drafting agent to say whether the end-to-end proof belongs
at `apply_triage` or one level up. It belongs here: `apply_triage` never reads a
label rubric, so it cannot observe which repository shape it is in, and the
non-interference contract is invisible from there.
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
2. `test_repository_with_its_own_labels_is_not_interfered_with`: with an injected
   runner whose label listing returns described `severity:*` labels, the run issues
   **zero** `gh label create` calls and no call that would rewrite a label
   description — asserted by argv over the whole sequence, not by absence of a
   single string. This replaces the withdrawn opt-out equality and is now the
   contract that keeps a repository's own severity scheme intact; weakening it to
   "does not appear to change labels" is not a move this unit has.
2b. `test_severity_recorded_when_repository_defines_none`: with an injected runner
   whose label listing returns no `severity:*` label, the run provisions the four
   labels through the `gh label create … --force` shape **before** the first
   `--add-label severity:<value>` call, and records severity exactly as in
   criterion 1. Ordering is asserted, because a label added before it exists fails
   (#3244).
3. Both the listing and any provisioning are once per `execute` run, not once per
   issue: a run over three untriaged issues issues exactly one `gh label list`, and
   at most one `gh label create` per label across the whole run.
4. A failing label listing, or an absent `gh` binary, leaves the run classifying
   and writing exactly as it does today — no severity, no raise, and **no label
   creation attempted** — which is T03's fail-soft `{}` observed at run level. This
   is the degradation path, and after the arm-checkpoint revision it is the only
   branch that still produces today's write sequence.

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

**Escalation triggers.** If criterion 2's non-interference assertion cannot be made
to hold — if a run against a repository declaring its own severity scheme issues any
`gh label create`, or rewrites any description it did not author — stop and
escalate. That is the contract protecting an operator's existing labels, and the
measured case is real: `severity:critical` / `major` / `minor`, all three described,
predating the policy. If wiring the rubric through requires
editing a module T03–T05 own, stop rather than reaching across the boundary.
