---
id: FEAT-2026-0100/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 6.00
model: opus
effort: high
oracle_env: macos_local
verdict: not_met
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0100-separate-judge-session/RETROSPECTIVE.md
gate_set: plannext
driver_version: 0.15.0
started_at: 2026-09-06T13:31:27.751849+00:00
duration_seconds: 2954.222
cost_usd: 8.315684
input_tokens: 184
output_tokens: 67162
---

# Gate 1 close — demonstrate the judge on fixtures, measure, and let the judge decide

**Objective.** Terminal close of FEAT-2026-0100: demonstrate each behaviour
in `GATE-01.md`'s definition of done on fixtures with an injected runner, in
this session, and record the measurements. This close is itself judged by
the mechanism it ships; measure, do not decide.

**Context.** Depends on T01-T05. Binding: `.specfuse/rules/close-discipline.md`
as T04 rewrote it. The driver owns the terminal `PLAN.md status` flip and,
from T02 on, dispatches the judge after this close's squash; the verdict
field is written by the driver from the judge's result. Baseline numbers are
in `PLAN.md` § Notes. Run `specfuse lint --closing` before reporting
`complete`.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table: the exit status of each of the eight fixture demonstrations in `GATE-01.md`, each next to the command run in this session; the lint sweep's ERROR count over every feature folder; `PLAN.template.md`'s `autonomy_default` value; whether this close's own dispatch was followed by a `judged` event in `events.jsonl` (read it after your squash is not possible; state what the driver will do and let the retrospective's reader confirm it from the event).
- `## Retrospective`: what the judge's evidence bundle lacked when the fixtures were built, if anything, and whether the eight behaviours were demonstrable without a live `gh` or network call.
- `## Cost analysis` reconciling `planned_cost_usd` ($29.00, per-WU) against `events.jsonl`, delta and restart count named.
- `## Consumer-visible contract changes`: a judge dispatch on every terminal close, the `judged` event, `judge_disabled`, `autonomy_default: auto` as the drafted default, one new lint ERROR; enumerate and add the `CHANGELOG.md` entry.
- `## Lessons`: one entry at most.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, templates, skills (T01-T05 own them);
`.git/`, secrets. This WU writes only its close record.

**Verification.** The `plannext` gate set plus the oracles above.

**Escalation triggers.** Emit `status: blocked` if a fixture demonstration
needs a live `gh` or a network call; every behaviour is designed to be shown
with an injected runner.
