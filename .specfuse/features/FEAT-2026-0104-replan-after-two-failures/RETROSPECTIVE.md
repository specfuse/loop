# FEAT-2026-0104 — re-plan after two failures instead of a third identical attempt

Two gates. Gate 1 built the re-plan trigger: a unit whose next attempt would be
its last permitted one is re-planned in place by a dispatched planning session
rather than re-dispatched with the identical prompt, and emits the `replan`
event `gate_eval.evaluate_auto_close` has consumed since FEAT-2026-0018. Gate 2
built the operator-facing half: a unit that still exhausts its budget escalates
`blocked_human` with a six-part brief whose first option and recommendation are
re-planning the remaining gate — recommended, never executed.

Nine implementation units, one intermediate close, one plan-next, one terminal
close. Every dispatched attempt passed on its first try. That last sentence is
the most important fact in this document, and the reason it is: a feature whose
mechanism only fires on failure cannot observe itself in a run where nothing
fails. The sections below measure that rather than talk around it.

## Measurements

Every command below was run fresh in this terminal close session, from the
repository root, against the working tree as this close found it. Exit codes are
read directly from the shell, never inferred from output text. Commands ran
through `.venv/bin/python`.

### feature_oracle: PASS

`GATE-02.md` declares `feature_oracle: "python3 -m unittest tests.test_spinout_brief_end_to_end -v -b"`.

```
$ .venv/bin/python -m unittest tests.test_spinout_brief_end_to_end -v -b
test_run_prints_a_conforming_brief_and_carries_it_on_the_event ... ok
Ran 1 test in 0.543s
OK
exit 0
```

`GATE-01.md`'s oracle is re-run here too — this is the feature's terminal close,
so gate 1's composite question is re-asked against the tree gate 2 left, not
inherited from gate 1's own close:

```
$ .venv/bin/python -m unittest tests.test_replan_end_to_end -v -b
Ran 1 test in 0.509s
OK
exit 0
```

### The brief a real run produces — four facts checked here

The oracle asserts the brief is *conforming*; it does not show what an operator
reads. The literal brief, taken from the `human_escalation` event of a real
`loop.run()` driven to attempt exhaustion, is reproduced verbatim below in
§ "The brief, as a real `loop.run()` produces it" — its own `## `-level part
headings would end this section early, so it is pasted there rather than here.
Four facts were checked against that run, not read off the source:

1. **It satisfies the escalation contract, and the event carries the same text.**
   `escalation.validate_escalation_body(message)` returned `[]`, and the
   assertion `message in captured_stdout` held — the event is not a
   separately-rendered copy of what the run printed.
2. **The `replan` event precedes the escalation.** Event stream from that run:
   `task_started, attempt_outcome, baseline_attribution, attempt_outcome,
   baseline_attribution, replan, attempt_outcome, baseline_attribution,
   human_escalation`. The automatic re-plan is spent before a person ever sees
   the brief — the premise `GATE-02.md` and T07's option text are both built on.
3. **`/unblock-wu` exists.** T07's criterion required every command the brief
   names to be verified against `.specfuse/skills/`; checked here rather than
   inherited — `.specfuse/skills/unblock-wu/SKILL.md` is present.
   `specfuse run --feature <id>` is the driver's own resume form.
4. **A tracer-bullet stub survived the gate.** Part 3 reads "(Full decision text
   is FEAT-2026-0104/T07's; this brief only guarantees the decision point
   exists.)" — an internal work-unit ID in operator-facing output. See
   § "A defect this close found".

### Fresh oracle re-runs, per acceptance criterion

| Command | Result | Covers |
|---|---|---|
| `.venv/bin/python -m unittest tests.test_spinout_brief_end_to_end -v -b` | exit 0, Ran 1 | gate 2 `feature_oracle`; T06 |
| `.venv/bin/python -m unittest tests.test_spinout_brief_replan_option -v -b` | exit 0, Ran 3 | T07 — option 1 + recommendation, the eleven-reason table, the negative observation that nothing flips |
| `.venv/bin/python -m unittest tests.test_replan_note_collision -v -b` | exit 0, Ran 1 | T08 — both records survive a re-planned attempt |
| `.venv/bin/python -m unittest tests.test_replan_end_to_end -v -b` | exit 0, Ran 1 | gate 1 `feature_oracle` |
| `.venv/bin/python -m unittest tests.test_replan_trigger tests.test_replan_turn_contract tests.test_replan_event_emission -v -b` | exit 0, Ran 20 | T02, T03, T04 |
| `.venv/bin/python -m unittest tests.test_deterministic_refusal_repeat -v -b` | exit 0, Ran 13 | `GATE-01.md` § "What this gate must not break" — a byte-identical refusal over an untouched tree still escalates where it did, and never becomes a re-plan |
| `.venv/bin/python .specfuse/scripts/event_type_gate.py` | exit 0 — "no validation errors across 74 events.jsonl file(s), 2078 event(s) checked" | T04's schema addition, over the whole corpus |
| `.venv/bin/python .specfuse/scripts/leak_scan.py --all` | exit 0 — "gitleaks 8.30.1", "clean" | T09's prose criterion |
| `.venv/bin/python .specfuse/scripts/lint_plan.py <feature_dir>` | exit 0 — "structurally valid" | narrow tier for `close` (`plannext`) |

The driver's own once-per-gate broad run for gate 2 is recorded in `GATE-02.md`:
`ok: true`, `failing: []`, `ran_at: 2026-09-11T03:12:25Z`, and
`work/gate-logs/tests-20260911T031159587497Z.log` shows `Ran 3927 tests`,
`OK (skipped=3)`. Gate 1's, in `GATE-01.md`, shows `Ran 3922 tests`,
`OK (skipped=3)`.

### The driver builds that actually ran this feature, and what was in them

This is the measurement that decides what the feature's own clean run is
evidence of, and it is checkable rather than argued. Each gate's driver is
pinned to a tree before the gate's units land, and the pins are recorded as
`driver_build_pinned` events. Grepping each pinned build's `loop.py`:

| Pinned tree | Dispatched | `should_replan_instead_of_retry` | `format_spinout_escalation_brief` |
|---|---|---|---|
| `2bbbe6d0` | gate 1, first run (discarded) | absent | absent |
| `0de44d13` | gate 1, run of record (T01–T05, G1-CLOSE-INTERMEDIATE, G1-PLAN) | absent | absent |
| `f68ab48b` | gate 2 (T06–T09, this close) | **present** | absent |

So: gate 1 was dispatched by a driver with no re-plan trigger — it could not have
re-planned anything. Gate 2 was dispatched by a driver that carried the trigger
but not the brief, because the pin was taken before T06 wrote it. **No driver
that ran any part of this feature contained the spin-out brief.** Whatever this
feature's own run shows, it cannot show the brief working in the field.

### Re-plan count across both gates: zero

The escalation trigger on this close is that a missing re-plan count is a defect
in the feature's own emit path. The count is recoverable and it is zero, which is
a measurement, not an absence of one:

- `events.jsonl` for this feature: 11 `attempt_outcome` events, all
  `outcome: "passed"` at `attempt: 1`, every `failure_class` and
  `failure_signature` null, every `re_arm_count` 0. No `replan` event, no
  `human_escalation` event, no `re_arm_dispatched` event.
- Across every `.specfuse/features/*/events.jsonl` in this repository: **0**
  `replan` events.
- The emit path is not broken, and that is separately checkable: the harness run
  reproduced above emitted `replan` into a real feature's `events.jsonl` in the
  right position, and `event_type_gate.py` validates it against the schema T04
  added. The reason the count is zero is that `should_replan_instead_of_retry`
  is consulted only on the failed-attempt path (`loop.py:10987`, inside the
  branch reached after an attempt fails), and no attempt failed.

So the answer to "how many attempts across both gates were re-plans, and did the
units that re-planned then pass" is **zero, and n/a** — the same answer gate 1
gave. What that leaves unproven is stated in § "What the loop did NOT verify".

### Human waits per feature, re-measured rather than assumed

`PLAN.md` records the metric that pulled this feature forward: human waits per
feature (mean `human_escalation` events per feature) moved from 1.16 on drivers
up to 0.14.x to **2.09** on 0.15.0 and later. Re-measured in this session by
re-running the corpus miner and the metrics script over the deduped corpus
(worktree and clone duplicates excluded, features cut by the `source_version`
that ran their attempts):

| Band | n features | Human waits / feature |
|---|---|---|
| baseline `<=0.14.x` | 224 | 1.16 (unchanged) |
| post-review `>=0.15.0` | 12 | **1.92** (was 2.09 at n=11) |
| `0.19.x` — this feature alone | 1 | 0.00 |
| target | — | < 0.5 |

#### The move from 2.09 to 1.92 is arithmetic, not evidence

2.09 × 11 ≈ 23
escalations; adding one feature with zero escalations gives 23 / 12 = 1.92. The
numerator did not move. Every part of the delta is the denominator growing by
this feature, and reporting it as an improvement would be reporting that we
counted one more thing.

#### One feature is not a trend, and this is a worse sample than most

Its own zero is not the mechanism working: no unit failed, so nothing escalated,
so the trigger was never consulted and the brief — absent from every driver that
ran here, per the pin table above — could not have rendered even if one had. A
run with zero failures tells you nothing about a mechanism that only fires on
failure. The honest reading is that the metric is unmoved and untested by this
feature, and stays untested until a real unit spins out on a driver built from
this branch.

### One environment artifact, named so it is not mistaken for a defect

`tests.test_replan_end_to_end`, `tests.test_spinout_brief_end_to_end`,
`tests.test_spinout_brief_replan_option` and `tests.test_replan_note_collision`
drive a real `loop.run()`, which preflights `require_session_env_writable`
against the agent session-env directory under the user home. A sandboxed shell
denies that write and every one of them errors with
`SystemExit: loop.py: cannot create a directory under '<session-env>' (Operation
not permitted)` before reaching a line of feature code. Observed again in this
session, then green unsandboxed. This is a report about where the suite ran, not
about the repository — gate 1's close recorded the same thing, and it recurred
exactly as predicted.

### Per-criterion state (`close-discipline.md` §5)

Gate 2 carries no `GATE-NN-CRITERIA.md` artifact, so there is no per-criterion
record to check and `close-l` does not apply. This is attempt 1 of this close, so
nothing could have been carried forward in any case: every oracle above — narrow
and broad alike — ran fresh in this session. Nothing in this document inherits a
producing unit's self-report.

## The brief, as a real `loop.run()` produces it

The oracle asserts the brief is conforming; it does not show what an operator
reads. Below is the brief taken from the `human_escalation` event's `message`
payload of a real `loop.run()` driven to attempt exhaustion through the same
harness the oracle uses (`integration_workspace()`, `dispatch` stubbed to report
complete, `verify` stubbed red, `max_attempts: 3`). It is the run's own output,
not a brief composed here: the script asserts `message in captured_stdout`
before printing, and that assertion held.

```
==== rc=1  validate_escalation_body=[]
==== event types: task_started, attempt_outcome, baseline_attribution, attempt_outcome,
     baseline_attribution, replan, attempt_outcome, baseline_attribution, human_escalation
==== brief printed by the run == brief on the event: True
```

```
<!-- specfuse:escalation id=FEAT-2026-8961/T01 -->

SPIN-OUT — FEAT-2026-8961/T01 (FEAT-2026-8961/T01)

## What has been done so far
Gate 1 is open. Work units finished so far: (none yet). FEAT-2026-8961/T01 was dispatched 3 time(s): attempt 1: failed, attempt 2: failed, attempt 3: failed. The automatic re-plan fired before the last attempt, and already failed: a fresh session rewrote the unit body after the earlier failures, and the rewritten body still did not pass.

## What this issue is about
FEAT-2026-8961/T01 exhausted its attempt budget without a passing verification run and has been escalated (spinning_detected).

## What decision is needed, and why
A person needs to decide how this unit proceeds. (Full decision text is FEAT-2026-0104/T07's; this brief only guarantees the decision point exists.)

Work units still waiting behind it: FEAT-2026-8961/G1-RETRO, FEAT-2026-8961/G1-LESSONS, FEAT-2026-8961/G1-DOCS, FEAT-2026-8961/G1-PLAN.

## Why it did not, or could not, close automatically
Every dispatched attempt failed its own verification and the unit's attempt budget (3) is exhausted, so no further automatic attempt is possible.

## Options, each with pros and cons
1. **Re-plan the remaining gate** — run `/unblock-wu` on FEAT-2026-8961/T01, FEAT-2026-8961/G1-RETRO, FEAT-2026-8961/G1-LESSONS, FEAT-2026-8961/G1-DOCS, FEAT-2026-8961/G1-PLAN, choosing re-arm (retry-as-is) for each. Re-arming resets each unit's `attempts` to 0, so the driver's automatic re-plan trigger — the automatic re-plan already ran once against FEAT-2026-8961/T01 and that rewritten attempt already failed — becomes reachable again for every re-armed unit in gate 1, not just the one that spun out. Pros: widens a remedy that already produced a rewrite once, without inventing a new mechanism. Cons: it is the same remedy that already failed for FEAT-2026-8961/T01; if nothing about scope or shape changes first, the re-plan may reproduce the same rewrite.
2. **Abandon the unit** — pros: unblocks the rest of the gate; cons: anything depending on this unit, and everything named in option 1 if it was re-armed instead, is stranded.

## A recommendation
Option 1. The unit met its own oracle three times and lost; a narrower unit is the remedy, and the remedy is already named and one command away — the automatic re-plan already ran once against FEAT-2026-8961/T01 and that rewritten attempt already failed, so this is widening it rather than proposing anything new.

Reply with the number of your choice, or prose if none fit:
1. Re-plan the remaining gate
2. Abandon the unit

Resume after deciding:
  specfuse run --feature FEAT-2026-8961
```

The four facts checked against this run are listed in
§ "The brief a real run produces — four facts checked here" above.

## Gate 1

Gate 1 built the re-plan trigger: a unit whose next attempt would be its last
permitted one is re-planned in place — a dispatched planning session rewrites
its body, the driver reloads it against the gate's own bookkeeping, and the
last attempt slot is spent on the rewritten prompt — and emits `replan` into
the `gate_eval.evaluate_auto_close` consumer that has waited for it since
FEAT-2026-0018. Five implementation units, all `passed` on attempt 1.

This is the gate's second run. The first was reverted to the plan baseline
after four units passed and the full suite hung; `PLAN.md` § "Gate 1 was
reverted once" holds that account and the criteria rewrite that followed.
The sections below are about the run of record unless they say otherwise.

### Measurements

Every oracle this gate's acceptance criteria name, re-run fresh in the close
session against the gate's final tree:

### feature_oracle: PASS

- `python3 -m unittest tests.test_replan_end_to_end -v -b` — exit 0, 1 test.
- `python3 -m unittest tests.test_replan_trigger tests.test_replan_turn_contract tests.test_replan_event_emission -b` — exit 0, 20 tests.
- `python3 .specfuse/scripts/event_type_gate.py` — exit 0.
- `python3 .specfuse/scripts/leak_scan.py --all` — exit 0.
- `python3 -m unittest tests.test_deterministic_refusal_repeat -b` — exit 0
  (T01's criterion that a byte-identical refusal over an untouched tree still
  escalates where it did before, rather than becoming a re-plan).

The driver's own gate-boundary broad run is recorded in `GATE-01.md`:
`ok: true`, `failing: []`, and `work/gate-logs/tests-20260910T201923*.log`
shows `Ran 3922 tests`, `OK (skipped=3)`.

One environment note, because it will recur and cost someone an attempt:
`tests.test_replan_end_to_end` drives a real `loop.run()`, which preflights
`require_session_env_writable` against the agent session-env directory under
the user home. A sandboxed shell denies that write and the test errors with
`PermissionError: [Errno 1] Operation not permitted` before touching a line of
re-plan code. It is green unsandboxed. The failure is about where the suite
ran, not about the repository.

### Did any unit in this gate re-plan?

**No.** Not once. `events.jsonl` for this feature contains zero events of
`event_type: "replan"`, and all five `attempt_outcome` events carry
`outcome: "passed"` at `attempt: 1` with `re_arm_count: 0`. The four string
matches on `replan` in the event log are test-module filenames inside
`files_touched`, not events.

So the question the acceptance criterion asks — *did the re-planned unit then
pass?* — has no instance to answer it. That matters more than it reads, and
gate 2 must not round it off:

- Every claim this gate makes about re-plan behaviour rests on tests that stub
  the `claude -p` boundary. `test_replan_end_to_end` drives a genuine
  `loop.run()` over a synthetic single-WU feature in a temp git repo, and
  `test_replan_turn_contract` proves the turn is a dispatched session rather
  than a string transform — the exact defect that made the first run's version
  of this unit hollow. Both are strong tests. Neither is a real spin.
- The trigger has therefore never selected a real failing unit, no real
  planner session has ever written a narrowed body, and no real re-planned
  attempt has ever been dispatched. The feature is proven **runnable**, not
  proven **useful**.
- The one thing that would have been the most direct evidence available —
  this feature tripping its own trigger on itself — did not happen because
  the gate's units were, this time, sized well enough not to fail. That is a
  good outcome and a thin one. Gate 2's brief work is being drafted against
  synthetic evidence only, and `G1-PLAN` should say so in `GATE-02.md` rather
  than let gate 2's criteria assume field behaviour that has not been
  observed.

### Interaction with FEAT-2026-0103's retained-tree repair

`GATE-01.md` § "What this gate must not break" asks how often a guard refusal
became a repair versus a re-plan, now that both sit on the same retry path.
From the attempt record: **zero and zero.**

Five `attempt_outcome` events, five `passed`, no `failure_class`, no
`failure_signature`, no guard refusal of any kind, no retained-tree repair
dispatched, no re-plan fired. The two mechanisms have never met on real input
in this feature's record, so the ordering claim between them is carried
entirely by T02's flag-scope table and by
`test_refusal_repeat_escalates_and_the_replanned_attempt_never_dispatches`,
which asserts directly that a unit tripping `detect_deterministic_refusal_repeat`
escalates there and never reaches the re-plan branch.

The design position is unchanged and worth restating so gate 2 does not
re-derive it: the guard-refusal branches sit in the `outcome == "passed"` arm
and `continue` before the re-plan predicate is consulted at all, and
`detect_deterministic_refusal_repeat` runs at the top of the loop before
dispatch. A repair and a re-plan cannot both claim one attempt. What is
untested is the *sequence* — a refusal repaired once, the repair failing, and
the unit then arriving at its next-to-last attempt. Nothing in this gate
exercises that path.

### Cost analysis

| WU  | planned | actual (`events.jsonl`) | variance |
|-----|---------|-------------------------|----------|
| T01 | 3.50    | 2.3217                  | −1.178 (−33.7%) |
| T02 | 3.00    | 1.6738                  | −1.326 (−44.2%) |
| T03 | 3.50    | 2.7132                  | −0.787 (−22.5%) |
| T04 | 2.50    | 1.2728                  | −1.227 (−49.1%) |
| T05 | 2.00    | 0.7775                  | −1.223 (−61.1%) |
| **total** | **14.50** | **8.7590**        | **−5.741 (−39.6%)** |

`events.jsonl` and the committed WU frontmatter agree exactly, per unit, on
`cost_usd` and on `attempts: 1`; there is no #3296-class disagreement to
escalate on.

**The variance is not estimation skill.** Each planned figure carried headroom
for a second attempt, and every unit passed on the first, so the −39.6% is the
retry pad going unspent — precisely the pattern `[FEAT-2026-0040/G3-CLOSE]`
warns about, where padding priced as one re-attempt of the largest unit prices
a retry at a figure a retry then disproves. Here it is worse than unspent,
because of the next paragraph.

**The reverted run's spend is not in this reconciliation and cannot be put
there.** `events.jsonl` opens with a `driver_build_pinned` at 15:47:59 and
then jumps to 19:19:50 — a three-and-a-half-hour hole with an orphaned pin
event at the top of it. The revert to the plan baseline took the first run's
`task_started` / `attempt_outcome` / `task_completed` events with it, so no
per-unit spend survives for four unit dispatches and two full-suite runs.
What does survive is `work/gate-logs/`, which is not reverted: six
verification passes in that window (15:56, 16:00, 16:04, 16:07 narrow; 16:36
and 16:51 full-suite). Bounding it by wall clock — the discarded run spanned
~64 minutes against the ~60 minutes that bought the $8.76 of record — the
true cost of getting gate 1 to green is roughly **$16–18, not $8.76**, i.e.
slightly *over* the $14.50 plan rather than 40% under it. The gate reads
under budget only because the expensive half was discarded along with the
code, and the ledger has no way to say so. Any reader taking $8.76 as this
gate's cost is being misled by an artifact of the revert, not by the estimate.

**A budget hole gate 2 inherits.** `PLAN.md`'s `planned_cost_usd: 30.00`
decomposes exactly as 14.50 (T01–T05) + 4.50 (this close) + 6.00 (`G1-PLAN`)
+ 5.00 (`G2-CLOSE`) — leaving **nothing** for gate 2's substantive work units,
which had not been drafted when the figure was set. Actual spend leaves
$21.24, and after the three remaining closing units at plan that is roughly
**$5.74 for all of gate 2's implementation**. `G1-PLAN` should either fit
gate 2 inside that or revise the feature estimate deliberately; discovering it
at `G2-CLOSE` would be discovering it too late.

### Failure-class breakdown

No non-passing attempts in the run of record: five attempts, five `passed`,
every `failure_class` and `failure_signature` null. There is nothing to
classify.

The reverted run's failure is unrecoverable from `events.jsonl` for the reason
given above, but `work/gate-logs/` pins it precisely.
`tests-20260910T163616*.log` and `tests-20260910T165118*.log` are both 817
lines and both stop mid-line at
`test_bookkeeping_commit_crash_run.TestRunHandlesBookkeepingCommitRejection.test_run_halts_gracefully_when_bookkeeping_commit_rejected`
— the same test, twice, never completing. That is the non-terminating unit
loop `PLAN.md` describes: the re-plan branch rewound the attempt counter to 0,
so the ceiling-relative trigger re-fired on every fresh budget. Classified by
hand it is a `hang`, not a `failed` — which is part of why it was expensive:
a hang produces no `attempt_outcome`, so it leaves no failure class for the
learnings pass to cluster on.

### Deferred verification

Acceptance criteria this gate did **not** verify in-loop:

- **"Fails on HEAD before this unit's edits"** (T01, T02, T03, T04). The
  driver verifies the green side; the red side is a claim about a tree that no
  longer exists, self-reported by the session that then deleted it. Not
  checked anywhere automated — CI on the PR also sees only green. This one
  stays deferred; the honest mitigation is that all four new modules are
  genuinely new files, so the pre-edit red is at least structurally certain.
- **"Run the full suite before reporting complete"** (T01–T04's
  **Verification**, the instruction added after the first run). The driver's
  exit oracle for these units was the narrow tier, and the gate logs show what
  that meant: `Ran 1 test`, `Ran 6 tests`, `Ran 13 tests`, `Ran 1 test`. No
  artifact records a session-side full-suite run. Where it actually got
  checked: the driver's own full-suite runs at T05's entry
  (`tests-20260910T201626*.log`, 3922 OK) and at the gate boundary
  (`tests-20260910T201923*.log`, 3922 OK) — after the fact, twice, both clean.
- **The trigger firing on a real spin.** No unit failed, so nothing selected a
  real failing unit. Checked only by the first real spin on a driver carrying
  this gate's build; gate 2 must not assume it has occurred.
- **The re-plan turn producing a genuinely better-scoped unit.**
  `test_narrowed_rewrite_has_fewer_acceptance_criteria`,
  `test_narrowed_rewrite_states_an_explicit_non_goal` and
  `test_narrowed_rewrite_passes_the_wu_lint` assert structure against a
  stubbed planner. Nothing in-loop can assert that a real planner's rewrite is
  *better*. Checked by operator judgment at the gate boundary on the first
  real re-plan.
- **T05's "the auto-close sentence at §2 is reconciled rather than
  duplicated."** Prose-quality judgment with no oracle; `grep -n "replan"
  docs/methodology.md` confirms both halves are present at lines 187–193 but
  cannot confirm they read as one statement. Checked by the human reflection
  note in `GATE-01.md` at review time.

### For G1-PLAN

Three things gate 2's draft should carry, all of them findings this session
made rather than restatements of the plan:

1. Gate 2 is being drafted on synthetic evidence. Say so in `GATE-02.md`, and
   do not write a gate-2 criterion whose oracle is "the trigger behaved well
   in the field."
2. The untested sequence is refusal → repair → repair fails → next-to-last
   attempt. If gate 2's escalation brief offers a re-plan as its default
   option, that sequence is the one an operator will hit first.
3. Gate 2 has roughly $5.74 of the feature's declared budget left. Either
   size it to that or revise `planned_cost_usd` explicitly.

## Gate 2

Gate 2 built the operator-facing half: a unit that exhausts its attempt budget
now escalates with a six-part brief whose option 1 and recommendation are
re-planning the remaining gate, and the brief travels on the `human_escalation`
event's `message` so `/attention` and `/gate-status` read it rather than
re-derive it. Four implementation units, all `passed` on attempt 1, no re-arms,
no escalations.

Three of the four were not in the plan when gate 1 was drafted. T08 exists
because `G1-PLAN`'s probe found a real defect — `persist_attempt_notes` writes
one `work/<wu>/attempt-N.md` per buffered entry and a re-planned attempt buffers
twice under the same N, so the re-plan transcript clobbered the failure evidence
that triggered it (measured on a real run: `attempt-1.md` 757 bytes,
`attempt-2.md` 59 bytes, `attempt-3.md` 3491 bytes). A brief that points an
operator at a record with a hole in it is worse than one that points nowhere.
Finding that from a probe rather than from a failing test is the gate's best
outcome, and it is an argument for the probe, not for the tests.

### Did any unit in gate 2 re-plan?

**No** — same answer as gate 1, and the sharper version of it. Gate 2's driver
pin (`f68ab48b`) is the first build in this feature's history that contained
`should_replan_instead_of_retry` at all, so gate 2 is the only place a re-plan
could have happened. It did not, because the trigger sits on the failed-attempt
path and all four attempts passed first try.

The evidence the automatic re-plan trigger works is therefore entirely: the four
gate-1 test modules (20 tests), `tests.test_replan_end_to_end` driving a real
`loop.run()` over a synthetic feature, and `G1-PLAN`'s probe, whose output is
pasted in `GATE-02-REVIEW.md` § "The probe" and which this close reproduced
independently (see § Measurements). Every one of those stubs the `claude -p`
boundary. None is a real spin.

### The execute-versus-recommend decision, re-read against what gate 2 built

`GATE-02.md` settled execute-versus-recommend as **recommend only**, on four
pieces of gate-1 evidence. That decision was due a second look here rather than a
re-affirmation by default. Re-read against what gate 2 actually built, the
gate-2 evidence is a mix, and it is worth separating:

**Two gate-2 findings weaken the case for recommend-only.**

1. The command the brief recommends is `/unblock-wu` on the spun-out unit plus
   every remaining unit in the gate, "choosing re-arm (retry-as-is) for each."
   That is not a re-plan the operator executes; it is a *re-arm* that makes the
   automatic trigger reachable again. The option's own text says so. So the
   gap between "recommend" and "execute" is narrower than the decision assumed:
   nobody is hand-authoring a rewrite either way, and what the operator is
   actually gating is whether the driver may reset some attempt counters.
2. Gate 2 raised no new blast-radius concern. T07's negative observation — after
   a run that renders the brief, every remaining unit's `status` and `attempts`
   are byte-identical and no second `replan` event is emitted — is green, and
   the code path that would execute is `/unblock-wu`'s, which already exists and
   is already exercised by operators.

**Three things hold the decision where it is, and they win.**

1. The success rate of a re-planned unit is still **n = 0**. Nothing in gate 2
   moved that number; gate 2's own clean run is precisely why it did not.
   Auto-executing a mechanism with no observed success rate is not a default.
2. `PLAN.md`'s stated precondition for widening — "deferred until re-plan has
   behaved on real spins" — is still unmet. Gate 2 produced no real spins either.
   Executing here would overrule a deferral on evidence that has not arrived.
3. The brief has never rendered in a real driver run: the pin table above shows
   `format_spinout_escalation_brief` absent from every build that dispatched any
   part of this feature. A recommendation that turns out to be badly worded costs
   an operator one confused read; the same text wired to an action that resets
   attempt counters across a gate costs a gate.

**Conclusion: no gate-2 evidence changes the decision, and finding 1 above is
recorded as the thing to re-read first when it is next revisited** — if the
recommended action is a re-arm rather than an authored re-plan, then the eventual
"execute" question is narrower than `GATE-02.md` framed it, and should be asked
in those terms.

### A defect this close found

Part 3 of the brief — "What decision is needed, and why" — still carries T06's
tracer-bullet placeholder:

> A person needs to decide how this unit proceeds. (Full decision text is
> FEAT-2026-0104/T07's; this brief only guarantees the decision point exists.)

T06 was licensed to stub "the option text and the recommendation" (parts 5 and
6); it stubbed part 3 as well. T07's criteria named parts 5 and 6, so nothing in
the gate owned part 3, and the parenthetical shipped. It is not a criteria
failure — every acceptance criterion in the gate is about parts 1, 5 and 6, and
`escalation.validate_escalation_body` only requires the part to be present and
non-empty — but it is an operator-facing string naming an internal work-unit ID,
which is exactly the class of thing `.specfuse/rules/human-output.md` exists to
keep out of a human's way.

Recorded here rather than fixed: this close's **Do not touch** does not cover
driver code, but rewriting an escalation string is an implementation change with
its own oracle, and doing it inside a close is the drift `result-contract.md` §2
names. It belongs in a bug issue against `format_spinout_escalation_brief`.

The generalizable half is in `LEARNINGS.md`: a tracer bullet that stubs more
parts than the plan licensed leaves stubs no later unit owns, because the later
units are scoped to what the plan said would be stubbed.

### Failure-class breakdown

No non-passing attempts in gate 2: four attempts, four `passed`, every
`failure_class` and `failure_signature` null. Nothing to classify. Across both
gates' runs of record the count is eleven attempts, eleven `passed`, zero
non-passing — which is why this feature could not observe its own mechanism.

The gate-1 first run's hang is unrecoverable from `events.jsonl` and is
classified by hand in § "Gate 1" above from `work/gate-logs/`; it is a `hang`,
not a `failed`, and it emits no `attempt_outcome`, so it appears in no aggregate.

## Consumer-visible contract changes

Four additions and one fix. Nothing was removed or renamed, and no existing
configuration file needs an edit.

1. **`replan` is now a valid driver event type** in
   `specfuse/loop/data/schemas/driver-event.schema.json`, with payload
   `{"attempt": <int>, "max_attempts": <int>}`. Additive to a published schema;
   a consumer validating driver events against the previous 15-type registry
   would have rejected it, and `.specfuse/scripts/event_type_gate.py` would have
   failed any feature emitting one. `gate_eval.evaluate_auto_close` has consumed
   this event since FEAT-2026-0018 — this feature supplies the emitter.
2. **The driver re-plans a unit whose next attempt would be its last permitted
   one**, instead of re-dispatching the identical prompt. Ceiling-relative, so at
   the default `MAX_ATTEMPTS = 3` it is "after two failures"; a unit declaring
   its own `max_attempts` keeps its ceiling, and a unit declaring
   `iterate_on_failure` is exempt outright. Because a `replan` event disables
   auto-close for its gate, a gate containing a re-planned unit now reaches a
   dispatched close where it previously could auto-close — a behaviour change
   visible to any project running this driver, with no config key to opt out.
3. **A `blocked_human` spin-out now prints a six-part operator brief and carries
   it on the `human_escalation` event's `message` field.** Previously that halt
   printed one line and the payload carried `reason`, `attempts` and
   `attempts_usage` only. `message` is a new payload field consumers may read;
   the brief satisfies `escalation.validate_escalation_body`, so an escalation
   issue filed from it is well-formed. Four of the eleven unit-level escalation
   reasons carry the re-plan option (`spinning_detected`,
   `spinning_signature_repeat`, `convergence_plateau`, `replan_unchanged_body`);
   the other seven get a plain re-arm option with the reason it is excluded.
4. **`replan_unchanged_body` is a new `blocked_human` escalation reason** — a
   re-plan turn that returns an unchanged body escalates rather than spending
   the last attempt on the same prompt.
5. **Fixed: a re-planned attempt no longer loses its failure evidence.** The
   attempt's re-plan transcript used to overwrite `work/<wu>/attempt-N.md`. Both
   records now persist under names that say which is which, and both are named
   in the escalation's bookkeeping commit. An un-re-planned attempt's note keeps
   its existing filename.

Documentation surfaces updated to match: `docs/methodology.md` (and its packaged
copy under `specfuse/loop/data/`), `.specfuse/verification.yml.example` (and its
packaged copy), and the `authoring-work-units` skill (and its `plugins/` canonical
copy). Each item above is appended to `CHANGELOG.md`'s `Unreleased` section,
classified and traced to `FEAT-2026-0104`.

Human acknowledgment of this list is the gate-boundary review step; it is
recorded in `GATE-02.md` § "Reflection notes", which is written by the operator
and is still the placeholder at the time this close reports.

## Cost analysis

`PLAN.md` carries `planned_cost_usd: 39.50`, revised at `G1-PLAN` from the
original 30.00. The original decomposed as 14.50 (T01–T05) + 4.50
(G1-CLOSE-INTERMEDIATE) + 6.00 (G1-PLAN) + 5.00 (G2-CLOSE) and left nothing at
all for gate 2's implementation, which had not been drafted when the number was
set. Gate 1's close flagged the hole and asked `G1-PLAN` to either fit gate 2
into the ~$5.74 remaining or revise deliberately; it revised, pricing gate 2's
four units at 9.50 for a feature total of **39.50**. Actuals below are read from
this feature's `events.jsonl` `attempt_outcome` payloads, not from WU
frontmatter — every `done` unit has exactly one attempt, so the two agree, but
the event log is the source that survives a re-arm.

| WU | Planned | Actual | Delta | Wall |
|---|---|---|---|---|
| T01 re-plan tracer bullet | $3.50 | $2.321728 | −$1.1783 (−33.7%) | 713.6s |
| T02 trigger predicate | $3.00 | $1.673818 | −$1.3262 (−44.2%) | 492.7s |
| T03 planning-turn contract | $3.50 | $2.713218 | −$0.7868 (−22.5%) | 744.0s |
| T04 emit the `replan` event | $2.50 | $1.272766 | −$1.2272 (−49.1%) | 490.4s |
| T05 document the trigger | $2.00 | $0.777467 | −$1.2225 (−61.1%) | 956.1s |
| **gate 1 substantive** | **$14.50** | **$8.758997** | **−$5.7410 (−39.6%)** | 56.6 min |
| G1-CLOSE-INTERMEDIATE | $4.50 | $2.918651 | −$1.5813 (−35.1%) | 432.0s |
| G1-PLAN | $6.00 | $6.050012 | +$0.0500 (+0.8%) | 631.1s |
| **gate 1 total** | **$25.00** | **$17.727660** | **−$7.2723 (−29.1%)** | — |
| T06 spin-out brief tracer bullet | $3.50 | $1.568016 | −$1.9320 (−55.2%) | 490.2s |
| T07 re-plan option, recommend-only | $3.00 | $1.178220 | −$1.8218 (−60.7%) | 433.5s |
| T08 re-plan note collision | $1.50 | $0.825284 | −$0.6747 (−45.0%) | 336.7s |
| T09 document the brief | $1.50 | $0.646968 | −$0.8530 (−56.9%) | 487.7s |
| **gate 2 substantive** | **$9.50** | **$4.218489** | **−$5.2815 (−55.6%)** | 29.1 min |
| G2-CLOSE (this attempt) | $5.00 | not yet recorded | — | — |
| **feature, recorded** | **$39.50** | **$21.946148** | **−$17.5539 (−44.4%)** | this close unpriced |

**Gate 1's variance, per gate.** −29.1%, and it is not estimating skill. Every
unit's estimate carried headroom for a second attempt and every unit passed on
the first, so the gap is the retry pad going unspent. The one unit priced with no
retry pad — `G1-PLAN`, a single-pass drafting session — came in at +0.8%, which
is the tell: estimates for units that cannot retry were accurate; estimates for
units that could were padded by roughly the cost of one retry, and no retry
happened.

**Gate 1's discarded run is named here, not netted out.** Gate 1's first run
dispatched T01–T04, all passed and committed, and the gate then died on a
non-terminating unit loop that hung the suite. The work was reverted to the plan
baseline — and `events.jsonl` is a committed artifact, so the revert took that
run's `task_started` / `attempt_outcome` / `task_completed` events with it. The
log opens with an orphaned `driver_build_pinned` at 15:47:59 and jumps three and
a half hours to 19:19:50. What survives is `work/gate-logs/`, which is untracked
and therefore not reverted: six verification passes in that window (15:56, 16:00,
16:04, 16:07 narrow; 16:36 and 16:51 full-suite, both 112,358 bytes and both
stopping mid-line at the same never-completing test). Bounded by wall clock —
~64 discarded minutes against the ~60 that bought the $8.76 of record — gate 1's
close put the discarded spend at roughly **$16–18**.

So the honest feature-level figure is not −44.4%. Recorded $21.95, plus $16–18
discarded, plus this close (unpriced; the comparable closing units cost $2.92 and
$6.05) puts the true cost of this feature at roughly **$41–46 against a $39.50
plan** — at plan or slightly over it, not 44% under. **Any reader taking the
−44.4% row as this feature's cost performance is reading an artifact of the
revert.** The revised 39.50 estimate was, in the end, close to right; it looks
generous only because the expensive half of gate 1 was discarded along with the
code, and the ledger has no way to say so.

**Restarts and re-arms.** Eight `driver_staleness_detected` events, all
non-halting — one after each unit that edited `specfuse/loop/loop.py`, which is
the predictable count. Zero `re_arm_dispatched` events. Zero `human_escalation`
events.

## What the loop did NOT verify

Gate 1 deferred five items. None is silently dropped below: each is carried
forward with what changed, or discharged with the evidence.

1. **"Fails on HEAD before this unit's edits"** (T01–T04, and again T06–T08).
   **Still deferred, now across both gates.** The driver verifies the green side;
   the red side is a claim about a tree that no longer exists, self-reported by
   the session that deleted it. CI on the PR also sees only green. The structural
   mitigation is unchanged and now covers seven units: every module named is a
   genuinely new file, so the pre-edit red is at least structurally certain.
   Where it is actually checked: nowhere automated.
2. **"Run the full suite before reporting complete"** (T01–T04, T06–T08).
   **Still deferred, with a new observation.** The driver's exit oracle for these
   units was the narrow tier, and gate 2's logs show what that meant: `Ran 1
   test`, `Ran 3 tests`, `Ran 1 test` for T06, T07, T08. No artifact records a
   session-side full-suite run for any of them. But the gate-1 lesson's drafting
   move worked: T09's `produces:` names only `docs/methodology.md`, so its narrow
   selection was empty, fell back to the full command, and ran `Ran 3927 tests,
   OK (skipped=3)` at 03:09 — one unit before the gate boundary, exactly where
   that lesson said to put it. Where it is actually checked: the driver's own
   full-suite runs at T09's entry and at the gate boundary (03:11, `Ran 3927
   tests, OK`), after the fact, both clean.
3. **The trigger firing on a real spin.** **Still deferred, and now measurably
   so.** Gate 2 was the first gate ever dispatched by a driver carrying the
   trigger (pin `f68ab48b`), and no unit failed, so the trigger was never
   consulted. Zero `replan` events exist in any feature in this repository.
   Where it is actually checked: the first real spin-out on a driver built from
   this branch. Nothing before then.
4. **The re-plan turn producing a genuinely better-scoped unit.** **Still
   deferred.** Three tests assert structure — fewer acceptance criteria, an
   explicit non-goal, the WU lint passes — against a stubbed planner. Nothing
   in-loop can assert a real planner's rewrite is *better*. Where it is actually
   checked: operator judgment at the gate boundary on the first real re-plan.
   This close re-affirms that this is the only oracle the feature has for rewrite
   quality, which is the load-bearing reason the brief recommends rather than
   executes.
5. **T05's "the auto-close sentence at §2 is reconciled rather than duplicated."**
   **Still deferred, and now larger.** Gate 1 deferred this to the human
   reflection note in `GATE-01.md`; that note is still the unwritten placeholder.
   T09 then added a third paragraph to the same passage under the same kind of
   criterion. `grep -n "replan" docs/methodology.md` confirms all three are
   present and cross-referenced (lines 187–197 for the auto-close and trigger
   halves, 215–230 for the operator half, which links back to check 2 by name);
   what no grep can confirm is that they read as one account. Where it is
   actually checked: the human reflection notes in `GATE-01.md` and `GATE-02.md`,
   both still placeholders at the time this close reports.

Gate 2 adds three of its own:

6. **The brief rendering in a real driver run.** `format_spinout_escalation_brief`
   is absent from every driver build that dispatched any part of this feature.
   Every observation of the brief in this document — including the literal paste
   above — comes from a `loop.run()` over a synthetic feature with the model
   boundary stubbed. Where it is actually checked: the first real `blocked_human`
   spin-out on a driver built from this branch.
7. **T07's flag-scope table as an exhaustive enumeration.** The table is correct
   about the eleven unit-level escalation reasons, and
   `test_matches_the_flag_scope_table_for_all_eleven_reasons` holds. Its stated
   derivation over-claims: `grep -o '"reason": "[a-z_]*"' specfuse/loop/loop.py`
   run in this session yields thirteen strings, five of which
   (`broad_run_gate_failure`, `gate_budget_exceeded`,
   `gate_budget_exceeded_post_dispatch`, `post_pass_invariant_failed`,
   `preexisting_gate_failure`) are gate- or feature-level halts a spun-out unit's
   brief never reaches, and three of the table's eleven
   (`spinning_detected`, `all_attempts_zero_token`, `human_step_required`) are
   assigned through a variable rather than that literal and so do not appear in
   the grep at all. The table's *content* is right; the sentence claiming the
   grep produces it is not. Mitigated by construction rather than by the
   enumeration: `replan_option_applies` returns `False` for any reason not in the
   table, verified by `test_unknown_reason_defaults_to_no_replan_option`, so a
   reason nobody enumerated fails closed. Where it is actually checked: that
   fail-closed default, not the enumeration.
8. **Part 3 of the brief.** No acceptance criterion in either gate asserts on it,
   and it still carries a tracer-bullet stub. See § "A defect this close found".

Nothing else was deferred. Everything in `GATE-02.md`'s definition of done other
than the human review step has an executed command behind it in § Measurements.

## Lessons

Three entries promoted to `.specfuse/LEARNINGS.md`, all tagged
`[FEAT-2026-0104/G2]`: a self-hosting gate cannot exercise its own code because
the driver pin predates the gate's commits; a feature whose mechanism fires only
on failure must buy its evidence with a committed probe rather than hope it trips
itself; and a tracer bullet must stub only the parts the plan licensed, because
later units are scoped to that list. The defect in § "A defect this close found"
is the concrete instance of the third.

Not promoted: gate 2's cost variance (the same retry-pad pattern gate 1 already
recorded and `[FEAT-2026-0040/G3-CLOSE]` already generalizes) and the sandbox
session-env artifact (already in gate 1's retrospective, and a property of where
the suite runs rather than a rule for drafting).

## Verdict

Advisory only — on a terminal gate the judge session writes the verdict the
terminal flips read, from the evidence in § Measurements and the gate diff, and
this section is deliberately withheld from it.

`verdict: met`, on this reading: every acceptance criterion in `GATE-02.md`'s
definition of done has an executed command behind it in § Measurements, the
gate's `feature_oracle` re-ran green in this session, all four implementation
units are `done`, and the documentation and roadmap surfaces match what shipped.

What that verdict does **not** claim, stated plainly because the temptation to
round it off is the whole reason this feature is worth a careful close: the
feature is proven **runnable**, not **useful**. Zero re-plans fired, zero units
escalated, and no driver that ran any part of this feature contained the spin-out
brief. The metric that motivated the feature is unmoved — its apparent
improvement from 2.09 to 1.92 is one more zero in the denominator, nothing else.
Every claim about field behaviour rests on tests and a probe that stub the
`claude -p` boundary. The first real spin-out on a driver built from this branch
is the first evidence that will mean anything, and until then eight items in
§ "What the loop did NOT verify" stay open.
