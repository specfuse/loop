# FEAT-2026-0104 — re-plan after two failures instead of a third identical attempt

Two gates. Gate 1 built the re-plan trigger: a unit whose next attempt would be
its last permitted one is re-planned in place by a dispatched planning session
rather than re-dispatched with the identical prompt, and emits the `replan`
event `gate_eval.evaluate_auto_close` has consumed since FEAT-2026-0018. Gate 2
built the operator-facing half: a unit that escalates `blocked_human` gets a
six-part brief, and where the reason is one re-planning can help, the brief's
first option and recommendation are re-planning the remaining gate —
recommended, never executed.

Ten implementation units, one intermediate close, one plan-next, one terminal
close on its **fourth** dispatch. Eleven of the twelve implementation attempts in
the run of record passed on the first try; the one that did not, T10's attempt 1,
failed on two ruff diagnostics in a new test file and passed at attempt 2. The
close's four dispatches are: two lowered by a judge (#3305, #3306), a third that
recorded its own `not_met` on a defect it found in T10's widening (#3308), and
this one, dispatched after that defect was fixed in tree. Every one of the three
findings lived in the same six-part brief, and every one was found by a reader
rather than by an oracle — the feature's own summary of itself, and § "Lessons"
is where it generalizes. **No unit in either gate has ever been re-planned**,
because no unit ever reached a second failure. That is the most important fact in
this document, and the reason it is: a feature whose mechanism only fires on
repeated failure cannot observe itself in a run that never repeats one. The
sections below measure that rather than talk around it.

## Measurements

Every command below was run fresh in this terminal close session, from the
repository root, against the working tree as this close found it. Exit codes are
read directly from the shell, never inferred from output text. Commands ran
through `.venv/bin/python`.

This is the **fourth dispatch** of this close, and the reason matters more than
the count. `events.jsonl` carries three `task_started` events for `G2-CLOSE`
(03:12, 11:26 and 16:47 on 2026-09-11) and three `judged` events. This fourth
dispatch is not in the log yet — it is evidenced instead by
`WU-90-gate-2-close.md`'s `started_at: 2026-09-11T17:17:10` and `GATE-02.md`'s
matching `broad_run.ran_at`:

| Dispatch | What it measured | Close verdict | Judge | Filed |
|---|---|---|---|---|
| 1 (03:12) | T06–T09 | `met` | lowered to `not_met` | **#3305** — part 3 of the brief shipped a tracer-bullet stub naming an internal work-unit ID |
| 2 (11:26) | T06–T09 plus #3305's fix | `met` | lowered to `not_met` | **#3306** — PLAN/roadmap/gate status not `done`; circular, tracked as a judge defect in **#3307** |
| 3 (16:47) | T06–T10, after the gate was reopened to add T10 | `not_met` | agreed, `lowered: false`, `disagreed: false` | **#3308** — part 3 claimed an exhausted attempt budget at the nine sites T10 widened it to |
| 4 (17:17, this one) | T06–T10 plus #3308's fix | — | — | — |

Dispatch 3 is the one that behaved as `close-discipline.md` §2 asks: it found
an operator-facing defect in its own gate's deliverable and recorded `not_met`
rather than a note, the judge agreed for the first time in this feature's
history (`lowered: false`, `disagreed: false`), and the driver filed #3308 and
re-armed. That is the loop working, and it is why this dispatch exists.

The close WU's own frontmatter reads `attempts: 1`: reopening the gate for T10
reset it, so the attempt counter is not the history. `events.jsonl` is.

Nothing below is inherited. The gate carries no `GATE-NN-CRITERIA.md`, so
`close-discipline.md` §5's carry-forward for `narrow` criteria has nothing to
read and does not apply; every command in this section was executed again in
this session, against a tree that now contains T10. What dispatch 1 found, and
the evidence that it is discharged, is in § "The defect this close found, and
what happened to it". **What dispatch 3 found is now discharged too** — the fix
and this session's end-to-end verification of it are in § "The defect T10's
widening shipped, and how it was discharged".

### feature_oracle: PASS

`GATE-02.md` declares `feature_oracle: "python3 -m unittest tests.test_spinout_brief_end_to_end -v -b"`.

```
$ .venv/bin/python -m unittest tests.test_spinout_brief_end_to_end -v -b
test_run_prints_a_conforming_brief_and_carries_it_on_the_event ... ok
Ran 1 test in 0.559s
OK
exit 0
```

`GATE-01.md`'s oracle is re-run here too — this is the feature's terminal close,
so gate 1's composite question is re-asked against the tree gate 2 left, not
inherited from gate 1's own close:

```
$ .venv/bin/python -m unittest tests.test_replan_end_to_end -v -b
Ran 1 test in 0.595s
OK
exit 0
```

One caveat on that PASS, said plainly rather than left for a reader to notice:
the gate's **declared `feature_oracle` no longer covers the whole gate**. `GATE-02.md`
declares one oracle, written when gate 2 ended at T09: it drives a run to
attempt exhaustion, which is the single escalation site T10 did *not* widen.
T10's own module is the oracle for the other nine sites, and it is green — but
it is not the gate's declared composite question, and the gate file was not
re-pointed when the gate was reopened. Recorded as a measurement, not repaired
here: editing `GATE-02.md`'s `feature_oracle` inside the close would change the
question after the answer.

```
$ .venv/bin/python -m unittest tests.test_brief_covers_every_unit_escalation -v -b
Ran 3 tests in 0.538s
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
4. **Part 3 now states the decision.** At attempt 1 this line reported a
   tracer-bullet stub — "(Full decision text is FEAT-2026-0104/T07's; this
   brief only guarantees the decision point exists.)", an internal work-unit ID
   in operator-facing output. In the run reproduced below it reads "Someone
   must choose how FEAT-2026-8972/T01 proceeds, because the driver has run out
   of ways to choose for it…", names the consequence of not deciding, and
   carries no `FEAT-2026-0104` reference. `grep -n "Full decision text is"
   specfuse/loop/loop.py` exits 1 (no match). See § "The defect this close
   found, and what happened to it".

### Fresh oracle re-runs, per acceptance criterion

| Command | Result | Covers |
|---|---|---|
| `.venv/bin/python -m unittest tests.test_spinout_brief_end_to_end -v -b` | exit 0, Ran 1 | gate 2 `feature_oracle`; T06 |
| `.venv/bin/python -m unittest tests.test_brief_covers_every_unit_escalation -v -b` | exit 0, Ran 3 | T10 — every per-unit escalation site carries `message`; a real `agent_reported_blocked` run renders a conforming brief; the four gate-level sites are unchanged |
| `.venv/bin/python -m unittest tests.test_spinout_brief_replan_option -v -b` | exit 0, **Ran 8** | T07 — option 1 + recommendation, the eleven-reason table, the negative observation that nothing flips; plus #3305's three (every part is >= 40 chars, no part leaks an implementing WU ID, part 3 states the decision and why); plus **#3308's two**, new since the previous dispatch: exhaustion is claimed only where the budget ran out, and part 3 does not contradict part 1 |
| `.venv/bin/python -m unittest tests.test_replan_note_collision -v -b` | exit 0, Ran 1 | T08 — both records survive a re-planned attempt |
| `.venv/bin/python -m unittest tests.test_replan_end_to_end -v -b` | exit 0, Ran 1 | gate 1 `feature_oracle` |
| `.venv/bin/python -m unittest tests.test_replan_trigger tests.test_replan_turn_contract tests.test_replan_event_emission -v -b` | exit 0, Ran 20 | T02, T03, T04 |
| `.venv/bin/python -m unittest tests.test_deterministic_refusal_repeat -v -b` | exit 0, Ran 13 | `GATE-01.md` § "What this gate must not break" — a byte-identical refusal over an untouched tree still escalates where it did, and never becomes a re-plan |
| `.venv/bin/python -m unittest tests.test_escalation_contract tests.test_operator_escalation_rule -v -b` | exit 0, Ran 20 | the escalation contract the brief is rendered against, re-run because #3305's fix rewrote a part the contract validates |
| `.venv/bin/python .specfuse/scripts/event_type_gate.py` | exit 0 — "no validation errors across 74 events.jsonl file(s), 2106 event(s) checked" | T04's schema addition, over the whole corpus |
| `.venv/bin/python .specfuse/scripts/leak_scan.py --all` | exit 0 — "gitleaks 8.30.1", "clean" | T09's prose criterion |
| `.venv/bin/python .specfuse/scripts/lint_plan.py <feature_dir>` | exit 0 — "structurally valid" | narrow tier for `close` (`plannext`) |
| `.venv/bin/python -c "from specfuse.loop.loop import escalate_unit"` | exit 0 | T10's §9 symbol check |
| `grep -n "Full decision text is" specfuse/loop/loop.py` | exit 1, no match | #3305 — the negative observation that the stub is gone from the built code, the inverse of the grep the judge used to find it |
| a real `loop.run()` driven to `agent_reported_blocked` (harness from `tests/test_brief_covers_every_unit_escalation.py`), part 1 and part 3 extracted from the `human_escalation` event's `message` | exit 0; `validate_escalation_body` `[]`; part 1 "dispatched 1 time(s)", part 3 "it stopped short of its attempt budget (3)"; `"every attempt its budget" in part 3` → **False** | #3308 — the end-to-end negative observation that the false exhaustion claim is gone at a non-exhaustion site. Verbatim in § "The defect T10's widening shipped, and how it was discharged" |
| a real `loop.run()` driven to attempt exhaustion (`spinning_detected`), same extraction | exit 0; part 1 "dispatched 3 time(s)", part 3 "every attempt its budget (3) allowed has been dispatched and has failed" | #3308's other half — the true claim still renders where it is true. Verbatim in § "The brief, as a real `loop.run()` produces it" |
| `grep -o '"reason": "[a-z_]*"' specfuse/loop/loop.py \| sort -u \| wc -l` | exit 0 — 13 | re-check of the flag-scope table's stated derivation; see § "What the loop did NOT verify" item 7 |

The driver's own once-per-gate broad run is the driver's, not this session's,
and gate 2's was re-run at this dispatch: `GATE-02.md` now records `ok: true`,
`failing: []`, `ran_at: 2026-09-11T17:17:10Z`, and
`work/gate-logs/tests-20260911T171644336963Z.log` shows `Ran 3935 tests`,
`OK (skipped=3)`, with `coverage-20260911T171646248927Z.log` at `TOTAL … 93%`
and `leak-scan-20260911T171658723920Z.log` `clean`. The suite has grown by
exactly the tests each round added — 3922 at gate 1, 3927 at close dispatch 1,
3930 after #3305's three-test class, 3933 after T10's three, 3935 after #3308's
two — and every one of those runs is `OK`. All five logs are on disk and all
five stand.

### The driver builds that actually ran this feature, and what was in them

This is the measurement that decides what the feature's own clean run is
evidence of, and it is checkable rather than argued. Each gate's driver is
pinned to a tree before the gate's units land, and the pins are recorded as
`driver_build_pinned` events. Grepping each pinned build's `loop.py`:

| Pinned tree | Dispatched | `should_replan_instead_of_retry` | `format_spinout_escalation_brief` | `escalate_unit` |
|---|---|---|---|---|
| `2bbbe6d0` | gate 1, first run (discarded) | absent | absent | absent |
| `0de44d13` | gate 1, run of record (T01–T05, G1-CLOSE-INTERMEDIATE, G1-PLAN) | absent | absent | absent |
| `f68ab48b` | gate 2 (T06–T09, **and close dispatch 1**) | **present** | absent | absent |
| `f05ff633` | gate 2 re-entry after the first `not_met` | **present** | **present** | absent |
| `3e879017` | close dispatch 2 | **present** | **present** | absent |
| `9f51243a` | T10, **and close dispatch 3** | **present** | **present** | absent |
| `e0e743a6` | close dispatch 4 (this one) | **present** | **present** | **present** |

Each row is a grep of that pin's own `loop.py` under
`<temp>/specfuse-pins/<tree>/specfuse/loop/`, run in this session. The last row
is new and it is the first row in the table that is fully present: a
`driver_build_pinned` event fired at 17:14:02 for tree `e0e743a6`, after #3308's
fix landed, so **this close is the first thing in the feature's history
dispatched by a driver that carries the whole feature** — trigger, brief,
`escalate_unit`, and the corrected part 3 (`grep -c "stopped short of its
attempt budget"` on that pin's `loop.py` returns 1; on every earlier pin, 0).

So: gate 1 was dispatched by a driver with no re-plan trigger — it could not
have re-planned anything. Every implementation unit of gate 2 ran on a driver
that carried the trigger but not the brief, because that pin was taken before
T06 wrote it. And T10, which widened the brief to nine further escalation sites,
ran on a driver with no `escalate_unit` at all. **The pattern is exact and
holds for all ten units: no work unit of this feature has ever been dispatched
by a driver containing the code that unit was about to write.** That is not an
accident of scheduling; it is what `[FEAT-2026-0104/G2]`'s first lesson says a
self-hosting gate cannot escape.

The one thing that changed at this dispatch is narrower than it looks and is
worth stating precisely so it is not over-read. A close session dispatches no
work units and fails no attempts, so a driver carrying the trigger and the brief
while running a close has nothing to fire either on. **No run of this feature
has still ever rendered a brief or fired a re-plan.** Whatever this feature's own
run shows, it cannot show any of this working in the field.

### Re-plan count across both gates: zero

The escalation trigger on this close is that a missing re-plan count is a defect
in the feature's own emit path. The count is recoverable and it is zero, which is
a measurement, not an absence of one:

- `events.jsonl` for this feature: **16** `attempt_outcome` events — eleven
  implementation attempts (T01–T09 at one each, T10 at two), G1's two closing
  units at one each, and three of this close's four dispatches (the fourth is
  this one, unrecorded until it ends). **Fifteen are `outcome: "passed"`;
  exactly one is `"failed"`.**
  Every `re_arm_count` is 0. No `replan` event, no `human_escalation` event, no
  `re_arm_dispatched` event.
- Across every `.specfuse/features/*/events.jsonl` in this repository: **0**
  `replan` events. (`event_type_gate.py`, run in this session, exit 0, reads 74
  event files and **2116** events; the count is over that whole set.)
- The emit path is not broken, and that is separately checkable: the harness run
  reproduced elsewhere in this document emitted `replan` into a real feature's
  `events.jsonl` in the right position, and `event_type_gate.py` validates it
  against the schema T04 added.

So the answer to "how many attempts across both gates were re-plans, and did the
units that re-planned then pass" is **zero, and n/a** — the same answer gate 1
gave.

#### But gate 2 can say something gate 1's close could not

Gate 1's zero was uninformative: nothing failed, so the trigger was never
reached. Gate 2's zero is informative, because **one attempt did fail and the
record shows exactly how far short of the trigger it stopped.**

`FEAT-2026-0104/T10`, attempt 1, 2026-09-11T16:29:54:

```
"attempt": 1, "outcome": "failed",
"failure_class": "lint", "failure_signature": "B905",
"agent_status": "complete", "re_arm_count": 0,
"files_touched": ["tests/test_brief_covers_every_unit_escalation.py"]
```

`should_replan_instead_of_retry` fires when the *next* attempt would be the
unit's last permitted one. T10 declared no `max_attempts`, so its ceiling is the
default 3, and the trigger point is the transition into attempt 3. T10 failed
once and passed at attempt 2, so the driver never reached the branch. The
trigger did not fail to fire; it was never asked. **One more failure and this
feature would have observed its own mechanism.**

What the one failure was is worth reading, because it is an argument about the
trigger's shape rather than a footnote. The `tests` gate in that same run was
green — `work/gate-logs/tests-20260911T162953455693Z.log` records `Ran 3 tests`,
`OK`, including the end-to-end assertion that a real `loop.run()` renders the
brief — and the AST check in that module can only pass against an edited
`loop.py`, so attempt 1 had done the work. What failed was `lint`, on two ruff
diagnostics in the new test file (`work/gate-logs/lint-20260911T162953527398Z.log`):

```
F401 [*] `json` imported but unused
  --> tests/test_brief_covers_every_unit_escalation.py:35:8
B905 `zip()` without an explicit `strict=` parameter
  --> tests/test_brief_covers_every_unit_escalation.py:149:25
Found 2 errors.
```

One unused import and one missing keyword argument. A failed `tests`/`lint`
gate resets the tree — deliberately, and FEAT-2026-0103 says so in terms: that
feature retained the tree for *bookkeeping-guard* refusals and explicitly
declined to extend it to gate failures, because "retaining a broken tree nobody
has measured is the design that mechanism deliberately rejected". So attempt 2
started from the base tree and re-authored the unit: $1.564567 discarded,
$3.039499 spent, and T10 became the only unit in the feature to finish **over**
its estimate (+15.1%).

There is the one place this feature's own record argues about its own premise.
Had T10 failed a second time the same way, the remedy the trigger would have
reached for is a *planning* turn — a rewrite of the unit's body into something
narrower. The unit's body was not the problem; two ruff diagnostics were.
Re-planning would have been the wrong medicine, applied confidently, on the last
attempt. `PLAN.md` frames spinning as "a unit-shape problem, not a retry-count
problem", and the one real failure this feature produced was neither: it was a
mechanical defect a `ruff --fix` would have cleared. n = 1 proves nothing about
the population, and this is not evidence the trigger is wrong. It is evidence
that the trigger's *selectivity* — which failure classes deserve a re-plan
rather than a retry — is untested, and that `failure_class` is sitting right
there in the event the trigger never consults.

What all of this leaves unproven is stated in § "What the loop did NOT verify".

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

Re-run again in this dispatch rather than carried over (`mine.py` then
`metrics.py`; 567 features and **4688** work units mined, with 224 and 12
surviving the dedup in the two bands). Every figure in the table is identical to
the previous dispatch's, down to this feature's row (`0.19.0 … esc=0 wus=13`).
That is the expected result and re-running is how it is known rather than
assumed: no feature anywhere in the corpus completed between the two dispatches,
and the only thing that changed inside this one is an attempt count, which the
per-feature escalation rate does not read. **Four close dispatches have now
re-measured this metric and it has not moved once.**

#### The move from 2.09 to 1.92 is arithmetic, not evidence

2.09 × 11 ≈ 23
escalations; adding one feature with zero escalations gives 23 / 12 = 1.92. The
numerator did not move. Every part of the delta is the denominator growing by
this feature, and reporting it as an improvement would be reporting that we
counted one more thing.

#### One feature is not a trend, and this is a worse sample than most

Its own zero is not the mechanism working: no unit failed, so nothing escalated,
so the trigger was never consulted and the brief — absent from every driver that
dispatched a unit which produced any of this feature's code, per the pin table
above — could not have rendered even if one had. A
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
not permitted)` before reaching a line of feature code. Gate 1's close recorded
it, close attempt 1 observed it recur exactly as predicted and then ran green
unsandboxed; this attempt ran every command unsandboxed from the start and so
did not reproduce it — recorded here as the standing property it is, not as an
observation this session made. It is a report about where the suite runs, not
about the repository.

### The defect T10's widening shipped, and how it was discharged

Close dispatch 3 found this, recorded `not_met` on it, and the judge agreed; the
driver filed **#3308** and re-armed the close. It was fixed in tree before this
dispatch was dispatched, and the discharge is verified below by executed command.
The finding is kept in full rather than compressed to a line, because what it
measured about the widening is the feature's own best evidence about itself.

T10 widened the brief from one render site to ten. Driven through a real
`loop.run()` in this session — the same harness `tests/test_brief_covers_every_unit_escalation.py`
uses, rigged so the session reports `status: blocked` on its first attempt — the
`human_escalation` event for `agent_reported_blocked` now carries
`['attempts', 'attempts_usage', 'blocked_reason', 'message', 'reason']`. Before
T10 it carried the same list without `message`. That is the widening working, on
the corpus's most common escalation reason of any kind.

`WU-10`'s justification rested on a corpus measurement, so this close re-ran it
rather than quoting it — every `.specfuse/features/*/events.jsonl` reachable
under the home directory, 526 event files, **637 `human_escalation` events**
(T10 measured 636; the corpus grew by one since):

| Reason | n | share | keyed on | brief before T10 |
|---|---|---|---|---|
| `agent_reported_blocked` | 141 | 22.1% | unit | none |
| `spinning_detected` | 120 | 18.8% | unit | **yes** |
| `spinning_signature_repeat` | 99 | 15.5% | unit | none |
| `gate_budget_exceeded` | 75 | 11.8% | feature | out of scope |
| `preexisting_gate_failure` | 71 | 11.1% | feature | out of scope |
| `gate_budget_exceeded_post_dispatch` | 69 | 10.8% | feature | out of scope |
| `deterministic_refusal_repeat` | 30 | 4.7% | unit | none |
| `post_pass_invariant_failed` | 20 | 3.1% | unit | none |
| `broad_run_gate_failure` | 5 | 0.8% | feature | out of scope |
| `all_attempts_zero_token` | 4 | 0.6% | unit | **yes** |
| `human_step_required` | 2 | 0.3% | unit | none |
| `prep_halted` | 1 | 0.2% | unit | none |

Before T10 the brief rendered at the attempt-exhaustion site only, which is
`spinning_detected` plus `all_attempts_zero_token`: **124 of 637, 19.5%** — the
~19% `GATE-02.md` cites, confirmed rather than repeated. After T10 it renders at
every unit-keyed reason: **417 of 637, 65.5%**. The remaining 220 are the four
gate-level halts, deliberately excluded. So T10 roughly tripled the brief's
reach, and the defect below is what it carried along with it.

**What dispatch 3 measured.** Part 3 of the brief that dispatch 3's run rendered
("What decision is needed, and why"), verbatim apart from the trailing sentence —
this is the **pre-fix** text:

```
Someone must choose how FEAT-2026-8963/T01 proceeds, because the driver has run
out of ways to choose for it: every attempt its budget allowed has been
dispatched and has failed, and no automatic re-plan applies to this unit. The
options below are the only ways gate 1 moves again. [...]
```

Part 1 of the same brief ("What has been done so far"), four lines above it:

```
[...] FEAT-2026-8963/T01 was dispatched 1 time(s): attempt 1: blocked. The
automatic re-plan did not fire during this run.
```

The unit declared `max_attempts: 3` and was dispatched once. **"Every attempt
its budget allowed has been dispatched and has failed" is false, and the brief
contradicts itself within four lines.** An operator reading part 3 would believe
the unit is out of attempts; two of its three remain unused, which changes what
option 1 ("re-arm the unit") actually means.

This was not an inference from the diff. The clause was unconditional in the
source, and the sentence immediately below it was not:

```
$ sed -n '3154,3181p' specfuse/loop/loop.py   # pre-fix
        "",
        f"## {ESCALATION_PART_HEADINGS[2]}",
        f"Someone must choose how {wu.wu_id} proceeds, because the driver "
        f"has run out of ways to choose for it: every attempt its budget "
        f"allowed has been dispatched and has failed, and "
        + ("the one automatic remedy available — re-planning the unit into "
           "a narrower one — has already been applied once and its attempt "
           "failed too. "
           if replanned else
           "no automatic re-plan applies to this unit. ")
        + f"The options below are the only ways gate {gate_number} moves "
        f"again. Until one is chosen nothing further is dispatched: "
        + (f"the {len(remaining_wu_ids)} work unit(s) waiting behind this "
           f"one stay blocked, and the gate cannot close."
           if remaining_wu_ids else
           "this gate cannot close."),
        "",
        f"Work units still waiting behind it: {remaining}.",
        "",
        f"## {ESCALATION_PART_HEADINGS[3]}",
        (
            f"Every dispatched attempt failed its own verification and the "
            f"unit's attempt budget ({wu_max_attempts}) is exhausted, so no "
            f"further automatic attempt is possible."
            if reason in ("spinning_detected", "all_attempts_zero_token") else
            f"No further automatic attempt is available for `{reason}`: "
            f"{scope_why}."
        ),
```

Part 4 gates the exhaustion claim on the two reasons where it is true. Part 3
makes the same claim unconditionally. Enumerating the render sites from the
source rather than from memory — the same AST walk T10's own test uses, re-run
here:

| Site | Reason | Budget genuinely exhausted? |
|---|---|---|
| `loop.py:11227` | `spinning_detected` / `all_attempts_zero_token` (the exhaustion `for-else`) | **yes** |
| `loop.py:3262` | dynamic (close/human-step path) | no |
| `loop.py:7774` | `post_pass_invariant_failed` | no |
| `loop.py:10010` | `produces_shape_invalid` | no |
| `loop.py:10148` | `deterministic_refusal_repeat` | no — escalates *earlier* than any ceiling, by design |
| `loop.py:10244` | `prep_halted` | no |
| `loop.py:10286` | `agent_reported_blocked` | no — measured above at 1 of 3 |
| `loop.py:10906` | `spinning_signature_repeat` | no |
| `loop.py:11081` | `convergence_plateau` | no |
| `loop.py:11140` | `replan_unchanged_body` | no |

At one of the ten sites the claim was true by construction. At the other nine it
was unwarranted — the unit may or may not have spent its budget — and in the one
case driven end-to-end it was flatly false, at 1 attempt of 3. Weighted by the
corpus table, the nine unwarranted sites are where **293 of the 417** unit-keyed
escalations land.

No oracle in the gate asserted on it, and **that was the same gap #3305
exposed**. `escalation.validate_escalation_body` requires each part to be present
and non-empty. `SpinoutBriefEveryPartHasContent` requires each part to be ≥ 40
characters, to leak no implementing work-unit ID, and — for part 3 — to state a
decision, a reason and a consequence. Part 3 did all of that; it just did it
untruthfully. `test_brief_covers_every_unit_escalation` asserts the brief exists
and validates at every site, not that its claims match the attempt record. Every
check the gate shipped was about the brief's *shape*.

#### Discharged — what changed, and how this session knows

The fix landed on this branch between dispatch 3 and this one, outside a work
unit (`fix(loop): stop part 3 claiming exhaustion a unit never reached`). Part 3's
exhaustion clause is now gated on the same two-reason test part 4 four lines below
it already applied — the code half of `FOLLOW-UPS.md`'s re-run condition, exactly
as it was written (the test half is where the two diverge; see the end of this
section):

```
$ sed -n '3154,3170p' specfuse/loop/loop.py   # post-fix
        f"## {ESCALATION_PART_HEADINGS[2]}",
        f"Someone must choose how {wu.wu_id} proceeds, because the driver "
        f"has run out of ways to choose for it: "
        # The exhaustion clause is true only where the budget actually ran
        # out. [...]
        + (f"every attempt its budget ({wu_max_attempts}) allowed has been "
           f"dispatched and has failed"
           if reason in ("spinning_detected", "all_attempts_zero_token") else
           f"it stopped short of its attempt budget ({wu_max_attempts}) for a "
           f"reason no further attempt would change ({reason})")
```

Three executed observations in this session, not a reading of the diff:

1. **A real `loop.run()` driven to `agent_reported_blocked`** — the corpus's most
   common per-unit reason, one of the nine sites, rigged through
   `tests/test_brief_covers_every_unit_escalation.py`'s harness on a unit
   declaring `max_attempts: 3`. `rc=1`,
   `validate_escalation_body(stdout) == []`, payload keys
   `['attempts', 'attempts_usage', 'blocked_reason', 'message', 'reason']`,
   and `message in stdout` → `True`. Part 1 and part 3 of that event's brief,
   verbatim:

   ```
   ## What has been done so far
   Gate 1 is open. Work units finished so far: (none yet). FEAT-2026-8971/T01 was dispatched 1 time(s): attempt 1: blocked. The automatic re-plan did not fire during this run.

   ## What decision is needed, and why
   Someone must choose how FEAT-2026-8971/T01 proceeds, because the driver has run out of ways to choose for it: it stopped short of its attempt budget (3) for a reason no further attempt would change (agent_reported_blocked), and no automatic re-plan applies to this unit. [...]
   ```

   `"every attempt its budget" in part 3` → **False**. Part 3 now reports the
   same attempt record part 1 does, and says why no further attempt is coming
   without claiming one was spent.

2. **The true claim still renders where it is true.** The same harness driven to
   attempt exhaustion (`spinning_detected`, three failed attempts, a `replan`
   event in between) renders part 1 "dispatched 3 time(s)" and part 3 "every
   attempt its budget (3) allowed has been dispatched and has failed". The fix
   narrowed the claim; it did not delete it. The full brief is pasted in § "The
   brief, as a real `loop.run()` produces it".

3. **It has an oracle now**, which is what keeps it from returning:
   `tests.test_spinout_brief_replan_option.BriefPartThreeAgreesWithPartOne` —
   `test_exhaustion_is_claimed_only_when_the_budget_ran_out` (the claim is
   present at `spinning_detected`, absent and replaced by "stopped short" at
   `agent_reported_blocked` and `deterministic_refusal_repeat`) and
   `test_part_three_does_not_contradict_part_one` (part 1 says "dispatched 1
   time(s)" and part 3 does not claim exhaustion against it). The module went
   from 6 tests to 8 and the broad run from 3933 to 3935, both green in this
   session.

**One gap between the fix and the re-run condition, stated rather than
smoothed over.** `FOLLOW-UPS.md` asked for "a test that drives a real
`loop.run()` to a non-exhaustion escalation and asserts that part 3's statement
about the attempt record agrees with part 1's". The committed test calls
`format_spinout_escalation_brief` directly with a hand-built attempts list; the
one committed test that *does* drive a real `loop.run()` to a non-exhaustion
escalation (`AgentReportedBlockedCarriesBriefEndToEnd`) asserts only
`validate_escalation_body` and the correlation marker. So the end-to-end half of
the re-run condition was satisfied by observation 1 above — this session — and
not by a committed regression barrier. The defect is discharged; the barrier is
one layer shallower than the follow-up asked for. Carried forward as item 9 in
§ "What the loop did NOT verify" and generalized in § "Lessons".

### Per-criterion state (`close-discipline.md` §5)

Gate 2 carries no `GATE-NN-CRITERIA.md` artifact, so there is no per-criterion
record to check and `close-l` does not apply. This is the fourth dispatch of this
close, and §5's carry-forward would have been available for `narrow` criteria
had that artifact existed — it does not, so there was nothing to carry and
nothing was: every oracle above, narrow and broad alike, ran fresh in this
session. Nothing in this document inherits a producing unit's self-report, and
nothing inherits any earlier dispatch's greens. That is not free — it is the
fourth full re-run of the same oracle set — and a `GATE-02-CRITERIA.md` would
have paid for itself three times over by now. Recorded as an observation for the
next feature that expects more than one close dispatch, not as a change made
here; `[FEAT-2026-0104/G2-CLOSE]`'s entry in `LEARNINGS.md` carries it.

## The brief, as a real `loop.run()` produces it

The oracle asserts the brief is conforming; it does not show what an operator
reads. Below is the brief taken from the `human_escalation` event's `message`
payload of a real `loop.run()` driven to attempt exhaustion through the same
harness the oracle uses (`integration_workspace()`, `dispatch` stubbed to report
complete, `verify` stubbed red, `max_attempts: 3`). It is the run's own output,
not a brief composed here: the script asserts `message in captured_stdout`
before printing, and that assertion held. **Re-run in this session against the
post-#3308 tree**, so the text below is what ships.

```
==== rc=1  validate_escalation_body=[]
==== event types: task_started, attempt_outcome, baseline_attribution, attempt_outcome,
     baseline_attribution, replan, attempt_outcome, baseline_attribution, human_escalation
==== brief printed by the run == brief on the event: True
==== reason: spinning_detected
```

```
<!-- specfuse:escalation id=FEAT-2026-8972/T01 -->

ESCALATED — FEAT-2026-8972/T01 (FEAT-2026-8972/T01)

## What has been done so far
Gate 1 is open. Work units finished so far: (none yet). FEAT-2026-8972/T01 was dispatched 3 time(s): attempt 1: failed, attempt 2: failed, attempt 3: failed. The automatic re-plan fired before the last attempt, and already failed: a fresh session rewrote the unit body after the earlier failures, and the rewritten body still did not pass.

## What this issue is about
FEAT-2026-8972/T01 has escalated for a human decision (spinning_detected) and no further automatic attempt will be dispatched until one is made.

## What decision is needed, and why
Someone must choose how FEAT-2026-8972/T01 proceeds, because the driver has run out of ways to choose for it: every attempt its budget (3) allowed has been dispatched and has failed, and the one automatic remedy available — re-planning the unit into a narrower one — has already been applied once and its attempt failed too. The options below are the only ways gate 1 moves again. Until one is chosen nothing further is dispatched: the 4 work unit(s) waiting behind this one stay blocked, and the gate cannot close.

Work units still waiting behind it: FEAT-2026-8972/G1-RETRO, FEAT-2026-8972/G1-LESSONS, FEAT-2026-8972/G1-DOCS, FEAT-2026-8972/G1-PLAN.

## Why it did not, or could not, close automatically
Every dispatched attempt failed its own verification and the unit's attempt budget (3) is exhausted, so no further automatic attempt is possible.

## Options, each with pros and cons
1. **Re-plan the remaining gate** — run `/unblock-wu` on FEAT-2026-8972/T01, FEAT-2026-8972/G1-RETRO, FEAT-2026-8972/G1-LESSONS, FEAT-2026-8972/G1-DOCS, FEAT-2026-8972/G1-PLAN, choosing re-arm (retry-as-is) for each. Re-arming resets each unit's `attempts` to 0, so the driver's automatic re-plan trigger — the automatic re-plan already ran once against FEAT-2026-8972/T01 and that rewritten attempt already failed — becomes reachable again for every re-armed unit in gate 1, not just the one that spun out. Pros: widens a remedy that already produced a rewrite once, without inventing a new mechanism. Cons: it is the same remedy that already failed for FEAT-2026-8972/T01; if nothing about scope or shape changes first, the re-plan may reproduce the same rewrite.
2. **Abandon the unit** — pros: unblocks the rest of the gate; cons: anything depending on this unit, and everything named in option 1 if it was re-armed instead, is stranded.

## A recommendation
Option 1. The unit met its own oracle three times and lost; a narrower unit is the remedy, and the remedy is already named and one command away — the automatic re-plan already ran once against FEAT-2026-8972/T01 and that rewritten attempt already failed, so this is widening it rather than proposing anything new.

Reply with the number of your choice, or prose if none fit:
1. Re-plan the remaining gate
2. Abandon the unit

Resume after deciding:
  specfuse run --feature FEAT-2026-8972
```

Part 2 reads differently from the paste the previous dispatch carried — it said
"exhausted its attempt budget without a passing verification run" and now says
"has escalated for a human decision … and no further automatic attempt will be
dispatched until one is made". That is #3308's fix reaching part 2 as well as
part 3: the old wording was the same unconditional exhaustion claim one part
earlier, and it was equally false at the nine sites T10 widened to. Part 4, which
is *only* reached on the two exhaustion reasons, still states the exhaustion in
full — as it should, and as it does above.

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

Gate 2 built the operator-facing half: a unit that escalates `blocked_human`
now does so with a six-part brief, and where the reason is one re-planning can
help, option 1 and the recommendation are re-planning the remaining gate. The
brief travels on the `human_escalation` event's `message` so `/attention` and
`/gate-status` read it rather than re-derive it. **Five** implementation units,
six attempts, five units `passed` at attempt 1 and T10 at attempt 2; no re-arms,
no escalations.

T10 was not in the gate when it was armed. The gate closed twice, was reopened,
and T10 widened the brief from the single attempt-exhaustion site to every
per-unit escalation site — the reading `GATE-02-REVIEW.md` had flagged at arming
("that narrowing is the draft's reading, not the plan's words") and the gate was
armed over anyway. `GATE-02.md` § "Gate 2 was widened once" records the
measurement that forced it: the brief reached about 19% of the corpus's 636
real escalations, and the single most common reason, `agent_reported_blocked`
at 22.2%, got none of it. Widening it was right, and the review was right at
arming; the cost of arming over a correct review was one reopened gate and two
further close dispatches. **What the widening then shipped, and its discharge,
is in § "The defect T10's widening shipped, and how it was discharged"** — the
render site moved and the text's conditionals did not, which is the same shape
of defect as #3305 one layer along. It took the third close dispatch to find and
the fourth to confirm fixed.

Three of the first four were not in the plan when gate 1 was drafted. T08 exists
because `G1-PLAN`'s probe found a real defect — `persist_attempt_notes` writes
one `work/<wu>/attempt-N.md` per buffered entry and a re-planned attempt buffers
twice under the same N, so the re-plan transcript clobbered the failure evidence
that triggered it (measured on a real run: `attempt-1.md` 757 bytes,
`attempt-2.md` 59 bytes, `attempt-3.md` 3491 bytes). A brief that points an
operator at a record with a hole in it is worse than one that points nowhere.
Finding that from a probe rather than from a failing test is the gate's best
outcome, and it is an argument for the probe, not for the tests.

### Did any unit in gate 2 re-plan?

**No** — same answer as gate 1, but for a better reason, and the difference is
the single thing this dispatch adds to the feature's own claim. Gate 2's driver
pin (`f68ab48b`) is the first build in this feature's history that contained
`should_replan_instead_of_retry` at all, so gate 2 is the only place a re-plan
could have happened. Gate 1's zero was vacuous: nothing failed. Gate 2's is not
— **T10 failed once**, which is one failure short of the trigger point
(`attempt == max_attempts - 1`, so attempt 2 of 3). The predicate was never
consulted; it did not decline to fire. The full reading, including what the
failure actually was and why re-planning would have been the wrong remedy for
it, is in § "Re-plan count across both gates: zero".

The evidence the automatic re-plan trigger works is therefore still entirely:
the four gate-1 test modules (20 tests), `tests.test_replan_end_to_end` driving
a real `loop.run()` over a synthetic feature, and `G1-PLAN`'s probe, whose
output is pasted in `GATE-02-REVIEW.md` § "The probe" and which this close
reproduced independently (see § Measurements). Every one of those stubs the
`claude -p` boundary. None is a real spin.

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

**A fourth thing arrived after attempt 1 and points the same way.** #3305 is
evidence about this brief specifically: its part 3 shipped an internal work-unit
ID to an operator, through a green `feature_oracle`, a green contract validator
and a close that read the text and did not fail on it. Only a judge session
reading the rendered output caught it. Text that fragile is cheap to correct
when a person is the one acting on it and reads it first; the same text wired to
an action that resets attempt counters across a gate would have executed before
anyone noticed the words were wrong. The finding is now fixed and carries its own
oracle, so it is not an argument that the brief is untrustworthy — it is a
measurement of how far the gate's checks sat from catching an operator-facing
error, and that distance is what "recommend only" is insuring against.

**A fifth thing arrived with T10, and it is the strongest of the three holding
the decision — and this dispatch, which watched it get fixed, does not weaken
it.** T10 widened the render from one escalation site to ten, and § "The defect
T10's widening shipped, and how it was discharged" measures what that widening
shipped: at nine of the ten sites, part 3 of the brief stated that the unit's
attempt budget was exhausted when it was not, contradicting part 1 of the same
brief. That text is exactly what an "execute" variant would act on.
`GATE-02.md`'s argument 3 was already that "a recommendation that turns out to be
badly worded costs an operator one confused read; the same text wired to an
action that resets attempt counters across a gate costs a gate."

The obvious objection to leaning on that now is that the defect is fixed, and the
fix is real: verified end-to-end in this session, carrying two regression tests.
But the base rate is the argument, not the open defect. **Three operator-facing
defects in the same six-part brief across four close dispatches — #3305's
placeholder, part 3's false exhaustion claim, and part 2's copy of the same claim
one part earlier — and not one of them was caught by an oracle.** Each was caught
by a session or a judge reading the rendered text. A brief whose observed
defect-discovery mechanism is "somebody read it" is exactly the artifact you want
a person in front of, and that is what "recommend only" puts there.

**Conclusion: no gate-2 evidence changes the decision, and this dispatch's
evidence holds it where it is more firmly than gate 1 left it.** Finding 1 above
remains the thing to re-read first when it is next revisited — if the recommended
action is a re-arm rather than an authored re-plan, then the eventual "execute"
question is narrower than `GATE-02.md` framed it and should be asked in those
terms. The precondition for asking it at all is unchanged and still unmet: a real
spin, on a real driver, with a re-planned unit whose outcome someone can look
at.

### The defect this close found, and what happened to it

**What it was.** Part 3 of the brief — "What decision is needed, and why" —
shipped T06's tracer-bullet placeholder:

> A person needs to decide how this unit proceeds. (Full decision text is
> FEAT-2026-0104/T07's; this brief only guarantees the decision point exists.)

T06 was licensed to stub "the option text and the recommendation" (parts 5 and
6); it stubbed part 3 as well. T07's criteria named parts 5 and 6, so nothing in
the gate owned part 3, and the parenthetical shipped. It was not a criteria
failure in the narrow sense — every acceptance criterion in the gate is about
parts 1, 5 and 6, and `escalation.validate_escalation_body` only requires each
part to be present and non-empty — but it was an operator-facing string naming
an internal work-unit ID, which is exactly the class of thing
`.specfuse/rules/human-output.md` exists to keep out of a human's way.

**What attempt 1 did with it, and why that was wrong.** Attempt 1 recorded the
finding here, declined to fix it — correctly, since rewriting an escalation
string is an implementation change with its own oracle and doing it inside a
close is the drift `result-contract.md` §2 names — and then wrote an advisory
`verdict: met` anyway, on the reasoning that no acceptance criterion asserted on
part 3. The judge disagreed and lowered it: `judged` carries
`close_verdict: "met"`, `judge_verdict: "not_met"`, `lowered: true`,
`disagreed: true`, `findings: 1`. The judge was right, and the split is worth
naming precisely, because the two halves of attempt 1's reasoning are not the
same question. *Where* to fix an operator-facing defect the close found is a
scope question, and "not in the close" is the right answer. *Whether the gate's
definition of done is met* is a different question, and a gate whose
user-visible deliverable ships a placeholder naming an internal work unit does
not meet it — whatever the per-unit criteria happened to assert on. Deferring
the fix is scope hygiene; deferring the verdict is a hedge, and
`close-discipline.md` §2 retired hedges.

**Discharged.** The driver filed the finding as **#3305**
(`followups_recorded`, `filed: 1`, `issue_numbers: ["3305"]`), and it was fixed
in tree before this attempt was dispatched. Verified here by executed command,
not by reading the diff:

- `grep -n "Full decision text is" specfuse/loop/loop.py` — **exit 1, no
  match**. The inverse of the grep the judge used to find it; the stub is gone
  from the built code, not merely from a diff.
- The brief pasted in § "The brief, as a real `loop.run()` produces it" is from
  a real `loop.run()` in this session. Its part 3 reads "Someone must choose how
  FEAT-2026-8972/T01 proceeds, because the driver has run out of ways to choose
  for it: every attempt its budget (3) allowed has been dispatched and has failed,
  and the one automatic remedy available … has already been applied once and its
  attempt failed too. … Until one is chosen nothing further is dispatched: the 4
  work unit(s) waiting behind this one stay blocked, and the gate cannot close."
  It states the decision, the reason it cannot be made automatically, and the
  consequence of not making it, and it names no `FEAT-2026-0104` anything.
- The fix carried its own oracle, which is what keeps it from regressing:
  `tests.test_spinout_brief_replan_option` grew a
  `SpinoutBriefEveryPartHasContent` class — `test_no_part_is_empty_or_a_placeholder`
  (every part >= 40 characters), `test_no_part_leaks_an_implementing_work_unit_id`
  (no `FEAT-2026-0104`, no "Full decision"), and
  `test_part_three_states_the_decision_and_why_it_is_needed` — taking the module
  from 3 tests to 6, all green in this session, and the broad run from 3927
  tests to 3930. #3308's `BriefPartThreeAgreesWithPartOne` later took the same
  module to 8 and the broad run to 3935.

**Why no separate `CHANGELOG.md` entry.** The stub never reached a release: the
brief itself is an `Unreleased` entry added by this feature, so the corrected
part 3 is the first version any consumer will ever see. A `Fixed` entry for a
defect that existed only between two commits on an unmerged branch would be the
changelog padding `close-discipline.md` §3 warns against. #3305 is the record
that it happened.

**The generalizable half** is in `LEARNINGS.md`, now in two entries: a tracer
bullet that stubs more parts than the plan licensed leaves stubs no later unit
owns; and a close that finds an operator-facing defect in its own gate's
deliverable owes the verdict, not just a note.

### The second finding, #3306, and why nothing here flips a status

Close dispatch 2 was lowered on a different finding: `PLAN.md` and
`.specfuse/roadmap.md` record `status: active` and `GATE-02.md` records
`status: open`, while the close bundle treats this as the feature's terminal
close. The driver filed it as **#3306** (`followups_recorded`, `filed: 1`,
`already_tracked: 1`, `issue_numbers: ["3305", "3306"]`).

It is circular, and `PLAN.md` § "Gate 2 was widened once" already says so: those
three flips are `fire_terminal_flips`' to make, they fire on a `met` verdict,
and a close cannot produce the state a `not_met` verdict withholds. Asking a
close to have already flipped them is asking it to pre-empt the judge. It is
tracked as a judge defect in **#3307**, not as feature work.

Re-measured in this session, the state is unchanged and correctly so:

```
$ grep -n "^status:" .../PLAN.md .../GATE-02.md
PLAN.md:10:status: active
GATE-02.md:3:status: open
```

This close does not touch either, and its own work unit's `Do not touch`
section is explicit about why: "`fire_terminal_flips` owns the terminal flip to
`done`, on both the dispatched-close and auto-close paths. A manual flip is
redundant." Whether those flips fire is settled by the judge's verdict on this
dispatch, not by an edit in this session; on the three dispatches so far the
verdict was `not_met` and they correctly did not.

### Failure-class breakdown

Gate 2 has exactly one non-passing attempt, and it is the feature's only one.

| | Attempts | Passed | Failed | Classes |
|---|---|---|---|---|
| gate 1 (run of record) | 7 | 7 | 0 | — |
| gate 2, T06–T09 | 4 | 4 | 0 | — |
| gate 2, T10 | 2 | 1 | 1 | `lint` / `B905` |
| G2-CLOSE dispatches | 3 recorded | 3 | 0 | — |

`failure_class: "lint"`, `failure_signature: "B905"`, `agent_status:
"complete"` — the session believed it was done, its own `tests` gate agreed
(`Ran 3 tests`, `OK`), and ruff refused on an unused import and a `zip()`
missing `strict=`. One attempt out of thirteen implementation-and-closing
attempts, and the class is the cheapest one there is.

**Three expensive things happened in this feature and the failure taxonomy names
none of them.** First, the judge lowered close dispatches 1 and 2 from `met` to
`not_met`. Second, dispatch 3 recorded its own `not_met`. All three
`attempt_outcome` events read `passed` — the driver's verification passed every
time; what did not pass was the gate's definition of done — so three full
re-closes appear in no failure-class aggregate and in no spend-by-outcome cut.
Third, gate 1's first run hung and emitted no `attempt_outcome` at all. Four
times in one feature, the most expensive thing that happened was invisible to the
taxonomy — and the one thing the taxonomy *did* catch cost $1.56 and was fixed by
deleting an import. `outcome: passed` on a close whose verdict is `not_met` is
not a mislabel; it is the taxonomy answering a different question from the one a
spend-by-outcome cut is asking.

The gate-1 first run's hang is unrecoverable from `events.jsonl` and is
classified by hand in § "Gate 1" above from `work/gate-logs/`; it is a `hang`,
not a `failed`, and it emits no `attempt_outcome`, so it appears in no aggregate.

## Consumer-visible contract changes

Five additions and one fix. Nothing was removed or renamed, and no existing
configuration file needs an edit. Item 6 is new since the previous close
dispatch and is T10's; every other item is unchanged from that dispatch's
enumeration.

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
   `attempts_usage` only. All six parts state their own content — part 3 names
   the decision, why no automatic move remains, and what stays blocked until it
   is made; the tracer-bullet placeholder it carried at close attempt 1 was
   #3305 and is fixed, with the enumeration above describing the text that
   actually ships. `message` is a new payload field consumers may read;
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

6. **Every per-unit `blocked_human` escalation now carries the brief on
   `message`, not only the one raised at attempt exhaustion.** Ten
   `human_escalation` sites keyed on a work unit's own `wu_id` emit `message`;
   before T10 exactly one did, and the other nine carried
   `reason`/`attempts`/`attempts_usage`/`blocked_reason` and nothing a person
   could act on. Measured against the corpus this takes the brief from about 19%
   of 636 real escalations to all per-unit ones, including
   `agent_reported_blocked` (22.2%), `spinning_signature_repeat` (15.6%) and
   `deterministic_refusal_repeat` (4.7%). **The four gate-level
   (`feature_id`-keyed) escalations are deliberately unchanged** — a gate-level
   halt has no single unit to brief about — and a test pins their exact payload
   keys so a later widening has to be on purpose. A consumer reading
   `human_escalation` payloads sees a new `message` field on nine event shapes
   that previously lacked it; nothing was removed. **The defect this carried at
   the previous dispatch is fixed** and the enumeration is updated to describe
   what now ships: parts 2 and 3 asserted the unit's attempt budget was exhausted
   at all ten sites, which is true only at the attempt-exhaustion one. Both are
   now gated on `reason in ("spinning_detected", "all_attempts_zero_token")` and
   render the unit's real position otherwise — part 3 as "it stopped short of its
   attempt budget (N) for a reason no further attempt would change (`<reason>`)",
   part 2 as "has escalated for a human decision (`<reason>`) and no further
   automatic attempt will be dispatched until one is made". Tracked as #3308, and
   the evidence is in § "The defect T10's widening shipped, and how it was
   discharged".

Documentation surfaces updated to match: `docs/methodology.md` (and its packaged
copy under `specfuse/loop/data/`), `.specfuse/verification.yml.example` (and its
packaged copy), and the `authoring-work-units` skill (and its `plugins/` canonical
copy). Each item above is appended to `CHANGELOG.md`'s `Unreleased` section,
classified and traced to `FEAT-2026-0104`; items 1–5 were appended by earlier
dispatches and item 6 by the previous one. **This close edits item 6's
`Unreleased` entry only**, to delete its "Known defect" clause and describe the
corrected text — the entry described what shipped at the time it was written, and
what ships changed. No new entry is added for the #3308 fix itself, for the same
reason no entry was added for #3305's: the brief is an `Unreleased` addition of
this feature, so the corrected wording is the first version any consumer will
ever see, and a `Fixed` line for a defect that existed only between two commits
on an unmerged branch is the changelog padding `close-discipline.md` §3 warns
against.

**Two documentation surfaces were stale for item 6 and are corrected by this
close**, because T10 declared neither in its `produces:` and no later unit owned
them:

- `docs/methodology.md` § "The spin-out brief" opened "a unit that still spins
  out after the automatic re-plan above escalates `blocked_human` with a
  six-part operator brief" — the pre-T10 scope. Retitled "The escalation brief"
  and rewritten to say every unit-level `blocked_human` escalation renders it,
  with the gate-level exclusion stated and the reason given. The one inbound
  cross-reference ("see the spin-out brief below") is updated to match. Both the
  `docs/` copy and the packaged copy under `specfuse/loop/data/docs/` are
  edited; `diff` between them exits 0 after the edit, as it did before.
- `.specfuse/roadmap.md`'s `**Shipped.**` paragraph described the brief's
  narrowing to the spin-out site as delivered scope. It now records the
  widening, keeps the re-plan *option*'s four-of-eleven narrowing (which is
  unchanged and deliberate), and keeps the proven-runnable-not-useful line with
  the new detail that the feature's one failed attempt stopped one failure short
  of the trigger. The row's `status` is untouched: `fire_terminal_flips` owns
  that flip, on a `met` verdict, and this close's `Do not touch` says so.

Human acknowledgment of this list is the gate-boundary review step; it is
recorded in `GATE-02.md` § "Reflection notes", which is written by the operator
and is still the placeholder at the time this close reports.

## Cost analysis

**The number to reconcile against moved twice, and this close's own work unit
carries the stale one.** `WU-90-gate-2-close.md` says to reconcile "against
`PLAN.md`'s `planned_cost_usd` **as revised by `G1-PLAN` to 39.50**". `PLAN.md`'s
frontmatter reads `planned_cost_usd: 43.50`. Both statements were true when
written:

| | Figure | Set at | Decomposition |
|---|---|---|---|
| original | $30.00 | drafting, before gate 2 had work units | 14.50 (T01–T05) + 4.50 (G1-CLOSE-INTERMEDIATE) + 6.00 (G1-PLAN) + 5.00 (G2-CLOSE) — **nothing for gate 2's implementation** |
| first revision | $39.50 | `G1-PLAN` | + 9.50 for gate 2's four units |
| second revision | **$43.50** | gate-2 re-entry, when T10 was added | + 4.00 for T10 |

The second revision is the one to reconcile against, and $43.50 is what the
frontmatter holds: 25.00 (gate 1) + 13.50 (gate 2 substantive) + 5.00
(G2-CLOSE). **`PLAN.md`'s prose has not caught up** — its section is still
headed "The estimate was revised once — $30.00 → $39.50 at G1-PLAN", which is an
accurate account of what `G1-PLAN` did and an incomplete account of the file it
sits in. Flagged rather than edited: rewriting the plan's history inside its own
terminal close is a worse habit than a stale heading, and the frontmatter — the
field every budget check actually reads (`arm_predicate_evaluated`'s
`budget_projection` among them) — is correct.

Actuals below are read from this feature's `events.jsonl` `attempt_outcome`
payloads, not from WU frontmatter. The two no longer agree, and § "Where the
committed ledger disagrees with the event log" says where.

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
| T10 brief at every unit escalation — attempt 1 (`failed`, `lint`/`B905`) | — | $1.564567 | — | 431.4s |
| T10 — attempt 2 (`passed`) | — | $3.039499 | — | 637.5s |
| **T10 total** | **$4.00** | **$4.604066** | **+$0.6041 (+15.1%)** | 1068.9s |
| **gate 2 substantive** | **$13.50** | **$8.822554** | **−$4.6774 (−34.6%)** | 47.5 min |
| G2-CLOSE dispatch 1 + its judge | — | $8.243503 + $0.291491 | — | 863.8s |
| G2-CLOSE dispatch 2 + its judge | — | $7.281791 + $0.281675 | — | 660.7s |
| G2-CLOSE dispatch 3 + its judge | — | $14.982412 + $0.386139 | — | 1271.6s |
| G2-CLOSE dispatch 4 (this one) | — | not yet recorded | — | — |
| **G2-CLOSE, three dispatches** | **$5.00** | **$31.467011** | **+$26.4670 (+529.3%)** | — |
| **feature, recorded** | **$43.50** | **$58.017225** | **+$14.5172 (+33.4%)** | this dispatch unpriced |

**The previous dispatch reported this line as −2.0% and warned that the number
was a coincidence. It has stopped being one.** At two recorded close dispatches
the over-run in the closing sequence happened to cancel a large systematic
under-run across the implementation units; dispatch 3 added $15.37 and the
cancellation is gone. The recorded figure is now **+33.4%**, and it is still an
under-count — see the end of this section. Broken out, nothing in it is close to
plan in either direction.

**Every substantive unit came in under estimate except the one that failed.**
Eight of nine substantive units landed between 22% and 61% under, and the
pattern is not estimating skill — each estimate carried headroom for a second
attempt and eight of nine units passed on the first, so the gap is the retry pad
going unspent. `G1-PLAN`, the one unit priced with *no* retry pad because a
single-pass drafting session cannot retry, came in at +0.8%. That is the tell,
and this dispatch adds the other half of it: **T10, the one unit that did
retry, came in +15.1% — over its estimate, which included a retry pad.** So the
pad was correctly sized in kind and slightly undersized in amount, and eight
units' worth of it was returned unspent while the ninth spent more than it held.
This is `[FEAT-2026-0040/G3-CLOSE]`'s pattern with its confirming case attached.

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

**The closing sequence is what this feature actually cost, and it is no longer
close.** Four dispatches of one close work unit plus three judge sessions,
against a $5.00 line that prices one. Three of the four are already recorded at
**$31.47 — $13.89 more than all ten implementation units cost together
($17.58), and 1.8× that total** — and the fourth is unpriced. Put plainly: this
feature spent more closing itself than building itself, by a wide margin. The
$5.00 was `planning-discipline.md` §5's terminal-close floor, and a floor prices
a close with nothing hard to reconcile. This one had a reverted gate, two
estimate revisions, a corpus metric to re-measure, a reopened gate, two
operator-facing defects found by reading rather than by an oracle, and — on every
one of the four dispatches — a full re-run of an oracle set no
`GATE-02-CRITERIA.md` existed to carry forward.

Dispatch 3 alone cost $14.98 — nearly what dispatches 1 and 2 cost together
($15.53) — and it is the one that did the most useful work: it found #3308,
recorded `not_met` on it, and was the only dispatch the judge agreed with
(`lowered: false`, `disagreed: false`). That is worth stating next to the number
rather than under it. The expensive dispatch was the one that earned its keep,
and the two cheaper ones were the two that were wrong.

**Three costs have no line in the plan and no event that classifies them.**
`planned_cost_usd` prices work units:

1. **The three re-closes.** A `not_met` verdict — whether the judge lowered it
   or the close recorded it — buys a whole further dispatch of a unit already
   priced once. There is no budget line and no failure class (see § "Failure-class
   breakdown"); the only place they appear is the `G2-CLOSE` rows above. The two
   recorded re-closes plus their judges are **$22.93 of the $31.47** the close
   has cost so far, and this fourth dispatch is a third re-close still unpriced.
2. **Two fix sessions between close dispatches.** #3305's, on this branch
   between dispatches 1 and 2, and #3308's (`fix(loop): stop part 3 claiming
   exhaustion a unit never reached`) between dispatches 3 and 4. Neither emitted
   an event into this feature's `events.jsonl` — correctly, neither was a work
   unit — so their spend is unrecoverable here in exactly the way gate 1's
   discarded run is. Both are nonetheless costs this feature caused, and the
   pattern is now a pattern rather than an incident: a judge-or-close finding
   that is a real code defect buys an unbudgeted fix session **and** a re-close.
3. **The gate-2 re-entry itself.** Reopening the gate for T10 re-ran the
   arm-predicate sweep and a broad run before T10 was dispatched at all.

**Where the committed ledger disagrees with the event log.** `WU-90-gate-2-close.md`'s
frontmatter reads `attempts: 1` and `cost_usd: 14.982412`. The event log carries
three recorded attempts for that unit summing $30.507706, plus $0.959305 of judge
spend — and this is its fourth dispatch. Reopening the gate and re-arming the
close each reset the unit's frontmatter, so the committed record reports as one
attempt what the log records as three. **Every per-unit figure in the table above
is therefore read from `events.jsonl`, which is append-only and survived both
resets.** For T01–T09 the two sources agree exactly; for `G2-CLOSE` they do not,
and the event log is right. Anyone reconciling this feature from WU frontmatter
alone will under-count its close by **$15.53 and two of its three recorded
dispatches** — and the gap grows by one dispatch every time the close is
re-armed, which is the shape of the problem rather than a one-off.

**So the honest feature-level figure is not +33.4% either — that is still the
floor.** Recorded $58.02, plus $16–18 discarded in gate 1, plus two unpriced fix
sessions on this branch (#3305's, and #3308's `fix(loop): stop part 3 claiming
exhaustion a unit never reached`), plus this fourth close dispatch (unpriced; the
three recorded ones were $8.24, $7.28 and $14.98) puts the true cost at roughly
**$85–100 against a $43.50 plan — 95% to 130% over**. Three of those five terms
are estimates rather than records, which is why it is a range; the sign is not
uncertain, and the range has roughly doubled since the previous dispatch reported
$64–75.

**The plan priced the planned work well.** Every substantive unit but one landed
under estimate, and the one that did not missed by 15%. The overrun is entirely
in what no plan had a line for — a reverted gate, three `not_met` verdicts, two
bug-fix sessions between close attempts, and a gate reopened on a review finding
that had been raised, correctly, at arming. A `planned_cost_usd` that prices work
units cannot price any of that, and this feature is the case that shows how far
apart the two numbers can get: the ceremony around the work cost roughly twice
the work.

**Restarts and re-arms.** Eleven `driver_staleness_detected` events, all
non-halting — one after each unit that edited `specfuse/loop/loop.py`, plus one
at the gate-2 boundary and one after #3308's fix landed. Zero `re_arm_dispatched`
events. Zero `human_escalation` events. Zero `replan` events. Three `judged`
events: two `lowered: true, disagreed: true` and one `lowered: false,
disagreed: false`.

## What the loop did NOT verify

Gate 1 deferred five items; gate 2's close dispatches added five more. None is
silently dropped below: each is carried forward with what changed, or discharged
with the evidence. **Item 9 is discharged at this dispatch and item 11 is new.**
Seven of the eleven remain open, and every one of the seven is open for the same
structural reason — the mechanism only fires on a failure this feature never
produced.

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
8. **Part 3 of the brief.** **Discharged, not deferred.** At attempt 1 no
   acceptance criterion in either gate asserted on part 3 and it carried a
   tracer-bullet stub; the judge filed it as #3305, it is fixed in tree, and it
   now has the oracle it lacked —
   `tests.test_spinout_brief_replan_option.SpinoutBriefEveryPartHasContent`
   asserts that every part says at least 40 characters, that no part leaks an
   implementing work-unit ID, and that part 3 states the decision, the reason no
   automatic move remains, and the consequence of not deciding. Verified in this
   session by that module's green run (Ran 8) and by `grep -n "Full decision
   text is" specfuse/loop/loop.py` exiting 1. Where it is checked from here:
   that test class, on every run of the suite. See § "The defect this close
   found, and what happened to it".

T10's widening adds three more, two of them at this dispatch:

9. **Part 3 of the brief at the nine escalation sites T10 widened it to.**
   **Discharged, not deferred.** Dispatch 3 found that part 3 asserted "every
   attempt its budget allowed has been dispatched and has failed"
   unconditionally, while part 4 four lines below gated the same claim on
   `reason in ("spinning_detected", "all_attempts_zero_token")`; at the other
   nine sites the assertion was false and contradicted part 1 of the same brief.
   The judge agreed, it was filed as **#3308**, and it is fixed in tree: part 3
   now carries the same two-reason conditional and renders "it stopped short of
   its attempt budget (3) for a reason no further attempt would change
   (`<reason>`)" everywhere else — and #3308's fix caught part 2, which carried
   the same claim one part earlier, at the same time. Verified in this session by
   a real `loop.run()` driven to `agent_reported_blocked` (part 1 "dispatched 1
   time(s)", part 3 without the exhaustion clause) and by a second driven to
   exhaustion (the true claim still renders). Where it is checked from here:
   `tests.test_spinout_brief_replan_option.BriefPartThreeAgreesWithPartOne`, two
   tests, on every run of the suite. See § "The defect T10's widening shipped,
   and how it was discharged".

10. **`GATE-02.md`'s declared `feature_oracle` no longer asks the gate's
    composite question.** It drives a run to attempt exhaustion — the one
    escalation site T10 did *not* widen — and was written when the gate ended at
    T09. It re-ran green in this session and is honestly recorded as PASS, but a
    green there now says nothing about nine of the gate's ten render sites.
    `tests.test_brief_covers_every_unit_escalation` is the oracle that does, and
    it is green too; it is simply not the declared one. Not repaired here:
    editing the gate's declared oracle inside its own terminal close changes the
    question after the answer. Where it is actually checked: T10's module, on
    every run of the suite.

11. **#3308's regression barrier is one layer shallower than its own re-run
    condition asked for.** `FOLLOW-UPS.md` specified "a test that drives a real
    `loop.run()` to a non-exhaustion escalation and asserts that part 3's
    statement about the attempt record agrees with part 1's". The committed test
    (`BriefPartThreeAgreesWithPartOne`) calls
    `format_spinout_escalation_brief` directly with a hand-built attempts list;
    the one committed test that *does* drive a real `loop.run()` to a
    non-exhaustion escalation (`AgentReportedBlockedCarriesBriefEndToEnd`)
    asserts only `validate_escalation_body` and the correlation marker. Both are
    green. What is not committed is the composition: a real run whose *rendered*
    part 3 is asserted against its own part 1. This session made that observation
    (see item 9), and a session's observation is not a barrier. The practical
    exposure is narrow — the attempts list part 1 renders from is the same object
    part 3's conditional reads — but "narrow" is the argument the previous two
    defects in this brief were also covered by. Where it is actually checked:
    the function-level test, plus whoever next reads a rendered brief.

Nothing else was deferred. Everything in `GATE-02.md`'s definition of done other
than the human review step has an executed command behind it in § Measurements.
Items 1–7 are honest deferrals — a claim about a tree that no longer exists, a
mechanism that only fires on a failure this feature never produced, a prose
judgment with no oracle — and items 8 and 9 are the two that were defects and are
now discharged with their own regression tests. Item 11 is the residue of item
9's discharge, and item 10 is a stale declaration in `GATE-02.md`'s frontmatter
rather than a defect in what shipped.

## Lessons

Three entries were promoted to `.specfuse/LEARNINGS.md` at close attempt 1, all
tagged `[FEAT-2026-0104/G2]`: a self-hosting gate cannot exercise its own code
because the driver pin predates the gate's commits; a feature whose mechanism
fires only on failure must buy its evidence with a committed probe rather than
hope it trips itself; and a tracer bullet must stub only the parts the plan
licensed, because later units are scoped to that list. The defect in § "The
defect this close found, and what happened to it" is the concrete instance of
the third.

A fourth is promoted by this attempt, tagged `[FEAT-2026-0104/G2-CLOSE]`, and it
is the lesson of the re-close itself: a close that finds an operator-facing
defect in its own gate's deliverable owes the verdict, not just a note. Attempt 1
found the part 3 stub, wrote it up accurately, declined to fix it in the close —
right, on scope — and then recorded `met` because no acceptance criterion
asserted on part 3. The judge lowered it and the gate cost a second close. Where
to fix and whether the gate is done are separate questions, and answering the
first does not discharge the second.

**A fifth is promoted by this dispatch**, tagged `[FEAT-2026-0104/T10]`, and it
is the generalizable half of § "The defect T10's widening shipped, and how it was discharged":
widening where a message is rendered is not the same change as widening what it
may claim, and a unit that moves a render site inherits every condition the old
site guaranteed. T10 moved the brief from one escalation site to ten and left
part 3's "budget is exhausted" clause unconditional, while part 4 — four lines
below, written by an earlier unit — had already been gated on exactly the two
reasons where that is true. No oracle caught it, because every oracle the gate
ships checks the brief's shape.

This is the third time in one feature that the same seam produced a defect: T06
stubbed a part the plan had not licensed it to stub (#3305), T07's criteria
scoped to parts 5 and 6 so nothing owned part 3, and T10 widened a render site
without widening its text's conditionals. The common cause is that the brief has
six parts and the gate's criteria are written per *unit*, so a part nobody's
criteria name ships whatever the last unit to touch it left there. The rule that
generalizes: when a deliverable has enumerable parts, one criterion must assert
on the enumeration, not one criterion per part the plan happened to think of.

**A sixth is promoted by this dispatch**, tagged `[FEAT-2026-0104/G2-CLOSE]`,
and it comes from watching #3308 get discharged: a follow-up's **re-run
condition is a specification for the discharging change's oracle**, and a fix
that clears the defect without meeting that specification leaves a gap nobody
re-reads. #3308's re-run condition asked for a test driving a real `loop.run()`
to a non-exhaustion escalation and asserting part 3 against part 1. The fix
shipped two function-level tests that assert exactly the right property one layer
down, and the end-to-end half was checked by this close session instead — which
discharges the defect and commits no barrier. Nothing in the loop compares a
discharging change against the re-run condition that asked for it: the driver
files the issue and writes the number back, and after that the two documents
never meet. The drafting move: write the re-run condition as the acceptance
criterion of the unit that will discharge it, and have the re-closing session
diff what shipped against it rather than against the defect.

Not promoted: gate 2's cost variance (the same retry-pad pattern gate 1 already
recorded and `[FEAT-2026-0040/G3-CLOSE]` already generalizes — T10's +15.1% is
its confirming case, which strengthens the existing entry rather than warranting
a new one) and the sandbox session-env artifact (already in gate 1's
retrospective, and a property of where the suite runs rather than a rule for
drafting).

## Verdict

Advisory only — on a terminal gate the judge session writes the verdict the
terminal flips read, from the evidence in § Measurements and the gate diff, and
this section is deliberately withheld from it.

`verdict: met`, on this reading. `GATE-02.md`'s definition of done is that "after
a work unit escalates with `blocked_human`, the operator-facing brief presents
re-planning the remaining gate as its default option, inside the six-part framing
`.specfuse/rules/operator-escalation.md` requires." Every clause of that has an
executed command behind it in § Measurements, and the two findings that stood
against it on earlier dispatches are discharged in tree and re-verified here:

- **The brief renders at every per-unit `blocked_human` escalation**, carried on
  the `human_escalation` event's `message`. Driven end to end twice in this
  session — once to attempt exhaustion, once to `agent_reported_blocked` — with
  `validate_escalation_body` returning `[]` on both and `message in stdout`
  holding on both.
- **Its six parts each state their own content, and none of them now states
  something the attempt record refutes.** That is the clause dispatch 3 recorded
  `not_met` on and the judge agreed with. #3308's fix gates part 3's exhaustion
  claim on the two reasons where it is true and renders "stopped short of its
  attempt budget" elsewhere; it caught part 2's copy of the same claim as well.
  Verified by the two runs above, not by reading the diff, and now held by
  `BriefPartThreeAgreesWithPartOne`.
- **The re-plan option is the first option and the recommendation where the
  reason is one re-planning can help**, on four of the eleven unit-level reasons,
  with the excluded seven each stating why — `test_spinout_brief_replan_option`,
  8 tests, exit 0.
- **Every implementation unit is `done`**, the declared `feature_oracle` and gate
  1's both re-ran `OK`, the driver's own broad run at this dispatch is `Ran 3935
  tests, OK (skipped=3)` with `ok: true, failing: []`, coverage 93%,
  `event_type_gate.py` clean over 2116 events in 74 files, `leak_scan.py` clean,
  and the narrow tier for this unit (`lint_plan.py`) exits 0.

**What that verdict does not claim.** Three things, stated here rather than left
for a reader to find:

1. **It is a verdict on the gate, not on the feature's usefulness.** Zero
   re-plans have fired and zero briefs have rendered outside a stubbed harness.
   § "What this feature proved, and what it did not" is the honest reading, and
   nothing in four close dispatches has moved it.
2. **Seven of the eleven items in § "What the loop did NOT verify" are open**,
   including item 11, which is the residue of this dispatch's own discharge: the
   committed regression barrier for #3308 is one layer shallower than the
   follow-up asked for. That is a real gap and it is named, not netted out.
   It is not an unmet acceptance criterion — no criterion in this gate asserts on
   where a regression test sits — which is why it is recorded here rather than
   argued into the verdict.
3. **`GATE-02.md`'s declared `feature_oracle` no longer asks the gate's
   composite question** (item 10). It is green and honestly recorded as PASS; the
   oracle that covers the other nine render sites is
   `tests.test_brief_covers_every_unit_escalation`, also green, and simply not
   the declared one. Repairing
   a gate's declared oracle inside its own terminal close would change the
   question after the answer, so it is recorded instead.

**Why this is not the same call dispatch 1 was lowered on.** Dispatches 1 and 2
recorded `met` while an operator-facing defect sat unfixed in the gate's own
deliverable, and the judge was right both times: *where* to fix a defect and
*whether the gate is done* are separate questions, and answering the first does
not discharge the second — `[FEAT-2026-0104/G2-CLOSE]`'s lesson. Dispatch 3
applied that lesson and recorded `not_met` on a defect of the same class. The
difference here is not a change of reading: **the defect is fixed**, in tree,
before this dispatch was dispatched, and this session re-derived its absence from
a real run rather than from the commit that claims it. There is no operator-facing
untruth in the brief that this close found and declined to act on. If there were,
the lesson says what to record, and it would be recorded.

### What this feature proved, and what it did not

Proven **runnable**, not **useful** — the same sentence gate 1's retrospective
asked this close to carry forward, and four dispatches of evidence have not moved
it:

- **Zero re-plans fired**, across both gates and across every feature in this
  repository. What is new is that the zero is no longer vacuous: T10 failed once,
  which is one failure short of the trigger point, and the failure was two ruff
  diagnostics — a class for which re-planning would have been the wrong remedy.
  That is the first real data the feature has about its own premise, and it
  points at a question the feature never asked: which failure classes deserve a
  re-plan rather than a retry.
- **Zero briefs rendered in the field.** The pin table shows
  `format_spinout_escalation_brief` absent from every driver build that
  dispatched any part of this feature, and `escalate_unit` absent even from the
  build running this close. Every observation of the brief in this document —
  including both verbatim pastes — comes from a `loop.run()` with the model
  boundary stubbed.
- **The motivating metric is unmoved.** Human waits per feature on drivers
  `>=0.15.0` reads 1.92 against a 2.09 baseline recorded in `PLAN.md`, and
  § "The move from 2.09 to 1.92 is arithmetic, not evidence" shows the numerator
  did not change: 2.09 × 11 ≈ 23 escalations, and adding one feature with zero
  gives 23 / 12 = 1.92. One feature is not a trend, and this is a worse sample
  than most — a run with almost no failures tells you nothing about a mechanism
  that only fires on repeated failure. The metric stays untested until a real
  unit spins out on a driver built from this branch.

Seven of the eleven items in § "What the loop did NOT verify" are open. The two
that are closed were both defects rather than unverifiable claims, both lived in
the same six-part brief, and both took a re-close to discharge: #3305's
placeholder in part 3, and #3308's false exhaustion claim in part 3 and part 2.
Neither was caught by an oracle. The feature's clearest finding about itself is
not about re-planning at all — it is that a six-part operator-facing deliverable
built by units whose criteria are written one part at a time will ship whatever
the last unit to touch a part left there, and that the only thing which caught it
three times running was a session reading the rendered output.

