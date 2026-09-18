---
id: FEAT-2026-0113/T07
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/agent/severity_backfill.py
  - specfuse/agent/run.py
  - tests/test_severity_backfill_end_to_end.py
---

# T07 — the backfill mode exists end to end, for one issue

**Objective.** An explicit `--backfill-severity` mode that re-reads one
already-marked, severity-less issue, amends its marker and projects the label —
and that a normal conductor run never enters.

**Context.** `FEAT-2026-0113/T07`, gate 3. **This unit is the gate's tracer
bullet** (`/authoring-work-units` §14): it is the only unit in gate 3 permitted
to stub, and what it may stub is named below. It exists because `GATE-03.md`'s
`feature_oracle` is appended to **every** attempt's gate list, so a gate whose
oracle module lands last fails every earlier unit on `ModuleNotFoundError` —
that is what cost gate 2 four attempts (`RETROSPECTIVE.md`, gate 2; the
`FEAT-2026-0113/T02H` insertion).

Stubbable here, and only here: selection breadth (T08 owns the predicate — this
unit may take a single issue number), the marker amendment (T08 owns
`amend_marker_severity`; this unit carries a local `_amend_marker` that T09
deletes when it switches the call site over), and classification (T10 owns the
session — this unit may inject a fixed severity). **Not** stubbable: the write
order. `PLAN.md`'s **Record precedence** is binding — the marker's `severity=`
field is authoritative, the `severity:<value>` label is a projection, and the
marker is written first.

The mode is explicit by construction: `default_providers` gains nothing, so the
backfill path is unreachable from a conductor run. That is the property
`GATE-03.md` names, and criterion 2 is what proves it.

**Acceptance criteria.**

1. `tests/test_severity_backfill_end_to_end.py::SeverityBackfill::test_marked_issue_without_severity_is_amended_then_labelled`
   fails on HEAD before this unit runs (an absent module is red) and passes
   after: with an injected runner whose issue listing returns one open issue
   whose body carries `<!-- specfuse:triage category=bug confidence=high -->`
   and whose labels carry `triage:bug`, the mode run with `--apply` issues
   `gh issue edit <n> --repo <r> --body` carrying a marker with `severity=`
   **before** `gh issue edit <n> --repo <r> --add-label severity:<value>`,
   asserted on the order of the recorded calls and not on their presence.
2. `test_a_conductor_run_never_backfills`: with
   `specfuse.agent.severity_backfill.backfill_severity` patched to raise,
   `specfuse.agent.run.main` returns normally for an argv carrying no
   `--backfill-severity`, and no `severity_backfill` reference appears inside
   `default_providers` or `run_agent` — the backfill path is reachable only from
   `main()`'s own flag branch.
3. `GATE-03.md`'s `feature_oracle` command exits 0 at this unit's tree — the
   walking-skeleton property, stated as a check rather than as a promise.
4. `python3 -c "from specfuse.agent.severity_backfill import backfill_severity"`
   exits 0, and the one stub this unit is permitted to leave is named
   `_amend_marker` so T09's switch-over has a single symbol to delete (§9).

**Do not touch.** `specfuse/loop/triage.py` (T08). `specfuse/loop/labels.py` and
`specfuse/agent/triage_invoke.py` (gate 2's, read through their published names
only). `specfuse/agent/providers/triage.py` — the normal triage path is gate 2's
and no gate-3 unit edits it. In the conductor entry point this unit does edit,
the protected surfaces are the bodies of `run_agent` and `default_providers` and
every argument `_build_arg_parser` already declares: this unit adds one new flag
and one new branch in `main()`, and changes no existing line in those three.
`.specfuse/agent-policy.yml` and `rules.bugs.min_severity`.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_agent_provider_triage tests.test_triage_severity_end_to_end -b`
(gate 2's behaviour, unedited), and criterion 4's import check.

**Escalation triggers.** If wiring the mode appears to require a change inside
`run_agent` or `default_providers` — anything that makes backfill reachable from
a normal run — stop and escalate: "never part of a normal run" is the boundary
this gate's whole risk acceptance rests on. If the marker cannot be amended
without appending a second marker to the body, stop and escalate rather than
appending: an issue carrying two markers is read by whichever one
`_MARKER_RE.search` finds first, and every later gate-3 unit is scoped to
amendment, not to repair.
