---
id: FEAT-2026-0069/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
---

# Gate 2 close — terminal close for FEAT-2026-0069

**Objective.** Close the feature: retrospective, lessons, docs, and the terminal
feature-arc verdict, in one session.

**Context.** This is `FEAT-2026-0069/G2-CLOSE`, the terminal close. **This file is a
`status: draft` placeholder**, scaffolded at feature-drafting time so `lint_plan.py`
reads gate 2 as the non-empty terminal gate and gate 1 as non-terminal. Gate 1's
`G1-PLAN` fills in gate 2's substantive work units above this entry in `PLAN.md`'s
graph, sets this WU's real `depends_on`, and refines the criteria below against what
gate 2 actually drafted.

Gate 2's definition of done, from `GATE-02.md`: `/derive-monitoring`, run against a repo
whose single deployable carries N triggers, emits **1 component with N targets** — not N
components.

**Acceptance criteria.** Refined by `G1-PLAN`; these are the obligations that hold
regardless of what gate 2 turns out to contain.

1. `RETROSPECTIVE.md` covers the full feature arc — both gates, per-WU outcomes,
   surprises, and `## What I'd change`.
2. **`## Cost analysis`** present, reconciling `PLAN.md`'s $34.00 and every WU's
   `planned_cost_usd` against actual spend from `events.jsonl`, with the delta named.
3. **`## What the loop did NOT verify`** present, enumerating every acceptance criterion
   whose verification was deferred — the criterion, why, and where verification actually
   happens. Required even when empty. If the list exceeds 2 entries or 30% of the
   feature's criteria, flag the feature's gate sizing under `## What I'd change`.
   **One entry is known at drafting time and must appear unless it was actually
   verified:** the issue's claim that target coordinates are mechanically extractable is
   confirmed only against a repo outside this tree. A fixture authored inside gate 2 is
   evidence the algorithm works on that fixture, not evidence the claim holds on real
   repositories. Verifying it needs an operator running `/derive-monitoring` against a
   real multi-trigger repo — the same post-merge operator step FEAT-2026-0039 recorded
   for its own skill.
4. **Oracles re-run fresh** (`close-discipline.md` §1): every oracle the feature's
   criteria name, full commands, exit codes read directly, never a producing WU's
   self-report. Regenerate into a clean directory before asserting on generated
   artifacts.
5. **Hedged follow-up record** (§2): on a `met_locally` verdict, a named record per unmet
   criterion — the criterion, why it is unverifiable here, and the exact re-run condition
   that upgrades it to `met`.
6. **Consumer-visible contract changes** (§3): enumerate every addition, removal, and
   rename across the whole feature, or write exactly
   `n/a — no consumer-visible contract change`. This will **not** be `n/a`: `dlq` gained a
   required field, `queue-stalled` is a new check type, and discovery's output shape
   changed. Block on human acknowledgment.
7. **The downstream constraint is restated for FEAT-2026-0040**, because it is the one
   thing that can silently undo this feature: **fingerprints must include the target
   key.** Without it, 20 DLQ targets collapse into one issue and the per-subscription
   attribution this feature paid two gates for is lost at the last step. State it in the
   retrospective and confirm the roadmap detail section for 0040 carries it.
8. Durable lessons promoted to `.specfuse/LEARNINGS.md`, tagged
   `[FEAT-2026-0069/G2-CLOSE]`.
9. The roadmap detail section reflects the feature's real outcome. Issue #245 and issue
   #247 are both referenced with their resolution.
10. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets`
    passes.

**Do NOT** add a "flip `PLAN.md status` to `done`" criterion. The driver owns the terminal
PLAN flip via `fire_terminal_flips`, gated on `verdict_permits_terminal_flips`, on both
the dispatched-close and agent-less auto-close paths. A manual agent flip is redundant.

`auto_close_disabled: true` is set because AC4, AC5, and AC6 are load-bearing close
obligations the auto-close predicate must not be able to skip.

**Do not touch.** The production surfaces — this WU closes, it does not implement.
`PLAN.md`'s `status` field. `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: close`, plus the
fresh oracle re-runs in AC4 and the plan lint in AC10.

**Escalation triggers.** Emit `status: blocked` if a fresh oracle re-run disagrees with a
WU's self-reported outcome, if gate 2's definition of done cannot be honestly asserted
(the N-trigger fixture does not actually yield one component with N targets), or if the
human acknowledgment AC6 requires is unavailable in this session. Prefer a `met_locally`
verdict with an honest hedged-follow-up record over a `met` verdict that overstates.
Blocked is a respectable outcome (`result-contract.md` rule 4).
</content>
