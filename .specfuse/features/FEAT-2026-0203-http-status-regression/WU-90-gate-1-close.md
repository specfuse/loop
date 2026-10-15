---
id: FEAT-2026-0203/G1-CLOSE
type: close
status: done
attempts: 1
verdict: met
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
gate_set: plannext
driver_version: 0.27.1
started_at: 2026-10-15T03:50:39.040765+00:00
duration_seconds: 234.002
cost_usd: 1.211677
input_tokens: 56
output_tokens: 25565
---

# Close gate 1 — a deployment that raises server-fault 4xx files one finding

**Objective.** Fold the retrospective, the durable lessons and the documentation
pass into one session, record what this gate actually proved, and leave the terminal
verdict to the judge.

**Context.** `FEAT-2026-0203/G1-CLOSE`, the terminal gate of a single-gate feature.
Binding: `.specfuse/rules/close-discipline.md` §§1–5. The required section skeleton
is scaffolded at dispatch; `specfuse lint --closing` is the check. The verdict that
advances the feature is written by a fresh judge session from `## Measurements`, the
gate's definition of done, the per-criterion state and the diff. Say what was
measured; do not say what verdict to write.

**Acceptance criteria.**

1. `## Measurements` records `### feature_oracle: PASS` or `FAIL` from an actual run
   of `python3 -m unittest tests.test_http_status_regression_end_to_end -v -b`.
2. `## Measurements` records that the adapter issues one query per check: the output
   of T01's `test_adapter_issues_one_query` and T04's
   `test_query_is_configuration_only`, so PLAN.md decision 5 is measured, not
   asserted.
3. `## Cost analysis` reconciles each WU's `planned_cost_usd` against the
   `attempt_outcome` events in `events.jsonl`, with the delta per WU.
4. `## What the loop did NOT verify` lists PLAN.md's post-merge live run and decision
   8's re-sighting residual, each with the criterion, the reason, and where it gets
   checked.
5. `CHANGELOG.md`'s `Unreleased` section carries an entry tracing to FEAT-2026-0203
   (the check type) and one tracing to #295 (the `stall_after` lint flip, classified
   `breaking` or `changed` with its migration note), and #295 is closed by
   reference.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` (the driver owns the terminal flip). The
substantive WU files' bodies. Any `specfuse/` source file: a source change found
necessary at close is a follow-up. `.specfuse/verification.yml`.

**Verification.** The `close` type's gate set, then `specfuse lint --closing` and the
gate's `feature_oracle`. The broad tier is the driver's.

**Escalation triggers.** Stop with `status: blocked` if the `feature_oracle` does not
pass at close time, or if the gate's diff shows a second `run_query` call in
`HttpStatusRegressionAdapter`: that contradicts PLAN.md decision 5 and is not a note
for the retrospective.
