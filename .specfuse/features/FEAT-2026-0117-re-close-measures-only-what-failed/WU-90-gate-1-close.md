---
id: FEAT-2026-0117/G1-CLOSE
type: close
status: done
attempts: 1
verdict: met
planned_cost_usd: 5.00
auto_close_disabled: true
duration_seconds: 324.404
cost_usd: 1.6891
input_tokens: 90
output_tokens: 25038
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-09-26T19:49:05+00:00
    prior_status: blocked_human
    prior_attempts: 1
    prior_cost_usd: 1.597012
    prior_duration_seconds: 591.147
    reason: "The close was right: T02H's events were missing because an operator git checkout discarded them mid-run. Restored from the unit's driver-stamped frontmatter (marked restored in the payload); nothing else changed."
cumulative_cost_usd: 1.597012
cumulative_duration_seconds: 591.147
cumulative_input_tokens: 74
cumulative_output_tokens: 27173
cumulative_attempts: 1
folded_through_re_arm: 1
model: sonnet
effort: high
gate_set: plannext
driver_version: 0.25.0
started_at: 2026-09-26T19:49:06.452425+00:00
---

# Close gate 1 — a re-close measures only what failed

**Objective.** Fold the retrospective, the durable lessons and the documentation
pass into one session, record what this gate actually proved, and leave the
terminal verdict to the judge.

**Context.** FEAT-2026-0117/G1-CLOSE, the terminal gate of a single-gate feature.
Binding: `.specfuse/rules/close-discipline.md` §§1–5. The required section
skeleton is scaffolded at dispatch — do not hand-copy heading literals;
`specfuse lint --closing` is the check. This is a terminal gate, so the verdict
that advances the feature is written by a fresh judge session reading
`## Measurements`, the gate's definition of done, the per-criterion state and the
diff — never this session's own prose. Say what was measured; do not say what
verdict to write.

**Acceptance criteria.**

1. `## Measurements` records the gate's `feature_oracle` verdict as
   `### feature_oracle: PASS` or `### feature_oracle: FAIL`, from an actual run
   of `python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b`.
2. `## Measurements` also records, if this close is itself a re-close, the
   line `carried forward: N criteria, re-measured: M` and this close's
   `cost_usd` beside the first close's from `events.jsonl` — or the literal
   line `first close of this gate; nothing carried`.
3. `## Cost analysis` reconciles each WU's `planned_cost_usd` against the
   `attempt_outcome` events in `events.jsonl`, with the delta stated per WU.
4. `## What the loop did NOT verify` lists the two post-merge checklist items
   from PLAN.md, each with the criterion, the reason, and where it actually gets
   checked.
5. Durable lessons are staged to the feature's `LEARNINGS-pending.md`, or the
   section states explicitly that this gate produced none.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip.
The four substantive WU files' bodies. `.specfuse/verification.yml`. Plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `close` type's gate set, then `specfuse lint --closing` and
the gate's `feature_oracle`. The broad tier is the driver's, once per gate —
never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the `feature_oracle` does
not pass at close time; or if the cost reconciliation cannot be built because
`events.jsonl` carries no `attempt_outcome` for a WU that reports `done`.
