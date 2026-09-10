---
id: FEAT-2026-0110/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
model: opus
effort: high
gate_set: plannext
driver_version: 0.18.0
started_at: 2026-09-10T00:47:07.579086+00:00
duration_seconds: 528.45
cost_usd: 5.582307
input_tokens: 108
output_tokens: 41745
---

# Close gate 1 — language-aware narrow test selection

**Objective.** Fold the retrospective, the durable lessons and the
documentation pass into one session, record what this gate actually proved, and
leave the terminal verdict to the judge.

**Context.** FEAT-2026-0110/G1-CLOSE, the terminal gate of a single-gate
feature. Binding: `.specfuse/rules/close-discipline.md` §§1–5. The required
section skeleton is scaffolded at dispatch — do not hand-copy heading literals
from anywhere; `specfuse lint --closing` is the check.

This is a terminal gate, so the verdict that advances the feature is written by
a fresh judge session reading `## Measurements`, the gate's definition of done,
the per-criterion state and the diff — never this session's own prose. Say what
was measured; do not say what verdict to write.

**Acceptance criteria.**

1. `## Measurements` records the gate's `feature_oracle` verdict as
   `### feature_oracle: PASS` or `### feature_oracle: FAIL`, from an actual run
   of `python3 -m unittest tests.test_language_aware_narrow_selection -v`.
2. `## Measurements` also records, for each of the three shapes the gate
   claims — Maven `class_name`/comma, Gradle `item_template` repeated flag, JS
   `path` — the resolved narrow command as a literal string, so the judge can
   read what the feature actually produces rather than that tests passed.
3. `## Cost analysis` reconciles each WU's `planned_cost_usd` against the
   `attempt_outcome` events in `events.jsonl`, with the delta stated per WU.
4. `## What the loop did NOT verify` lists the changed-file half (out of scope,
   still `tests/`-shaped, contract recorded in PLAN.md's scope boundary) and
   the consumer wall-clock claim from #3281 (measurable only in that
   consumer's repo, so a post-merge observation), each with the criterion, the
   reason, and where it actually gets checked — or the explicit
   `(nothing — every acceptance criterion was verified in-loop)` line if
   neither applies.
5. Durable lessons are promoted to `.specfuse/LEARNINGS.md`, or the section
   states explicitly that this gate produced none.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal
flip via `fire_terminal_flips`, gated on the judge's verdict. The three
substantive WU files' bodies. `.specfuse/verification.yml`. Plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `close` type's gate set, then `specfuse lint --closing`
and the gate's `feature_oracle`. The broad tier is the driver's, once per gate —
never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the `feature_oracle`
does not pass at close time (a terminal gate whose own definition of done is
red is not a verdict to write, it is a gate to reopen); or if the cost
reconciliation cannot be built because `events.jsonl` carries no
`attempt_outcome` for a WU that reports `done`.
