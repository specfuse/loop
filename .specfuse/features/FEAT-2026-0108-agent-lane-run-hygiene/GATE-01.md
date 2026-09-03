---
gate: 1
status: open
cost_budget_usd: 50.00
---

# Gate 1 — an unattended agent run isolates, waits, reports, and counts correctly

## Definition of done

Stated as behaviours demonstrable on fixtures with an injected runner, not as
six units:

- An agent run over two fixture items leaves each item's edits on its own
  worktree and branch; a fixture item that ends without committing leaves
  nothing on the tree the next item starts from, and its work is reachable
  under an item-tagged ref named in the run summary.
- A `/fix-bug` invocation built by the lane carries a wall-clock timeout, runs
  its gate commands in the foreground, and a fixture whose gate takes longer
  than the item's reasoning would have is still reported from its RESULT
  block rather than as `could_not_proceed`.
- A PR whose checks are still `queued` at the poll deadline is declined
  `ci_pending` with the `bug-lane:ci-pending` label, never `ci_not_green`; a
  red run is still `ci_not_green`.
- The lane evaluates guardrails on the PR number `/fix-bug`'s RESULT block
  reported; the list lookup runs only when the block carried none.
- An item that escalates with a PR already open says so and links it; an
  item with commits on an unpushed branch names the branch.
- Every provider outcome carries `spend` from the CLI's usage envelope; a run
  with `max_tokens_per_run` set below one item's spend stops after that item
  with `STOP_CAP`, and the summary's `tokens spent` is non-zero.

If all six units are `done` and any behaviour above cannot be demonstrated,
this gate is not done.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **T04 adds a declining reason and a label.** PLAN.md answers §2: a concluded
  run never reports `ci_pending`; the registry test enforces the label row.
- No flag is introduced or flipped.
- **The close is load-bearing** (it runs the six fixture demonstrations) and
  carries `auto_close_disabled: true`.

## Reflection notes

<Written by the human at review time.>
