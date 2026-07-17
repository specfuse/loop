---
id: FEAT-2026-0031/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - .specfuse/features/FEAT-2026-0031-configurable-integration-branch/RETROSPECTIVE.md
  - .specfuse/LEARNINGS.md
generated_surfaces: []
---

# Gate 1 close — retrospective, lessons, docs, terminal verdict

**Objective.** Close FEAT-2026-0031: write the feature's retrospective, promote
generalizable lessons to `.specfuse/LEARNINGS.md`, reconcile planned against actual
cost, enumerate what the loop did not verify, and record the terminal verdict.

**Context.** Correlation `FEAT-2026-0031/G1-CLOSE`. Terminal `close` for a
single-gate feature — this session collapses retrospective + lessons + docs +
verdict. Read `PLAN.md` in this folder for the draft-time decisions, and the
`events.jsonl` attempt records for T01–T03 for what actually happened.

The feature made the base branch an explicit frontmatter property read by one
resolver: `resolve_base` / `ensure_base_ref` (T01), branch creation + staleness guard
(T02), PR base (T03).

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in this feature folder, grounded in the T01–T03 attempt
   records — not in the plan's intentions.
2. A `## Cost analysis` section reconciles `planned_cost_usd` (5.50 feature-level;
   1.20 / 1.60 / 1.20 / 1.50 per WU) against actual spend from `events.jsonl`, with
   the delta named.
3. A `## What the loop did NOT verify` section enumerates each acceptance criterion
   whose verification was deferred — for each: the criterion, why deferred, and where
   verification actually happens. The section is required even if empty; write
   `(nothing — every acceptance criterion was verified in-loop)` if so.
4. That section is expected to carry **exactly two** entries, both from T03 and both
   known at draft time:
   - live `gh pr create --base <base>` against a real repo — deferred, `gh`
     unreachable in `claude -p`; verified by the operator post-merge on this
     feature's own PR.
   - `wrap-feature` agent-followed prose producing a correctly-targeted PR —
     deferred, verified when an operator next wraps a feature declaring a `base`.
   If the list exceeds 2 entries or 30% of the gate's criteria, `## What I'd change`
   must flag this feature's single-gate sizing.
5. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`, tagged
   `[FEAT-2026-0031/G1-CLOSE]`. A lesson that only restates this feature's plan is
   not generalizable — cut it.
6. `## What I'd change` is written honestly, including the sizing check from
   criterion 4.
7. The roadmap detail section for FEAT-2026-0031 reflects what was actually built,
   including the out-of-scope gaps that survived (`fix-bug` and `scaffold-upgrade`
   still hardcode `main`).
8. A terminal `verdict:` is written to this WU's frontmatter reflecting the honest
   gate state. Reserve `met` for a gate whose acceptance actually held.

**Candidate lessons — evaluate, do not assume.** These are draft-time hypotheses;
promote only what the run's evidence supports:
- Whether the "one resolver, no threading" shape held once three callers existed, or
  whether a caller wanted a base the resolver could not give it.
- Whether re-anchoring the staleness guard to the base (Q2) broke an existing
  HEAD-anchored assumption the plan did not foresee.
- Whether classifying a missing base three ways (Q3) earned its complexity versus a
  blanket halt — a rule about when to classify a failure rather than merge cases.
- Whether the `gh pr view` direct-`subprocess.run` bypass (found while drafting, not
  by a test) points at a general rule for injected-runner modules: a runner that only
  covers *some* calls gives tests false confidence.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip
(`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`); a manual flip is
redundant. Source files under `specfuse/loop/` — T01–T03 own the implementation; if
you find a bug, record it in the retrospective and file it, do not fix it from inside
a close session (weakening or patching a gate from its own close is the failure mode
LEARNINGS FEAT-2026-0020/G1-CLOSE-INTERMEDIATE names). Generated directories,
secrets, `.git/`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`events.jsonl` carries no cost records for T01–T03 (the cost analysis would be
fabricated — say so instead of inventing numbers); the retrospective cannot be
grounded because attempt records are missing; or a T01–T03 acceptance criterion is
discovered unmet — a close session must not paper over an incomplete gate, and
`blocked` is a respectable outcome (`result-contract.md` rule 4).
