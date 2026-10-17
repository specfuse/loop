---
id: FEAT-2026-0205/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
model: sonnet
effort: high
gate_set: plannext
verdict: met
driver_version: 0.28.2
started_at: 2026-10-17T19:14:33.385632+00:00
duration_seconds: 148.718
cost_usd: 0.806492
input_tokens: 48
output_tokens: 17387
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: a diagnosis carries a severity, labelled on the
finding, ordering autofix, with findings kept out of the bug lane.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and that no `unittest.skip` survives in the oracle
   module.
2. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`.
3. Per `[FEAT-2026-0204/G1-CLOSE]`, one opt-in live headless diagnosis of a fixture
   finding is run and its marker's severity recorded, or Deferred verification names
   why not; the deferred list also names the post-merge live check in `PLAN.md`.
4. `CHANGELOG.md`'s Unreleased section carries the user-visible change, and the docs
   T04 updated match the shipped behaviour.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than docs. Other features.

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a changed autofix eligibility decision:
record `not_met` with a follow-up.
