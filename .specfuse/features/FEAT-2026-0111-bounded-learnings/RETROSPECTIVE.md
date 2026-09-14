# FEAT-2026-0111 — bounded LEARNINGS on the dispatch path

One gate, six implementation units (five planned, plus hygiene unit T04H
inserted after a halt), one terminal close, now on its second run. T01 built
the word counter and wired a stub distillate. T02 built the weights and T03 the
accept step. T04 trimmed the three binding rules and made the cap blocking.
T04H re-synced the packaged rule mirrors T04 left stale, and T05 documented the
budget. Every implementation unit is `done`.

The first close recorded `not_met`, and the judge agreed independently
(`judged` event, 16:32:19, `disagreed: false`, 3 findings). Two measured
failures went to `FOLLOW-UPS.md` and were filed as #3315 and #3316. The operator
then re-scoped gate 1 ("re-scope it, I'd rather not touch the cap yet"). The
definition of done in `GATE-01.md` dropped the human-accepted-content clause and
the 500-word sub-budget clause, and the cap question moved to roadmap row
FEAT-2026-0112. No code changed between the two closes. The driver re-pinned at
17:50 (`cdc742c`) and ran the broad set again at 17:55 (`ok: true`,
`failing: []`). This retrospective measures against the **re-scoped**
definition, and it keeps the removed clauses' measurements in view because the
removal is the part a reviewer should weigh.

## Measurements

Every command below ran fresh in this close session, from the working tree,
with the repository venv and no git. Following the dispatch contract, this
session ran no full suite, coverage or `tier: broad` gate. Those results come
from the driver's broad run and are cited, not re-run.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_binding_block_budget -v -b` | `Ran 5 tests`, `OK` | 0 |
| Every test module the gate produced or named | `python3 -m unittest tests.test_binding_block_budget tests.test_learnings_weights tests.test_distilled_accept_step tests.test_binding_block_allocation tests.test_result_block_audience tests.test_scaffold_data_in_sync -b` | `Ran 40 tests`, `OK` | 0 |
| Live count, blocking form | `check_binding_block_budget()` | returns `total 2461, cap 2500`, no raise | 0 |
| Narrow tier for `close` (`plannext`: `plan-lint`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | `structurally valid`; WARN: 24 acceptance criteria across the gate, above 20 | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | reported in this close's RESULT block | — |

Before this session wrote anything, the closing lint exited 1 with `close-b`,
`close-c` and `close-d` unmet. The first close's `LEARNINGS.md` lines and
retrospective were already committed, so nothing showed in the working tree
yet, and the re-arm had cleared `verdict:`.

**Driver broad run, cited and not re-run.** `broad_run_result` at
`2026-09-14T17:55:02Z` recorded `ok: true, failing: []` on the tree in
`GATE-01.md`'s `broad_run:` block. That run's logs are the `*20260914T1754*` and
`*20260914T1755*` files in `work/gate-logs/`.

### Definition of done, criterion by criterion (re-scoped)

| Criterion (`GATE-01.md`) | Measured |
|---|---|
| Lint resolves the block's actual `@` references | `binding_block_word_count()` returns the four files listed in `.claude/CLAUDE.md`'s block, in block order, including `.specfuse/rules-local/learnings-distilled.md` |
| …is blocking | `check_binding_block_budget` raises `AssertionError` over cap (probe below: 97 words gives `binding block is 2501 words, over its 2500-word cap`). It is enforced by `tests.test_binding_block_allocation` under the `tests` gate. |
| …and passes on this tree | 2,461 ≤ 2,500, no raise |
| Weights: cost primary, reach tiebreaker, age bias stated in output, self-citation excluded | `score_learnings_entries()` on the live corpus returns 246 entries, and its `reach_caveat` names the tiebreaker role and the older-entry bias. Ordering and self-citation exclusion are covered by `tests.test_learnings_weights` (in the 40 above). |
| Accept step ranks against a word budget and writes nothing without explicit accept, by negative observation | `propose_distilled_learnings(word_cap=96)` gives 0 proposed / 246 cut; `word_cap=500` gives 3 / 243. Byte-identity on decline is in `tests.test_distilled_accept_step` (in the 40 above). |
| Distilled file wired into the block and counted | listed at 57 words in `files` |
| Every implementation WU `done` | T01, T02, T03, T04, T04H, T05 frontmatter: `status: done` |
| Retrospective exists; lessons promoted | this file; one new `LEARNINGS.md` entry from this close (below) |
| Per-criterion state (§5) | no `GATE-01-CRITERIA.md` in the feature folder, so `close-l` does not apply |

### Binding block word count: before and after

**Before: 2,574 words. After: 2,461 words. Net −113.**

The "before" figure comes from the pre-feature pinned build `a9374296`, pinned
at 14:39 before T01 dispatched. Its `data/rules/` mirrors were counted with
`str.split()`, the same tokenizer `binding_block_word_count` uses. That pin has
no `binding_block_word_count` (`grep -c "def binding_block_word_count"` = 0; the
current pin `cdc742c` has 1), which confirms it predates the feature. T01's own
per-file count in `PROGRESS.md` matches it file by file.

| File | Before (pin `a9374296`) | After (canonical and packaged mirror, both counted) | Δ |
|---|---|---|---|
| `.specfuse/rules/result-contract.md` | 1,078 | 1,045 | −33 |
| `.specfuse/rules/never-touch.md` | 639 | 576 | −63 |
| `.specfuse/rules/security-boundaries.md` | 857 | 783 | −74 |
| **Three binding rules** | **2,574** (74 over the cap) | **2,404** | **−170** |
| `.specfuse/rules-local/learnings-distilled.md` | absent, no `@` line | 57 | +57 |
| **Block total** | **2,574** | **2,461** (39 under) | **−113** |

**What was trimmed.** Rewording and de-duplication only, per the first close's
diff against the pin. No numbered rule, section or prohibition disappeared, and
this session's reading of the three current files agrees. `result-contract.md`
tightened its audience paragraph, Verify step 3, the failing-check paragraph,
rule 7 and closing obligations 1–4. `never-touch.md` folded §1's generated-dir
bullets and compressed §2's "must not" list. `security-boundaries.md` replaced
its restated secrets enumeration with a pointer to `never-touch.md` §2 and
compressed escalation steps 1–4. **137 of the 170 words came from
`never-touch.md` and `security-boundaries.md`, which are vendored from core**,
and which T01 had said held "no clearly-safe cut … without a human call".

**What the distilled file cost: 57 words, 2.3% of the block, and none of them is
accepted content.** The file is still T01's placeholder. With the rules at
2,404 words, the cap leaves 96 words for a distillate, and the stub uses 57 of
them.

### The sub-budget probe (re-run; this clause is now out of the definition of done)

`check_binding_block_budget` ran against a temp copy of `.claude/CLAUDE.md` and
the three current rules, with `loop.REPO_ROOT` pointed at the copy and a
synthetic distillate of N words. The counter resolves `@` paths against
`REPO_ROOT`, not against the `claude_md` argument. A first run without the patch
read the real tree and passed every N at 2,461, which is worth knowing before
reusing this probe.

```
96  PASS total 2500
97  FAIL binding block is 2501 words, over its 2500-word cap
200 FAIL binding block is 2604 words, over its 2500-word cap
500 FAIL binding block is 2904 words, over its 2500-word cap
501 FAIL .specfuse/rules-local/learnings-distilled.md is 501 words, over its 500-word sub-budget
```

Unchanged since the first close. The 500-word sub-budget is still unreachable
on the real tree, and `LEARNINGS_DISTILLED_WORD_CAP`, `docs/methodology.md` and
`.specfuse/rules-local/README.md` still state 500. The re-scope removed the
criterion but did not change the stated number. #3316 and FEAT-2026-0112 carry
it.

### Off-plan signal for gate 1, computed here

`gate_eval.evaluate_off_plan_signal(Path(feature_dir), 1)`:

```
auto=True, reasons=[]
per_wu_cost: T01 0.823196, T02 1.021311, T03 0.486376, T04 1.368262,
             T04H 0.186327, T05 0.963139, G1-CLOSE 4.022428
gate_total_cost=8.871039, blocked_human_events=[], replan_events=[], warnings=[]
```

`loop.reflection_required(Path(feature_dir), 1)` returns `False`.
`_gate_number_from_wu_id("FEAT-2026-0111/G1-CLOSE")` returns `1`, so the close-e
guard does consult it for this close. For `…/T05` it returns `None`.

**Negative observation, both directions.** Each run used a temp copy of the
feature folder, with `verdict: met` written into the close and the
`## Cost analysis` heading renamed away:

- **A, as-is.** `reasons=[]`, `reflection_required` = `False`, and
  `assert_cost_analysis_section_when_met` returns `(True, '')`. The section is
  waived.
- **B, T01's `cost_usd` forced to 19.00.** Reasons become
  `per_wu_cost_overrun: T01 actual=$19.00 planned=$6.00 ratio=3.17x` and
  `per_wu_hard_overrun: …`. `reflection_required` = `True`, and the guard
  returns `(False, "… verdict=met and gate went off-plan but '## Cost analysis'
  section absent from RETROSPECTIVE.md")`.

**What the signal does not read.** In `gate_eval.py`, the per-WU ratio checks
skip `close` and `close-intermediate` units (`_CLOSING_TYPES`), with a ceiling
of 1.5× (`PER_WU_COST_RATIO_CEILING`) and a hard ratio of 2.0×. `events.jsonl`
line 21 is a `human_escalation` (`preexisting_gate_failure`, 15:28:53), yet the
computed `blocked_human_events` is `[]`. Its `correlation_id` is the feature ID,
not a unit ID. So none of the following moved the signal: that halt, the
inserted T04H, T05's discarded attempt cycle, a close that recorded `not_met`,
or the definition-of-done re-scope.

## Was reflection suppressed for this gate? What that means for FEAT-2026-0106

**The gate stayed on-plan by the mechanism's definition.** `reasons=[]`, and
`reflection_required` returns `False` on a live gate whose pinned build carries
the function (`grep -c "def reflection_required"` = 1 in both `a9374296` and
`cdc742c`). This is the first time that has happened on a real gate. Probes A
and B show the guard waiving and demanding the section correctly.

**Reflection was not suppressed in practice, on either close.** This WU's body
lists a `## Cost analysis` section as an acceptance criterion, so the plan
author opted back into the prose the guard would waive. The section below
exists because the body asked for it, not because a guard required it.

**What that means for FEAT-2026-0106: the mechanism works as coded, and this
gate is a weak test of whether it should.** Two findings:

- **"On-plan" here means "no implementation unit overran its estimate". It does
  not mean the gate went as planned.** This gate had a feature-level halt, an
  operator-inserted unit, a discarded attempt cycle, a `not_met` close and a
  re-scoped definition of done, and the signal saw none of them (see "What the
  signal does not read"). A gate this eventful being classed as needing no
  reflection is the opposite of what FEAT-2026-0106 set out to decide.
- **It is one-sided on cost.** Units came in at 0.11×–0.39× of estimate. Nothing
  distinguishes accurate estimates from padded ones, so a plan that over-prices
  every unit suppresses reflection indefinitely. Close spend is excluded too, so
  no amount of close re-work flips it.

**Did `PROGRESS.md` carry enough?** No, not on its own. It now has eight lines.
T01's note carried the exact per-file "before" counts, and the first close's
`note:` carried the 96-word finding the re-scope rested on. Those are the two
figures this feature turns on, and both arrived. T04, T04H and T05 are fallback
lines (`attempt N outcome=passed`), so the trim's size and location, the
core-owned files and T05's failures are absent. The halt, T04H's insertion and
the re-scope are recorded only in `events.jsonl`, `PLAN.md` and `GATE-01.md`,
because `PROGRESS.md` logs unit outcomes and none of those is a unit outcome.

## Deferred verification

Criteria this close did not verify in-loop, each with the reason and where it
is actually checked:

- **The red-test-first halves of T01–T04 ("fails on HEAD before this unit's
  edits").** Re-running at a pre-feature commit needs a checkout, and a close
  runs no git. This session verified partial evidence: pin `a9374296` lacks
  `binding_block_word_count`. The first close found none of the five new symbols
  in that pin. A reviewer checks this by running each module at the branch's
  merge-base with `main`.
- **T04H's commit message** ("names the two core-owned files, the 137 words …
  and that a future core sync will halt"). This needs `git log`. It is checked at
  PR review. The 137 figure is verified above (−63 plus −74).
- **Full suite, coverage, bandit, leak-scan and the bats suites.** These are
  `tier: broad` and belong to the driver. They are cited from the 17:55
  `broad_run_result`, not re-run.
- **The designed halt on the next core sync** for `never-touch.md` and
  `security-boundaries.md` (#581 baseline guard). It is observable only with a
  core checkout present, and is checked on the next `scripts/sync-scaffold.sh`
  run with core as a sibling.
- **`GATE-01.md` arming §4, "paste the failing set into `GATE-01-REVIEW.md`
  before arming".** No such file exists in the feature folder. It was an
  arming-time human step, not part of the definition of done, and no in-loop
  surface checks it.
- **"Anything it writes to the scaffold's own block must not clobber a
  consumer's `@` lines."** This is vacuous if `specfuse/loop/scaffold.py` is
  unchanged from pin `a9374296`. That comparison is reported in this close's
  RESULT block. The only `@` line this feature added is in this repository's own
  `.claude/CLAUDE.md`.
- **Enforcement beyond this repository.** The cap is blocking only through this
  repository's `tests` gate. No driver path, lint script or `specfuse upgrade`
  step calls `check_binding_block_budget`, so consumers get the helper, not the
  check. This is stated in `CHANGELOG.md`, and no gate criterion asks for more.
- **Removed from the definition of done, not deferred:** human-accepted
  distillate content (#3315) and a reachable sub-budget (#3316). Both stay open
  in `FOLLOW-UPS.md` and FEAT-2026-0112.

## Consumer-visible contract changes

Three additions and one change. Nothing was renamed or removed, and no
configuration key changed. The first close appended all four to `CHANGELOG.md`'s
`Unreleased` section with this feature's ID. Nothing has changed since, so this
close adds no further entries.

1. **added:** `binding_block_word_count`, `check_binding_block_budget`,
   `BINDING_BLOCK_WORD_CAP` (2,500) and `LEARNINGS_DISTILLED_WORD_CAP` (500) in
   `specfuse.loop.loop`. They are enforced only by this repository's tests;
   consumers get the helper, not the check.
2. **added:** `score_learnings_entries`, `propose_distilled_learnings` and
   `apply_distilled_decisions`. Python API only; no skill or CLI.
3. **added:** budget documentation in `docs/methodology.md` and the seeded
   `.specfuse/rules-local/README.md`. The README is seeded once, so existing
   projects keep their copy.
4. **changed:** the three binding rules shipped in `specfuse/loop/data/rules/`
   are 170 words shorter, reworded with nothing removed. Consumers receive them
   on `specfuse upgrade`. Two are core-owned, and the next core sync halts on
   them by design.

## Cost analysis

**Budget of record.** `PLAN.baseline.json` totals **$28.00**: T01 $6.00, T02
$4.00, T03 $4.50, T04 $5.00, T05 $2.50 and G1-CLOSE $6.00. `PLAN.md` says
$29.50, which adds T04H's $1.50. Actuals are summed from `events.jsonl`
`attempt_outcome.cost_usd` and cross-checked against `task_completed.cost_usd`,
WU frontmatter and `gate_eval`'s `per_wu_cost`.

| WU | Planned | Actual (`events.jsonl`) | `gate_eval` / frontmatter | Actual ÷ planned | Attempts |
|---|---|---|---|---|---|
| T01 counter + stub (driver) | $6.00 | $0.823196 | $0.823196 | 0.14× | 1 |
| T02 weights (driver) | $4.00 | $1.021311 | $1.021311 | 0.26× | 1 |
| T03 accept step (driver) | $4.50 | $0.486376 | $0.486376 | 0.11× | 1 |
| T04 allocation + trim (driver) | $5.00 | $1.368262 | $1.368262 | 0.27× | 1 |
| T04H mirror sync (not in baseline) | $1.50 | $0.186327 | $0.186327 | 0.12× | 1 |
| T05 docs, surviving cycle | $2.50 | $0.963139 | $0.963139 | 0.39× | 2 |
| T05 docs, discarded first cycle | — | $0.884954 | **not counted** | — | 1 |
| **Implementation** | **$22.00** baseline / $23.50 | **$5.733566** | $4.848611 | **0.26×** | 8 |
| G1-CLOSE, first close attempt | $6.00 | $4.022428 | $4.022428 | 0.67× | 1 |
| Judge on the first close | — | $0.211180 | **not counted** | — | — |
| G1-CLOSE, this re-close | (same $6.00) | not yet in `events.jsonl` | — | — | — |
| **Recorded so far** | **$28.00** | **$9.967174** | $8.871039 | **0.36×** | |

**Reconciliation.** Frontmatter, `task_completed` and `gate_eval` agree on every
unit to six decimals. T05's surviving cycle sums exactly:
$0.4671766 + $0.4959626 = $0.9631392. **The two ledgers differ by $1.096134,
made of exactly two items.** One is T05's discarded first cycle ($0.884954), and
the other is the judge ($0.211180). $8.871039 + $0.884954 + $0.211180 =
$9.967173, which matches to rounding. The T05 cycle failed on
`test_packaged_copy_is_byte_identical` because T04 had not re-synced the
packaged mirrors. The driver halted `preexisting_gate_failure` and attributed
the failure to T05, the operator inserted T04H, and the re-arm dropped that
cycle from frontmatter. The judge's cost rides on the `judged` event, not on an
`attempt_outcome` for any unit. Neither item is an error, but `gate_eval`
understates real spend by 11%.

This re-close's own cost is unknown to this session. With $9.97 recorded, the
feature stays inside the $28.00 plan unless this attempt costs more than
$18.03. G1-CLOSE's frontmatter still carries the first attempt's $4.022428 with
no `cumulative_cost_usd`, so whether the driver adds or overwrites is visible
only after this attempt.

**Was the $5–6 correction for driver-touching units enough? It overshot, by
roughly 5×.** T01–T04 were planned at $19.50 and cost $3.699145 (19.0%), with
every unit between 0.11× and 0.27×. The corrected estimates were each above
FEAT-2026-0106's actuals ($9.13 and $6.13 against $3.50, which is 2.61× and
1.75×), while this feature's driver units cost less than the $3.50 default they
replaced. The "driver-touching" label did not predict cost in either direction.
What differed was rework. None of T01–T04 had a failed attempt, and their
sessions read 0.81M–3.91M cache tokens (`attempt_outcome.cache_read_input_tokens`).
The only non-passing attempts in this gate are T05's two mirror-sync failures,
on a unit priced at $2.50 and not labelled risky. Across both features,
actual/planned spans 0.11× to 2.61× per unit. A plan-time label moved the
estimate without capturing the variable that moves cost.

Mechanically, the over-estimate is what kept the gate on-plan. With 1.5×
ceilings and actuals at 0.11–0.39×, no unit could have tripped the signal short
of a four- to thirteen-fold miss. That makes "on-plan" here a property of the
estimates as much as of the work.

**Wall clock.** From the pin at 14:39 to the first broad run at 16:20 took 101
minutes. About 20 of those, from the 15:28 halt to the 15:49 re-pin, went to
inserting T04H. From the first close's end at 16:32 to the re-pin at 17:50 took
78 minutes of operator time on the re-scope. All four `driver_staleness_detected`
events were `halted: false`.

### Failure-class breakdown

| Failure class | Signature | Unit | Attempts | Cost | Cause |
|---|---|---|---|---|---|
| `tests` | `test_packaged_copy_is_byte_identical` | T05 (first cycle) | 1 | $0.884954 | T04 edited `.specfuse/rules/` without running `scripts/sync-scaffold.sh`; `coverage` reported `no_gate_marker` behind it |
| `tests` | `test_package_data_matches_canonical` | T05 (second cycle, attempt 1) | 1 | $0.467177 | T05's own doc edits were not mirrored to `specfuse/loop/data/docs/`; fixed in attempt 2 |

Both are one class: a canonical edit with no packaged-mirror sync. The close
units' spend is excluded because neither close attempt failed. The first close
passed its guards, and only its verdict was `not_met`.

## Retrospective

- **The instrument works and measured its own feature short. The re-scope made
  that the honest scope, not a pass.** The counter, blocking check, weights,
  accept step and trim are real and consistent with their docs. Zero LEARNINGS
  entries reach dispatch, and under the current cap zero whole entries could.
  The roadmap goal, "the rules worth following reach every dispatched session",
  is not delivered by this feature. FEAT-2026-0112 owns the decision that would
  let it be.
- **The definition of done was revised after the gate ran.** `PLAN.md` records
  this deliberately, with the operator's reason, and the removed clauses stay
  tracked (#3315, #3316) rather than dropped. Whether to accept that is the
  reviewer's call. The measurements above are unchanged either way.
- **The plan's named decision point was skipped.** `PLAN.md` and `GATE-01.md`
  said a human decides where the trim comes from. The driver ran T01 → T04 with
  no halt, because nothing in the task graph made it a stop. T04 took most of
  the trim from the two core-owned files T01 had flagged.
- **FEAT-2026-0106's reflection gate got its first on-plan gate, and the gate
  showed what "on-plan" misses.** The lesson promoted to `.specfuse/LEARNINGS.md`
  from this close is that feature-level halts, inserted units, discarded cycles,
  close outcomes and re-scopes are all outside the signal. A gate can be as
  eventful as this one and still read as needing no reflection. The first
  close's two lessons (nested budgets; don't order the full suite in a WU body)
  stand.
