---
id: FEAT-LOOP-2026-0248/G1-CLOSE
type: close
status: done
attempts: 1
judge_edit_acknowledged:
  paths:
    - specfuse/loop/agent_policy.py
    - specfuse/loop/ids.py
  reason: "Reviewed the diff; policy resolves aliases, ids additive, no guard weakened"
unsandboxed: true
unsandboxed_rationale: "Acceptance criterion 2 re-runs T05's --rehearse, which adds and removes a git worktree and runs the full suite in it; inside the sandbox that produced about 160 false errors in T05's dispatch. Same rationale as T05."
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
gate_set: plannext
driver_version: 0.30.0
started_at: 2026-10-29T19:57:52.322427+00:00
verdict: met
duration_seconds: 764.922
cost_usd: 1.080722
input_tokens: 54
output_tokens: 26443
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: after `ids migrate --all --apply` a repository is
valid, the rename can be rehearsed on a throwaway copy, and this repository's own full
suite passes a rehearsal of its rename with key `LOOP`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and that no `unittest.skip` survives in
   `tests/test_migrate_all_repo_stays_valid.py`.
2. Measured, not restated: re-run T05's rehearsal command (its narrowed prose scope) and quote its validation result
   and test summary line; record its exit status.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`.
4. "What the loop did NOT verify" names, at minimum: applying the rename to `main` (an
   operator decision), prose mentions that cite another repository's feature (the
   operator's `--exclude-id` choice), and GitHub/git-history references (alias map only).
5. `CHANGELOG.md`'s Unreleased section carries the user-visible change: post-apply
   validation, real-folder structural matching, scoped `--include-prose`, `--exclude-id`
   and `--rehearse`, and that this repository now sets `ids.key: LOOP`.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than docs. The real tree's feature
folders (no `--apply`).

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a rehearsal that does not exit zero: record
`not_met` with a follow-up.
