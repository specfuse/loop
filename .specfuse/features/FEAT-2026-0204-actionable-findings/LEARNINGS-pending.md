# Learnings pending — FEAT-2026-0204

- **A plan's enumerated deliverable list must be mapped, item by item, into unit
  criteria at arm time, because the feature oracle can only assert what the
  criteria name.** `FEAT-2026-0204`'s "Diagnostic context" listed what each check's
  finding must carry; `T08` restated the `heartbeat` and `queue-stalled` entries
  from memory and left out the heartbeat's earliest heartbeat and the queue's last
  completed message. Every unit met every criterion and the oracle was green, and
  only the close's table comparing a rendered fixture against the plan's list
  showed two items missing. Generalizable: when a `PLAN.md` section is a checklist
  the gate's definition of done refers to ("the sections the plan names"), arm time
  should diff that checklist against the criteria and either assert each item or
  record its removal in the plan.

- **A unit that changes what an adapter needs to emit a finding can break tests it
  does not own; name the dispatch-level tests in its verification.** `T04` made `heartbeat` need an earlier heartbeat to evaluate, and
  `test_monitor_cli.TestAllCheckTypesDispatch`, whose heartbeat stub had no history,
  went red. The narrow tier ran only the unit's own modules, so the failure surfaced
  at the gate's broad run (the 16:03Z `broad_run_result`) and cost a repair commit
  and a second broad run (`ab4c8b1`).
