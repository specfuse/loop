---
id: FEAT-2026-0247/G1-CLOSE
type: close
status: pending
attempts: 0
judge_edit_acknowledged:
  paths:
    - produces_driver_helper
    - specfuse/loop/agent_policy.py
    - specfuse/loop/arm_eval.py
    - specfuse/loop/data/schemas/driver-event.schema.json
    - specfuse/loop/gate_eval.py
    - specfuse/loop/ids.py
    - specfuse/loop/lint_plan.py
    - specfuse/loop/loop.py
    - specfuse/loop/upgrade_merge_gate.py
  reason: "Reviewed the diff; pattern swaps and alias lookup, no guard weakened"
planned_cost_usd: 5.00
auto_close_disabled: true
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: a repo that sets `ids.key` allocates and uses
`FEAT-<KEY>-YYYY-NNNN` on every loop surface, a repo without one is unchanged, and the
core-owned grammar is widened and vendored.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and that no `unittest.skip` survives in
   `tests/test_keyed_feature_ids_end_to_end.py`.
2. Measured, not restated: `grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/` returns only
   `specfuse/loop/ids.py` (quote the output).
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`, including T07's operator wait.
4. "What the loop did NOT verify" names, at minimum: key uniqueness across repos (by
   convention only), a real second repository adopting a key (post-merge checklist), the
   lexical name-sort sites (PLAN Known limits), and a real full rename of an existing
   repository with `--all` (only temporary-repository fixtures ran) — each with where it actually gets
   checked.
5. `CHANGELOG.md`'s Unreleased section carries the user-visible change: the optional
   `ids.key`, the keyed form, `ids next`, `ids migrate --planned-only`, the opt-in
   `ids migrate --all` full rename with its alias map, and that nothing changes for a repo
   without a key.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than docs. Other features. This
repository's own `ids.key` (post-merge, operator's decision).

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a second copy of the feature-ID pattern
outside `ids.py`: record `not_met` with a follow-up.
