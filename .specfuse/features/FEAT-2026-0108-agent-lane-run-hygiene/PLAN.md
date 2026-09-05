---
feature_id: FEAT-2026-0108
title: Agent lane run hygiene — one worktree per item, foreground gates, honest CI and PR state, real cost accounting
slug: agent-lane-run-hygiene
branch: feat/FEAT-2026-0108-agent-lane-run-hygiene
roadmap_goal: An unattended `specfuse agent` run never attributes one item's edits to another, never loses a finished fix to a session that ended while a gate command ran, never reports a pending CI run as red or a found PR as missing, and records the tokens each item spent so `max_tokens_per_run` can fire.
autonomy_default: review
status: active
planned_cost_usd: 40.00
---

# Plan: Agent lane run hygiene

The 2026-09-02 unattended `specfuse agent` run over the generator repository
attempted 78 items, merged 2, and escalated 72. Reading the escalations
(issues #3177, #3178, #3179, #3180, #3183) shows that most were not the agent
failing at bugs; they were the lane failing at running. Twenty items escalated
`could_not_proceed` with the same recorded reason, that the session was
"waiting for the background test run's completion notification": the fix was
done, the gate was running, and the headless session ended. Seven were declined
`ci_not_green` seconds after their PR opened, before CI had a conclusion. Three
were reported `pr_not_found` for PRs that existed. One item's complete, passing
fix was left as uncommitted edits on a branch named for a different issue. And
every run reports `tokens spent: 0`, so the token budget an operator configures
can never fire.

The WU driver lane already has each of these right: one fresh session per
unit, `--output-format json` with the usage envelope harvested, a per-unit
squash on the unit's own commit, and gates run by the driver rather than by the
session. This feature brings the agent lane up to the same standard, in six
units.

`main` has moved since the reporter's 0.12.1: CI is polled for up to 600 s
(#1786) and the PR lookup reads the repository's PR list instead of the lagging
search index (#1984). What remains is what those fixes left explicitly for
later — a pending-at-deadline result still declines under the wrong name, and
the PR number is still re-discovered rather than carried.

## Scope boundary

**IN.** `specfuse/agent/` (run loop, budget, worktree, the three invoke
modules, providers), `specfuse/loop/bug_lane.py`, `bug_lane_run.py`,
`labels.py`, the `/fix-bug` skill's headless RESULT block, and
`monitor/autofix_invoke.py` only where it builds the `/fix-bug` argv.

**OUT, deliberately.**

- **Parallel items.** One worktree per item is what parallel dispatch will
  need, but items still run one at a time here. FEAT-2026-0105 owns fan-out
  for the driver; the agent lane follows it.
- **The WU driver's own gates, squash, or dispatch** (`loop.py`). Nothing here
  touches the feature loop.
- **Changing what the bug lane merges.** Guardrail semantics stay; only the
  pending state gets its own name.
- **The signature-extraction defect** (#3222) and **live tests filing scratch
  issues** (#3223). Separate bugs.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rn "output-format" specfuse/agent/*.py specfuse/monitor/autofix_invoke.py
  -> 0 hits. Every agent-lane dispatch omits it; loop.py:3243 passes it and
     loop.py:1391-1396 harvests the usage block. T01 lifts that into one
     shared invoker rather than copying the parse four times.

grep -rn "spend=" specfuse/
  -> 0 hits. ActionOutcome.spend (run.py:141) is never set; budget.record_tokens
     (run.py:543) faithfully records zero. T01 sets it.

grep -n "def " specfuse/agent/worktree.py
  -> current_branch, is_dirty, restore_branch. Saves and restores the branch
     the run started on; no per-item isolation. T02 builds on it.

grep -n "timeout" specfuse/agent/run.py specfuse/loop/bug_lane_run.py
  -> 0 hits in the runner (_default_runner, run.py:221). The session ends on
     its own; the "item budget" in #3178 is the headless session's turn/wall
     limit, reached while a backgrounded gate command was still running. T03
     keeps gates in the foreground and gives the invocation a real timeout.

grep -n "_CI_PENDING\|deadline_seconds" specfuse/loop/bug_lane_run.py
  -> pr_ci_conclusion already polls to CI_WAIT_SECONDS (600) and its
     docstring says the pending-at-deadline split "is safe whenever someone
     wants it". T04 wants it.

grep -n "_find_pr_for_issue\|REASON_PR_NOT_FOUND" specfuse/loop/bug_lane_run.py
  -> lookup fixed (#1984), payload fixed (#3180); the number is still
     re-discovered. T05 carries it from the RESULT block.
```

**Verdict: extending five existing mechanisms; building one small new one (the
shared invoker) and one new guardrail reason.**

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T04 adds a new declining reason, `ci_pending`, with its own label. **What does
the guardrail report on an input already in its intended final state?** A
concluded run reports `success` or the existing `ci_not_green`; `ci_pending` is
returned only when the poll deadline passes with a check still queued or
running. It is a decline (fail closed) that names a retry as the right response,
never a merge. The label registry test (`tests/test_bug_lane_labels_registered.py`)
requires every declining reason to have a label; T04 adds the row.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0108/T01
        file: WU-01-shared-invoker-and-spend.md
        depends_on: []
      - id: FEAT-2026-0108/T02
        file: WU-02-worktree-per-item.md
        depends_on: []
      - id: FEAT-2026-0108/T03
        file: WU-03-foreground-gates-and-timeout.md
        depends_on: [FEAT-2026-0108/T01]
      - id: FEAT-2026-0108/T04
        file: WU-04-ci-pending-reason.md
        depends_on: []
      - id: FEAT-2026-0108/T05
        file: WU-05-carry-pr-number.md
        depends_on: [FEAT-2026-0108/T03]
      - id: FEAT-2026-0108/T06
        file: WU-06-escalation-reads-run-state.md
        depends_on: [FEAT-2026-0108/T02, FEAT-2026-0108/T05]
      # --- hygiene precursor to the close's re-run, authored after the close's
      # first attempt recorded not_met on one criterion (see WU-05H body) ---
      - id: FEAT-2026-0108/T05H
        file: WU-05H-escalating-outcomes-carry-pr-number.md
        depends_on: [FEAT-2026-0108/T05, FEAT-2026-0108/T06]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0108/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0108/T01
          - FEAT-2026-0108/T02
          - FEAT-2026-0108/T03
          - FEAT-2026-0108/T04
          - FEAT-2026-0108/T05
          - FEAT-2026-0108/T05H
          - FEAT-2026-0108/T06
```

## Post-merge checklist

- Run `specfuse agent` unattended against the generator repository for one
  night and compare the escalation mix with 2026-09-02's: `could_not_proceed`
  with a "waiting for" reason should be zero, `ci_not_green` should name only
  red builds, `pr_not_found` should be zero, and the summary's `tokens spent`
  should be non-zero.

## Notes

- **Single gate, six substantive units** (threshold 8, `docs/methodology.md` §6).
- **Dependencies are about shared files, not logic.** T03 and T05 edit the
  same invocation path after T01 reshapes it; T06 reads what T02 and T05
  record. T02 and T04 could run in parallel with T01 on a driver that fans out.
- **None of these units edit `specfuse/loop/loop.py`**, so no driver-restart
  halt is expected. T04 edits `bug_lane.py` and `labels.py`; check whether the
  driver's staleness path counts those (`driver_paths_in`) and expect one halt
  if it does.
- **Measurement baseline** for the close: `spend=` occurrences in
  `specfuse/`: 0; `--output-format` in agent invocations: 0; declining reasons:
  8; the 2026-09-02 run's escalation mix as recorded in #3177-#3183.
- **Evidence folder.** The run report these issues were written from is
  summarised in the issues themselves; the operator's local analysis of the
  loop's own history is under `reviews/` (gitignored) and is not needed by
  any unit.
