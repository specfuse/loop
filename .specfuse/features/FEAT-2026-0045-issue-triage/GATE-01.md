---
gate: 1
status: awaiting_review
cost_budget_usd: 23.00
baseline:
  sha: c62ee5ac0261121709d90c19fe4c8829db80799c
  probed_at: 2026-08-09T21:46:31.563443+00:00
  failing: []
---

# Gate 1 — inbound issues get a category, a route, and a durable record

## Definition of done

A repository can scan its open issues, obtain a per-issue category and route, and have
that decision recorded in an authoritative body marker projected to a human-visible
label — interactively through `/triage-issues`, or headlessly behind an explicit `auto`
argument that applies only high-confidence decisions.

Verified in-loop over fixture issue JSON with an injected runner. No work unit in this
gate calls live GitHub; see PLAN.md's sandbox constraint for why that is a design
requirement rather than a shortcut.

Concretely:

- Every implementation work unit in this gate is `done`.
- `specfuse/loop/triage.py` exists and exports the closed category vocabulary, the
  category→route map, the marker render/parse pair, and the untriaged scan.
- `apply_triage` writes marker-first, projects the label best-effort, is idempotent on
  re-run, and honours the `auto` argument.
- `/triage-issues` exists at the canonical plugin path and is vendored in sync.
- The terminal close is written: retrospective, lessons, docs, roadmap reconciliation,
  and the terminal verdict with its hedged follow-up record.

`cost_budget_usd` is $23.00 — the $18.00 WU sum plus one re-attempt of the largest WU,
per `planning-discipline.md` §5's corollary.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This is the feature's only gate, so there is no next gate to arm. The checks below apply
to arming *this* gate:

- **Flag-scope table (§3).** T02 introduces the `auto` behaviour flag and must carry a
  flag-scope table. Check it against the headline claim: *"`auto` applies only
  high-confidence categorisations and leaves the rest for human triage."* Specifically
  confirm the table marks the marker write as **ungated** — a dial that skipped the
  marker would re-triage every low-confidence issue on every run, forever.
- **Runtime probe for a default/severity flip (§4).** Not applicable. `auto` defaults to
  `False`, which is today's behaviour; no default or severity is flipped.
- **Escalation-predicate satisfiability (§2).** Not applicable. No check is raised to
  `ERROR` and no "zero issues" predicate is asserted.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
