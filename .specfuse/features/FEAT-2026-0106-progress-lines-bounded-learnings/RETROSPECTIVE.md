# FEAT-2026-0106 — progress lines and conditional reflection

One gate, four implementation units, one terminal close. T01 made the driver
write a `PROGRESS.md` line per dispatched unit from the RESULT block it already
parses. T02 added the optional `forward_note` RESULT field. T03 made the two
reflective closing sections conditional on `gate_eval`'s off-plan signal. T04
documented the new shape in `docs/methodology.md` §6 and `close-discipline.md`
§1a. Every unit passed; T01 needed two attempts.

**The one fact to read first.** None of the three mechanisms ran on this
feature's own gate. The driver pinned its build at tree `c76216a` before T01
started, and every later dispatch ran on that pin, this close included. The
three `driver_staleness_detected` events all read `halted: false`. The pinned
build's `loop.py` has no `append_progress_entry` and no `reflection_required`,
so no `PROGRESS.md` was written, and the post-squash guard that will check this
close is the old one, where `## Cost analysis` is always required on `met`.
Everything below that says a mechanism works rests on tests that drive the real
`loop.run()`, not on this gate's own run.

## Measurements

All commands were run fresh in this close session, from the working tree at
gate 1's head, under `.venv`. Test modules ran unsandboxed, because the sandbox
falsely fails this repo's git tests. Per the dispatch contract, this session did
not run the full suite, coverage, or any `tier: broad` gate. Those figures come
from the driver's once-per-gate broad run, which is cited by log and not re-run.

### feature_oracle: PASS

| Oracle | Command | Result | Exit |
|---|---|---|---|
| Gate `feature_oracle` | `python3 -m unittest tests.test_progress_lines_end_to_end -v -b` | `Ran 1 test`, `OK` | 0 |
| T01–T03 modules plus closing lint | `python3 -m unittest tests.test_progress_lines_end_to_end tests.test_progress_forward_note tests.test_conditional_reflection tests.test_lint_closing -b` | `Ran 29 tests`, `OK` | 0 |
| Symbol check (§9) | `python3 -c "from specfuse.loop.loop import append_progress_entry, reflection_required, record_progress_entry"` | imports | 0 |
| Narrow tier for `close` (`plannext` set: `plan-lint`) | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | `structurally valid` | 0 |
| Closing lint (checkout) | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | `CLOSING-READY` (close-h, close-i are post-pass notes) | 0 |
| Closing lint (CLI form) | `specfuse lint --closing <feature_dir>` | `CLOSING-READY`, run by the **installed** pipx build, which warns that it is not measuring the checkout, so the row above is the authoritative one | 0 |

**Driver broad run, cited and not re-run.** `broad_run_result` at
`2026-09-14T01:44:51Z` gave `ok: true, failing: []`, on the tree recorded in
`GATE-01.md`'s `broad_run:` block. From `work/gate-logs/`:
`tests-20260914T014424543895Z.log` shows `Ran 3960 tests in 173.560s`,
`OK (skipped=3)`, and `coverage-20260914T014426585289Z.log` shows `TOTAL … 93%`
against `--fail-under=90`. `security`, `leak-scan` and all six bats gates are
logged in the same run.

### Off-plan signal for gate 1, computed here

`gate_eval.evaluate_off_plan_signal(feature_dir, 1)`, verbatim:

```
reasons=['per_wu_cost_overrun: T01 actual=$9.13 planned=$3.50 ratio=2.61x',
         'per_wu_hard_overrun: T01 actual=$9.13 planned=$3.50 ratio=2.61x',
         'per_wu_cost_overrun: T03 actual=$6.13 planned=$3.50 ratio=1.75x']
metrics: blocked_human_events=[], replan_events=[], gate_total_cost=17.304441
```

`loop.reflection_required(feature_dir, 1)` returns `True`.
`evaluate_auto_close` gives the same three reasons.

### PROGRESS.md in this feature's folder

The file is absent. `find . -name PROGRESS.md` over the repo returns nothing.
Of the 40 pinned builds on this machine, `grep` finds `append_progress_entry` in
`c76216a` zero times. It appears in the later pins (`57c622d`, `e9e25b2`,
`bc533d9`, `2310015`) that the staleness events name as `next_pin_tree`, but no
dispatch ran on any of those.

### Agent-supplied RESULT fields: the emission rate, measured

`events.jsonl` cannot answer this question. `attempt_outcome` does not carry the
agent's `summary`, and neither does any other event. So the figure below comes
from the final RESULT block in each dispatched session's local Claude Code
transcript. Those transcripts are uncommitted, on the operator's machine, and
are the only place the agent's own text survived.

| Attempt | `summary` non-empty | `forward_note` present | Field existed at dispatch? |
|---|---|---|---|
| T01 attempt 1 (failed, `lint`/`E741`) | yes | no | no |
| T01 attempt 2 | yes, multi-line | no | no |
| T02 | yes | yes | T02 created it |
| T03 | yes | yes | yes |
| T04 | yes | yes | yes |

- **`summary`: 5 of 5 dispatched attempts (100%).**
- **`forward_note`: 3 of 3 attempts dispatched after the field existed.** Leave
  out T02, which wrote the field and can't be a fair test of whether agents
  pick it up. That leaves **2 of 2 independent attempts** (T03, T04).

**What T01 actually recorded is different, and wrong.** T01's criterion asked
the unit to report the rate "from this gate's own run". Attempt 1 said `1/1`,
meaning its own RESULT. Attempt 2 said `0/1 carried a non-empty agent-supplied
summary`, having read attempt 1's `attempt_outcome` event, where `summary` is
absent. But attempt 1's transcript shows it did emit a non-empty `summary`.
T01 measured the event log and reported the result as agent behaviour. The
plan's 8% corpus figure came from the same surface and has the same flaw, as
`PLAN.md` itself notes: every one of those 8% is set by the driver.

**Were the forward notes worth anything? Checked by running them, not by reading
them.**

- T03's note says any future off-plan check must call
  `evaluate_off_plan_signal`, not `evaluate_auto_close`, or it fails closed on
  every load-bearing gate. This holds for this gate: its close carries
  `auto_close_disabled: true`, and `evaluate_off_plan_signal` returned real
  evidence above.
- T04's note says `scripts/sync-scaffold.sh` has no `docs/` stage, although
  `tests/test_scaffold_data_in_sync.py`'s `DOCS_TRACKED` checks
  `specfuse/loop/data/docs/` against `docs/`. `grep -n docs
  scripts/sync-scaffold.sh` matches only two `echo` strings, so the gap is real.
  No surface that the next unit or the operator reads carries this note.
- T02's note says to run `sync-scaffold.sh` after any rules edit. That is
  accurate, and T04 then ran into the `docs/` half of the same trap.

## Was reflection suppressed for this gate?

**No. Reflection was not suppressed.** By its own verdict the gate went
off-plan: `per_wu_cost_overrun: T01 actual=$9.13 planned=$3.50 ratio=2.61x`,
`per_wu_hard_overrun` on the same unit, and `per_wu_cost_overrun: T03
actual=$6.13 planned=$3.50 ratio=1.75x`. `reflection_required` returns `True`,
so `## Cost analysis` and `### Failure-class breakdown` are written in full
below.

`GATE-01.md` framed this close as "the sharpest possible test of whether
`PROGRESS.md` is a good enough substitute". That test did not happen, and for
two separate reasons, either of which would have been enough on its own:

1. **The gate was off-plan**, so the rule never offered to skip anything.
2. **Even an on-plan gate could not have tested it on this run.** No
   `PROGRESS.md` exists to substitute for anything, and the pinned post-squash
   guard enforces `## Cost analysis` on `met` whatever the off-plan signal says.
   `specfuse lint --closing` imports from the working tree and would have
   predicted a skip, so on an on-plan gate the lint and the guard would have
   disagreed. They agree here only because the gate went off-plan.

**The nearest first-hand evidence available.** This session did its job
without `PROGRESS.md`, but not without leaving the committed record: the RESULT
text it needed exists only in local transcripts. Counterfactually, a
`PROGRESS.md` from a current driver would have held a summary line for each
unit's terminal outcome (T01's failed and retried attempt 1 gets none) plus the
three notes. That would have answered the emission-rate criterion directly, and
T02's escalation trigger could have been evaluated at all. It would not have
been enough for the cost reconciliation, which needs `events.jsonl`, or for the
off-plan verdict, which needs `gate_eval`. **So `PROGRESS.md` would have
replaced the transcript dig and nothing else. That is exactly what it claims to
do, and less than "a substitute for reflection" suggests.**

## Consumer-visible contract changes

Two additions and one behaviour change. Nothing was removed or renamed, and no
existing configuration file needs an edit.

1. **added: an optional `forward_note` field in the RESULT block**
   (`.specfuse/rules/result-contract.md`, T02). No guard requires it. When it is
   absent, the `PROGRESS.md` entry is byte-identical to one written without it.
2. **added: the driver writes `PROGRESS.md` into every feature folder** (T01,
   `append_progress_entry` / `record_progress_entry`). It writes one line for
   each dispatched unit's terminal outcome: passed, agent-blocked, or any of the
   blocked-human escalation paths. The line is the agent's `summary`, or
   `attempt N outcome=<outcome>` when the RESULT block is missing or malformed.
   The file rides the unit's own squash commit and is excluded from
   `git_diff_names` and from the deliverable filter, so it can never count as a
   unit's deliverable. Consumer projects will see a new committed file in each
   feature folder.
3. **changed: `close-e` (`## Cost analysis`), `close-f` and
   `close-intermediate-d` (`### Failure-class breakdown`) are required only when
   the gate went off-plan** (T03). Off-plan means a blocked-human event, a
   `replan` event, or a cost overrun, per the new
   `gate_eval.evaluate_off_plan_signal`. Their existing `verdict==met` /
   failures-present conditions still apply as well. `specfuse lint --closing`
   mirrors the check. `## Measurements`, the `feature_oracle` verdict line and
   every other closing requirement stay unconditional. An on-plan `met` close
   that previously failed for a missing `## Cost analysis` now passes.

All three are appended to `CHANGELOG.md`'s `Unreleased` section with this
feature's ID.

## Cost analysis

**Budget of record:** `PLAN.md` `planned_cost_usd: 16.50`, which matches
`PLAN.baseline.json`: T01 $3.50 + T02 $2.50 + T03 $3.50 + T04 $2.00 +
G1-CLOSE $5.00. The actuals below come from `events.jsonl`'s `task_completed`
`cost_usd`, checked against the per-attempt `attempt_outcome` payloads and
against each WU's committed frontmatter.

| WU | Planned | Actual (events) | Frontmatter | Delta | Attempts | Wall |
|---|---|---|---|---|---|---|
| T01 progress lines tracer | $3.50 | $9.130225 | $9.130225 | +$5.630 (+160.9%) | 2 | 3743.9s |
| T02 `forward_note` field | $2.50 | $0.833840 | $0.83384 | −$1.666 (−66.6%) | 1 | 595.4s |
| T03 conditional reflection | $3.50 | $6.133309 | $6.133309 | +$2.633 (+75.2%) | 1 | 1275.1s |
| T04 document the shape | $2.00 | $1.207067 | $1.207067 | −$0.793 (−39.6%) | 1 | 1071.0s |
| **Implementation** | **$11.50** | **$17.304441** | agrees | **+$5.804 (+50.5%)** | 5 | 111.4 min |
| G1-CLOSE (this unit) | $5.00 | not yet in `events.jsonl` | — | — | — | — |

**Frontmatter and events agree** on all four units to the six decimals written,
and T01's two attempts sum exactly ($4.1717394 + $4.9584854 = $9.1302248). The
escalation trigger for a ledger disagreement does not fire. One gap is noted,
not a disagreement: T01's frontmatter lacks the `model` / `effort` / `gate_set`
/ `driver_version` / `started_at` keys that T02–T04 carry. Its cost, token and
duration fields are present and correct.

**Against the whole $16.50 plan, implementation alone came in $0.80 over
(104.9%) before the close had spent anything.** If the close lands on its $5.00
estimate, the feature ends near $22.30, about 35% over plan. The close's real
figure will be in `events.jsonl` after this dispatch, and the judge's spend will
be folded in by `record_judge_cost_fold`.

**Why T01 cost 2.61×.** There are three causes, each measured from
`events.jsonl` or the session transcripts:

- **$4.17 (46% of T01, 24% of all implementation spend) went to a failed
  attempt.** Attempt 1 produced working code, and its own tests were green. The
  `lint` gate then refused it on `E741`, the ambiguous single-letter variable
  name rule. The driver reset the tree and attempt 2 started again from the
  base. The correction was one character; the cost was a whole attempt.
- **The unit's own verification clause told it to run the full suite**
  ("the narrow tier is NOT sufficient … run the full suite"). The transcripts
  show 5 full `discover` runs in attempt 1 and 6 in attempt 2, at roughly 174 s
  each by the broad-run log. That is about 30 minutes of wall clock inside the
  sessions, spent paying for context replay.
- **Attempt 2 built the write twice.** Its RESULT records a first design with a
  separate bookkeeping commit, which broke `test_pin_honesty_and_integrity`'s
  tree-hash invariant. It was reverted in favour of writing before the squash,
  and a regression in `detect_deterministic_refusal_repeat`'s untracked-files
  signal was then fixed along the way. Attempt 2 read 16.95 M cache tokens
  against attempt 1's 13.51 M.

The plan priced T01 as "a persist plus a write, not a new mechanism". The write
itself was that small, but it had to fit through the attempt loop's commit and
pin seams, and the plan priced none of that.

**Why T03 cost 1.75×.** T03 touched four driver modules (`loop.py`,
`gate_eval.py`, `lint_closing.py`, `closing_requirements.py`) plus two test
modules. It carried a 20-row flag-scope table and needed a new predicate entry
point, `evaluate_off_plan_signal`, because load-bearing closes short-circuit
`evaluate_auto_close`. Its transcript shows 125 tool calls and 22 edits, and it
read 20.96 M cache tokens in one attempt, more than either T01 attempt. It ran
the full suite only once. The overrun is breadth, not rework.

**Why T02 and T04 came in under.** T02 was a single field and one renderer
branch: 34 tool calls, 2.24 M cache-read tokens. T04 was prose across two
documents, yet it ran the full suite 5 times against a clause that asked for the
narrow tier plus `leak_scan`. Even so it finished $0.79 under, which suggests
the $2.00 estimate for a docs unit had slack.

**Restarts: zero halts, three staleness events.** In the pinned regime the
driver does not stop when a unit edits it. That is why the gate ran straight
through in 117.9 minutes from pin to broad run. It is also why none of the
gate's code ran on the gate itself (see the top of this file).

**Ceremony share, as planned.** The close is $5.00 of $16.50, or 30% of plan,
against the review's 12% target. The realised share will be lower if the close
lands near plan, only because implementation overran.

### Failure-class breakdown

| Gate 1 | Attempts | Passed | Failed | Classes |
|---|---|---|---|---|
| T01 | 2 | 1 | 1 | `lint` / `E741` |
| T02–T04 | 3 | 3 | 0 | — |

The one non-passing attempt is T01's attempt 1: `failure_class: "lint"`,
`failure_signature: "E741"`, `agent_status: "complete"`. The session believed it
was done, and its own narrow tests agreed. `baseline_attribution` fired once
after that failure (`failing: []`, `attributed_to: FEAT-2026-0106/T01`), which
correctly classified it as a genuine failure rather than a pre-existing one. The
failure excerpt ends in `NO VERDICT FOUND` twice, for gates whose output tail
did not carry the lint verdict, so the excerpt names the class correctly but
points the reader at the wrong gates' logs.

**The driver's own breakdown for this gate reads "no non-passing attempts in
scope", and that is a defect, not a finding about this gate.**
`summarize_attempt_failure_classes(feature_dir, 1, …)` filters by
`_gate_number_from_wu_id(cid) == 1`. That parser only matches `G<n>-` segments,
so `_gate_number_from_wu_id("FEAT-2026-0106/T01")` returns `None` (checked here;
`FEAT-2026-0104/T10` gives the same). Every implementation unit with a `TNN` id
is therefore invisible to the gate-scoped breakdown. So is `close-f`'s and
`close-intermediate-d`'s failures-present condition, which `lint_closing.py`
computes through the same helper, and so is the dispatch-time skeleton stub that
would have scaffolded this section. The defect predates this feature, but T03
chained the new off-plan condition onto that failures-present check, so it
matters more now: an off-plan gate whose only failures belong to `TNN` units
will never be asked for this section. It is recorded here as a follow-up
candidate, not fixed, because it is out of this close's scope.

## What the loop did NOT verify

Each entry gives the criterion, why it went unverified in this loop, and where
it actually gets checked.

1. **A real driver run writes `PROGRESS.md`, one entry per dispatched unit**
   (gate definition of done, T01). *Reason:* every dispatch in this gate ran on
   pinned build `c76216a`, which predates T01, so no production run has written
   the file. *Checked by:* `tests.test_progress_lines_end_to_end`, which drives
   the real `loop.run()` with dispatch and verify patched and reads the file the
   run wrote, and `tests.test_progress_forward_note` (6 tests). Both were
   re-run here and are green. *Real evidence:* the first feature dispatched on a
   driver pinned at or after this branch's merge.
2. **An on-plan close skips reflective prose, and the judge still gets its
   measurements** (T03). *Reason:* this gate went off-plan, and the post-squash
   guard checking this close is the pinned pre-T03 build anyway.
   *Checked by:* `tests.test_conditional_reflection` (14 tests, including the
   `judge.build_judge_bundle` assertion) and `tests.test_lint_closing`, both
   re-run here. *Real evidence:* the first on-plan `met` close dispatched on a
   post-merge driver.
3. **The optional field is never required, asserted by a full gate whose units
   emit no such field** (T02). *Reason:* this gate's T01 attempts emitted no
   `forward_note` and passed, but on a driver that doesn't know the field, so
   that proves nothing. *Checked by:* `tests.test_progress_forward_note`.
4. **"Fails on HEAD before this unit's edits"** (T01, T02, T03). *Reason:* the
   red side is self-reported by the session that went on to make it green.
   *Mitigation:* each unit's `produces:` module is a new file (`attempt_outcome`
   `files_touched`), so the pre-edit red is structurally certain.
   *Checked by:* nothing automated.
5. **"How often a real agent emits `summary:` is recorded"** (T01). *Reason:*
   T01 recorded a figure, but from `events.jsonl`, which never carries the
   agent's `summary` (see § Measurements). The true figure, 5/5, was measured in
   this session from local transcripts that are not committed. *Checked by:*
   nothing reproducible from the repository. From the next post-merge feature
   on, `PROGRESS.md` makes it reproducible, because non-fallback entries are
   agent text.
6. **T02's escalation trigger ("stop if T01's recorded rate says agents rarely
   emit RESULT fields")**. *Reason:* the trigger could not be evaluated. T01's
   figure lived only in T01's RESULT block, which the pinned driver did not
   persist, so T02 had no surface to read it from. Read literally, T01's
   recorded `0/1` would have fired the trigger. *Checked by:* nothing; recorded
   here as evidence for the lesson below.

The full suite that T01, T02 and T03 were told to run is **verified, not
deferred**: the transcripts show 6, 3 and 1 full-suite runs, and the driver's
broad run is green at 3960 tests. T04's `leak_scan.py --all` is verified by the
broad run's `leak-scan` gate.

## Lessons

One entry is promoted to `.specfuse/LEARNINGS.md`, tagged
`[FEAT-2026-0106/G1-CLOSE]`. It says: measure an agent-supplied field from what
the agent returned, never from the driver's event log; and when a criterion
asks a unit to record a figure that a later unit's trigger reads, the criterion
must name the durable surface the figure goes to.

The self-hosting-pin observation (none of this feature's code ran on its own
gate) is **not** promoted again. `[FEAT-2026-0104/G2]` already carries it. Its
recurrence here, where the close body promised to be "the first close to run
under T03's rule", shows that lesson has not yet changed how close bodies are
drafted. That is worth `/learnings-curate`'s attention, not a duplicate entry.

## Verdict

This section is advisory only. The judge writes the verdict the terminal flips
read, from § Measurements and the gate diff, and this section is withheld from
it.

`verdict: met` on this reading, with the scope stated. `GATE-01.md`'s definition
of done is behavioural: after a gate runs, `PROGRESS.md` carries one entry per
dispatched unit, and an on-plan gate closes without reflective prose while an
off-plan gate gets it in full. Both halves are proven by tests that drive the
real `loop.run()` and were re-run green in this session, and the gate's
`feature_oracle` passes. Neither half was observed on this gate's own run, for
the pin reason above; items 1 and 2 of the deferred list carry that forward
rather than presenting it as evidence. All four implementation units are `done`,
this retrospective exists, and a lesson is promoted.
