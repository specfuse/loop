---
id: FEAT-2026-0108/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0108-agent-lane-run-hygiene/RETROSPECTIVE.md
---

# Gate 1 close — demonstrate the six behaviours on fixtures, verdict

**Objective.** Terminal close of FEAT-2026-0108: demonstrate each behaviour in
`GATE-01.md`'s definition of done on fixtures with an injected runner, in this
session, and write `met` or `not_met`.

**Context.** Depends on T01-T06. Binding: `.specfuse/rules/close-discipline.md`.
The driver owns the terminal `PLAN.md status` flip. Baseline numbers are in
`PLAN.md` § Notes. On `not_met`, write `FOLLOW-UPS.md` with one entry per
failed criterion. The unattended run against a real repository is the
`## Post-merge checklist` in `PLAN.md`, not a criterion here. Run
`specfuse lint --closing` before reporting `complete`.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table, before and after: `spend=` occurrences, `--output-format` occurrences in agent invocations, declining-reason count, and the exit status of each of the six fixture demonstrations, each next to the command run in this session.
- `## Retrospective` answers whether the six units together would have changed the 2026-09-02 run's escalation mix, class by class, from the evidence in #3177-#3183.
- `## Cost analysis` reconciling `planned_cost_usd` ($37.00, per-WU) against `events.jsonl`, delta named.
- `## Consumer-visible contract changes`: a new declining reason and label, an optional `pr_number:` RESULT line, two new `budgets:` keys, per-item worktrees; enumerate and add the `CHANGELOG.md` entry.
- `## Lessons`: one entry at most.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** Source, tests, skills (T01-T06 own them); `.git/`, secrets.

**Verification.** The `plannext` gate set plus the oracles above.

**Escalation triggers.** Emit `status: blocked` if a fixture demonstration
needs a live `gh` or a network call; every behaviour above is designed to be
shown with an injected runner, and a close that needs the network has found a
unit that did not keep that promise.
