<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0067: one fold path, driven by a marker

Single terminal gate, three implementation work units, one close. The feature's
headline claim is that a re-arm now folds the prior cycle's spend into
`cumulative_*` **every time**, driven by an explicit marker rather than inferred
from `cost_usd > 0` — and that every re-armed work unit in this repository
carries one shape.

The forward-looking half of that claim is delivered and verified fresh in this
session. The retroactive half is delivered for the **marker** and not for the
**values**: the migration stamped all 8 re-armed units, but one of the two it
folded now double-counts a $0.16 spend that was already sitting in `cost_usd`,
and one pre-existing record's `cumulative_cost_usd` under-counts by $9.23 for
reasons this feature deliberately scoped out. Both are quantified below. The
verdict is hedged on the first, which this feature introduced.

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

### The census, re-run rather than asserted

Acceptance criterion 3. Re-run in this session over
`.specfuse/features/**/WU-*.md`, reading frontmatter through the driver's own
parser:

```
re-armed WUs total: 8
carrying folded_through_re_arm: 8
missing marker: 0

  MARKED  FEAT-2026-0020/WU-02-personal-refs-grep.md      re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0020/WU-04-gh-content-sweep.md        re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0053/WU-04-shadow-eval-wiring.md      re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0053/WU-07-lint-blocking-under-auto.md re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0060/WU-01-driver-event-registry.md   re_arm_count=3  folded_through=3
  MARKED  FEAT-2026-0060/WU-02-drift-guard-and-gate.md    re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0069/WU-03-dlq-targets-required.md    re_arm_count=1  folded_through=1
  MARKED  FEAT-2026-0073/WU-02-widen-the-gate.md          re_arm_count=1  folded_through=1
```

**Every re-armed work unit in this repository carries `folded_through_re_arm`,
and every marker equals its `re_arm_count`** — so `detect_rearm_dispatch` returns
False on all 8, which is the correct answer for a unit whose fold is not owed.
The count matches `PLAN.md`'s drafting-time census of 8 re-armed units exactly;
no unit appeared or disappeared between drafting and close.

### Idempotence, demonstrated on a real re-armed record

`GATE-01.md`'s second review check, and this close's third escalation trigger:
the guarantee had to hold on something other than a fixture. Demonstrated
against a **copy** of `FEAT-2026-0060/T01` — the repository's only thrice-re-armed
unit, and the one carrying real accumulator values — with a simulated fourth
re-arm. The tracked file was not written to.

```
state on disk:  cost_usd=2.593786  cum_cost=4.478344  cum_dur=772.327
                cum_in=156  cum_out=41202  cum_attempts=3  folded_through=3
fold owed with marker caught up (re_arm_count=3, folded_through=3)?  False
after simulated 4th re-arm -> fold owed?                             True

after fold #1:  cost_usd=0.0  dur=0.0  in=0  out=0
                cum_cost=7.07213  cum_dur=2131.01  cum_in=4229  cum_out=63502
                cum_attempts=4  folded_through=4
fold owed after #1?                                                  False
after fold #2:  (byte-identical to fold #1)
IDEMPOTENT ON REAL RECORD:                                           True
```

All four accumulators plus `cumulative_attempts` are unchanged by the second
call, and the marker correctly closes the fold after the first. The old guard
prevented a double-fold as a side effect of zeroing `cost_usd`; the marker now
prevents it on purpose, and says so in the file.

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
somewhere else in the file.

### The finding: the migration double-counted one record

Found by this close, reconciling every re-armed WU's frontmatter against its own
`events.jsonl`. Not one of this WU's acceptance criteria; it is the reason the
verdict is hedged.

```
wu_id                        events_sum  fm(cost+cum)       delta
FEAT-2026-0020/T02             1.011715      1.011715   -0.000000
FEAT-2026-0020/T04             0.163090      0.326180   +0.163090  <-- MISMATCH
FEAT-2026-0053/T04             3.756955      3.756955   -0.000000
FEAT-2026-0053/T07             9.289682      9.291823   +0.002141
FEAT-2026-0060/T01            16.303334      7.072130   -9.231204  <-- MISMATCH
FEAT-2026-0060/T02             2.389101      2.389100   -0.000001
FEAT-2026-0069/T03             7.645400      7.645399   -0.000001
FEAT-2026-0073/T02             7.115892      7.115892   -0.000000
```

**`FEAT-2026-0020/T04` is a defect this feature introduced.** That WU was
re-armed and then **never re-dispatched** — its frontmatter carries
`completed_out_of_loop: true` and a note saying it was finished in the operator's
own session because the `gh` CLI needs an unsandboxed subprocess. So its
`cost_usd: 0.16309` is not a new cycle's spend; it is the *same* spend recorded
in `re_arm_history[0].prior_cost_usd: 0.16309`. The migration folded the history
figure into `cumulative_cost_usd` without resetting `cost_usd`, so the file now
reads $0.33 for a unit whose one and only `attempt_outcome` event cost $0.163.
`cumulative_duration_seconds: 42.693` duplicates `duration_seconds: 42.693` the
same way.

The root cause is worth naming precisely, because it is the feature's own lesson
turned back on it: `fold_cumulative_on_rearm` may safely fold `cost_usd` because
it runs *at dispatch*, where `cost_usd` provably holds the prior cycle. The
migration runs *offline*, where `cost_usd` means "the prior cycle" **or** "the
current cycle" depending on whether a re-dispatch ever happened — a value with
two meanings, read as if it had one. That is precisely the defect class this
feature exists to remove.

**Blast radius, stated honestly.** `wu_lifetime_cost_usd` is events-first and
falls back to frontmatter only for a WU with no `attempt_outcome` events at all.
`FEAT-2026-0020/T04` has one such event, so the accessor returns $0.163090 and no
current consumer reads the wrong number. Verified in this session. The damage is
to the record a human reads, and to any downstream WU that is re-armed, never
re-dispatched, and has no event history — where the fallback would return double.

**I did not fix it.** `rearm_migration.py` is T02's file and
`FEAT-2026-0020/T04` is an already-`done` feature's record; both are on this WU's
**Do not touch** list. See the hedged-verdict follow-up record below.

**`FEAT-2026-0060/T01` is pre-existing and deliberately out of scope.** Its
`cumulative_cost_usd: 4.478344` accounts for one of three prior cycles;
`re_arm_history`'s three `prior_cost_usd` entries sum to $13.709549, and with the
current cycle's $2.593786 the events total is $16.303334. This is the old
value-guard's under-count, frozen in a `done` record. `PLAN.md` ruled back-filling
cost onto `done` features' records out of scope and T02's criterion 2 required
`cumulative_cost_usd` be left *unchanged* on a fold-ran unit, so the migration
correctly stamped it and did not repair it. It is named here so a reader does not
mistake "carries the marker" for "reads its own lifetime correctly".

`FEAT-2026-0053/T07`'s $0.002141 delta is rounding inside the migration's $0.02
tolerance, not a fold error.

### This close was not re-armed

The WU body asked for this to be said either way. `WU-90-gate-1-close.md` carries
`attempts: 1` and no `re_arm_history`, so this close did not exercise the fold
path on itself. The best available evidence for the converged contract on a real
record is therefore the `FEAT-2026-0060/T01` demonstration above, not this
session.

### Consumer-visible contract changes

Enumerated per `close-discipline.md` §3. Four, all real; the same four appended
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
   should run it once after upgrading. Read item 4 of the follow-up record first
   — the fold-never-ran branch has a known defect on units that were re-armed and
   never re-dispatched.

4. **`WU.template.md`'s frontmatter notes changed, in both shipped copies.**
   *(changed)* The template that `specfuse init` and `specfuse upgrade` place in
   every downstream project now documents `folded_through_re_arm` and states the
   unconditional `cumulative_*` contract. The canonical
   `specfuse/loop/data/templates/WU.template.md` and the vendored
   `.specfuse/templates/WU.template.md` are asserted byte-identical by test.

Human acknowledgment of this list is the gate review's business
(`autonomy_default: review`; gate 1 lands at `awaiting_review`).

## Cost analysis

`events.jsonl`'s `attempt_outcome` sum is authoritative. It reconciles against
every WU's frontmatter exactly — **no gap, no lower bound needed**.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — explicit fold marker | $4.00 | 1 | **$1.2600597** | −$2.74 (−68%) |
| T02 — migrate existing shapes | $3.00 | 1 | **$2.2002231** | −$0.80 (−27%) |
| T03 — contract and accessor | $2.00 | 1 | **$1.1096172** | −$0.89 (−45%) |
| **Implementation subtotal** | **$9.00** | **3** | **$4.5699000** | **−$4.43 (−49%)** |
| G1-CLOSE — this session | $5.00 | 1 (in flight) | not yet in `events.jsonl` | — |
| WU sum incl. close | $14.00 | — | $4.57 + close | — |
| Gate budget | $14.00 | — | headroom before close: **$9.43** | — |

Per-attempt ledger, in emission order — every attempt passed first try:

```
T01 attempt 1  passed  $1.2600597   793.346s   -> task_completed cost_usd 1.26006
T02 attempt 1  passed  $2.2002231   824.828s   -> task_completed cost_usd 2.200223
T03 attempt 1  passed  $1.1096172   665.581s   -> task_completed cost_usd 1.109617
                       -----------  ---------
attempt_outcome sum    $4.5699000  2283.755s (38m 04s)
```

Frontmatter reconciliation, each line checked independently:

- T01 `cost_usd: 1.26006` = 1.2600597 rounded ✔
- T02 `cost_usd: 2.200223` = 2.2002231 rounded ✔
- T03 `cost_usd: 1.109617` = 1.1096172 rounded ✔
- No WU in this feature was re-armed, so no `cumulative_*` field participates ✔
- Sum of all three = $4.5699000 = the `attempt_outcome` total ✔

**Acceptance criterion 1's "$10.00 WU sum" does not reconcile against any figure
in this feature, and is not invented into one here.** The four WUs'
`planned_cost_usd` frontmatter reads 4.00 + 3.00 + 2.00 + 5.00 = **$14.00**, which
is also `GATE-01.md`'s `cost_budget_usd`. The implementation-only subtotal is
**$9.00**. Neither is $10.00. The most likely reading is a drafting-time estimate
that moved before the WUs were written and was not carried into the close's
criterion; the $14.00 gate-budget half of the same criterion is correct. Named
rather than reconciled, per this WU's escalation trigger on cost figures.

**The gate budget carries no headroom by construction.** `planning-discipline.md`
§5's corollary asks for the WU sum **plus one re-attempt of the largest WU**;
$14.00 is the bare sum. It was not tested: all three implementation WUs passed
first try at 49% under estimate, leaving $9.43 against a $5.00 close. Had any WU
spun, the gate would have halted on budget with the padding absent.

**The estimates were uniformly high, not noisy.** All three came in under, by 27%
to 68%. Each WU shipped one focused module plus one red-first test file, and each
had its oracle named and its red-on-HEAD test spelled out in the body before
dispatch — the arming discipline `GATE-01.md` recorded, including the runtime
probe that reproduced the defect rather than arguing it. That is the cheapest
shape a work unit comes in.

### Failure-class breakdown

**Zero non-passing attempts.** Three implementation WUs, three attempts, three
passes: 100% first-attempt success, $0.00 spent on refused or failed attempts
against the 28%-of-closing-spend baseline `planning-discipline.md` §5 records. No
`failure_class` is non-null anywhere in this feature's `events.jsonl`, no
`human_escalation` event was emitted, and no `work/` attempt notes exist. The
table this section would otherwise carry has no rows.

## Deferred verification

Per acceptance criterion 2, one entry per criterion not verified in-loop.

**1. The migration's behaviour against a real downstream project.**
- *Criterion:* T02's "ship the migration as code, not a one-off edit", whose
  stated purpose is that a downstream project upgrading past this contract has
  the same two shapes in its own feature folders.
- *Why not verified in-loop:* this repository is the only corpus available to the
  session. `rearm_migration.py` was run against exactly one tree — this one —
  with 8 re-armed units, of which 2 were fold-never-ran. Every other shape it
  handles is exercised only by fixtures in `tests/test_rearm_migration.py`.
- *Where it actually gets checked:* the first downstream project that runs
  `migrate_repo` against its own `.specfuse/features/` after upgrading. See *What
  the loop did NOT verify*.

**2. That `cumulative_*` reads correctly on every already-`done` record.**
- *Criterion:* `GATE-01.md`'s definition of done, "every re-armed work unit in
  this repository carries one shape".
- *Why not verified in-loop:* verified for the **marker** — 8 of 8, quoted above.
  Not verified for the **values**, and `PLAN.md` deliberately scoped back-filling
  cost onto `done` features' records out, while T02's criterion 2 required
  `cumulative_cost_usd` be left unchanged on a fold-ran unit. The reconciliation
  in this close is the first time the values were checked at all, and it found
  `FEAT-2026-0060/T01` under-counting by $9.23.
- *Where it actually gets checked:* nowhere automatically — the honest answer.
  `wu_lifetime_cost_usd`'s events-first precedence means no consumer reads the
  under-count, which is exactly why it survived. The reconciliation script quoted
  above is the check; nothing runs it on a schedule.

**3. That no consumer reads `cumulative_*` directly. — `PLAN.md`'s claim is
wrong, corrected here.**
- *Criterion:* `PLAN.md`'s existing-mechanism search, "`arm_eval.py:172` only,
  via `wu_lifetime_cost_usd`. No consumer reads `cumulative_*` directly, so
  changing when it is written breaks no reader."
- *Why not verified in-loop:* it was verified — by re-grepping in this session —
  and **it does not hold**. There is a third reader the plan's grep missed:
  `specfuse/loop/loop.py`'s `task_completed` emitter reads
  `cumulative_cost_usd` (and `cumulative_attempts`) straight from frontmatter to
  compute the event's lifetime payload, added by #199 and predating this feature.
  It does not go through `wu_lifetime_cost_usd`. So T01's change **does** reach a
  reader: for a re-arm the old guard would have skipped, the `task_completed`
  event now carries a larger, more complete `cumulative_cost_usd`. That is the
  intended direction and it is still a behaviour change the plan asserted would
  not occur. The complete in-repo reader set is: the fold in `loop.py`, the
  `task_completed` emitter in `loop.py`, and `cost.py`'s fallback line.
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
fixture. This matters more than usual because the one real fold-never-ran shape
the migration met that its fixtures did not model — a unit re-armed and never
re-dispatched — is precisely the one it got wrong.

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
from any producing WU's self-report:

```
$ python3 -m unittest tests.test_rearm_fold_marker tests.test_rearm_migration \
                     tests.test_fold_contract_documented -v
Ran 22 tests in 0.017s
OK

$ python3 -m unittest discover -s tests -b
Ran 2310 tests in 108.534s
OK (skipped=3)
```

## Hedged-verdict follow-up record

One entry, per `close-discipline.md` §2.

### FU-1 — the migration double-counts a unit that was re-armed and never re-dispatched

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"A re-arm
  folds the prior cycle's spend into `cumulative_*` every time, driven by an
  explicit marker rather than by inferring 'already folded' from a zero. Every
  re-armed work unit in this repository carries one shape, and the frontmatter
  contract says which."*
- **Why it is unmet:** the marker half is met — 8 of 8, quoted above. The shape
  half is not, for one record. `rearm_migration.py`'s fold-never-ran branch folds
  `re_arm_history[].prior_cost_usd` into `cumulative_cost_usd` without resetting
  `cost_usd`. That is correct for a unit that was re-armed and re-dispatched,
  where `cost_usd` holds the new cycle. It duplicates the spend for a unit
  re-armed and never re-dispatched, where `cost_usd` still holds the prior cycle.
  `FEAT-2026-0020/T04` is such a unit — `completed_out_of_loop: true` — and its
  frontmatter now reads $0.326180 against an events total of $0.163090.
- **Why it was not fixed in-session:** `specfuse/loop/rearm_migration.py` is
  T02's file and `FEAT-2026-0020/T04` is an already-`done` feature's record.
  Both are on this WU's **Do not touch** list. Fixing either here would be the
  scope drift `result-contract.md` §2 names, on the last work unit of the feature.
- **The exact re-run condition that would upgrade the verdict to `met`:** amend
  `migrate_file`'s fold-never-ran branch so that, when `cost_usd` already equals
  the `re_arm_history` prior sum within the existing $0.02 tolerance, it treats
  the money as already present — resetting `cost_usd` to `0.0` in the same write
  set rather than adding a second copy — repair `FEAT-2026-0020/T04`'s record,
  then re-run the reconciliation quoted under *The finding*. It upgrades to `met`
  when every re-armed WU's `cost_usd + cumulative_cost_usd` equals its
  `attempt_outcome` sum, with `FEAT-2026-0060/T01`'s pre-existing $9.23
  under-count excluded by name — that one is out of scope by `PLAN.md`, not by
  this fix.
- **kind:** `externally-verifiable-later`

**Verdict ceiling:** one entry, `externally-verifiable-later` — so **rework
exists**, and the operator has a real choice between accepting the hedge now and
running the fix above. This is not a case where `met` is unreachable.

## Lessons promoted

Two entries appended to `.specfuse/LEARNINGS.md`, both tagged
`FEAT-2026-0067/G1-CLOSE`.

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
the fourth instance this close produced — the migration double-count in FU-1, in
which the fix for a value-with-two-meanings introduced a value with two meanings.
The `#593` framing offered by the criterion is recorded above as not holding,
rather than counted.

**2. A guard that reads a field is not the same guard when it runs somewhere
else.** The general form of FU-1, and the more useful of the two: T01's fold may
read `cost_usd` safely because it runs at dispatch, where the field provably
holds the prior cycle. T02's migration reads the same field offline, where its
meaning depends on history the file does not state. The invariant was in the
*call site*, not in the field, and moving the read broke it silently.

## Verdict

**`partially_met`.**

What is met, verified fresh in this session rather than inherited: the fold is
triggered by an explicit marker and no longer reads `cost_usd`'s value; a
zero-cost re-arm folds; the fold is idempotent across all four accumulators,
demonstrated on a real thrice-re-armed record and not only on fixtures; all 8
re-armed work units in this repository carry `folded_through_re_arm` equal to
their `re_arm_count`; the template and `cost.py` state the converged contract in
both shipped copies; and the full suite is green at 2310 tests.

What is not: one of the two records the migration folded now double-counts
$0.163090, because `rearm_migration.py` read `cost_usd` offline as though it
carried the meaning it carries at dispatch. The feature's own defect class,
reproduced by its own fix, on the record of a work unit that was re-armed and
never re-dispatched. It is masked from every current consumer by
`wu_lifetime_cost_usd`'s events-first precedence, and it is still wrong in the
file a human reads.

The hedge is deliberate and narrow. FU-1 names the one-branch fix and the exact
reconciliation that upgrades this to `met`. The pre-existing $9.23 under-count on
`FEAT-2026-0060/T01` is **not** part of the hedge: `PLAN.md` scoped back-filling
`done` records out before any work began, and a close does not get to re-scope a
feature retroactively in order to report a cleaner number.
