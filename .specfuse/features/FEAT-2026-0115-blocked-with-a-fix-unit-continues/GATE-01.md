---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b"
cost_budget_usd: 40.00
---

# Gate 1 — a block that names its fix unit continues the gate

## Definition of done

A work unit whose session reports `status: blocked` with `blocked_next:` naming
a drafted fix unit file does not stop the gate: the driver validates the draft,
inserts it into the gate ahead of the blocked unit, flips it to `pending`,
re-arms the blocked unit behind it, records a `fix_unit_inserted` event and a
progress line, commits the bookkeeping, and dispatches the fix unit next — with
no `human_escalation`. A draft the stop classes refuse, a third insertion for
the same unit, or a feature under `review` escalates as today with the reason
named in the brief.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It drives `loop.run()` with a stubbed
dispatch: the first dispatch of T01 writes `WU-05-fix.md` (`status: draft`,
`provenance: agent`, five sections) and returns a blocked RESULT with
`blocked_next: {kind: fix_unit, file: WU-05-fix.md, id: FEAT-X/T05}`; the oracle
asserts the next dispatch is T05, then T01 again, that the feature ends with
both `done`, that `events.jsonl` carries `fix_unit_inserted` and no
`human_escalation`, and that `PLAN.md`'s graph lists T05 with T01 depending on
it.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged (feature-local `LEARNINGS-pending.md`).
- Documentation reflects what was actually built, canonical and mirror.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session.

## The sites and the switch

| surface | today | after this gate |
| --- | --- | --- |
| `agent_reported_blocked` handler in `run()` | reset tree, `blocked_human`, escalate, return 1 | if `blocked_next:` validates: insert, re-arm, continue; else today |
| `REPLAN_OPTION_SCOPE["agent_reported_blocked"]` | no option offered | brief names the drafted fix and the arming command when insertion was refused |
| `gate_eval.evaluate_auto_close` | reads `replan` as off-plan | also reads `fix_unit_inserted` |
| `verification.yml` `defaults.fix_unit_insertion` | absent | `false` ignores the key; absent means on |
| `defaults.max_fix_units_per_unit` | absent | default 2 |

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T01 changes what a
  blocked RESULT does. Before arming, run
  `python3 -m unittest tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option tests.test_replan_end_to_end tests.test_arm_eval tests.test_arm_txn -v -b`
  on the tree this gate starts from and paste the result here; T01's criterion
  4 names the modules that must keep passing unchanged.
- **Flag-scope table (§3).** The table above is it.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
