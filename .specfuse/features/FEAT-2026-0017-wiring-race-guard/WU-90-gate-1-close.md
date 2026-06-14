---
id: FEAT-2026-0017/G1-CLOSE
type: close
model: claude-opus-4-7
effort: high
status: done
attempts: 10
planned_cost_usd: 1.20
oracle_env: macos_local
verdict: met
prior_attempts:
  - attempt: 1
    outcome: blocked_human
    reason: agent_reported_blocked
    duration_seconds: 87.011
    cost_usd: 0.90931
    notes: "Refused verdict: met because T01 hollow-passed (loop.py unchanged, three declared symbols absent). Existence check per authoring-work-units §9 caught it. Re-armed after T01 escalated to Opus 4.7 with hardened body."
  - attempts: 3
    outcome: blocked_pre_existing_methodology_bug
    duration_seconds: 839.536
    cost_usd: 4.97415
    notes: "Spun on assert_doc_or_roadmap_diff guard requiring docs/ or roadmap.md touch in squash, but WU body forbids roadmap.md edit (FEAT-2026-0015/T06 consolidated driver-side) and scaffold has no docs/. T07 guard contract contradicts T06 consolidation. Hygiene-fix applied: guard now also accepts .specfuse/LEARNINGS.md and RETROSPECTIVE.md."
  - attempts: 3
    outcome: hollow_pass_via_diff_bypass
    duration_seconds: 705.545
    cost_usd: 4.700944
    notes: "Attempts 1+2 failed assert_verdict_well_formed. Attempt 3 passed via the diff-only-touches-wu bypass in assert_closing_deliverables (loop.py:1465-1468) without producing RETROSPECTIVE.md or LEARNINGS append. Driver flagged inconsistency. Hollow squash reset; bypass removed in commit 6084a89 with regression test."
  - attempts: 3
    outcome: blocked_opus_verdict_blindspot
    duration_seconds: 715.0
    cost_usd: 4.701
    notes: "With bypass removed, agent satisfied retrospective + learnings + doc-diff every attempt but consistently failed to flip verdict: not_set despite explicit retry feedback (3 retries with identical failure_note: 'verdict not_set absent or not in VERDICT_VALUES'). Model-level blind-spot; logged for deep-analysis. Operator finished close manually."
duration_seconds: 0
cost_usd: 0
input_tokens: 0
output_tokens: 0
---

# Gate 1 close — terminal close ceremony (NEW contract; recursive dogfood)

**Objective.** Close this single-gate feature in one session using
the new `type: close` contract. Produce RETROSPECTIVE.md, append
durable LEARNINGS, reconcile docs, write the feature-arc verdict,
include `## Cost analysis` section. Driver-side terminal flips
(gate → passed, roadmap row → done, auto-archive) fire automatically
when `verdict: met`. **Recursive dogfood**: this WU's own pass
exercises T01's `assert_terminal_flips_fired` guard against itself.
T01 wiring failure → guard fires → this attempt fails → next attempt
retried with the bug observable.

**Context.** This is `FEAT-2026-0017/G1-CLOSE`. Read this feature's
`events.jsonl`, the gate's commits, root `.specfuse/LEARNINGS.md`,
PLAN.md's `roadmap_goal`. Single-gate, so no next gate to forward-
design. Reference the binding rules under `.specfuse/rules/`; honor
`result-contract.md`, `never-touch.md`. The driver owns all git.

This is the first dogfood of T01's `assert_terminal_flips_fired`
against an actual close ceremony. Set `verdict: met` ONLY when the
roadmap_goal is genuinely achieved AND you can confirm T01 + T02
produced their deliverables in the squash commits AND you've audited
the `## Cost analysis` section against events.jsonl.

**Cross-repo contracts (load-bearing strings; verify before
completing).**

- `verdict: met` — drives driver-side `fire_terminal_flips` AND T01's
  post-pass invariant check. Hedged values (`met_locally`,
  `partially_met`) intentionally skip the guard per T01 AC2.
- `<a id="feat-2026-0017"></a>` (anchor literal) — must be present
  in `roadmap-archive.md` after `fire_terminal_flips` runs. T01's
  guard reads this literal.
- `[→ archive](roadmap-archive.md#feat-2026-0017)` (back-link
  literal) — must be in the Detail cell of FEAT-2026-0017's row
  in `roadmap.md` after `fire_terminal_flips` runs.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in this feature folder. Sections:
   per-WU outcome (T01, T02) with what worked / what failed /
   attempts taken / final cost; gate-level summary; surprises;
   `## Cost analysis` (mandatory per T08 contract).
2. **`## Cost analysis` section** quotes `planned_cost_usd` from
   PLAN.md and each WU's frontmatter; computes actual `cost_usd`
   per WU from events.jsonl; reports per-WU delta % and gate total
   delta %. Variance > 50% on any unit requires a one-paragraph
   rationale.
3. Durable, generalizable lessons appended to root
   `.specfuse/LEARNINGS.md`, tagged `FEAT-2026-0017/G1-CLOSE`.
   Most likely lesson surface: "post-pass driver-state invariants
   are a distinct guard category from closing-deliverable file
   asserts (T07); the load-vs-dispatch race for verdict-shaped
   fields demands re-read at the check site." If nothing
   generalizes, append nothing and say so.
4. `# Feature-arc verdict` section appended to RETROSPECTIVE.md.
   Verdict states whether `roadmap_goal` is met. The verdict text
   MUST cite:
   - T01's deliverables landed (POST_PASS_INVARIANTS_BY_TYPE +
     assert_terminal_flips_fired + verify_post_pass_invariants
     exist via grep + import check).
   - T02's deliverables landed (`produces_driver_helper` field
     reads cleanly; lint warns on a synthetic missing-declaration
     case).
   - The regression test `test_feat_2026_0015_t06_regression` is
     present and asserts the new guard catches the T06 pattern.
5. Set `verdict:` frontmatter field on this WU to one of `met`,
   `met_locally`, `partially_met`, `not_met` per the criteria
   above. `not_set` (the placeholder) is REJECTED — the driver's
   verdict_permits_terminal_flips check requires a real value.
6. **Recursive dogfood assertion.** After the driver fires
   `fire_terminal_flips`, T01's `assert_terminal_flips_fired`
   MUST run against THIS WU's own state. The assertion checks
   the very flips this WU just produced. If it returns False,
   either T01's implementation is broken (the recursive case
   we're testing for) or this WU's verdict was set to `met`
   without the flips actually firing (operator-side bug). Either
   way: the driver's post-pass guard catches it; this attempt
   fails; spinning detection kicks in if it persists 3 times.

**Do not touch.** Source code (`loop.py`, `lint_plan.py`,
templates, skills) — this is a closing unit, it does not change
behavior. Other WU files, generated directories, secrets, `.git/`.
The agent writes `RETROSPECTIVE.md`, appends to `LEARNINGS.md`,
sets `verdict:` in this WU's frontmatter. NOTHING else.

`roadmap.md` row flip and `roadmap-archive.md` anchor insertion are
DRIVER-SIDE per FEAT-2026-0015/T06's state-flip consolidation.
This WU does NOT directly edit either roadmap file. If you find
yourself opening either file for write, emit `status: blocked` —
the consolidation contract is being violated.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml` (`lint_plan.py` on this feature —
structural validity preserved). Plus T07's closing-deliverable
guards (assert_retrospective_exists, assert_learnings_appended,
assert_cost_analysis_section_when_met, assert_verdict_well_formed)
fire on this close WU and must pass. Plus T01's new post-pass
guard fires AFTER flip and must pass when `verdict: met`.

**Escalation triggers.**

1. **T01 deliverables missing.** If grep against `loop.py` for
   `POST_PASS_INVARIANTS_BY_TYPE` returns 0 hits, T01 hollow-passed.
   Emit `status: blocked` with `blocked_reason: "T01 deliverable
   POST_PASS_INVARIANTS_BY_TYPE absent — close must not declare
   roadmap_goal met"`. Do NOT set `verdict: met`.
2. **T02 deliverables missing.** Same shape for
   `produces_driver_helper` field on WorkUnit and the
   `detect_driver_wiring` function in lint_plan.py.
3. **State-flip violation.** If the agent edits `roadmap.md` or
   `roadmap-archive.md` directly in this WU's session, emit
   `status: blocked` — violates the FEAT-2026-0015/T06 ownership
   consolidation.
4. **Cost analysis section absent.** Per T07's
   `assert_cost_analysis_section_when_met` guard: if `verdict: met`
   and RETROSPECTIVE.md has no `## Cost analysis` section, the
   driver's guard fires before terminal flips. Don't bypass by
   setting verdict to anything non-`met`. Write the section.
5. **Conflicting roadmap state.** If `roadmap.md` already shows this
   feature as `done` (some prior driver run completed), do not
   re-flip. Reconcile in the verdict and stop.
