---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_changelog_fragments -v -b"
cost_budget_usd: 26.00
---

# Gate 1 — concurrent PRs stop conflicting on the changelog, and no entry gets lost

## Definition of done

**Stated as an outcome.** In temporary git repositories driven through the real code:

1. Two branches each run `add` in `fragments` mode, and the second merges clean with real
   `git merge` after the first. Control: the same flow in `single` mode conflicts.
2. A feature whose entry exists only as a fragment passes `close-k`, `specfuse lint --closing`
   and the terminal auto-close guard. A feature with no entry in either form fails all three.
3. A release leaves every fragment in the new section, the section parses clean, and no
   consumed fragment remains. A malformed fragment refuses the release with the tree untouched.
4. `check` exits non-zero naming a malformed fragment, and zero on a valid or absent directory.
5. A project with no `changelog.mode` key behaves as before: `add` edits `CHANGELOG.md`, and a
   release with no fragments produces the same output as today.

The `feature_oracle` proves 1–5. It is red on the current tree;
`FEAT-LOOP-2026-0249/T01` is the walking skeleton that creates it and turns clause 1 and clause 5's writer
half green, with every other class `unittest.skip` naming its owner (T02–T04). A skip
surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One reader, one writer.** All three guards go through one helper; skills and rules call `add`.
- **Positive controls.** Clause 1 pairs with the conflicting `single` flow, clause 2 with the
  no-entry failure.
- **Temp repos only.** Fixture commits set `-c commit.gpgsign=false`.
- **Expected self-halt.** `loop.py`, `closing_requirements.py`, `lint_closing.py` and shipped
  rules are judge surfaces; acknowledge the stop with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
