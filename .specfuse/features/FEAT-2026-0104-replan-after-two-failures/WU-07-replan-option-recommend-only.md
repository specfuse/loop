---
id: FEAT-2026-0104/T07
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces_driver_helper:
  - replan_option_applies
produces:
  - tests/test_spinout_brief_replan_option.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-11T02:48:24.434318+00:00
duration_seconds: 433.518
cost_usd: 1.17822
input_tokens: 74
output_tokens: 21413
---

# Make re-planning the remaining gate the brief's default option — and only a recommendation

**Objective.** Give the brief its option set: re-planning the remaining gate
is option 1 and the recommendation, it names the units and the command, and
the driver performs no flip.

**Context.** FEAT-2026-0104/T07. `GATE-02.md` § "The question gate 1 left
open" settles execute-versus-recommend as **recommend only** and cites the
four pieces of gate-1 evidence; do not relitigate it here. The brief already
renders (T06); this unit owns parts 5 and 6 and the scope of which
escalations get it. Two facts from the probe recorded in `GATE-02-REVIEW.md`
shape the wording: the driver has *already* re-planned this unit once by the
time the brief prints, and that re-planned attempt already failed — so
option 1 is widening a spent remedy, not proposing a fresh one, and must say
so.

**Flag-scope table (`.specfuse/rules/planning-discipline.md` §3).** Every
`blocked_human` escalation reason in `loop.py`, enumerated by
`grep -n '"reason": "' specfuse/loop/loop.py`:

| Escalation reason | Offers re-plan? | Why |
|---|---|---|
| `spinning_detected` | yes | The unit met its own oracle three times and lost; a narrower unit is the remedy. |
| `spinning_signature_repeat` | yes | Same failure twice — the unit's shape, not the attempt. |
| `convergence_plateau` | yes | Progress stopped short of the oracle; re-scoping is what moves it. |
| `replan_unchanged_body` | yes | The unit-scoped re-plan produced nothing; widening is the next step, and only a human can authorise it. |
| `all_attempts_zero_token` | no | No session ever ran. A CLI, quota or connectivity fault; re-planning fixes nothing. |
| `deterministic_refusal_repeat` | no | `GATE-01.md` § "What this gate must not break" binds this to escalate where it does. |
| `produces_shape_invalid` | no | Pre-dispatch frontmatter refusal; nothing was attempted. |
| `spinning_reproduction_missing` | no | A re-arm gate, not a failure; the operator is mid-decision already. |
| `prep_halted` | no | Pre-dispatch halt, no session spawned. |
| `agent_reported_blocked` | no | The session named a boundary; its own `blocked_reason` is the better lead. |
| `human_step_required` | no | Not a spin-out; `format_human_unit_brief` owns it. |

**Acceptance criteria.**

- `tests/test_spinout_brief_replan_option.py` fails on HEAD before this
  unit's edits and passes after.
- Driving a real `loop.run()` to `spinning_detected`, the printed brief's
  option 1 is the re-plan of the remaining gate, part 6 recommends that same
  option by number, and part 1 states that the automatic re-plan already ran
  and its attempt failed.
- **Negative observation** (`.specfuse/rules/verification-discipline.md`):
  after that run, every remaining unit's `status` and `attempts` on disk are
  byte-identical to before the halt, and `events.jsonl` carries no second
  `replan` event. The brief recommends; it flips nothing.
- `replan_option_applies(reason)` decides the table above — one predicate the
  brief consults, so the scope is testable per reason rather than on one
  sampled path — and a test asserts its verdict for all eleven reasons.
- Every command the brief names is verified to exist against
  `.specfuse/skills/` before this unit reports complete
  (`/authoring-work-units` §8) — an invented command is worse than prose.

**Do not touch.** The re-plan trigger, `run_replan_turn`, and the attempt
accounting — gate 1 owns them and this unit changes no dispatch behaviour.
`format_human_unit_brief`. The sibling WU files in this gate.

**Verification.** Narrow tier for `implementation`: the `code` gates minus
`tier: broad`, plus
`python3 -m unittest tests.test_spinout_brief_replan_option tests.test_spinout_brief_end_to_end -v -b`
— T06's oracle must stay green. Symbol check (§9):
`python3 -c "from specfuse.loop.loop import replan_option_applies"`. Run the
full suite before reporting complete for the same reason T06 does.

**Escalation triggers.** Stop with `status: blocked` if the brief cannot name
a command that performs the re-scope without inventing one — an option whose
"how" is missing is not an option, and adding the command is a different
unit. Stop also if any *no* row above turns out to be unreachable in a test,
rather than asserting a scope you could not observe.
