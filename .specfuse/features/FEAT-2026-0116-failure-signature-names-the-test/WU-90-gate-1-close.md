---
id: FEAT-2026-0116/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
model: sonnet
effort: high
gate_set: plannext
driver_version: 0.25.0
started_at: 2026-09-26T18:21:27.659352+00:00
duration_seconds: 530.888
cost_usd: 3.06685
input_tokens: 144
output_tokens: 50486
---

# Close gate 1 — the failure signature names the failing test

**Objective.** Fold the retrospective, the durable lessons and the documentation
pass into one session, record what this gate actually proved, and leave the
terminal verdict to the judge.

**Context.** FEAT-2026-0116/G1-CLOSE, the terminal gate of a single-gate feature.
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
   of `python3 -m unittest tests.test_failure_signature_names_the_test -v -b`.
2. `## Measurements` also records the output of
   `python3 -m specfuse.loop.replay_spin --failing-sets` over this repository's
   `.specfuse/features/*/events.jsonl`: historical `spinning_signature_repeat`
   escalations, how many would still fire, how many the replay could not
   classify.
3. `## Cost analysis` reconciles each WU's `planned_cost_usd` against the
   `attempt_outcome` events in `events.jsonl`, with the delta stated per WU.
4. `## What the loop did NOT verify` lists the two post-merge checklist items
   from PLAN.md, each with the criterion, the reason, and where it actually gets
   checked.
5. Durable lessons are staged to the feature's `LEARNINGS-pending.md`, or the
   section states explicitly that this gate produced none.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip.
The three substantive WU files' bodies. `.specfuse/verification.yml`. Plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `close` type's gate set, then `specfuse lint --closing` and
the gate's `feature_oracle`. The broad tier is the driver's, once per gate —
never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the `feature_oracle` does
not pass at close time; or if the cost reconciliation cannot be built because
`events.jsonl` carries no `attempt_outcome` for a WU that reports `done`.
