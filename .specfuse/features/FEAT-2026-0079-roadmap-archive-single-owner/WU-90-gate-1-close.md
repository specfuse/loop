---
id: FEAT-2026-0079/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
---

# G1-CLOSE — Terminal close for gate 1

## Context

Terminal close for a single-gate feature: retrospective, lessons, docs and the terminal
verdict collapse into this one session. The required section skeleton is scaffolded at
dispatch — see `.specfuse/rules/close-discipline.md` §4 and the registry in
`specfuse/loop/closing_requirements.py`. Do not restate heading literals; `specfuse lint
--closing` is the check.

Do **not** flip `PLAN.md status` to `done` — `fire_terminal_flips` owns the terminal flip,
gated on `verdict_permits_terminal_flips`, on both the dispatched and auto-close paths.

## Acceptance criteria

1. `RETROSPECTIVE.md` carries a `## Cost analysis` heading — the literal heading
   `assert_cost_analysis_section_when_met` requires when the verdict is `met`; it is checked
   after dispatch, so omitting it costs a full re-attempt. Under it, cost analysis reconciles each WU's actual `cost_usd` against its `planned_cost_usd`
   ($4.50 / $4.50 / $5.00) using `events.jsonl` as the source, and against the gate's
   `cost_budget_usd` of $19.00.
2. **The settlement is staged into `.specfuse/LEARNINGS.md`** as the operator chose at
   drafting: when a skill and the driver implement one algorithm, the driver owns it and the
   skill delegates — with the reason the previous precedent (`[FEAT-2026-0010/G1]`) failed to
   hold, namely that it lived only in a retrospective nobody queried. Under
   `autonomy_default: review` the append goes to `.specfuse/LEARNINGS.md` directly; the
   `LEARNINGS-pending.md` staging route applies only under `auto`.
3. *What the loop did NOT verify* names, at minimum: that **an agent following the rewritten
   skill prose produces a correct archive on an unseen tree is unverified**. The guard proves
   the prose does not restate mechanics; it does not compose prose and code. State where that
   would actually get checked (a real `/roadmap-archive` run by an operator) rather than
   letting the green read as "the skill is proven" — `[FEAT-2026-0069/G2-CLOSE]`.
4. The retrospective records whether the per-feature `--auto` loop proved clumsy in practice,
   since that was the named trigger for the deliberately-deferred CLI `--auto` mode.
5. `specfuse lint --closing` exits 0 before this WU reports `complete`.

## Do not touch

- `PLAN.md` `status` — `fire_terminal_flips` owns the terminal flip; a manual flip is a second
  writer on terminal state.
- The roadmap row and its detail section — the driver's terminal-flip pass owns both.
- Any source file under `specfuse/` — this is a reflective session, not an implementation one.

## Escalation triggers

Stop and escalate rather than guessing:

- The verdict is anything other than `met` and the reason is not already recorded by T01/T02's
  own outcomes — a hedged verdict on a two-unit gate needs the operator, not a narrative.
- `specfuse lint --closing` cannot be made to exit 0 without weakening an acceptance criterion.

## Verification

- `specfuse lint --closing`
- `python3 -m unittest discover -s tests -v -b`
