# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check refuses to pass if
its diff touches `.specfuse/LEARNINGS.md` while this feature is in `auto`
mode — this file is where those lessons go instead.

**How a human promotes an entry from here.** At PR review for this feature:

1. Read each entry below. Judge it the way you would judge any
   `LEARNINGS.md` candidate — does it generalize into a rule that should
   change how a FUTURE work unit, in any feature, is written or executed?
2. For each entry you accept, copy it into `.specfuse/LEARNINGS.md` (below
   the `<!-- lessons work units append below this line -->` marker, in that
   file's existing entry format) in the same commit or a follow-up commit to
   the PR branch.
3. For each entry you reject or narrow, leave it here — do not delete it
   silently; a short note on why it didn't generalize helps the next person
   who drafts a similar feature.
4. This file is not read by planning. Nothing here shapes another feature
   until a human has done step 2.

## Format

```
- [FEAT-YYYY-NNNN/G1] Implementation WUs must name the module a new route/handler
  lives in; "add it to the router" cost a blocked attempt when no router existed yet.
```

## Promotion disposition — recorded 2026-08-23

All four entries were judged at PR review for #2695 and promoted to
`.specfuse/LEARNINGS.md`. Entries are left below rather than deleted, per step 3.

- **Entry 1 (exemption scope unit)** — promoted in full, as
  `an-exemption-scoped-to-the-wrong-unit-inverts-a-guards-coverage`. No existing
  entry covered exemption scoping.
- **Entry 2 (assert the corpus size)** — promoted and **widened**, as
  `pin-the-corpus-size-and-expect-it-to-move-both-ways`. The staged text said to
  assert the corpus size. It then proved itself a second time in a direction it
  had not anticipated: the pin's only member was this feature, so closing the
  feature emptied the corpus and the tripwire failed on the acceptance commit
  itself. The promoted entry carries that second instance and adds two rules the
  staged text did not have — write the failure message for shrinkage as well as
  growth, and prefer asserting membership over size where membership is the real
  claim. Cross-referenced to `[FEAT-2026-0055/G1-CLOSE]` and
  `[FEAT-2026-0053/G1-CLOSE]`, which are adjacent but distinct.
- **Entry 3 (cost counters reset on re-arm)** — promoted **narrowed**, as
  `attempts-lifetime-exceeding-attempts-marks-a-re-armed-unit`. The general rule
  was already in `LEARNINGS.md` at `[FEAT-2026-0053/G2-CLOSE]`, with equivalent
  evidence, and `LEARNINGS.md` is loaded whole into every planning session and
  asks for de-duplication. What was genuinely new is kept: the cheap detection
  test (`attempts_lifetime > attempts` marks a re-armed unit) and a second
  instance showing the under-count can invert sign rather than merely lose
  magnitude. The restated general rule was dropped in favour of a pointer.
- **Entry 4 (close WU *Do not touch*)** — promoted in full, as
  `a-close-wus-do-not-touch-must-permit-its-own-binding-obligations`. Existing
  Do-not-touch entries cover bounding a WU's write surface; none covers a close
  WU's *own binding obligations* being excluded by its boundary, nor the
  guard-passes-on-absence shape. Cross-referenced to
  `[meta/six-bug-sweep/detecting-a-condition-is-not-handling-it]` as a sibling.

**Still outstanding, and named by entry 4 itself:** the `close-discipline.md` §3
`CHANGELOG.md` `Unreleased` append for this feature was never made. Entry 4 is
the general rule derived from that omission; the omission itself is unrepaired.

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0058/G1] **An exemption scoped to the wrong unit silently inverts a
  guard's coverage; measure a new check's live coverage over the corpus it will
  guard, not just its red-before fixture.** T02's non-restatement check is the
  load-bearing half of this feature by its own PLAN's D1 — "if artifacts may
  only cite, there is no second copy to drift". Its legitimate-quotation
  exemption is correct in intent and was tested (a close WU quoting a decision
  while citing its ID must not be a false positive), but it is scoped **per
  whole artifact file**: one `D3` token anywhere exempts that entire document
  from restatement checking for D3. Measured after the fact over the feature's
  own six graph artifacts × four decisions, the check is live on 3 of 24 pairs —
  12.5% — and `PLAN.md`, which restates D1 and D3 near-verbatim today, is fully
  exempt. Every unit test passed; the tree was green; the drift the feature
  exists to remove was present, in the dogfood, unflagged. Authoring rule: a WU
  that introduces an exemption must state the exemption's **scope unit** (line,
  paragraph, section, file) as an acceptance criterion, and must assert live
  coverage — "N of M (subject, rule) pairs are actually checked" — over a real
  corpus, not only that a synthetic positive fires and a synthetic exempt case
  does not. A red-before test proves the check *can* fire; only a coverage
  measurement says how often it *will*.

- [FEAT-2026-0058/G1] **A sequencing precondition enforced only by prose gets
  skipped, and it takes the gate's headline claim with it — encode it as a
  machine check on corpus size.** `PLAN.md` D2 and `GATE-01.md` both required
  FEAT-2026-0050's decision prose to be migrated in its own PR *before* this
  gate ran, and `GATE-01.md` spelled out the consequence of skipping it: "T02
  will find the tree already clean for the wrong reason — no feature cites
  anything yet — and its ERROR-on-a-populated-tree claim becomes
  unfalsifiable." It then said "Check before arming." Nothing checked. The
  migration never happened, the upstream feature reached `done` and became
  permanently exempt as sealed history, and the feature's satisfiability test
  now sweeps a live in-scope corpus of exactly one folder — the one the feature
  wrote itself. The test is green and proves nothing. Authoring rule: when a
  criterion's meaning depends on the corpus being non-trivial, **assert the
  corpus size in the test** (`assertGreaterEqual(len(in_scope), 2)`) rather than
  only asserting zero findings. A sweep that returns "clean" over an empty or
  self-authored corpus is indistinguishable from a working check, and that is
  the one failure a green suite cannot show you.

- [FEAT-2026-0058/G1] **Cost counters reset on re-arm, so a close reconciling
  from `cumulative_cost_usd` under-reports every re-armed unit — sum
  `attempt_outcome` rows across arming cycles instead.** T01 escalated
  `spinning_detected` after three failed attempts costing `$4.95`, was re-armed,
  and passed first try at `$1.87`. Its `task_completed` payload records
  `cost_usd: 1.865657` and `cumulative_cost_usd: 1.865657`, so the gate ledger
  reads 31% of a `$6.00` plan for a unit that actually spent `$6.82` — 114% of
  plan, and 170% of the `$4.00` it was originally estimated at. Reading the
  ledger alone turns the feature's single largest overrun into its biggest
  apparent saving, and the calibration signal a cost analysis exists to produce
  is inverted rather than merely lost. Close rule: reconcile per WU by summing
  every `attempt_outcome.cost_usd` for that correlation ID across the whole
  event log, report it alongside the ledger figure, and say which is which. Any
  unit whose `attempts_lifetime` exceeds its `attempts` has been re-armed and
  needs this treatment.

- [FEAT-2026-0058/G1] **A close WU's "Do not touch" must explicitly permit the
  surfaces its own binding close obligations require, or the obligation is
  dropped silently by a guard that passes on absence.**
  `close-discipline.md` §3 requires a close to enumerate consumer-visible
  contract changes *and* append them to `CHANGELOG.md`'s `Unreleased` section;
  `close-k` enforces the link. But `close-k` only fires when the
  `## Consumer-visible contract changes` heading is present and is not the `n/a`
  line — so a close that omits the heading passes. This WU's *Do not touch* read
  "any surface outside this feature's folder", which excludes `CHANGELOG.md`,
  leaving three outcomes: violate the scope rule, fail the close, or omit the
  heading and pass. The third is the one an agent under attempt pressure will
  take, and it is invisible afterwards — a passing close with no §3 section
  looks identical to a feature that had nothing to enumerate. Authoring rule:
  when writing a close WU's *Do not touch*, enumerate the closing surfaces the
  binding rules require it to write (`RETROSPECTIVE.md`, `LEARNINGS-pending.md`
  or `.specfuse/LEARNINGS.md`, `CHANGELOG.md`, `.specfuse/roadmap.md`) as
  explicit exceptions. Reviewing rule: treat a passing close with **no** §3
  heading as unreviewed, not as `n/a` — the `n/a` line is a claim someone made,
  and absence is not.
