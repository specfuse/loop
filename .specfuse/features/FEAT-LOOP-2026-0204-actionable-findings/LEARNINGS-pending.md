# Learnings pending — FEAT-LOOP-2026-0204

- **A plan's enumerated deliverable list must be mapped, item by item, into unit
  criteria at arm time, because the feature oracle can only assert what the
  criteria name.** `FEAT-LOOP-2026-0204`'s "Diagnostic context" listed what each check's
  finding must carry; `T08` restated the `heartbeat` and `queue-stalled` entries
  from memory and left out the heartbeat's earliest heartbeat and the queue's last
  completed message. Every unit met every criterion and the oracle was green, and
  only the close's table comparing a rendered fixture against the plan's list
  showed two items missing. Generalizable: when a `PLAN.md` section is a checklist
  the gate's definition of done refers to ("the sections the plan names"), arm time
  should diff that checklist against the criteria and either assert each item or
  record its removal in the plan.

  > **Accepted 2026-10-17** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0204/G1-CLOSE]`.
- **A unit that changes what an adapter needs to emit a finding can break tests it
  does not own; name the dispatch-level tests in its verification.** `T04` made `heartbeat` need an earlier heartbeat to evaluate, and
  `test_monitor_cli.TestAllCheckTypesDispatch`, whose heartbeat stub had no history,
  went red. The narrow tier ran only the unit's own modules, so the failure surfaced
  at the gate's broad run (the 16:03Z `broad_run_result`) and cost a repair commit
  and a second broad run (`ab4c8b1`).

  > **Accepted 2026-10-17** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0204/G1-CLOSE]`.
- **A stub-transport oracle proves the shape of a query and a body, never that the
  backend accepts the query, so a feature that writes KQL needs one opt-in live
  render before its close, not only after release.** FEAT-LOOP-2026-0204's `error-logs`
  and `http-5xx` queries passed the checked-in schema reference, the one-query
  assertion and every context test, and still did not parse in App Insights (a `\{`
  inside an ordinary KQL string). Rendering real findings against the consumer's
  workspace with the opt-in live tests also showed "First seen" was the harvest time
  rather than the first occurrence, and a `dlq` exception cut off its handler frame
  behind ten framework frames. None of the three is visible to a fixture-fed test.
  When a unit emits a query or renders evidence a human will read, its close should
  run the opt-in live tests, or name in Deferred verification why not.

  > **Accepted 2026-10-17** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0204/G1-CLOSE]`.

