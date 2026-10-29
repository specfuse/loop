---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_migrate_all_repo_stays_valid -v -b"
cost_budget_usd: 28.00
broad_run:
  tree: 054923b0bea95ba720a9a42a693f4da9e9ea960f:0914de97ded0fcbacedb4b7362a31ef9ce1e269e:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:6dd6c8d6e05565b4d72ac742014b0b59baf2a9d9:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9b3386cac79ef7bbd03df4b421ab7dc4a900d9d6:bbd1aea514612d76722a18c7aece7c767cf1a076:be95bbbe8af961d4ea40db9c5d192a34bb0ff086:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d8bc23684bdcd9c4ba7e11762bbb5134984b899a:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:e5e805779fc87473b32b3b126543f4a235f89475:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-10-29T19:42:39.557346+00:00
  ok: true
  failing: []
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
