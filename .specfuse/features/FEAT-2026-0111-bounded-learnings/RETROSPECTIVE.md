# FEAT-2026-0111 — bounded LEARNINGS on the dispatch path

One gate, six implementation units (five planned, plus hygiene unit T04H
inserted after a halt), one terminal close. T01 built the word counter and
wired a stub distillate. T02 built the weights and T03 the accept step. T04
trimmed the three binding rules and made the cap blocking. T04H re-synced the
packaged rule mirrors T04 left stale, and T05 documented the budget. Every unit
passed. T05 needed three dispatched attempts across two attempt cycles.

**Two facts to read first.**

1. **The binding block went from 2,574 to 2,461 words.** That is 170 words
   trimmed from the three rules and 57 added by the distillate. **None of those
   57 words is a LEARNINGS entry.** The distillate is still T01's placeholder;
   no human accepted anything into it, and nothing outside the tests calls the
   accept step.
2. **The distillate's 500-word sub-budget cannot be spent.** With the trimmed
   rules at 2,404 words, the block has 96 words of room. Any distillate from 97
   to 500 words fails the total cap first, and the ranked proposal at 96 words
   selects 0 of 244 entries.

Both are measured below, and both are recorded in `FOLLOW-UPS.md`.

## Measurements

All commands ran fresh in this close session, from the working tree at gate 1's
head, sandboxed, with no git. Per the dispatch contract, this session did not
run the full suite, coverage, or any `tier: broad` gate. Those figures come
from the driver's once-per-gate broad run, cited by log.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` (narrow) | `python3 -m unittest tests.test_binding_block_budget -v -b` | `Ran 5 tests`, `OK` | 0 |
| All test modules this gate produced or named | `python3 -m unittest tests.test_binding_block_budget tests.test_learnings_weights tests.test_distilled_accept_step tests.test_binding_block_allocation tests.test_result_block_audience tests.test_scaffold_data_in_sync -b` | `Ran 40 tests`, `OK` | 0 |
| Symbol check (§9) | `python3 -c "from specfuse.loop.loop import binding_block_word_count, check_binding_block_budget, score_learnings_entries, propose_distilled_learnings, apply_distilled_decisions"` | imports | 0 |
| Mirrors byte-identical (T04H) | `cmp .specfuse/rules/<f>.md specfuse/loop/data/rules/<f>.md` for all three | identical | 0 ×3 |
| Narrow tier for `close` (`plannext`: `plan-lint`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | `structurally valid`; one WARN: 24 acceptance criteria across the gate, above 20 | 0 |
| Closing lint | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | see the end of this section | — |

**Driver broad run, cited and not re-run.** `broad_run_result` at
`2026-09-14T16:20:24Z` recorded `ok: true, failing: []`, on the tree in
`GATE-01.md`'s `broad_run:` block. The logs are in `work/gate-logs/`.
`tests-20260914T161954053406Z.log` shows `Ran 3986 tests in 207.616s`,
`OK (skipped=3)`. `coverage-20260914T161956329337Z.log` shows `TOTAL … 93%`
against `--fail-under=90`. `leak-scan-20260914T162010746243Z.log` shows
`leak-scan: clean`, and `lint-…161954104522Z.log` shows `All checks passed!`.

### Binding block word count: before and after

**Before: 2,574 words.** Two independent sources agree on it. The first is the
pre-feature pinned driver build `a9374296` (pinned before T01; its
`data/rules/` mirrors were in sync with canonical until T04). Counting its
files with Python's `str.split()`, the same tokenizer `binding_block_word_count`
uses, gives:

| File | Before (pin `a9374296`) | T01's recorded count (`PROGRESS.md`) | After (`binding_block_word_count()`) | Δ |
|---|---|---|---|---|
| `.specfuse/rules/result-contract.md` | 1,078 | 1,078 | 1,045 | −33 |
| `.specfuse/rules/never-touch.md` | 639 | 639 | 576 | −63 |
| `.specfuse/rules/security-boundaries.md` | 857 | 857 | 783 | −74 |
| `.specfuse/rules-local/learnings-distilled.md` | absent | 57 (stub) | 57 | +57 |
| **Total** | **2,574** (74 over) | 2,631 | **2,461** (39 under) | **−113** |

The second source is T01's own count, which matches the pin file by file. The
pin also carries none of the five new symbols (`grep -c "def <symbol>"` = 0 for
each), which confirms it predates the feature. The "after" row is also
`check_binding_block_budget()`'s return value (no raise). The three packaged
mirrors are byte-identical to it.

**What was trimmed.** From `diff <pin>/data/rules/<f>.md .specfuse/rules/<f>.md`:
rewording and de-duplication only. No numbered rule, section or prohibition
disappeared.

- `result-contract.md` (−33). Tightened the audience paragraph, Verify step 3,
  the failing-check paragraph, rule 7 and closing obligations 1–4. T01 had named
  the closing-obligations section (~180 words) as the densest candidate. T04
  took 33 words from this whole file.
- `never-touch.md` (−63). The §1 generated-directory paragraph and its three
  bullets became two bullets. The §2 enumeration and "must not" bullets were
  compressed.
- `security-boundaries.md` (−74). The restated secrets enumeration became a
  pointer to `never-touch.md` §2. Escalation steps 1–4 and the "common mistake"
  paragraph were compressed.

137 of the 170 words came from the two files that T01 had said held "no
clearly-safe cut … without a human call". Both are core-owned (T04H's body).

**Who saw the headroom before the trim.** T01's Do-not-touch says trimming is
"T04's, after a human has seen the number". `events.jsonl` shows T01
`task_completed` at `14:47:35`, T02 at `14:51:42`, and T04 `task_started` at
`14:51:42`. Between them there is no halt, no `human_escalation` event and no
`awaiting_review`. No `GATE-01-REVIEW.md` exists in the feature folder. The
driver ran from T01 to T04 with no stop at which a human could have seen the
number.

**What the distilled file cost: 57 words, 2.3% of the block, and none of them
is accepted content.** The file reads `# Distilled LEARNINGS (stub)` /
"Placeholder for the human-accepted, weight-ranked distillate …". A `grep` over
`specfuse/`, `scripts/`, `.specfuse/scripts/` and `plugins/` finds no caller of
`propose_distilled_learnings` or `apply_distilled_decisions` outside their
definitions. Only `tests/test_distilled_accept_step.py` calls them.
`check_binding_block_budget`'s only caller is
`tests/test_binding_block_allocation.py`. The cap is held in this repository by
the `tests` gate. It is not a lint script, and no consumer project enforces it.
`scaffold.py` is byte-identical to the pin's, so the scaffold writes neither the
`@` line nor the check into consumer blocks.

### The sub-budget probe

`check_binding_block_budget` ran against a temp copy of the real
`.claude/CLAUDE.md` and three trimmed rules, with a synthetic distillate of N
words:

```
96  PASS total 2500
97  FAIL binding block is 2501 words, over its 2500-word cap
200 FAIL binding block is 2604 words, over its 2500-word cap
500 FAIL binding block is 2904 words, over its 2500-word cap
501 FAIL .specfuse/rules-local/learnings-distilled.md is 501 words, over its 500-word sub-budget
```

T04's criterion says "exceeding it fails before the total does". That holds
only in `test_sub_budget_failure_is_named_before_the_total_failure`'s fixture,
whose block contains the distillate alone.

**Corpus probe of the weights (T02/T03).** `score_learnings_entries()` on the
live `LEARNINGS.md` returns 244 scored entries under 144 distinct tags. 118
carry cost > 0, 112 carry at least one matched `failure_signatures` value (46%,
the share T02's escalation trigger asked about), and 158 have reach > 0. The
plan's "82 of 133" is on a different counting unit and an older corpus, so the
two are not directly comparable. `propose_distilled_learnings(word_cap=96)`
proposes **0** entries (244 cut). `word_cap=500` proposes **3** (241 cut).

### Off-plan signal for gate 1, computed here

`gate_eval.evaluate_off_plan_signal(feature_dir, 1)`:

```
auto=True, reasons=[]
per_wu_cost: T01 0.823196, T02 1.021311, T03 0.486376, T04 1.368262,
             T04H 0.186327, T05 0.963139, G1-CLOSE 0.0
gate_total_cost=4.848611, blocked_human_events=[], replan_events=[]
```

`loop.reflection_required(feature_dir, 1)` returns `False`. The close is
running on pin `1f9d987`, where `grep -c "def reflection_required"` = 1, so the
FEAT-2026-0106 mechanism is present in the build that will judge this close.

**Negative observation, both directions.** Both runs used a temp copy of the
feature folder, with `verdict: met` written into the close and no
`## Cost analysis` section:

- **A, as-is (on-plan).** `reflection_required` = `False`, and
  `assert_cost_analysis_section_when_met` returns `(True, '')`. The section is
  not demanded.
- **B, T01's cost forced to $19.00.** Reasons become
  `per_wu_cost_overrun: T01 actual=$19.00 planned=$6.00 ratio=3.17x` and
  `per_wu_hard_overrun: …`. `reflection_required` = `True`, and the guard
  refuses with `verdict=met and gate went off-plan but '## Cost analysis'
  section absent`.

### PROGRESS.md: what it held, and where the rest came from

`PROGRESS.md` exists (unlike FEAT-2026-0106's close) and has six entries. Three
are agent summaries: T01 with a `note:`, then T02 and T03. Three are fallback
lines: T04, T04H and T05, each `attempt N outcome=passed`. The dispatched
sessions' local transcripts show why. T04's final message is "Full test suite
running unsandboxed in background; will report RESULT once it completes." and
T04H's is "Will get notified when background suite finishes." Neither emitted a
RESULT block. T05's final attempt emitted a block with no `summary:` the driver
parsed. Both T04 and T04H bodies told the unit to run the full suite.

| What this close needed | Did `PROGRESS.md` carry it? | Where it actually came from |
|---|---|---|
| Per-file "before" word counts | **yes**, T01's note, exact match | cross-checked against pin `a9374296` |
| Size and location of the trim | no, T04's line is a fallback | `diff` against pin `a9374296` |
| Which trimmed files are core-owned | no, T04H's line is a fallback | T04H's WU body |
| Why T05 failed and the gate halted | no, T05's line is a fallback | `events.jsonl` |
| Costs, off-plan verdict | not its job | `events.jsonl`, `gate_eval` |

Transcript profile of the dispatched sessions (tool calls / `unittest discover`
invocations): T01 33/3, T02 43/0, T03 15/0, T04 57/2, T04H 6/1, T05 43/6, 18/1
and 28/0 across its three attempts.

### Closing lint

`python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` was run after
this file, `FOLLOW-UPS.md`, the `LEARNINGS.md` entries, the `CHANGELOG.md`
entries and `verdict:` were all written. Its exit code is reported in this
close's RESULT block. Before any of them existed, the same command exited 1
with close-a, close-b, close-c and close-d unmet.

## Was reflection suppressed for this gate? What that means for FEAT-2026-0106

**The gate stayed on-plan.** `evaluate_off_plan_signal` returned no reasons,
with no blocked-human event, no `replan` and no cost overrun. This is the first
real gate on which `reflection_required` returned `False`, on a build that
carries it.

**The guard's suppression worked, and probe A/B above shows it both ways.
Reflection was not suppressed in practice on this close, for two reasons.**

1. This close's own WU body requires a `## Cost analysis` section as an
   acceptance criterion. The plan author opted back into the prose the guard
   would have waived.
2. The advisory verdict here is `not_met`, and `close-e` applies only on `met`.
   So the guard never had a `met` close to waive on this gate.

**What that means for FEAT-2026-0106.** The mechanism is now observed firing
correctly on a live gate, not only in tests. The question FEAT-2026-0106 left
open, whether `PROGRESS.md` carries enough to replace reflection, is only
partly answered, and the answer is "not on this gate". It carried the one number
the drafting of T04 depended on. It carried nothing about the trim itself, the
core-owned files or the halt, because half its entries were fallback lines.

Two findings qualify "on-plan":

- **The predicate is one-sided.** It fires on overruns only. This gate's units
  came in at 11–39% of estimate, and nothing in the signal distinguishes "on
  plan" from "padded by 3–9×". A plan that over-prices every unit will suppress
  reflection indefinitely.
- **A re-armed cycle's cost is invisible to it.** T05's first attempt cycle
  ($0.884954, failed on T04's stale mirrors) was discarded at the re-arm.
  `per_wu_cost` reads T05 at $0.963139, and so does T05's frontmatter.
  `events.jsonl` has $1.848093 for T05. Here the gap did not change the verdict.

One more observation for whoever maintains `close-f`. The dispatch skeleton's
`summarize_attempt_failure_classes(feature_dir, 1, …)` returns
`(no non-passing attempts in scope)` for this gate, although `events.jsonl`
holds two failed T05 attempts. `_gate_number_from_wu_id("FEAT-2026-0111/T05")`
returns `None`, so `T`-numbered units are filtered out of the gate scope, and no
`RETROSPECTIVE.md` skeleton was pre-created for this close.

## Deferred verification

Criteria this close did not verify in-loop, each with the reason and where it
is actually checked:

- **"Fails on HEAD before this unit's edits" (T01, T02, T03, T04 red-test
  halves).** Re-running a test at a pre-feature commit needs a checkout, and a
  close session runs no git. Partial evidence: pin `a9374296` defines none of
  the five symbols, so each module would fail at import. Fully checkable only
  by a reviewer running each module at the branch's merge-base with `main`.
- **T04H: "the commit message names the two core-owned files, the 137 words …
  and that a future core sync will halt".** Needs `git log`, which a close
  cannot run. It is checked at PR review against commit `e471a2f`. The 137
  figure itself is verified here: never-touch −63 plus security-boundaries −74.
- **T04H/T05: full suite green; T05: `leak_scan.py --all` exits 0.** These are
  `tier: broad` and belong to the driver. They are cited from the 16:20 broad
  run logs above, not re-run.
- **The designed halt on the next core sync** (`never-touch.md`,
  `security-boundaries.md` vs core's baseline, #581). It can only be observed
  with a core checkout present. It is checked on the next
  `scripts/sync-scaffold.sh` run with core as a sibling.
- **`GATE-01.md` arming §4: "apply [the severity flip] locally and paste the
  failing set into `GATE-01-REVIEW.md` before arming".** That file does not
  exist in the feature folder. It was an arming-time human step, and no in-loop
  surface checks it.
- **"Anything this gate writes to the scaffold's own block must not clobber a
  consumer's `@` lines" (`GATE-01.md`).** Verified vacuously: `scaffold.py` is
  byte-identical to pin `a9374296`'s, so this gate wrote nothing to the
  scaffold's block. The only `@` line added is in this repository's own
  `.claude/CLAUDE.md`.

## Consumer-visible contract changes

Three additions and one change. Nothing was renamed, and no configuration key
changed. All four are appended to `CHANGELOG.md`'s `Unreleased` section with
this feature's ID.

1. **added:** `binding_block_word_count`, `check_binding_block_budget`,
   `BINDING_BLOCK_WORD_CAP` (2,500) and `LEARNINGS_DISTILLED_WORD_CAP` (500) in
   `specfuse.loop.loop`. Enforced only by this repository's tests; consumers get
   the helper, not the check.
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
$4.00, T03 $4.50, T04 $5.00, T05 $2.50 and G1-CLOSE $6.00. `PLAN.md` now says
$29.50, which adds T04H's $1.50 from the re-arm. Actuals are summed from
`events.jsonl` `attempt_outcome.cost_usd` and cross-checked against
`task_completed.cost_usd`, WU frontmatter, and `gate_eval`'s `per_wu_cost`.

| WU | Planned | Actual (events) | Frontmatter / `gate_eval` | Actual ÷ planned | Attempts | Wall |
|---|---|---|---|---|---|---|
| T01 counter + stub (driver) | $6.00 | $0.823196 | $0.823196 | 0.14× | 1 | 486.9s |
| T02 weights (driver) | $4.00 | $1.021311 | $1.021311 | 0.26× | 1 | 245.9s |
| T03 accept step (driver) | $4.50 | $0.486376 | $0.486376 | 0.11× | 1 | 138.1s |
| T04 allocation + trim (driver) | $5.00 | $1.368262 | $1.368262 | 0.27× | 1 | 592.1s |
| T04H mirror sync (not in baseline) | $1.50 | $0.186327 | $0.186327 | 0.12× | 1 | 512.2s |
| T05 docs, surviving cycle | $2.50 | $0.963139 | $0.963139 | 0.39× | 2 | 786.7s |
| T05 docs, discarded first cycle | — | $0.884954 | **not counted** | — | 1 | 1253.1s |
| **Implementation** | **$22.00** baseline / $23.50 | **$5.733566** | $4.848611 | **0.26×** / 0.24× | 7 | |
| G1-CLOSE (this unit) | $6.00 | not yet in `events.jsonl` | — | — | — | — |

**Reconciliation.** Frontmatter, `task_completed` and `gate_eval` agree on
every unit to six decimals. T05's surviving cycle sums exactly:
$0.4671766 + $0.4959626 = $0.9631392. **The one variance between ledgers is
$0.884954.** That was T05's first attempt cycle, 15:03–15:24, which failed with
`test_packaged_copy_is_byte_identical` because T04 had not re-synced the
packaged rule mirrors. The driver then halted `preexisting_gate_failure` and
attributed the failure to T05, although T04 caused it. The operator inserted
T04H and re-armed T05, and the re-arm dropped that cycle from frontmatter and
from `gate_eval`. It remains only in `events.jsonl`. Including it,
implementation spend is $5.73 of the $28.00 plan (20.5%) before the close.

**Was the $5–6 correction for driver-touching units enough? It overshot.**
T01–T04 were planned at $19.50 and cost $3.70 (19.0%), with every unit between
0.11× and 0.27×. FEAT-2026-0106's comparable units cost $9.13 against $3.50 and
$6.13 against $3.50. The obvious explanations don't account for the difference:

- **Not the model.** Every implementation attempt in both features ran
  `sonnet` / `medium`, per `attempt_outcome.model`.
- **Not "touches the driver".** All four T01–T04 units edited `loop.py`, and
  each raised a `driver_staleness_detected` event.
- **What did differ is session length and rework, visible in cache-read
  tokens.** FEAT-2026-0106's T01 read 13.5M + 17.0M across two attempts,
  including one full attempt lost to an `E741` lint refusal. Its T03 read 21.0M
  over 125 tool calls. Here the driver units read 0.8M–3.9M over 15–57 tool
  calls, with no failed attempt and at most 3 full-suite runs each.

Across both features, per-unit actual/planned spans 0.11× to 2.61×. The
"driver-touching" label moved the estimate but did not predict the cost.
Whether an attempt fails and has to replay its context predicts it far better,
and no plan-time label captures that.

**The halt cost wall clock, not dollars.** The pin at 14:39 to the broad run at
16:20 took 101 minutes. About 20 of those, from the 15:28 halt to the 15:49
re-pin, were the operator inserting T04H. Four `driver_staleness_detected`
events fired, all `halted: false`.

### Failure-class breakdown

| Failure class | Signature | Unit | Attempts | Cost | Cause |
|---|---|---|---|---|---|
| `tests` | `test_packaged_copy_is_byte_identical` | T05 (first cycle) | 1 | $0.884954 | T04 trimmed `.specfuse/rules/` without running `scripts/sync-scaffold.sh`; the `coverage` gate reported `no_gate_marker` behind it |
| `tests` | `test_package_data_matches_canonical` | T05 (second cycle, attempt 1) | 1 | $0.467177 | T05's own doc edits were not mirrored to `specfuse/loop/data/docs/`; fixed in attempt 2 |

Both are the same class: a canonical edit with no packaged-mirror sync.
FEAT-2026-0106's T02 forward note ("run `sync-scaffold.sh` after any rules
edit") and T04 note (`sync-scaffold.sh` has no `docs/` stage) described both
halves one feature earlier. Neither note reached this feature's drafting.

## Retrospective

- **The instrument works, and it measured its own feature short.** The counter,
  the blocking check and the trim are real, and the mirrors and docs are
  consistent with them. The feature's goal, "the rules worth following reach
  every dispatched session", has not happened: zero LEARNINGS entries reach
  dispatch. Under the current cap, zero whole entries could, without a human
  editing them shorter at the accept step.
- **The plan's loud uncertainty resolved without the stop it asked for.**
  `PLAN.md` and `GATE-01.md` both said a human decides where the trim comes
  from. The driver ran T01 → T04 without a halt, and T04 took most of the trim
  from the two files T01 flagged as needing a human call. The trim is rewording
  and reads as defensible. The decision point the plan named was still skipped,
  because nothing in the task graph made it a stop: there was no `type: human`
  unit and no gate boundary.
- **Lessons promoted** to `.specfuse/LEARNINGS.md`: the nested-budget rule, and
  the rule against ordering the full suite in a WU body, which lost two RESULT
  blocks here.
