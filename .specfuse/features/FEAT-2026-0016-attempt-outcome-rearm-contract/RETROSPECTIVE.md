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
