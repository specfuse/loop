<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0067: one fold path, driven by a marker

Single terminal gate, four implementation work units, one close that ran twice.
The feature's headline claim is that a re-arm now folds the prior cycle's spend
into `cumulative_*` **every time**, driven by an explicit marker rather than
inferred from `cost_usd > 0` — and that every re-armed work unit in this
repository carries one shape.

Both halves are now delivered and verified fresh in this session. The forward
half was delivered by T01 and green at the first close. The retroactive half was
delivered for the **marker** but not for the **values**: the migration's
fold-never-ran branch double-counted a $0.163090 spend on a unit that was
re-armed and never re-dispatched. The first close found that by reconciling
rather than asserting, could not fix it inside its own **Do not touch**
boundary, and returned `partially_met` with FU-1 naming the one-branch fix and
the exact reconciliation that would upgrade the verdict. The operator chose
fix-and-re-close over accepting the hedge; T04 executed FU-1's stated re-run
condition; this re-armed close re-ran the reconciliation and it now clears.
Verdict: `met`.

## Gate 1 — the code and the contract agree on one fold path

### What was built

**T01 — the explicit fold marker (`done`, 1 attempt, $1.26 against $4.00).**
`detect_rearm_dispatch` no longer reads `cost_usd`'s value. It compares
`re_arm_count` against a new `folded_through_re_arm` frontmatter integer and
returns True when the count is ahead of the marker; an absent marker reads as
`0`. `fold_cumulative_on_rearm` stamps `folded_through_re_arm = re_arm_count` in
the same write set as the four accumulators, so idempotence is deliberate rather
than the accidental side effect the old zeroing guard provided. Oracle:
`tests/test_rearm_fold_marker.py`, red on HEAD.

**T02 — the migration (`done`, 1 attempt, $2.20 against $3.00).** Shipped as
code, not a one-off edit: `specfuse/loop/rearm_migration.py` is importable and
testable, and running it against this repository is how this repository's own
records were migrated. It classifies each re-armed WU as `fold_ran` or
`fold_never_ran`, stamps the former and folds-then-stamps the latter, and cross-
checks each folded figure against that WU's own `events.jsonl` before writing.
Oracle: `tests/test_rearm_migration.py`, red on HEAD.

**T03 — the written contract (`done`, 1 attempt, $1.11 against $2.00).**
`WU.template.md` — both the canonical `specfuse/loop/data/templates/` copy and
the vendored `.specfuse/templates/` one, asserted byte-identical — now documents
`folded_through_re_arm` and states that `cumulative_*` accumulates across every
re-arm including one whose prior cycle cost nothing. `cost.py`'s module docstring
stopped presenting fold-never-ran as a supported ongoing shape and names it as a
pre-migration legacy the fallback tolerates. `wu_lifetime_cost_usd`'s logic is
unchanged, asserted by test. Oracle: `tests/test_fold_contract_documented.py`,
red on HEAD.

**T04 — the offline-fold repair (`done`, 1 attempt, $1.38 against $2.50).**
Added after the first close, to discharge FU-1. `migrate_file`'s fold-never-ran
branch now detects the case where `cost_usd` already agrees with the
`re_arm_history` prior-cost sum within `_COST_TOLERANCE_USD` — meaning the money
is already in the file and no new cycle ran — and resets `cost_usd` /
`duration_seconds` to `0.0` in the same write set instead of adding a second
copy. The re-armed-and-re-dispatched case, where the two genuinely differ, is
unchanged and has its own regression test, so the fix cannot trade a
double-count for an under-count. `FEAT-2026-0020/T04`'s record was repaired with
no invented number. The module docstring now carries the warning at the site of
the mistake, for the next person who adds an offline reader of `cost_usd`.
Oracle: `tests/test_rearm_migration.py`, extended by three cases verified present
and green in this session — `test_never_redispatched_unit_is_not_double_counted`,
`test_redispatched_unit_still_folds_both_cycles` (the regression that stops the
fix trading a double-count for an under-count), and
`test_prior_cost_agreement_within_tolerance_migrates`. The first was red on HEAD
before T04 ran; that is T04's own criterion 1 and its report, not something this
close re-observed — what this close verified is the repaired record and the
reconciliation below.

### The census, re-run rather than asserted

Acceptance criterion 3. Re-run in this session over
`.specfuse/features/**/WU-*.md`, reading frontmatter through the driver's own
parser (`specfuse.loop.loop.read_frontmatter`):

```
re-armed WUs total: 9
carrying folded_through_re_arm: 9
missing marker: 0

  MARKED  FEAT-2026-0020/WU-02-personal-refs-grep.md        re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0020/WU-04-gh-content-sweep.md          re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0053/WU-04-shadow-eval-wiring.md        re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0053/WU-07-lint-blocking-under-auto.md  re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0060/WU-01-driver-event-registry.md     re_arm_count=3  folded_through=3
  MARKED  FEAT-2026-0060/WU-02-drift-guard-and-gate.md      re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0067/WU-90-gate-1-close.md              re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0069/WU-03-dlq-targets-required.md      re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0073/WU-02-widen-the-gate.md            re_arm_count=1  folded_through=1
```

**Every re-armed work unit in this repository carries `folded_through_re_arm`,
and every marker equals its `re_arm_count`** — so `detect_rearm_dispatch` returns
False on all 9, which is the correct answer for a unit whose fold is not owed.

**The count moved from 8 to 9, and the ninth is this close.** `PLAN.md`'s
drafting-time census found 8 re-armed units and the first close confirmed 8. The
new entry is `WU-90-gate-1-close.md` itself, re-armed by the operator between the
two close cycles. It was not migrated by `rearm_migration.py`: it was marked by
the live driver path, at dispatch, which is what the next section is about.

### This close was re-armed, and the fold ran on its own record

The WU body asked for this to be said either way, and this time it happened. The
first close carried `attempts: 1` and no `re_arm_history`, so it could only
demonstrate the contract on a copy of somebody else's record. This one was
re-armed, and the driver's own `fold_cumulative_on_rearm` ran on it before this
session started. Its frontmatter, as the driver left it:

```
re_arm_count = 1                       folded_through_re_arm = 1
cost_usd = 0.0                         cumulative_cost_usd = 8.102319
duration_seconds = 0.0                 cumulative_duration_seconds = 953.536
input_tokens = 0                       cumulative_input_tokens = 140
output_tokens = 0                      cumulative_output_tokens = 60331
                                       cumulative_attempts = 1
re_arm_history[0].prior_cost_usd        = 8.102319
re_arm_history[0].prior_duration_seconds = 953.536
```

All four accumulators equal the prior cycle exactly, the per-cycle fields are
reset, and the marker is stamped at `1` — caught up with `re_arm_count`, so
`detect_rearm_dispatch` reports no fold owed. The prior cycle's `attempt_outcome`
event records `cost_usd: 8.102319499999998` and `duration_seconds: 953.536`; the
frontmatter is that figure, rounded, and nothing else. **This is the best
evidence the feature can produce: the changed path ran unattended, on a real
work unit, in the ordinary course of the driver's operation, and it moved the
money to the right place.**

Idempotence, re-checked on a copy of that same record with a simulated second
re-arm and a non-zero current cycle grafted on (the tracked file was hashed
before and after and is unmodified):

```
fold owed on the real record (re_arm_count=1, folded_through=1)?   False
after simulated 2nd re-arm on a COPY -> fold owed?                 True

copy before fold:  cost=4.5  dur=600.0  in=70  out=30000
                   cum_cost=8.102319  cum_dur=953.536  cum_in=140  cum_out=60331
after fold #1:     cost=0.0  dur=0.0  in=0  out=0
                   cum_cost=12.602319 cum_dur=1553.536 cum_in=210 cum_out=90331
                   cum_attempts=1  folded_through=2
fold owed after #1?                                                False
byte-identical after fold #2?                                      True
```

All four accumulators plus `cumulative_attempts` are unchanged by the second
call, and the marker closes the fold after the first. The old guard prevented a
double-fold as a side effect of zeroing `cost_usd`; the marker now prevents it on
purpose, and says so in the file.

### T02's choice: migrate, not annotate — and why

`WU-02`'s body offered two defensible treatments for the two fold-never-ran
units and required that one be applied to both. **Option (a), migrate, was
chosen.** Recorded here so a later reader finds it without opening a work-unit
body.

The two units were `FEAT-2026-0020/T04` (`WU-04-gh-content-sweep.md`) and
`FEAT-2026-0053/T07` (`WU-07-lint-blocking-under-auto.md`) — the same two the
roadmap row's drafting-time census named.

The reason, in `rearm_migration.py`'s own words, is that the feature's decision
was *converge*: leaving two units whose prior spend lives only in
`re_arm_history[].prior_cost_usd` would preserve, in the records, exactly the
two-shapes reading the code had just stopped supporting. Annotating would have
made the divergence documented rather than removed — the option `PLAN.md`
rejected at feature level, re-appearing at record level.

Two constraints bounded the migration, and both were honoured:

- **No invented numbers.** Only `prior_cost_usd` and `prior_duration_seconds`,
  already present in the file, were folded. `prior_input_tokens` /
  `prior_output_tokens` were never recorded on either unit, so
  `cumulative_input_tokens` / `cumulative_output_tokens` were left unset rather
  than back-filled from `events.jsonl` — that would have made the event log a
  second, undeclared source of truth for the same accumulator.
- **Cross-checked before writing.** Each folded figure was compared against that
  WU's own `attempt_outcome` total through the re-arm timestamp, raising
  `PriorCostDisagreement` and writing nothing on a disagreement beyond $0.02.

That cross-check is also where the defect below slipped through: it verified the
figure being folded was *correct*, not that the same money was already sitting
somewhere else in the file. T04's fix is exactly that missing second question.

### The finding that forced the re-close, and its repair

Found by the **first** close cycle, reconciling every re-armed WU's frontmatter
against its own `events.jsonl` — not one of that WU's acceptance criteria, and
the reason its verdict was `partially_met`. `FEAT-2026-0020/T04` read $0.326180
against an events total of $0.163090: a unit re-armed and then **never
re-dispatched** (`completed_out_of_loop: true`, finished in the operator's own
session because the `gh` CLI needs an unsandboxed subprocess), whose `cost_usd`
therefore still held the prior cycle rather than a new one. The migration folded
`re_arm_history[0].prior_cost_usd: 0.16309` into `cumulative_cost_usd` without
resetting `cost_usd`, so the same money appeared twice.
`cumulative_duration_seconds: 42.693` duplicated `duration_seconds: 42.693` the
same way.

The root cause, named precisely because it is the feature's own lesson turned
back on it: `fold_cumulative_on_rearm` may safely fold `cost_usd` because it runs
*at dispatch*, where `cost_usd` provably holds the prior cycle. The migration runs
*offline*, where `cost_usd` means "the prior cycle" **or** "the current cycle"
depending on whether a re-dispatch ever happened — a value with two meanings,
read as if it had one. That is precisely the defect class this feature exists to
remove.

**The reconciliation, re-run in this session after T04:**

```
wu_id                        events_sum  fm(cost+cum)       delta
FEAT-2026-0020/T02             1.011715      1.011715   -0.000000
FEAT-2026-0020/T04             0.163090      0.163090   +0.000000   <-- repaired
FEAT-2026-0053/T04             3.756955      3.756955   -0.000000
FEAT-2026-0053/T07             9.289682      9.291823   +0.002141
FEAT-2026-0060/T01            16.303334      7.072130   -9.231204   <-- pre-existing, out of scope
FEAT-2026-0060/T02             2.389101      2.389100   -0.000001
FEAT-2026-0067/G1-CLOSE        8.102319      8.102319   -0.000000
FEAT-2026-0069/T03             7.645400      7.645399   -0.000001
FEAT-2026-0073/T02             7.115892      7.115892   -0.000000
```

`FEAT-2026-0020/T04` now reads `cost_usd: 0.0` + `cumulative_cost_usd: 0.16309`
= $0.163090, matching its single `attempt_outcome` event exactly, with
`duration_seconds: 0.0` + `cumulative_duration_seconds: 42.693` treated the same
way. No number was introduced that was not already in that file. This close's own
row reconciles to zero as well, which is the fold-on-re-arm evidence stated in
cost terms.

**`FEAT-2026-0060/T01` remains out of scope, deliberately and by name.** Its
`cumulative_cost_usd: 4.478344` accounts for exactly one of its three prior
cycles; `re_arm_history`'s three `prior_cost_usd` entries sum to $13.709549, and
with the current cycle's `cost_usd: 2.593786` the file totals $7.072130 against
an events total of $16.303334. This is the old value-guard's
under-count, frozen in a `done` record. `PLAN.md` ruled back-filling cost onto
`done` features' records out of scope before any work began, T02's criterion 2
required `cumulative_cost_usd` be left unchanged on a fold-ran unit, and T04's
criterion 7 required this row be excluded by name rather than quietly repaired.
It is named here so a reader does not mistake "carries the marker" for "reads its
own lifetime correctly", and it is **not** a residual hedge: it is a pre-existing
condition this feature chose not to touch, recorded as such at plan time.

`FEAT-2026-0053/T07`'s $0.002141 delta is rounding inside the migration's $0.02
tolerance, not a fold error.

### Consumer-visible contract changes

Enumerated per `close-discipline.md` §3. Five, all real; the same five appended
to `CHANGELOG.md`'s `Unreleased`.

1. **`folded_through_re_arm` — a new work-unit frontmatter field.** *(added)*
   An integer written by `fold_cumulative_on_rearm` in the same write set as the
   accumulators, read by `detect_rearm_dispatch`. Every re-armed WU in every
   downstream project will carry it from the next re-arm onward. Absent reads as
   `0`, so a project that upgrades and does nothing keeps working — the field is
   additive, not required.

2. **`cumulative_*`'s meaning is now unconditional.** *(changed)*
   `cumulative_cost_usd`, `cumulative_duration_seconds`, `cumulative_input_tokens`,
   and `cumulative_output_tokens` accumulate on **every** re-arm, including one
   whose prior cycle cost $0.00. Previously the fold ran only when `cost_usd > 0`
   at dispatch, so a zero-cost prior cycle left its duration and token counts
   unaccumulated as well. Anything reading these four fields is reading a
   different quantity than it was before — a larger and more complete one.

   **This reaches the event log, which `PLAN.md` said it would not.** The plan's
   existing-mechanism search concluded no consumer reads `cumulative_*` directly.
   It missed one: `loop.py`'s `task_completed` emitter reads
   `cumulative_cost_usd` and `cumulative_attempts` straight from frontmatter to
   build the event's lifetime payload (#199), bypassing `wu_lifetime_cost_usd`.
   So a `task_completed` event for a re-arm the old guard would have skipped now
   carries a larger `cumulative_cost_usd` than it would have before. Anything
   downstream that aggregates `events.jsonl` — a cost report, a `learnings-suggest`
   sweep, an orchestrator rollup — sees the corrected figure. Intended, and
   worth knowing before it shows up as an unexplained step in a spend chart.

3. **`specfuse/loop/rearm_migration.py` — a new importable module.** *(added)*
   `census(root)`, `migrate_file(path)`, and `migrate_repo(root)` stamp the marker
   onto already-re-armed WUs and fold the fold-never-ran shape forward. A
   downstream project has the same two shapes in its own feature folders and
   should run it once after upgrading.

4. **The migration no longer double-counts a unit that was re-armed and never
   re-dispatched.** *(fixed)* Shipped by T04 in the same module, before any
   downstream project ran it. When `cost_usd` already agrees with the
   `re_arm_history` prior-cost sum within `_COST_TOLERANCE_USD`, the money is
   already accounted for and `cost_usd` / `duration_seconds` are reset to `0.0`
   in the same write set rather than a second copy being added. A downstream
   project whose feature folders contain `completed_out_of_loop` work units — or
   any unit re-armed without a subsequent dispatch — would otherwise have had
   those records inflated by exactly one prior cycle. The re-armed-and-
   re-dispatched case is unchanged.

5. **`WU.template.md`'s frontmatter notes changed, in both shipped copies.**
   *(changed)* The template that `specfuse init` and `specfuse upgrade` place in
   every downstream project now documents `folded_through_re_arm` and states the
   unconditional `cumulative_*` contract. The canonical
   `specfuse/loop/data/templates/WU.template.md` and the vendored
   `.specfuse/templates/WU.template.md` are asserted byte-identical by test.

Human acknowledgment of this list is the gate review's business
(`autonomy_default: review`; gate 1 lands at `awaiting_review`). Items 1–3 and 5
were acknowledged at the first review checkpoint, where the operator's decision
was to fix rather than accept; item 4 is what that decision produced and is new
to this list.

## Cost analysis

`events.jsonl`'s `attempt_outcome` sum is authoritative. It reconciles against
every WU's frontmatter exactly — **no gap, no lower bound needed**.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — explicit fold marker | $4.00 | 1 | **$1.2600597** | −$2.74 (−68%) |
| T02 — migrate existing shapes | $3.00 | 1 | **$2.2002231** | −$0.80 (−27%) |
| T03 — contract and accessor | $2.00 | 1 | **$1.1096172** | −$0.89 (−45%) |
| T04 — offline-fold repair | $2.50 | 1 | **$1.3756533** | −$1.12 (−45%) |
| **Implementation subtotal** | **$11.50** | **4** | **$5.9455533** | **−$5.55 (−48%)** |
| G1-CLOSE cycle 1 (`partially_met`) | $5.00 | 1 | **$8.1023195** | +$3.10 (+62%) |
| **Recorded total** | **$16.50** | **5** | **$14.0478728** | **−$2.45 (−15%)** |
| G1-CLOSE cycle 2 — this session | (re-arm, no new estimate) | 1 (in flight) | not yet in `events.jsonl` | — |
| Gate budget | $20.00 | — | headroom before this cycle: **$5.95** | — |

Per-attempt ledger, in emission order — every attempt passed first try:

```
T01      attempt 1  passed  $1.2600597   793.346s   -> task_completed cost_usd 1.26006
T02      attempt 1  passed  $2.2002231   824.828s   -> task_completed cost_usd 2.200223
T03      attempt 1  passed  $1.1096172   665.581s   -> task_completed cost_usd 1.109617
G1-CLOSE attempt 1  passed  $8.1023195   953.536s   -> verdict partially_met, then re-armed
T04      attempt 1  passed  $1.3756533   722.285s   -> task_completed cost_usd 1.375653
                            -----------  ---------
attempt_outcome sum         $14.0478728  3959.576s (1h 05m 59.6s)
```

Frontmatter reconciliation, each line checked independently:

- T01 `cost_usd: 1.26006` = 1.2600597 rounded ✔
- T02 `cost_usd: 2.200223` = 2.2002231 rounded ✔
- T03 `cost_usd: 1.109617` = 1.1096172 rounded ✔
- T04 `cost_usd: 1.375653` = 1.3756533 rounded ✔
- G1-CLOSE `cost_usd: 0.0` + `cumulative_cost_usd: 8.102319` = 8.1023195 rounded ✔
  — the only WU in this feature that was re-armed, and the fold accounts for it
  exactly rather than leaving the prior cycle out of the sum
- Sum of all five = $14.0478728 = the `attempt_outcome` total ✔

**Acceptance criterion 1's "$10.00 WU sum and $14.00 gate budget" reconciles
against nothing in the feature's current state, and is not invented into one
here.** Both figures were true of an earlier shape of this gate and neither was
updated when T04 was added. The authoritative values today: the five WUs'
`planned_cost_usd` frontmatter reads 4.00 + 3.00 + 2.00 + 2.50 + 5.00 =
**$16.50**, which is also `PLAN.md`'s `planned_cost_usd`; `GATE-01.md`'s
`cost_budget_usd` reads **$20.00**. The first close reconciled against the
then-current $14.00 / $14.00 and recorded the same criterion drift; adding T04
moved both numbers again, and the criterion text in `WU-90` still moved with
neither. Named rather than reconciled, per this WU's escalation trigger on cost
figures. This is a WU-body maintenance gap, not a spend discrepancy — the spend
itself reconciles to the cent.

**The gate budget now carries headroom, and it was earned rather than planned.**
`planning-discipline.md` §5's corollary asks for the WU sum plus one re-attempt
of the largest WU. The original $14.00 was the bare sum and carried none; the
operator's raise to $20.00 when arming T04 supplied $3.50 over the new $16.50
sum. It was still not tested — all four implementation WUs passed first try at
48% under estimate.

**The implementation estimates were uniformly high; the close estimate was
uniformly low.** All four implementation WUs came in 27% to 68% under, each
shipping one focused module plus one red-first test file with its oracle named
and its red-on-HEAD test spelled out before dispatch. The close overran by 62%
on the first cycle and is now on its second, which is $5.00 of estimate against
at least $8.10 of spend. Two things worth separating. §5 is explicit that a
closing-WU retry is a defect to diagnose rather than a cost to budget for, and
that holds here in the best way: the second cycle exists because the first found
a real defect it could not fix, which is the mechanism working, not waste. But
the *first* cycle's $8.10 against $5.00 is not a retry — it is a single passing
attempt, above §5's own p90 of $5.42 for a `close` and inside its observed max of
$11.44. One observation against a 61-WU distribution changes nothing on its own;
recorded here rather than generalised, because §5's provenance note is explicitly
about two earlier revisions that each set a floor from a single feature.

### Failure-class breakdown

**Zero non-passing attempts.** Five work-unit cycles, five attempts, five
passes: 100% first-attempt success, $0.00 spent on refused or failed attempts
against the 28%-of-closing-spend baseline `planning-discipline.md` §5 records. No
`failure_class` is non-null anywhere in this feature's `events.jsonl`, no
`human_escalation` event was emitted, and no `work/` attempt notes exist. The
table this section would otherwise carry has no rows.

**The re-arm is not a failure and is not counted as one.** `G1-CLOSE`'s first
cycle emitted `outcome: passed` with `failure_class: null`; it was re-armed by
operator decision, not by the driver's spinning guard. Counting it as waste
would misprice the one mechanism that caught the feature's only real defect.

## Deferred verification

Per acceptance criterion 2, one entry per criterion not verified in-loop.

**1. The migration's behaviour against a real downstream project.**
- *Criterion:* T02's "ship the migration as code, not a one-off edit", whose
  stated purpose is that a downstream project upgrading past this contract has
  the same two shapes in its own feature folders.
- *Why not verified in-loop:* this repository is the only corpus available to the
  session. `rearm_migration.py` was run against exactly one tree — this one —
  with 8 re-armed units at migration time, of which 2 were fold-never-ran. Every
  other shape it handles is exercised only by fixtures in
  `tests/test_rearm_migration.py`, T04's additions included.
- *Where it actually gets checked:* the first downstream project that runs
  `migrate_repo` against its own `.specfuse/features/` after upgrading. See *What
  the loop did NOT verify*.

**2. That `cumulative_*` reads correctly on every already-`done` record.**
- *Criterion:* `GATE-01.md`'s definition of done, "every re-armed work unit in
  this repository carries one shape".
- *Why not verified in-loop:* verified for the **marker** — 9 of 9, quoted above
  — and now verified for the **values** on 8 of those 9, by the reconciliation
  under *The finding*. The ninth, `FEAT-2026-0060/T01`, under-counts its lifetime
  by $9.23 and was excluded by name at plan time: `PLAN.md` scoped back-filling
  cost onto `done` features' records out, and T02's criterion 2 required
  `cumulative_cost_usd` be left unchanged on a fold-ran unit.
- *Where it actually gets checked:* nowhere automatically — the honest answer,
  unchanged from the first close. `wu_lifetime_cost_usd`'s events-first precedence
  means no consumer reads the under-count, which is exactly why it survived. The
  reconciliation script quoted above is the check; nothing runs it on a schedule,
  and a future feature that wants `cumulative_*` to be trustworthy on historical
  records will have to schedule it.

**3. That no consumer reads `cumulative_*` directly. — `PLAN.md`'s claim is
wrong, corrected here.**
- *Criterion:* `PLAN.md`'s existing-mechanism search, "`arm_eval.py:172` only,
  via `wu_lifetime_cost_usd`. No consumer reads `cumulative_*` directly, so
  changing when it is written breaks no reader."
- *Why not verified in-loop:* it was verified — by re-grepping — and **it does
  not hold**. There is a third reader the plan's grep missed:
  `specfuse/loop/loop.py`'s `task_completed` emitter reads `cumulative_cost_usd`
  (and `cumulative_attempts`) straight from frontmatter to compute the event's
  lifetime payload, added by #199 and predating this feature. It does not go
  through `wu_lifetime_cost_usd`. So T01's change **does** reach a reader: for a
  re-arm the old guard would have skipped, the `task_completed` event now carries
  a larger, more complete `cumulative_cost_usd`. That is the intended direction
  and it is still a behaviour change the plan asserted would not occur. The
  complete in-repo reader set is: the fold in `loop.py`, the `task_completed`
  emitter in `loop.py`, and `cost.py`'s fallback line.
- *Where it actually gets checked:* the consumer-visible contract-change list
  above, item 2, at the operator's acknowledgment of this gate — which is the
  mechanism `close-discipline.md` §3 provides for exactly this. Nothing checks
  it for code outside this repository that reads WU frontmatter, and nothing
  re-runs the plan's grep after the plan is written, which is why a stale
  existing-mechanism verdict survived to close time.

## What the loop did NOT verify

**No downstream project has been migrated, and the migration's behaviour against
a real downstream repository is unverified here.** This is stated plainly because
it is the feature's largest residual risk and no amount of in-repo testing
reduces it.

`rearm_migration.py` was executed against one tree: this one. Its
fold-never-ran branch ran on exactly two files, its fold-ran branch on six, and
its not-rearmed branch on the remainder. Every other condition it handles —
a `re_arm_history` entry with no `prior_cost_usd`, a feature folder with no
`events.jsonl`, a `PriorCostDisagreement` beyond tolerance, a WU whose
frontmatter the parser rejects — is exercised only by fixtures. A fixture proves
the branch runs; it does not prove a real project's records look like the
fixture. That distinction is not hypothetical here: the one real fold-never-ran
shape the migration met that its fixtures did not model — a unit re-armed and
never re-dispatched — is precisely the one it got wrong, and T04 exists because
of it. T04 added a fixture for that shape; it did not add a downstream corpus.

**A downstream project that upgrades and never runs the migration is safe, and
that is not an accident.** An absent `folded_through_re_arm` reads as `0`, so
`detect_rearm_dispatch` reports a fold owed on the next dispatch of an
already-re-armed unit — and that fold folds the *current* cycle's `cost_usd`,
which is the correct action at dispatch time regardless. Running the migration
makes the record explicit and the guard exact; not running it does not corrupt
anything. Verified by reading the dispatch call site, not assumed.

**No auto-close debt was inherited.** This feature has one gate and one close, no
predecessor gate auto-closed, and `grep -rn "specfuse:autoclose-debt"` over the
feature folder returns no matches.

**Oracles re-run fresh in this session** (`close-discipline.md` §1), not inherited
from any producing WU's self-report and not inherited from the first close cycle:

```
$ python3 -m unittest tests.test_rearm_fold_marker tests.test_rearm_migration \
                     tests.test_fold_contract_documented
Ran 24 tests in 0.026s
OK

$ python3 -m unittest discover -s tests -b
Ran 2312 tests in 104.281s
OK (skipped=3)
```

**One environmental caveat on the full suite, recorded rather than smoothed
over.** The first run of the full suite in this session reported
`FAILED (errors=16, skipped=5)`. Every one of the 16 was a fixture repository's
`git commit` returning 128 with `error: Couldn't get agent socket?` — the
session sandbox blocks the SSH signing-agent socket that this machine's git
identity requires, so temp-repo fixtures cannot create a commit. Reproduced in
isolation before being attributed to the environment, and the green run above is
the same command with the sandbox off. No test source was changed to obtain it.

## Hedged-verdict follow-up record

One entry, per `close-discipline.md` §2, carried forward from the first close
cycle. **It is discharged**; it is kept rather than deleted so the fix-and-
re-close path is legible to a later reader.

### FU-1 — the migration double-counts a unit that was re-armed and never re-dispatched — **DISCHARGED by T04**

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"A re-arm
  folds the prior cycle's spend into `cumulative_*` every time, driven by an
  explicit marker rather than by inferring 'already folded' from a zero. Every
  re-armed work unit in this repository carries one shape, and the frontmatter
  contract says which."*
- **Why it was unmet at the first close:** the marker half was met — 8 of 8. The
  shape half was not, for one record. `rearm_migration.py`'s fold-never-ran
  branch folded `re_arm_history[].prior_cost_usd` into `cumulative_cost_usd`
  without resetting `cost_usd`. Correct for a unit re-armed and re-dispatched,
  where `cost_usd` holds the new cycle; a duplicate for a unit re-armed and never
  re-dispatched, where `cost_usd` still holds the prior cycle.
  `FEAT-2026-0020/T04` is such a unit — `completed_out_of_loop: true` — and its
  frontmatter then read $0.326180 against an events total of $0.163090.
- **Why it was not fixed in that session:** `specfuse/loop/rearm_migration.py`
  was T02's file and `FEAT-2026-0020/T04` an already-`done` feature's record.
  Both were on the close's **Do not touch** list. Fixing either there would have
  been the scope drift `result-contract.md` §2 names, on the last work unit of
  the feature.
- **The exact re-run condition that would upgrade the verdict to `met`:** amend
  `migrate_file`'s fold-never-ran branch so that, when `cost_usd` already equals
  the `re_arm_history` prior sum within the existing $0.02 tolerance, it treats
  the money as already present — resetting `cost_usd` to `0.0` in the same write
  set rather than adding a second copy — repair `FEAT-2026-0020/T04`'s record,
  then re-run the reconciliation quoted under *The finding*. It upgrades to `met`
  when every re-armed WU's `cost_usd + cumulative_cost_usd` equals its
  `attempt_outcome` sum, with `FEAT-2026-0060/T01`'s pre-existing $9.23
  under-count excluded by name.
- **kind:** `externally-verifiable-later`
- **Discharge, verified in this session:** the operator armed
  `FEAT-2026-0067/T04` against this entry's re-run condition rather than
  accepting the hedge. T04 landed the one-branch fix with its own regression test
  for the re-dispatched case, repaired `FEAT-2026-0020/T04`'s record with no
  invented number, and passed first try at $1.38. The reconciliation under *The
  finding* was re-run here: every re-armed WU's `cost_usd + cumulative_cost_usd`
  equals its `attempt_outcome` sum, `FEAT-2026-0060/T01` excluded by name. The
  stated condition is satisfied exactly as written.

**Verdict ceiling, as it was:** one entry, `externally-verifiable-later` — so
rework existed and the operator had a real choice between accepting the hedge and
running the fix. They ran the fix. The ceiling is no longer binding.

## Lessons promoted

Three entries in `.specfuse/LEARNINGS.md`, all tagged `FEAT-2026-0067/G1-CLOSE`.
The first two were appended by the first close cycle and are unchanged — the
defects they describe are history, and a discharged follow-up does not make the
lesson less true. The third is new to this cycle.

**1. A guard that infers "already done" from a value cannot distinguish it from
"never happened". Assessed against all three named instances, and promoted — but
not on the framing the criterion offered.**

Acceptance criterion 5 named three instances and asked whether the pattern holds
across all of them. Inspected:

- **This fold guard.** `detect_rearm_dispatch`'s `cost_usd > 0`. A zero means
  "the prior cycle cost nothing" or "a prior fold already moved it". Exact fit.
- **#306, the frontmatter scan running off the end.** The scan for the closing
  `---` advanced `j` to `len(lines)` and the caller then read the terminal index
  as "terminator found". "Found it" and "ran out of file" produced the same
  value, so an unterminated block was parsed as though the whole document were
  frontmatter and the failure was reported against an arbitrary body line. Fit —
  a sentinel with two meanings rather than a cost with two meanings, same shape.
- **#593. The criterion's framing does not hold; the underlying defect does.**
  #593's headline, as `CHANGELOG.md` records it and as the criterion phrases it,
  is that a `produces:` directory was refused *post-session* instead of
  pre-dispatch — $6.42 across three byte-identical refusals. That is a **timing**
  defect: the check was correct and ran too late. Timing is a different axis from
  value ambiguity and the pattern does not hold on it. It does hold one layer
  down, on the defect that made the directory worth refusing: a directory
  satisfied `assert_declared_deliverables`' presence test — exists and non-empty —
  while failing `assert_produces_in_diff`'s diff match, so "the deliverable was
  produced" and "a directory happens to sit at that path" were the same truthy
  value. `produces_shape_error`'s comment says so in as many words.

So: two clean fits, one partial. The pattern is promoted on the two that fit plus
the fourth instance this feature produced — the migration double-count, in which
the fix for a value-with-two-meanings introduced a value with two meanings. The
`#593` framing offered by the criterion is recorded above as not holding, rather
than counted.

**2. A guard that reads a field is not the same guard when it runs somewhere
else.** The general form of FU-1: T01's fold may read `cost_usd` safely because it
runs at dispatch, where the field provably holds the prior cycle. T02's migration
reads the same field offline, where its meaning depends on history the file does
not state. The invariant was in the *call site*, not in the field, and moving the
read broke it silently.

**3. New this cycle — a hedged verdict with a named re-run condition is
machinery, and this feature is the worked example.** `close-discipline.md` §2
requires the follow-up record because without it `met_locally` is a dead end. The
mechanism was exercised end to end here for the first time in this repository:
the close *measured* rather than asserted and found a defect none of its own
criteria named; it was structurally forbidden from fixing it; it wrote FU-1 with
an executable re-run condition; the operator armed a WU against that condition
verbatim; the WU passed first try at $1.38; the re-armed close re-ran the same
reconciliation and the hedge cleared. The transferable part is that FU-1's
re-run condition was **written as a specification, not as a regret** — it named
the branch, the tolerance, the record to repair, and the exact table that would
prove it — which is why T04 could be authored from it directly. Promoted in full
to `LEARNINGS.md`.

## Verdict

**`met`.**

Verified fresh in this session rather than inherited from any producing WU or
from the first close cycle:

- The fold is triggered by an explicit marker and no longer reads `cost_usd`'s
  value; a zero-cost re-arm folds.
- The fold is idempotent across all four accumulators plus `cumulative_attempts`,
  demonstrated on a copy of a real re-armed record with a second call proven
  byte-identical.
- **The contract ran unattended on this close's own work unit.** `G1-CLOSE` was
  re-armed between cycles; the driver's fold moved $8.102319, 953.536s, 140 input
  and 60331 output tokens into `cumulative_*`, reset the per-cycle fields, and
  stamped the marker — matching the prior `attempt_outcome` event exactly. The
  feature's changed path is verified by a production run of itself, not only by
  fixtures.
- All 9 re-armed work units in this repository carry `folded_through_re_arm`
  equal to their `re_arm_count`.
- Every re-armed WU's `cost_usd + cumulative_cost_usd` equals its
  `attempt_outcome` sum, with `FEAT-2026-0060/T01` excluded by name as
  pre-existing and scoped out at plan time.
- The template and `cost.py` state the converged contract in both shipped copies.
- The full suite is green at 2312 tests.

The single hedge from the first cycle is discharged, not accepted:
`FEAT-2026-0020/T04` read $0.326180 against $0.163090 and now reads $0.163090,
and the branch that produced the error carries both a regression test and a
docstring warning at the site where the next offline reader of `cost_usd` would
make the same mistake.

`FEAT-2026-0060/T01`'s $9.23 lifetime under-count is real, named in three places
in this document, and **not** part of the verdict: `PLAN.md` scoped back-filling
`done` records out before any work began, and a close does not get to re-scope a
feature retroactively — in either direction. It is a candidate for a future
feature, not an unmet criterion of this one.
