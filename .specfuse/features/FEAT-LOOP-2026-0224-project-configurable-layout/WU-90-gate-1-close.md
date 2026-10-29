---
id: FEAT-LOOP-2026-0224/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
model: sonnet
effort: high
gate_set: plannext
auto_close_disabled: true
driver_version: 0.29.1
started_at: 2026-10-28T01:50:24.814820+00:00
verdict: met
duration_seconds: 252.141
cost_usd: 1.576418
input_tokens: 76
output_tokens: 30908
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: an optional `.specfuse/layout.yml` declares a
project's decision records, `lint_roadmap`, `block-feature`, the roadmap template and
the blocker wording follow it, and a project without one is unchanged.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and that no `unittest.skip` survives in
   `tests/test_layout_end_to_end.py`.
2. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`, and records whether the expected `judge_editing` halt (PLAN
   decision 3) fired and what it cost.
3. The goldens' integrity is re-checked: `git log` shows the `lint_roadmap` goldens
   committed before T05's first edit to `lint_roadmap.py`, and no golden file changed
   after that.
4. "What the loop did NOT verify" names, at minimum: the umbrella
   `specfuse layout get` delegated command (cross-repo, post-merge, PLAN decision 2)
   and a real entries-style consumer project — each with where it actually gets
   checked (the PLAN post-merge checklist).
5. `CHANGELOG.md`'s Unreleased section carries the user-visible change, including the
   fragment-link behaviour change for projects without a layout.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than docs. Other features.

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a changed no-layout golden: record
`not_met` with a follow-up.
