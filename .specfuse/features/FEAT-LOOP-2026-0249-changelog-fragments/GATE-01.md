---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_changelog_fragments -v -b"
cost_budget_usd: 26.00
baseline:
  sha: 3443a23c22cf48eac997f12f7c9288e001cb22e9
  probed_at: 2026-11-02T16:30:40.442893+00:00
  tree: 12064a6191eeb830a9826d911a8543fbaba3da75:16339b18c202f8359cc4b4b153715fa6895a079e:1ccc3c2339db27f65e69ab179e57fa95b5890a80:20240e3de99e3993fc6a09485409d69e78eab577:27968248a450a842ccd187b7dce0fb0ded934866:2e29b2f7e073a0cbe290f01d3b397e1cdd10c81c:3472f7e05a2871a017bb583f5374d42e34db8ee1:42796ea0e0a6c03811b0e4bc9dbd3b5ee62dd2e4:4acc6dfc5e8cece358c167d876515eba4a39a500:6c679295e2c653c7a11f14b3c522196f71302111:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:ba9407c8db4db0875eafe248590b4ea99fc19601:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366:fb566fdbeba19af285d03c14d675b03bdc228c9f
  entry_sha: 3443a23c22cf48eac997f12f7c9288e001cb22e9
  source: attributed:FEAT-LOOP-2026-0249/T06
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "(failures=1,"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
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
