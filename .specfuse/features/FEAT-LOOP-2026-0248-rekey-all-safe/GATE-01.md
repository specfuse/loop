---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_migrate_all_repo_stays_valid -v -b"
cost_budget_usd: 28.00
---

# Gate 1 — a full rename leaves a repository valid, and can be rehearsed first

## Definition of done

**Stated as an outcome.** In temporary git repositories driven through the real module:

1. After `ids migrate --all --apply`, an `agent-policy.yml` queue naming an old ID
   validates clean (resolved through `.specfuse/id-aliases.yml`).
2. `--apply` ends by running `lint_plan` over every feature, `lint_roadmap` and agent-policy
   validation; it exits zero on a valid result and non-zero, naming each error and how to
   undo, on an invalid one.
3. A `features/<ID>-<slug>` path or `<ID>-<slug>` string in code, config or tests is
   rewritten only when that exact folder exists; a fixture-only path is left alone, and an
   exact folder name in a code table (an exemption dict) is rewritten.
4. `--include-prose <path>…` rewrites prose only under the named paths; bare
   `--include-prose` still means all; `--exclude-id` leaves every mention of that ID alone.
5. `--rehearse` runs the rename in a throwaway worktree, runs the tests command there,
   reports pass/fail with the failing tests, removes the worktree and leaves the real tree
   byte-identical.
6. On this repository, `ids migrate --all` with key `LOOP` and this feature's chosen prose
   scope, run with `--rehearse`, exits zero: the full suite passes on the renamed copy.

The `feature_oracle` proves 1–5. It is red on the current tree;
`FEAT-LOOP-2026-0248/T01` is the walking skeleton that creates it and turns clauses 1 and 2
green, with every other class `unittest.skip` naming its owner (T02–T04). Clause 6 is T05's
rehearsal, recorded in its evidence and re-run by the close. A skip surviving to the close
is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One alias reader.** Every old-ID lookup goes through `ids.resolve`.
- **Positive controls.** Every "left alone" fixture is paired with one that is rewritten.
- **The real tree is never renamed.** No unit runs `--apply` against this repository's
  working tree; rehearsals run in throwaway worktrees.
- **Expected self-halt.** `agent_policy.py` and `ids.py` are judge surfaces; acknowledge
  the stop with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
