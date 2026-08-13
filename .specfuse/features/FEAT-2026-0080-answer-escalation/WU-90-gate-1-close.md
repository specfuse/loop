---
id: FEAT-2026-0080/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 1 — retrospective, lessons, docs and terminal verdict

**Objective.** Fold the retrospective, the generalizable lessons, the
documentation reconciliation and the terminal verdict for FEAT-2026-0080 into one
session, and record honestly what this gate did not verify.

**Context.** Correlation ID `FEAT-2026-0080/G1-CLOSE`. Gate 1 is terminal — this
feature is single-gate under `docs/methodology.md` §6 ceremony proportionality — so
this is a `close`, not a `close-intermediate`, and there is no next gate to draft.

`auto_close_disabled: true` is set deliberately: this close is load-bearing. It
carries consumer-visible contract changes (a new operator-facing skill, and a
changed instruction inside an existing one) and two named deferred verifications
that the auto-close predicate must not be allowed to skip.

Binding by reference, not restated here: `.specfuse/rules/close-discipline.md`,
`.specfuse/rules/human-output.md`, and the requirement registry in
`specfuse/loop/closing_requirements.py`. The section scaffold is created for you at
dispatch; fill it with substance rather than re-deriving its headings.

**Acceptance criteria.**

1. Every oracle this feature's criteria name is re-run fresh from a clean state and
   its exit code read directly — never taken from T01's or T02's self-report. At
   minimum: the full `code` gate set, plus both per-WU `diff` byte-identity checks
   and the `CATEGORY_LABELS` coverage check.
2. `RETROSPECTIVE.md` exists and contains a `## Cost analysis` heading — write that
   heading literally; `assert_cost_analysis_section_when_met` checks for it *after*
   dispatch, so its absence costs a full re-attempt. Under it, reconcile actual
   cost against the `planned_cost_usd` estimates ($8.00 T01, $3.00 T02, $5.00 this
   WU, $16.00 feature total) using the `cost_usd` values in `events.jsonl`, naming
   any WU that landed more than 10% off and why.
3. `## What the loop did NOT verify` names both deferred verifications recorded in
   PLAN.md § "Verification the loop cannot perform", each with the exact re-run
   that settles it:
   - whether the guidance-comment marker survives a real `gh issue comment` write
     and is found by a subsequent `gh issue view --comments`;
   - the `gate-review` routing branch, unexercisable while the repository has zero
     open `gate-review` escalations and zero `awaiting_review` gates.
   If either was in fact exercised during the gate, say so and remove it rather
   than carrying a stale deferral.
4. `## Consumer-visible contract changes` enumerates every addition, removal and
   rename across T01 and T02 — at minimum the new `/answer-escalation` skill and
   its trigger phrases, the `<!-- specfuse:operator-guidance … -->` marker as a new
   public format, and the changed Step 1 command in `/fix-bug` — or writes exactly
   `n/a — no consumer-visible contract change` if that enumeration turns out empty.
5. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`, or the close
   states explicitly that nothing generalizes and why. A candidate worth weighing:
   whether "an instruction naming a command that cannot satisfy it" is a recurring
   defect shape worth a durable rule, given `/fix-bug` Step 1 held that form
   undetected.
6. Per-criterion state and the narrow/broad oracle contract per
   `close-discipline.md` §5: if a `GATE-01-CRITERIA.md` artifact exists, its `kind`
   and `state` per entry are written by this close, never inferred.
7. Documentation and the roadmap detail section reflect what was actually built,
   including the D1 scope boundary — that agent-side autonomous execution was
   excluded rather than deferred — so a later reader does not record it as
   unfinished work.
8. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Close obligations.**

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — see `.specfuse/rules/close-discipline.md` §4.

Criteria 1, 3, 4 and 6 above are the §1 / §2 / §3 / §5 obligations respectively. On
a `met_locally` verdict, each unmet criterion needs a named follow-up record
carrying `- **kind:** \`<value>\`` from the recognised set — the two deferrals in
criterion 3 are `externally-verifiable-later`, since both are settled by a live
round-trip this gate could not perform rather than by anything left unbuilt.

**Do not touch.** Any file under `specfuse/` — this feature ships markdown and
tests only, and a close that edits driver code is out of contract. The work units'
own deliverables are `done` by the time you run; do not revise them to make a
criterion pass. Generated directories, secrets, `.git/`. The driver owns all git
operations and owns the terminal `PLAN.md` status flip — do not write
`PLAN.md status` yourself. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0, plus the full `code` set re-run fresh per
criterion 1.

**Escalation triggers.** Stop and emit `status: blocked` rather than pushing
through if: a re-run oracle disagrees with what T01 or T02 reported at their own
completion (that is a real finding and the operator must see it before any verdict
is recorded); or `events.jsonl` carries no `cost_usd` values, making criterion 2's
reconciliation impossible to perform honestly. Do not write a cost analysis from
estimates alone and present it as actuals.
