---
id: FEAT-LOOP-2026-0251/G1-CLOSE
type: close
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: the three diff-only deliverable refusals run before
verification (with an opt-out), their retry note lists the changed paths, and `specfuse lint`
warns on a `produces:` path its unit never mentions.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven
   and by which test, and that no `unittest.skip` survives in
   `tests/test_fail_fast_deliverables.py`. It lists every pre-existing test whose assertion on
   the order of verify and guard was changed (clause 6), with why.
2. Each consumer-visible change (the new order, `defaults.fail_fast_deliverables`, the retry
   note's path list, the lint WARN) is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0251`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`, and
   reports T04's measured warning rate.
4. "What the loop did NOT verify" names, at minimum: a real project whose gates write a declared
   deliverable (the opt-out is tested only with stubs), and real refused attempts on the new
   build (every attempt in this feature ran on a build pinned before the change).
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or an early refusal whose outcome or failure class
differs from the late one for the same input: record `not_met` with a follow-up.
