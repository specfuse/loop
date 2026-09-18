---
id: FEAT-2026-0113/T08H
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.50
produces:
  - specfuse/loop/triage.py
  - specfuse/agent/severity_backfill.py
  - tests/test_severity_backfill_limit.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.20.1
started_at: 2026-09-18T11:36:07.523315+00:00
duration_seconds: 124.275
cost_usd: 0.706654
input_tokens: 50
output_tokens: 12262
---

# T08H — `--limit` bounds candidates, and a zero-candidate run says so

**Objective.** `--limit N` means "amend at most N candidates", not "look at the
N newest open issues", and a run that selects nothing prints a reason instead of
exiting silently.

**Context.** Hygiene unit, inserted after `T11`'s live dry run against the
repository where `PLAN.md`'s stranded issues were measured. Two defects, both
measured rather than reasoned:

**1. `--limit` bounds the listing.** `list_severity_backfill_candidates`
(`specfuse/loop/triage.py:369`) passes `limit` straight into
`_list_open_issues`, which is the `gh issue list --limit` window. Measured
against the real repository:

```
--limit   5 -> 0 candidates
--limit 100 -> 74 candidates
--limit 200 -> 84 candidates
```

191 open issues, 84 candidates scattered through them. The five newest carry no
triage marker at all, so `--limit 5` selected nothing. **The default of 100
silently ignores the oldest 91 issues**, and a stranded backlog is old by
construction — this is the wrong reading for exactly the population a backfill
exists to serve. It also makes `GATE-03-REVIEW.md`'s Q3 moot: under listing
semantics a *lower* default does not bound the blast radius, it hides more of
the backlog.

**2. A zero-candidate run is silent.** `_print_run_report`
(`specfuse/agent/severity_backfill.py:310`) returns without printing when
`reason` is `None` and `rows` is empty. Exit 0, no output — indistinguishable
from a crash. `T10`'s criterion 3 required a reason for the empty-*rubric* case
only; empty *candidates* had no such requirement.

**Why its own unit.** `T08` owns the selection predicate and is `done`; `T10`
owns the run shape and is `done`. Re-arming either folds cost into
`cumulative_*` and re-opens finished work for a bounded fix. This is the pattern
`T01H`, `T02H` and `T07H` already used in this feature.

**Acceptance criteria.**

1. `tests/test_severity_backfill_limit.py::LimitBoundsCandidates::
   test_limit_counts_candidates_not_listed_issues` fails on HEAD before this
   unit runs and passes after: with an injected runner returning 50 open issues
   of which every tenth is a candidate, `list_severity_backfill_candidates(...,
   limit=3)` returns exactly 3 candidates — not 0, and not every candidate among
   the first 3 issues listed.
2. The listing is paged until `limit` candidates are found or open issues are
   exhausted, and **the page size is not the candidate limit** — a `limit=3` run
   over a repository whose only candidates are the 80th–84th newest issues still
   returns 3. Asserted with an injected runner that records each `gh issue list`
   argv, so paging is measured rather than assumed.
3. Exhaustion terminates: a repository with fewer candidates than `limit`
   returns what exists and issues no unbounded loop — asserted by a recorded
   argv count that is finite and by the returned length.
4. `test_a_zero_candidate_run_reports_why`: a run selecting no candidates prints
   a line naming the repository and the limit it searched under, and exits 0.
   Silence is not an acceptable report for "nothing to do".
5. `list_untriaged`'s own `limit` semantics are **unchanged** — it is a
   different question ("the newest N issues, which of them are untriaged") with
   a live caller in `TriageProvider.advertise`, and its existing tests pass
   unedited.

**Do not touch.** `list_untriaged` and every other function in
`specfuse/loop/triage.py` — criterion 5 is what holds that line.
`parse_marker` / `parse_marker_fields` and the marker format. The selection
*predicate* itself: which issues qualify is `T08`'s decision and is correct —
this unit changes only how many are gathered and how the count is reported.
The write path and its ordering (`T09`). The rubric and its two sources
(`T03`, gate 2). `rules.bugs.min_severity`.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_agent_provider_triage tests.test_severity_backfill_run tests.test_severity_backfill_apply -b`.

**Escalation triggers.** If bounding candidates appears to require changing
which issues qualify — any edit to the predicate's exclusions — stop: that is
`T08`'s decision and a different unit. If paging appears to need a `gh` flag or
API this repository does not already use elsewhere, stop and report which,
rather than introducing a new GitHub surface inside a hygiene unit. If
`list_untriaged` must change to share the paging, stop: criterion 5 says it does
not, and a shared helper that alters its semantics is a re-scope.
