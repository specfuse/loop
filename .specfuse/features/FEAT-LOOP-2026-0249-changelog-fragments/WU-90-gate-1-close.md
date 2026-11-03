---
id: FEAT-LOOP-2026-0249/G1-CLOSE
type: close
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
gate_set: plannext
judge_edit_acknowledged:
  paths:
    - .specfuse/rules/close-discipline.md
    - .specfuse/verification.yml
    - produces_driver_helper
    - specfuse/loop/arm_eval.py
    - specfuse/loop/changelog_fragments.py
    - specfuse/loop/closing_requirements.py
    - specfuse/loop/data/rules/close-discipline.md
    - specfuse/loop/ids.py
    - specfuse/loop/lint_closing.py
    - specfuse/loop/loop.py
  reason: "guards not weakened, single-file behavior unchanged"
driver_version: 0.31.1
started_at: 2026-11-03T13:06:22.977425+00:00
verdict: met
duration_seconds: 198.085
cost_usd: 1.131743
input_tokens: 52
output_tokens: 19755
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: concurrent PRs stop conflicting on the changelog in a
project that opts in, and every entry reaches the released section. T07 turned fragments on for
this repository, so this close writes its entry through the new flow.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven and
   by which test, and that no `unittest.skip` survives in `tests/test_changelog_fragments.py`.
2. Each consumer-visible change in the §3 enumeration is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0249`.
3. `CHANGELOG.md` on this branch has no entry tracing to `FEAT-LOOP-2026-0249`, so the driver's changelog guard
   passes on fragments alone; record the command and its output.
4. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`.
5. "What the loop did NOT verify" names, at minimum: GitHub's merge button (the oracle uses real
   `git merge`), and an adopter's own release script calling `collate`.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a guard that passes only because `CHANGELOG.md`
carries this feature's entry: record `not_met` with a follow-up.
