---
id: FEAT-2026-0069/G2-CLOSE
type: close
status: done
verdict: met
attempts: 1
planned_cost_usd: 8.00
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
gate_set: plannext
driver_version: 0.4.0
started_at: 2026-07-26T20:31:24.716366+00:00
duration_seconds: 1054.646
cost_usd: 7.038172
input_tokens: 112
output_tokens: 60216
---

# Gate 2 close — terminal close for FEAT-2026-0069

**Objective.** Close the feature: retrospective, lessons, docs, and the terminal
feature-arc verdict, in one session.

**Context.** This is `FEAT-2026-0069/G2-CLOSE`, the terminal close. Gate 1's `G1-PLAN`
drafted gate 2's substantive work units above this entry in `PLAN.md`'s graph and set
this WU's real `depends_on`; the criteria below are refined against what it drafted.

Gate 2's definition of done, from `GATE-02.md`: `/derive-monitoring`, run against a repo
whose single deployable carries N triggers, emits **1 component with N targets** — not N
components.

The four work units this close reconciles, and where each one's evidence lives:

| WU | deliverable | its own oracle |
|---|---|---|
| `T05` | `invariant` may not carry `targets`; `_check_targets` docstring corrected | `tests.test_lint_monitoring.TestInvariantTargetsRejected` |
| `T06` | `discover_components` re-keyed onto deployment evidence | `tests.test_derive_monitoring_discovery.TestDeploymentKeyedDiscovery` |
| `T07` | Stack C (1 deployable, 3 subscriptions + 2 schedules) + per-schedule `heartbeat` targets | `tests.test_derive_monitoring_discovery.TestOneDeployableManyTriggers` |
| `T08` | skill Step 1 / Seams prose, canonical then synced | `tests.test_derive_monitoring_skill_registration.TestStep1IsDeploymentKeyed` |

`T07`'s oracle is the one that decides the definition of done. Re-run it fresh under AC5;
do not inherit its RESULT block.

**Acceptance criteria.** Refined by `G1-PLAN`; these are the obligations that hold
regardless of what gate 2 turns out to contain.

1. `RETROSPECTIVE.md` covers the full feature arc — both gates, per-WU outcomes,
   surprises, and `## What I'd change`.
2. **`## Cost analysis`** present, reconciling `PLAN.md`'s $34.00 and every WU's
   `planned_cost_usd` against actual spend from `events.jsonl`, with the delta named.

   **`PLAN.md`'s $34.00 was deliberately NOT re-baselined at gate-1 arming**, per
   `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`'s rule against measuring a gate against a plan
   re-based onto its own failure. Reconcile against the as-drafted $34.00 and report the
   gap honestly; do not adjust either number to make them meet.

   **Split the variance by cause, not by gate.** Gate 1's substantive WUs came in at
   $11.94 against $11.00 (+8.6%, four of five under); its two closing WUs came in at
   $26.45 against $10.00 (+165%). A single blended percentage hides that the estimating
   was good and a rules-supplied constant was not.
3. **A `## Planning-floor revision` section is present**, and it is the deliverable that
   stops this recurring. `planning-discipline.md` §5 sets a flat $5.00 floor for
   `plan-next` / `close` / `close-intermediate`. Two datasets now say it is wrong for
   `plan-next` in particular — $15.65 (FEAT-2026-0049) and $16.44 (this feature's
   `G1-PLAN`) — and `[FEAT-2026-0069/GATE-1-ARM]` in `.specfuse/LEARNINGS.md` records the
   full table and the proposed replacements ($12.00 for `plan-next`, $8.00 for
   `close` / `close-intermediate`).

   This section must state this feature's own per-type actuals, say whether they support,
   weaken, or refine those figures, and name the concrete next action — the issue or
   feature that changes `planning-discipline.md` §5 and the `WU.template.md` comment that
   quotes it. **A retrospective that merely observes the overrun does not discharge this
   criterion.** FEAT-2026-0049 produced the same evidence and it was recorded as
   provenance *for* the $5.00 floor rather than as a reason to move it; that is exactly
   the failure this criterion exists to prevent, and this is the third feature to pay for
   the constant.
4. **`## What the loop did NOT verify`** present, enumerating every acceptance criterion
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
5. **Oracles re-run fresh** (`close-discipline.md` §1): every oracle the feature's
   criteria name, full commands, exit codes read directly, never a producing WU's
   self-report. Regenerate into a clean directory before asserting on generated
   artifacts.
6. **Hedged follow-up record** (§2): on a `met_locally` verdict, a named record per unmet
   criterion — the criterion, why it is unverifiable here, and the exact re-run condition
   that upgrades it to `met`.
7. **Consumer-visible contract changes** (§3): enumerate every addition, removal, and
   rename across the whole feature, or write exactly
   `n/a — no consumer-visible contract change`. This will **not** be `n/a`: `dlq` gained a
   required field, `queue-stalled` is a new check type, and discovery's output shape
   changed. Block on human acknowledgment. Gate 1's close already tabled nine items in
   `RETROSPECTIVE.md` § *Consumer-visible contract changes* — carry that table forward
   rather than re-deriving it, and add gate 2's: item 6's `invariant` fall-through is
   **superseded by `T05`** (`targets` now rejected on `invariant`, decided rather than
   inherited), and the `patterns` table contract that `discover_components` consumes is a
   **breaking** change for anyone who wrote a pattern table against gate 1's
   `evidence_markers` shape.
8. **The downstream constraint is restated for FEAT-2026-0040**, because it is the one
   thing that can silently undo this feature: **fingerprints must include the target
   key.** Without it, 20 DLQ targets collapse into one issue and the per-subscription
   attribution this feature paid two gates for is lost at the last step. State it in the
   retrospective and confirm the roadmap detail section for 0040 carries it.
9. Durable lessons promoted to `.specfuse/LEARNINGS.md`, tagged
   `[FEAT-2026-0069/G2-CLOSE]`.
10. The roadmap detail section reflects the feature's real outcome. Issue #245 and issue
   #247 are both referenced with their resolution.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets`
    passes.

**Do NOT** add a "flip `PLAN.md status` to `done`" criterion. The driver owns the terminal
PLAN flip via `fire_terminal_flips`, gated on `verdict_permits_terminal_flips`, on both
the dispatched-close and agent-less auto-close paths. A manual agent flip is redundant.

`auto_close_disabled: true` is set because AC5, AC6, and AC7 are load-bearing close
obligations the auto-close predicate must not be able to skip.

**Do not touch.** The production surfaces — this WU closes, it does not implement.
`PLAN.md`'s `status` field. `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: close`, plus the
fresh oracle re-runs in AC5 and the plan lint in AC11.

**Escalation triggers.** Emit `status: blocked` if a fresh oracle re-run disagrees with a
WU's self-reported outcome, if gate 2's definition of done cannot be honestly asserted
(the N-trigger fixture does not actually yield one component with N targets), or if the
human acknowledgment AC7 requires is unavailable in this session. Prefer a `met_locally`
verdict with an honest hedged-follow-up record over a `met` verdict that overstates.
Blocked is a respectable outcome (`result-contract.md` rule 4).
