---
id: FEAT-2026-0048/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/loop/bug_lane_state.py
  - tests/test_bug_lane_state.py
produces_driver_helper: GitHubMergeCapState, triaged_bug_intake
---

# GitHub-resident lane state — the durable merge cap and the triaged-bug intake

**Objective.** Create `specfuse/loop/bug_lane_state.py` with two readers whose
state lives on GitHub rather than on the runner's disk: `GitHubMergeCapState`
(implementing T02's Protocol) and `triaged_bug_intake` (triaged bug issues as a
lane input alongside diagnosed findings).

**Context.** Correlation ID `FEAT-2026-0048/T03`. Depends on
`FEAT-2026-0048/T02`, which defined the state-reader `Protocol` this WU
implements.

**Both readers are here for the same reason: the process's memory must survive
to the next invocation, and the runner's disk does not.** Per
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]` —
the runner is a GitHub Actions container today and an AKS CronJob tomorrow, so
each invocation starts with an empty disk. A disk-backed merge counter would
never reach its cap: nothing errors, no log line appears, and code review sees a
rate limiter. **The guarantee would be decorative.**

**Copy `specfuse/monitor/autofix_state.py` exactly.** Read it first. It solved
this same problem for the autofix daily cap and is the shape to follow:

- an HTML-comment marker written onto the artifact the work is about,
- `ROLLING_WINDOW_SECONDS = 24 * 60 * 60`,
- a count **re-derived from that state on every read**, never a maintained
  counter anyone must keep in sync,
- an injected `runner` callable so tests never reach the network.

**Do not import from it** — the two caps count different events on different
artifacts. Copy the convention, not the code.

**Marker convention.** Follow the repo's existing `<!-- specfuse:… -->` prefix
family (`specfuse:finding`, `specfuse:diagnosis`, `specfuse:autofix-attempt`).
This WU's marker is `<!-- specfuse:bug-automerge at={at} -->`, written onto the
merged PR. Fix this literal here; T04 quotes it verbatim.

**The intake reader.** `triaged_bug_intake(runner, repo, *, limit) -> list`
returns issues eligible to enter the lane: those carrying a triage marker whose
category is the bug category, per `specfuse.loop.triage`'s existing
`parse_marker` / `CATEGORIES`. **Call triage's parser; do not re-parse the
marker format here** — a second parser for one format is drift waiting to
happen. Diagnosed monitoring findings remain the other intake and are already
handled by `monitor/autofix_run.py`; this WU adds the second door, it does not
replace the first.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_bug_lane_state.py::TestGitHubMergeCapState::test_count_is_rederived_from_markers`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/bug_lane_state.py` defines `GitHubMergeCapState` satisfying
   the state-reader `Protocol` T02 declared — a test asserts an instance is
   accepted by `evaluate_merge_guardrails` with no adapter.
3. `ROLLING_WINDOW_SECONDS = 24 * 60 * 60` is a module-level constant.
4. The merge marker literal is exactly
   `<!-- specfuse:bug-automerge at={at} -->` and lives in a module-level
   template constant. A test asserts the rendered marker round-trips through the
   module's own parser.
5. The 24h count is **re-derived** by reading markers on each call — a test
   asserts that two successive reads over the same fixture data return the same
   count with no stored counter, and that a marker outside the window is
   excluded.
6. A malformed or unparseable marker is **ignored**, not fatal, and does not
   inflate or deflate the count. A test covers a garbage marker among valid ones.
7. Every GitHub access goes through an injected `runner` callable — a test
   exercises the whole module with a fake runner and no network. A test asserts
   the module opens no local file for cap state.
8. `record_merge(runner, repo, pr_number, *, at)` writes the marker onto the
   merged PR, and is idempotent: called twice for the same PR it does not
   produce two markers. A test covers the second call.
9. `triaged_bug_intake(runner, repo, *, limit) -> list` returns only issues
   whose triage marker names the bug category, using
   `specfuse.loop.triage.parse_marker` and `CATEGORIES` — a test asserts an
   untriaged issue, a triaged non-bug issue, and a triaged bug issue are
   classified correctly.
10. A test asserts `triaged_bug_intake` re-uses triage's parser rather than
    re-implementing it: `bug_lane_state` contains no second regex over the
    triage marker format.
11. An issue already carrying the `auto-fix-attempted-failed` label
    (`autofix_state.AUTOFIX_FAILED_LABEL`) is excluded from the intake — a
    failed prior attempt does not re-enter the lane on the next run. Import that
    constant; do not retype the label string.
12. `python3 -m unittest tests.test_bug_lane_state -v` exits zero after this
    WU's edits.
13. `python3 -c "from specfuse.loop.bug_lane_state import GitHubMergeCapState, triaged_bug_intake"`
    exits zero.

**Do not touch.** `specfuse/monitor/autofix_state.py` — read it for shape, do
not edit or import it (except `AUTOFIX_FAILED_LABEL` per criterion 11).
`specfuse/loop/triage.py` — call its parser, do not modify it.
`specfuse/loop/bug_lane.py` — T02 owns the predicate; this WU supplies state to
it. Anything that performs a merge — T04. `.specfuse/roadmap.md`. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 12 and the symbol check in 13.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`triage.parse_marker` / `CATEGORIES` do not expose a bug category usable for
intake filtering (report the actual shape rather than inventing a second
classification); or the marker convention would collide with an existing
`specfuse:` marker prefix already in use on pull requests. If
`specfuse/loop/bug_lane_state.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
