# Retrospective — FEAT-2026-0016 (per-attempt outcome events + re-arm contract)

## Gate 1

Data-layer foundation. Shipped attempt_outcome emission across all
dispatch outcomes (T01), re-arm WU frontmatter contract + driver
cumulative-fold logic (T02), and unit tests covering both (T03).
Consumers (spinning-detector hook, /gate-status, /unblock-wu) deferred
to gate 2.

### T01 — attempt_outcome emission completion + standardization

- **Attempts:** 1 (passed).
- **Cost:** $1.87 actual vs $2.50 planned (0.75×).
- **Blockers:** none.
- **Surprises:** none — the four-site migration + three new emission
  sites (passed/failed/blocked) + four new helpers
  (`emit_attempt_outcome`, `parse_gate_failure_signature`,
  `extract_failure_excerpt`, `git_diff_names`) landed in a single
  attempt on the xhigh-effort spec. Tight pre-flight (§10
  helper-duplication grep) caught no collisions; the spec's bootstrap-
  gap call-out (T01's own events lack the new payload — driver runs
  OLD code while dispatching T01) was load-bearing: events.jsonl lines
  1–6 carry only the legacy `task_started`/`task_completed`/
  `human_escalation` shapes. First WU to emit the full v1
  `attempt_outcome` payload is T03 (line 8). Confirms the documented
  pattern in `[FEAT-2026-0006/G1-CLOSE]`.

### T02 — re-arm frontmatter contract + cumulative-fold logic

- **Attempts:** 1 (passed).
- **Cost:** $1.03 actual vs $1.80 planned (0.57×).
- **Blockers:** none.
- **Surprises:** none. Two new helpers (`fold_cumulative_on_rearm`,
  `detect_rearm_dispatch`) + `re_arm_dispatched` event +
  `task_started` payload extension + six frontmatter fields documented
  in `WU.template.md`, all in one attempt. No pre-existing
  `cumulative_*`/`re_arm_*` collisions surfaced by §10 pre-flight, so
  the lint-allowlist widening risk (Escalation #3) didn't fire.

### T03 — unit tests for attempt_outcome emission + cumulative-fold

- **Attempts:** 2 (first attempt blocked-agent-correct-diagnosis;
  re-arm passed).
- **Cost:** $0.84 (blocked attempt) + $1.48 (passed attempt) = $2.31
  vs $1.50 planned (1.54×).
- **Blocker:** spec bug in AC7e — `git diff --name-only HEAD` excludes
  untracked files, but the test file `tests/test_attempt_outcome_emission.py`
  is newly created and therefore untracked. The check failed
  spuriously; the agent correctly diagnosed and proposed the combined
  `{ git diff --name-only HEAD; git ls-files --others
  --exclude-standard; }` pattern that matches LEARNINGS
  `[driver/files_changed-guard]`. Same broken pattern existed in this
  WU's own AC6 (creates RETROSPECTIVE.md); fixed pre-emptively in
  commit 3f77530.
- **Surprises:** the broken-AC pattern is a recurring class — every
  closing-deliverable WU whose AC checks for "is this new file
  in the diff?" needs the combined diff+ls-files form. Worth
  promoting to LEARNINGS (see below).

## Cost analysis

Per-WU reconciliation. Cost figures sourced from WU frontmatter
`cost_usd` (terminal-cycle write) + `prior_attempts[*].cost_usd`
(pre-re-arm spend). events.jsonl `task_completed.attempts_usage[*].cost_usd`
agrees with frontmatter for all three WUs at the cycle granularity.

| WU | planned | actual | delta % | notes |
|----|---------|--------|---------|-------|
| T01 | $2.50 | $1.87 | -25% | within plan |
| T02 | $1.80 | $1.03 | -43% | within plan |
| T03 | $1.50 | $2.31 | +54% | rationale below |
| **Gate 1 substantive** | **$5.80** | **$5.21** | **-10%** | within plan |
| G1-CLOSE-INTERMEDIATE | $1.20 | (in flight) | — | this WU |

**T03 variance rationale (+54%).** T03's overrun crosses predicate v1
criterion 3 (1.5× per-WU soft threshold) but stays below criterion 4
(2× hard threshold). Root cause: spec bug — AC7e's symbol-existence
check used a pattern (`git diff --name-only HEAD`) that does not
match a newly-created file. The agent's first attempt ($0.84) was a
correct blocked diagnosis with a documented prior LEARNINGS reference;
the re-arm ($1.48) completed cleanly under the same effort band. The
overrun is methodology cost (spec correctness on closing-deliverable
patterns), not implementation cost. Mitigation already landed:
commit 3f77530 fixed both T03's AC7e and this WU's AC6 pre-emptively;
the lesson is generalized below.

**Predicate v1 evaluation.** Gate-substantive total stays well under
the $10.00 gate budget; the only non-trivial cost ratio is T03 at
1.54× (informational, not blocking). The predicate returns
`auto=False` solely on `blocked_human_in_chain` (T03's correct
blocked attempt — see Predicate self-check below). For an intermediate
close, the predicate verdict is informational; the operator chose to
re-arm T03 with a revised spec rather than abandon, which is the
documented correct response when the block is a spec defect.

## Predicate self-check

```
FEAT-2026-0016  predicate=v1
  G01  auto=False
    reasons:
      - blocked_human_in_chain: T03 escalated 2026-06-14
    metrics:
      gate_total_cost: $4.37
      gate_budget: $10.00
```

(`gate_total_cost: $4.37` reflects the predicate's per-WU sum of the
terminal-cycle `cost_usd` only — T03's pre-re-arm $0.84 is in
`prior_attempts`, which the predicate does not currently aggregate.
The true cumulative gate-1 substantive spend is $5.21. Worth flagging
for a future predicate v2 refinement: aggregate `prior_attempts[*].cost_usd`
into cost-ratio criteria so blocked-then-recovered cycles count
correctly. Out of scope for this gate.)

## Gate 2 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 3.

- feature_id: FEAT-2026-0016
- predicate_version: v1
- gate_total_cost: $1.43
- gate_budget: $12.00
- reasons: [] (auto=True)

## Gate 3

Close-ceremony / skill / docs gate. Shipped T07 (`### Failure-class
breakdown` subsection helper + close-guard wired into
`CLOSE_GUARDS`), T08 (`/learnings-suggest` read-only signature-
clustering skill + `.claude/skills` symlink), T09 (methodology.md
per-attempt event contract + re-arm frontmatter paragraph +
roadmap-archive move of the merged-in original 0016 scope).

### T07 — close-ceremony `### Failure-class breakdown` subsection + guard

- **Attempts:** 1 (passed).
- **Cost:** $1.117 actual vs $1.00 planned (1.12×).
- **Blockers:** none.
- **Surprises:** one — `summarize_attempt_failure_classes(feature_dir,
  gate_n=N)` resolves the gate of a `correlation_id` via
  `_gate_number_from_wu_id`, which only matches **closing-WU** IDs
  (`G<n>-…` segments). Substantive-WU IDs (`TNN`) return `None` from
  that helper and are therefore filtered out when `gate_n` is set.
  Net effect: the helper called on this very feature with
  `gate_n=3` returns the `(no non-passing attempts in scope)`
  sentinel **even though T08 has one non-passing
  `attempt_outcome` record** (the sandbox-block first attempt;
  see events.jsonl line carrying `outcome: blocked` for
  `correlation_id: FEAT-2026-0016/T08`). This is the recursive-
  dogfood finding the §G3-CLOSE spec called out as load-bearing —
  the helper is the contract, and its gate-bucketing is degraded
  for substantive WUs. The guard
  `assert_failure_class_breakdown_when_failures_present`
  consequently passes (sentinel route) regardless of whether the
  retrospective renders a breakdown — i.e. the guard does **not**
  catch a missing breakdown for substantive-WU failures bucketed
  by gate. Promoted to LEARNINGS (rule below). Helper still works
  correctly when called without `gate_n` (all gates), and the
  AC10c existence check in `WU-90-gate-3-close.md` independently
  derives gate-3 WU IDs from PLAN.md and **does** count T08's
  blocked attempt — so the contract surfaces require the heading
  even when the helper sentinel says otherwise. We render the
  helper output verbatim per AC3 (helper-is-the-contract), and
  document the gap here + in the breakdown subsection below.

### T08 — `/learnings-suggest` skill

- **Attempts:** 2 (first attempt
  blocked-sandbox-correct-diagnosis; re-arm passed).
- **Cost:** $0.404 (blocked attempt, per events.jsonl) + $0.327
  (passed attempt, per frontmatter `cost_usd`) = **$0.731**
  cumulative vs $1.20 planned (0.61×). Frontmatter
  `cost_usd: 0.327` records only the terminal cycle; the
  `prior_attempts[0]` entry omits a `cost_usd` field, so events.jsonl
  is the authoritative source for the blocked-cycle spend. Same
  data-drift pattern documented in gate-1 retrospective's
  "Predicate self-check" note.
- **Blocker:** first attempt ran in the dispatched session's
  Claude Code sandbox, which lists `.claude/skills` under
  `denyWithinAllow`. The agent could create
  `.specfuse/skills/learnings-suggest/SKILL.md` (allowed) but
  could NOT create the discovery symlink `.claude/skills/learnings-suggest`
  (denied by sandbox even with WU `unsandboxed: true`, because the
  deny rule sits inside an allow). The agent correctly diagnosed
  the boundary, emitted `status: blocked` with a precise
  `blocked_reason`, and left the operator a one-line manual fix
  (`cd .claude/skills && ln -s ../../.specfuse/skills/learnings-suggest learnings-suggest`)
  runnable from the main Claude Code session which carries
  different sandbox permissions. Operator ran it; re-arm passed.
- **Surprises:** the sandbox boundary is a recurring class —
  skill-adding WUs that need to write under `.claude/skills`
  will reproduce this even with `unsandboxed: true` on the WU.
  The mitigation pattern is "operator-side symlink, agent-side
  SKILL.md authoring"; worth pre-emptive scope-splitting in
  future skill-adding WU specs. Promoted to LEARNINGS (rule
  below).

### T09 — docs (methodology.md + roadmap-archive)

- **Attempts:** 1 (passed).
- **Cost:** $0.549 actual vs $0.50 planned (1.10×).
- **Blockers:** none.
- **Surprises:** none. Methodology.md gained two new §3
  subsections (per-attempt outcome events + re-arm frontmatter)
  and one cross-link to the WU template. Roadmap-archive move
  matched the documented anchor + back-link convention used by
  every prior archived feature. Additive-only discipline held.

## Cost analysis

Per-WU reconciliation. Cost figures sourced from WU frontmatter
`cost_usd` (terminal-cycle write) + events.jsonl
`attempt_outcome.cost_usd` (every cycle, including pre-re-arm
when frontmatter `prior_attempts` omits the field). Gate-3 rows
appended below; gates 1 + 2 + 3 substantive subtotals roll up to
the feature total.

| WU | planned | actual | delta % | notes |
|----|---------|--------|---------|-------|
| T04 | $2.00 | $0.76 | -62% | within plan |
| T05 | $1.20 | $0.27 | -78% | within plan |
| T06 | $1.50 | $0.40 | -73% | within plan |
| **Gate 2 substantive** | **$4.70** | **$1.43** | **-70%** | within plan |
| G2-CLOSE-INTERMEDIATE | $1.20 | $0.00 | auto-closed | skipped per predicate |
| G2-PLAN | $1.50 | $4.78 | +219% | rationale below |
| T07 | $1.00 | $1.12 | +12% | within plan |
| T08 | $1.20 | $0.73 | -39% | cumulative (blocked + re-arm) |
| T09 | $0.50 | $0.55 | +10% | within plan |
| **Gate 3 substantive** | **$2.70** | **$2.40** | **-11%** | within plan |
| G3-CLOSE | $1.50 | (in flight) | — | this WU |
| **Feature substantive (gates 1+2+3)** | **$13.20** | **$9.04** | **-32%** | within plan |

**T08 cumulative vs frontmatter.** Frontmatter `cost_usd: 0.327`
records only the post-re-arm cycle. The pre-re-arm cycle's
$0.404 lives in events.jsonl `attempt_outcome` for T08 attempt 1
(`outcome: blocked`); the matching `prior_attempts[0]`
frontmatter entry omits the `cost_usd` field entirely. Events
remain authoritative for cumulative spend; the predicate's per-WU
cost reads frontmatter only and therefore under-counts T08 by
$0.404. Same data-drift pattern as gate 1's T03 (documented in
gate-1's "Predicate self-check"). Predicate-v2 candidate: roll
`prior_attempts[*].cost_usd` (or the events.jsonl join) into the
cost-ratio criteria — out of scope per PLAN.md "Scope OUT".

**G2-PLAN variance rationale (+219%).** G2-PLAN's overrun crosses
predicate v1 criterion 4 (2× hard threshold). The WU drafts the
full gate-3 substantive graph (three substantive WUs + the
terminal close WU) at high effort; the WU spec is closing-
deliverable-shaped (heavy authoring + binding-rule reads). Each
draft is a substantial author cycle. The overrun is methodology
cost (drafting fidelity), not implementation cost. Worth flagging
for predicate v2: `plan-next` WUs have a different planned-cost
profile than substantive implementation WUs and should be
isolated in the predicate's cost-ratio criteria. Out of scope per
PLAN.md "Scope OUT".

**Predicate v1 evaluation (gate 3).** Gate-substantive total ($2.40)
stays well under the $7.00 gate budget. T07's overrun (1.12×) is
below criterion 3 (1.5×). The predicate returns `auto=False` solely
on `blocked_human_in_chain` (T08's correct blocked attempt — see
self-check below). Same shape as gate 1's predicate result: a
correct agent-emitted block on a real boundary (gate-1 spec defect;
gate-3 sandbox boundary), recovered cleanly via re-arm, but the v1
predicate cannot distinguish a blocked-then-recovered cycle from a
blocked-and-abandoned cycle. The operator chose to re-arm both
times — documented correct response.

### Failure-class breakdown

(no non-passing attempts in scope)

(The helper-rendered subsection above is shown verbatim per AC3
contract. As documented in the T07 sub-section above, the helper's
`_gate_number_from_wu_id` gate-bucketing matches closing-WU IDs
only — substantive-WU IDs return `None` and are filtered out when
`gate_n` is set, so the gate-3 sentinel does **not** reflect T08's
one non-passing attempt. The PLAN-derived gate membership
referenced in `WU-90-gate-3-close.md` AC10c is the authoritative
source for "what is in gate 3"; rendering it for the breakdown is
deferred to a follow-up fix on the T07 helper, captured in
LEARNINGS below.)

## Predicate self-check (gate 3)

```
FEAT-2026-0016  predicate=v1
  G03  auto=False
    reasons:
      - blocked_human_in_chain: T08 escalated 2026-06-14
    metrics:
      gate_total_cost: $1.99
      gate_budget: $7.00
```

(`gate_total_cost: $1.99` reflects the predicate's per-WU sum of
the terminal-cycle `cost_usd` only — T08's pre-re-arm $0.404 is
in events.jsonl but absent from frontmatter `prior_attempts[0]`,
which the predicate does not aggregate. True cumulative gate-3
substantive spend is $2.40. Same observation as gate 1.)

Auto-close did NOT fire on gate 3 (this WU is running, which
implies the predicate's `auto=False` blocked auto-close — exactly
the recursive-dogfood scenario PLAN.md "Notes" calls out: gate 3
evaluates the predicate on a feature whose data layer the
predicate consumes for the first time at full payload fidelity.
T01's bootstrap-gap absence already documented in gate 1.)

# Feature-arc verdict

**Verdict: met_locally.** The `attempt_outcome` data layer (T01)
+ re-arm WU-frontmatter contract + driver cumulative-fold logic
(T02) + unit tests (T03) + spinning-detector driver hook (T04) +
`/gate-status` per-attempt surface (T05) + `/unblock-wu`
rationale-history (T06) + close-ceremony `### Failure-class
breakdown` subsection helper + close-guard (T07) +
`/learnings-suggest` skill (T08) + methodology.md docs +
roadmap-archive (T09) all shipped, end-to-end, against PLAN.md's
`roadmap_goal`. Predicate v1 reads `events.jsonl` directly; no
consumer relies on driver stdout. The hedge to `met_locally`
(not `met`) covers two explicit scope-deferred items: (a)
predicate v2 — relaxed check 1 / structured check 7 — explicitly
left for a future feature per PLAN.md "Scope OUT", to be designed
against the accumulated real attempt_outcome data this feature
just shipped; (b) T07's helper gate-bucketing is degraded for
substantive-WU IDs (closing-WU IDs only resolve in
`_gate_number_from_wu_id`), surfaced as recursive-dogfood
evidence this very close-ceremony retrospective, and captured as
a LEARNINGS rule for the follow-up fix.
