---
id: FEAT-2026-0075/G1-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.9.3
started_at: 2026-08-07T04:53:47.330395+00:00
duration_seconds: 860.743
cost_usd: 5.82051
input_tokens: 84
output_tokens: 63207
---

# Draft gate 2 — the arm-time refusal and the sanctioned hold

**Objective.** Draft gate 2's substantive work units and write `GATE-02-REVIEW.md`,
from gate 1's retrospective, its **observed warn output**, and
`.specfuse/LEARNINGS.md`.

**Context.** This is `FEAT-2026-0075/G1-PLAN`, gate 1's forward-design unit. Gate 1
made the staleness hazard *visible*: detection keyed on the squash diff, an immediate
warning at the squash site, a gate-completion summary, and a
`driver_staleness_detected` event. Gate 2 makes it *preventable*: an arm-time refusal
when a driver-editing unit is scheduled ahead of a close in the same gate, plus a
sanctioned status for the two-invocation hold. Read `PLAN.md`, `GATE-01.md`,
`GATE-02.md`, and this gate's `RETROSPECTIVE.md` before drafting.

`GATE-02.md` records the intent captured at draft time. **That is a proposal from a
session that had not yet seen gate 1 run, and gate 1 was designed to produce the
evidence that tests it.** Accept, revise, or reject it against what the retrospective
and the observed warn output actually show, and say which you did and why.

**Three constraints are load-bearing and not gate 2's to relitigate silently:**

- **The refusal must report zero on a correctly-ordered gate.** This is
  `planning-discipline.md` §2 and it is the reason the two shapes were split across
  two gates: gate 1's summary output is the evidence that answers it. If the observed
  output shows correctly-ordered gates would trip the refusal, the refusal is
  mis-scoped and the WU must be re-drafted before arming — not softened at arm time.
- **The hold ships with the refusal or the refusal does not ship.** `draft` is
  rejected by the arm check for the entire gate; `blocked_human` reads as a failure in
  `/attention` and every other consumer. Forcing an operator into an improvised hold
  is worse than no refusal at all.
- **Extend `arm_eval`'s existing class-2 detection, do not add a second detector.**
  `arm_eval.py:294-305` already flags drafted driver-editing units as
  `judge_editing`. `planning-discipline.md` §1 exists to prevent exactly the
  parallel-mechanism build, and `PLAN.md`'s existing-mechanism search records this
  hit.

**Consider whether gate 2 should shrink or not exist.** If gate 1's observed output
shows the immediate warning reliably lands in the window before the close dispatches,
the marginal value of a blocking refusal drops sharply — and a refusal carries a real
false-positive cost on every driver-editing feature. Recommending a smaller gate 2, or
recommending the feature close after gate 1 with the refusal returned to the roadmap
as its own row, is a legitimate outcome of this unit and should be surfaced loudly in
`GATE-02-REVIEW.md` rather than avoided because a gate was scaffolded.

Apply `.specfuse/rules/planning-discipline.md` at draft time — §1's existing-mechanism
search for anything gate 2 designs, §2's satisfiability answer for the refusal, §3's
flag-scope table for any behavior flag, §4's runtime probe recorded as an arming
precondition in `GATE-02.md`, and §5's cost floors. Apply `/authoring-work-units` §12:
every behaviour-introducing implementation WU names a scoped test that fails on HEAD
before it runs. **And if any gate-2 unit edits `specfuse/loop/` ahead of `G2-CLOSE`,
carry the driver-restart step into `GATE-02.md`'s arming discipline** — this feature
of all features must not ship having skipped its own mitigation.

Gate 2 is the terminal gate. Its closing sequence is the single `close` WU already
scaffolded as `WU-90-gate-2-close.md` — insert gate 2's substantive WUs **before** it
in `PLAN.md`'s graph and update its `depends_on`. Do not add a `close-intermediate` or
a second `plan-next`.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `GATE-02.md`'s `## Definition of done` is rewritten from gate 1's retrospective and
   observed output, with each bullet traceable to a stated goal in `PLAN.md` or to
   something gate 1 observed. Any bullet inherited unchanged from the draft-time
   proposal is marked as deliberately accepted, with one line of why.
2. `GATE-02.md` records the §2 satisfiability answer for the refusal — what it reports
   on a gate that is already correctly ordered — citing gate 1's observed output as
   the evidence rather than asserting zero.
3. The sanctioned-hold work is drafted as its own work unit, or `GATE-02-REVIEW.md`
   states explicitly why the refusal can ship without it.
4. Gate 2's substantive work units are written as `WU-*.md` files in this folder with
   `status: draft`, each carrying the five mandatory sections and a
   `planned_cost_usd`.
5. `PLAN.md`'s gate 2 `work_units` list names each drafted WU with its `depends_on`,
   ordered before the `G2-CLOSE` entry, and `G2-CLOSE`'s `depends_on` names every
   substantive WU drafted.
6. Every behaviour-introducing implementation WU drafted names a scoped test that
   fails on HEAD before it runs, or carries an explicit `Red-test exempt: <reason>`
   line.
7. `GATE-02.md`'s `## Arming discipline` carries the §4 runtime-probe requirement for
   the refusal, and the driver-restart step if any drafted unit edits
   `specfuse/loop/` ahead of `G2-CLOSE`.
8. `GATE-02-REVIEW.md` is written, with `open_questions` in its frontmatter as an
   explicit list — `[]` if nothing blocks execution. A missing field is not an empty
   list.
9. `GATE-02.md` carries a `cost_budget_usd` equal to the sum of its WU estimates plus
   one re-attempt of its largest WU, per `planning-discipline.md` §5's corollary.
10. Any recommendation to shrink gate 2, or to close the feature after gate 1, is
    surfaced in `GATE-02-REVIEW.md` with its reasoning rather than applied silently.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0075-driver-edit-staleness`
    exits 0 after the edits.

**Do not touch.** `GATE-01.md`'s status or its work units — gate 1 is closed and
`plan-next` never touches a passed gate. Any file under `specfuse/`. Any other
feature's folder under `.specfuse/features/`. `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. Generated directories, secrets,
`.git/`. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition run criterion 11's `lint_plan.py` invocation verbatim
and paste its output.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: gate
1's retrospective shows the immediate warning did not fire in a correctly restarted
driver, which invalidates gate 2's premise and is an operator decision rather than
something to draft around; the §2 satisfiability answer in criterion 2 comes out
non-zero and no scoping of the refusal reaches zero; `lint_plan.py` fails for a reason
this unit did not introduce; or `GATE-02-REVIEW.md` cannot be written with an explicit
`open_questions` list because a genuine blocking question exists — record the question
rather than writing `[]`.
