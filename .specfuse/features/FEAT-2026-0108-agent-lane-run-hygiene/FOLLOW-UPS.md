# Follow-ups — FEAT-2026-0108, gate 1

One entry per criterion in `GATE-01.md`'s definition of done that this close
could not demonstrate. The other five behaviours were demonstrated on fixtures
in this session and are recorded in `RETROSPECTIVE.md` § Measurements.

### An item that escalates with a PR already open says so and links it

Criterion, verbatim from `GATE-01.md` § Definition of done:

> An item that escalates with a PR already open says so and links it; an item
> with commits on an unpushed branch names the branch.

**The second clause holds; the first does not, end to end.** The escalation
payload renders `PR #<n>` correctly when it is handed a stopped result carrying
a PR number — that is what `tests/test_agent_escalation_run_state.py::test_stopped_item_with_open_pr_links_it`
pins, by constructing `BugLaneResult(outcome=could_not_proceed, pr_number=1532)`
directly. But `run_bug_lane` never produces that value. Its escalating branch
(`specfuse/loop/bug_lane_run.py:642-648`) returns a literal `pr_number=None` for
both `refused` and `could_not_proceed`, without calling
`extract_pr_number(session_output)` — the function T05 added, already imported in
the same module, and already proven to read the field. So the provider's
`if result.pr_number:` branch is unreachable from a real run, and item #1481's
exact escalation — PR #1532 open, text saying the lane "never reached a guardrail
or merge decision" — is still what the lane produces.

**Evidence.** Both commands run in this session, unsandboxed, against the gate's
own tree.

1. `python3 $TMPDIR/close-demos/demo5_escalation_state.py` — **exit 1**. The
   demonstration drives `BugsProvider.execute()` with a scripted `claude`/`gh`/
   `git` runner whose session output is a stopped `/fix-bug` result carrying
   `pr_number: 1532`. Three checks failed:

   ```
   FAIL the escalation names PR #1532
   FAIL and does not claim the lane never reached a guardrail
   FAIL the run summary detail names it — 'could_not_proceed'
   ```

   The same script's clauses 2, 3 and 4 passed: an unpushed `fix/1481-off-by-one`
   branch is named with its commit count, a `wip/bug-1481` ref is named with its
   commit count, and the generic sentence survives only when the run really left
   nothing behind.

2. Root cause isolated directly, same session:

   ```
   classify_outcome  -> could_not_proceed
   extract_pr_number -> 1532
   run_bug_lane      -> could_not_proceed pr_number= None
   ```

   `extract_pr_number` reads the field from the same text `run_bug_lane` throws
   away.

**Why this close did not fix it.** `WU-90`'s *Do not touch* reserves source,
tests and skills for T01–T06. The fix is a source change in
`specfuse/loop/bug_lane_run.py`, which is T04's and T05's file, not this close's.

**Re-run when.** `run_bug_lane`'s escalating branch calls
`extract_pr_number(session_output)` and puts the result on the returned
`BugLaneResult` (and, for symmetry with the rendering layer T06 already shipped,
`unpushed_work` stays the fallback when the block carried no number). Re-run
`python3 $TMPDIR/close-demos/demo5_escalation_state.py` and require exit 0; add a
`tests/test_bug_lane_pr_number_carried.py` case pinning that a stopped outcome
carrying `pr_number:` returns it, so the end-to-end path is covered and not only
the payload renderer.

**Scope note.** The change is small and additive — one call and one field on an
existing return — and it does not alter what the lane merges: a stopped outcome
never reaches a guardrail, so carrying the number forward only affects what the
escalation says.
