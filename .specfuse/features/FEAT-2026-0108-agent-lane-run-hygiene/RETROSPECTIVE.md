# Retrospective — FEAT-2026-0108, agent lane run hygiene

## Gate 1

Gate 1 is the only gate. Six substantive units (T01–T06) and this close. All six
are `done`. Five of the six behaviours in `GATE-01.md`'s definition of done were
demonstrated on fixtures with an injected runner in this session; **the sixth
was demonstrated to fail.** `GATE-01.md` says so itself: *"If all six units are
`done` and any behaviour above cannot be demonstrated, this gate is not done."*
**Verdict: `not_met`.**

The failure is narrow and its cause is known: `run_bug_lane` never puts a PR
number on a stopped outcome, so the escalation payload T06 shipped — which
renders `PR #<n>` correctly when handed one — can never receive one from a real
run. `FOLLOW-UPS.md` carries the one entry, with the evidence and the re-run
condition.

Everything else landed. Per-item worktrees, the wall-clock timeout, the
foreground-gate rule, `ci_pending`, the carried PR number and real token
accounting all work end to end on fixtures.

## Measurements

Every "after" figure is a command run in this session, unsandboxed, against the
tree the driver will squash. Every "before" figure is `PLAN.md` § Notes'
recorded baseline, taken before T01 ran — this session may not run `git`, so the
pre-feature tree is not readable here and the plan's recorded baseline is the
only honest source for it.

| Measurement | Command run in this session | Before | After |
|---|---|---|---|
| `spend=` occurrences in `specfuse/` | `grep -rn "spend=" specfuse/ \| wc -l` | 0 | **16** |
| … of those, in `specfuse/agent/providers/` | `grep -rn --include="*.py" "spend=" specfuse/agent/providers/ \| wc -l` | 0 | **15** — every provider that dispatches a session sets it |
| `--output-format` in agent invocations | `grep -rn "output-format" specfuse/agent/*.py specfuse/monitor/autofix_invoke.py \| wc -l` | 0 | **6** (the plan's own baseline command, re-run) |
| … of those, executable rather than docstring | `grep -rn --include="*.py" '"--output-format"' specfuse/agent/ specfuse/monitor/ \| wc -l` | 0 | **1** — `invoke.py:148`, the single place the flag is appended |
| Hand-rolled `claude` argvs left | `grep -rn 'argv = \["claude"' specfuse/agent/ specfuse/monitor/autofix_invoke.py \| wc -l` | (not baselined) | **0** |
| `run_claude(` call sites | `grep -rn --include="*.py" "run_claude(" specfuse/ \| grep -v "def run_claude"` | 0 | **4** — `autofix_run.py`, `providers/triage.py`, `providers/findings_diagnose.py`, `providers/feature.py` |
| Declining reasons — `REASON_*` constants in `bug_lane.py` | `grep -c "^REASON_" specfuse/loop/bug_lane.py` | 8 | **9** |
| … of those, actual declines (`DECLINE_LABELS`) | `python3 -c "from specfuse.loop.bug_lane import DECLINE_LABELS; print(len(DECLINE_LABELS))"` | 7 | **8** — `REASON_ELIGIBLE` is not a decline and has no label |

**On the declining-reason count.** `PLAN.md` § Notes records the baseline as
"declining reasons: 8". That figure matches the `REASON_*` constant count at
baseline, which includes `REASON_ELIGIBLE` — not a declining reason. Both
readings are given above so the row is unambiguous: one new reason
(`ci_pending`) was added, on either count.

### The six fixture demonstrations

The scripts are throwaway drivers written and run in this session, under
`$TMPDIR/close-demos/`. They call the real functions against temporary
fixtures with injected runners; none touches the network, none shells out to
`gh`, and the one that needs a repository builds a fresh one under `$TMPDIR`.
They are deliberately **not** re-runs of the producing units' own tests: each
asserts its behaviour sentence from `GATE-01.md` clause by clause, so a
demonstration can fail even when the unit that owns it is green — which is what
happened to behaviour 5.

| # | Behaviour from `GATE-01.md` § Definition of done | Command run in this session | Exit |
|---|---|---|---|
| 1 | Each item's edits land on its own worktree and branch; an item that ends without committing leaves nothing on the next item's tree and its work is reachable under an item-tagged ref named in the run summary | `python3 $TMPDIR/close-demos/demo1_worktree.py` | **0** (11 checks) |
| 2 | The `/fix-bug` invocation carries a wall-clock timeout, gates run in the foreground, and a fixture whose gate outruns the item's reasoning is still reported from its RESULT block | `python3 $TMPDIR/close-demos/demo2_timeout_foreground.py` | **0** (14 checks) |
| 3 | Checks still queued at the poll deadline decline `ci_pending` with `bug-lane:ci-pending`, never `ci_not_green`; a red run is still `ci_not_green` | `python3 $TMPDIR/close-demos/demo3_ci_pending.py` | **0** (13 checks) |
| 4 | Guardrails run on the PR number the RESULT block reported; the list lookup runs only when the block carried none | `python3 $TMPDIR/close-demos/demo4_pr_number.py` | **0** (11 checks) |
| 5 | An item that escalates with a PR already open says so and links it; an item with commits on an unpushed branch names the branch | `python3 $TMPDIR/close-demos/demo5_escalation_state.py` | **1** (10 checks, **3 failed**) |
| 6 | Every provider outcome carries `spend` from the usage envelope; `max_tokens_per_run` below one item's spend stops with `STOP_CAP`; `tokens spent` is non-zero | `python3 $TMPDIR/close-demos/demo6_spend.py` | **0** (14 checks) |

Plus the two oracles the acceptance criteria name, re-run fresh:

| Oracle | Command run in this session | Exit |
|---|---|---|
| Full suite | `python3 -m unittest discover -s tests -q` | **0** — `Ran 3683 tests in 153.022s / OK (skipped=3)` |
| Smoke test | `bash scripts/smoke-test.sh` | **0** — `smoke test: OK` |

**Where the suite ran.** The first full-suite run, inside the sandbox, reported
`FAILED (failures=2, errors=88, skipped=3)`, with the errors sharing one
signature — `SSLError(SSLCertVerificationError('OSStatus -26276'))` reaching
`pypi.org`, plus git network refusals. That is a report about where the suite
ran, not about the repository (`result-contract.md` §7). The `OK` recorded above
is the unsandboxed re-run of the identical command.

**What demonstration 1 asserted specifically**, because reading the source does
not establish it: two fixture items received two *different* `working_dir`
values, neither the repository root, and both directories were gone when the run
ended; the item that returned without committing left `refs/heads/wip/bug-102`
whose `bug-102.txt` blob contains that item's edit; `git status --porcelain` on
the main tree was empty and `bug-102.txt` was not loose on it; the rendered run
summary carried `uncommitted work committed on: wip/bug-102 (git show
wip/bug-102)`; and the item that *did* commit kept `refs/heads/agent/bug-101`
with no `wip/` ref invented behind it.

**What demonstration 6 asserted specifically**: the spend is not a written-in
constant. A CLI envelope carrying `input_tokens: 200`, `output_tokens: 1000`,
`cache_read_input_tokens: 900000` was parsed by `run_claude`, `usage_spend`
returned **1200** (cache reads excluded, matching the driver's own cost line),
and a run with `max_tokens=1000` over two items started one, never ran the
second, stopped `cap`, and rendered `tokens spent:     1200`.

**What demonstration 5 asserted, and what failed**: clauses 2 and 3 pass — an
unpushed `fix/1481-off-by-one` branch is named with its commit count, and a
`wip/bug-1481` ref left by a per-item worktree is named with its commit count —
and clause 4 passes, the generic "never reached a guardrail" sentence surviving
only when the run really left nothing. Clause 1 fails: driven through
`BugsProvider.execute()` with a scripted runner whose session output is a
stopped `/fix-bug` result carrying `pr_number: 1532`, the escalation neither
names PR #1532 nor drops the generic sentence. See § Retrospective for the cause
and `FOLLOW-UPS.md` for the entry.

Every row above was re-run after this close wrote `RETROSPECTIVE.md`,
`FOLLOW-UPS.md`, `CHANGELOG.md` and `.specfuse/LEARNINGS.md`, so the exit
statuses describe the tree the driver will squash, not the tree before this
close's own edits.

### Failure-class breakdown

Seven dispatched attempts across T01–T06; **one did not pass**, read directly
from `events.jsonl` in this session.

| WU | Attempt | Outcome | `failure_class` | Signature |
|---|---|---|---|---|
| T01 | 1 | `produces_not_in_diff` | `produces_not_in_diff` | `run.py` — `specfuse/agent/run.py` was declared in `produces:` and not changed |

Every other attempt (T01 attempt 2, and T02–T06 attempt 1 each) passed first
time. T01's refusal is the guard working as designed: the attempt touched
fourteen files including `specfuse/loop/bug_lane_run.py`, but not the declared
`specfuse/agent/run.py`, and the driver refused the pass rather than accept a
deliverable that was never written. The re-attempt delivered it and cost $3.68.

`summarize_attempt_failure_classes(feature_dir, gate_n=1)` returns
`(no non-passing attempts in scope)` for this feature. That is wrong, and it is
the known degradation `[FEAT-2026-0016/G3-CLOSE]` already records in
`LEARNINGS.md`: the helper buckets by `_gate_number_from_wu_id`, which resolves
`G<n>-CLOSE` ids and returns `None` for substantive ids like
`FEAT-2026-0108/T01`, so the one non-passing attempt is silently filtered out.
This is the third recorded observation of that defect; the table above was built
by reading `events.jsonl` directly. Not repeated as a new lesson.

## Retrospective

### Would the six units together have changed the 2026-09-02 run's escalation mix?

The run attempted 78 items, merged 2 and escalated 72. `PLAN.md` reads the
escalations as five classes, from issues #3177, #3178, #3179, #3180 and #3183.
Taking them in order, and marking each as *mechanically prevented* (the fix is
in code the run loop always executes), *instruction-shaped* (the fix depends on
a dispatched session following a skill rule), or *unchanged*:

**Class 1 — 20 items, `could_not_proceed` "waiting for the background test
run's completion notification" (#3178). Mostly fixed, but instruction-shaped,
and the residue is now recoverable rather than lost.** T03 does two things.
`resolve_item_timeout_seconds` gives the invocation a real deadline read from
`budgets.item_timeout_minutes` (demonstration 2 resolved `45` to 2700 s and
watched `run_claude` forward it), and `/fix-bug`'s headless section now binds
gate commands to the foreground. The deadline is mechanical; the foreground rule
is not — it is prose the dispatched session must follow, and no oracle in this
repository can prove a future session obeys it. What the deadline *does*
guarantee is that the failure mode changes shape: an overrun is now a named
`could_not_proceed` carrying the elapsed time rather than a session that ended
with no recorded outcome, and demonstration 2 showed a 41-minute gate inside a
45-minute deadline still being read from its RESULT block and going on to
guardrail evaluation. Two of T02's and T06's mechanisms also apply here: even a
session that still ends mid-wait now leaves its edits under `wip/<item_id>` and
gets an escalation naming that ref with a commit count. So the honest claim is
**this class shrinks substantially and its remainder stops losing work** — not
that it goes to zero.

**Class 2 — 7 items declined `ci_not_green` seconds after their PR opened
(#3177). The mislabel is fixed; most of the class was already fixed upstream.**
`PLAN.md` records that `main` has polled CI for up to 600 s since #1786, which
post-dates the 0.12.1 the run used. Most of those seven would now simply
conclude inside the poll and never be declined at all. T04's contribution is the
residue: a PR still queued *at* the deadline is now declined `ci_pending` with
`bug-lane:ci-pending`, which reads as "retry", and demonstration 3 confirmed the
split holds in both directions — a failing check still declines `ci_not_green`
with `bug-lane:ci-not-green`, and a concluded green run reports `eligible` and
never `ci_pending`, which is the satisfiability claim `PLAN.md` § Escalation-
predicate satisfiability made before arming. **Mechanically prevented**, for the
part T04 owns.

**Class 3 — 3 items reported `pr_not_found` for PRs that existed (#3180).
Fixed, with one dependency on the session.** T05 carries the number from
`/fix-bug`'s own RESULT block; demonstration 4 confirmed that a session output
carrying `pr_number: 42` evaluates guardrails on 42 with the runner seeing *no*
`gh pr list` call at all. The dependency: the session has to write the line, and
the sessions in the 2026-09-02 run had no such contract. Where it is absent the
lane still falls back to the list and now retries it once after a short wait,
which is itself an improvement on the single read those three items got.
**Mechanically prevented when the field is present; improved when it is not.**

**Class 4 — 1 item's complete, passing fix left as uncommitted edits on a branch
named for a different issue (#3179). Fixed outright.** This is the one class the
six units close mechanically, because the isolation lives in the run loop rather
than in anything a session does: `specfuse agent`'s `main()` passes
`isolate_items=True`, so every item gets a `git worktree` on `agent/<item_id>`
cut from a base commit, a dirty starting tree refuses to dispatch at all, and an
item that ends uncommitted has its edits committed under `wip/<item_id>` and
named in the run summary. Demonstration 1 exercised all of it. **Mechanically
prevented.**

**Class 5 — every run reported `tokens spent: 0`, so `max_tokens_per_run` could
never fire (#3183). Fixed outright.** T01's shared invoker appends
`--output-format json`, parses the envelope, and every dispatching provider sets
`ActionOutcome.spend` from it; demonstration 6 drove a real envelope through to
a `STOP_CAP` after one item with `tokens spent: 1200` on the rendered summary.
**Mechanically prevented.**

**The sixth thing the evidence names, and the one that is unchanged.** Item
#1481 in that run had already opened PR #1532 and still escalated with text
saying the lane "never reached a guardrail or merge decision" (#3178). T06's
whole objective was that sentence. Its payload renderer is correct and its test
passes — but the test constructs `BugLaneResult(outcome=could_not_proceed,
pr_number=1532)` directly, and `run_bug_lane`'s escalating branch
(`bug_lane_run.py:642-648`) returns a literal `pr_number=None` without calling
`extract_pr_number(session_output)`, the function T05 added in the same module.
Isolated in this session:

```
classify_outcome  -> could_not_proceed
extract_pr_number -> 1532
run_bug_lane      -> could_not_proceed pr_number= None
```

So item #1481's escalation would read **exactly as it did on 2026-09-02**. The
two items that left commits on unpushed branches would now be named with their
commit counts — that half works end to end — but the PR-linking half does not.
**Unchanged.**

### Why both units passed and the behaviour still does not exist

Neither T05 nor T06 was wrong about its own scope, and neither hollow-passed.
T05 `produces:` `bug_lane_run.py` and its acceptance criteria are all about the
*completed* path — the lookup, the retry, the `pr_not_found` fallback — with its
*Do not touch* explicitly reserving "escalation payload text (T06)". T06
`produces:` `providers/bugs.py` only, with `bug_lane.py` and the invoke modules
off limits, and its criteria specify the injection: *"`outcome=could_not_proceed,
pr_number=1532` yields a payload containing `PR #1532`"*. The value each unit
needed the other to supply was never assigned to either.

T06's *Objective* did name the missing work — *"extend `BugLaneResult` with
`pr_number` populated from T05 even on a stopped outcome"* — but that sentence
is prose in the objective, not one of the four acceptance criteria, and nothing
verified it. A criterion that hands the renderer the value the producer is
supposed to compute cannot fail when the producer does not compute it.

### What this close deliberately did not do

Fix it. `WU-90`'s *Do not touch* reserves source, tests and skills for T01–T06,
and the fix is a source change in `bug_lane_run.py`. Making it here would be the
close editing the thing it is meant to verify. The entry in `FOLLOW-UPS.md`
names the change, the file, the line range and the re-run condition.

### One thing worth knowing about the plan's restart prediction

`PLAN.md` § Notes predicted at most one driver-restart halt, reasoning that
"none of these units edit `specfuse/loop/loop.py`". Three fired — after T01
(`bug_lane_run.py`), after T04 (`agent_policy.py`, `bug_lane.py`,
`bug_lane_run.py`, `labels.py`) and after T05 (`bug_lane_run.py`). The staleness
path counts **any** module under `specfuse/loop/` the running process has
imported, not only `loop.py`. Each halt cost an operator resume, no dollars, and
nothing was lost. Recorded here rather than promoted: it is a fact about this
driver's staleness rule, not a rule about how to write a plan.

## Cost analysis

`planned_cost_usd` is declared per-WU and sums to **$37.00**, which is also
`PLAN.md`'s feature-level figure: T01 $6, T02 $7, T03 $5, T04 $5, T05 $5,
T06 $4, and this close $5. Read from `events.jsonl`'s `task_completed` payloads
in this session.

| WU | Attempts | Planned | Spent | Delta |
|---|---|---|---|---|
| T01 | 2 | $6.00 | $7.81 | **+$1.81** |
| T02 | 1 | $7.00 | $4.21 | −$2.79 |
| T03 | 1 | $5.00 | $2.72 | −$2.28 |
| T04 | 1 | $5.00 | $2.57 | −$2.43 |
| T05 | 1 | $5.00 | $1.97 | −$3.03 |
| T06 | 1 | $4.00 | $1.59 | −$2.41 |
| **T01–T06** | **7** | **$32.00** | **$20.87** | **−$11.13 (−34.8%)** |
| G1-CLOSE | 1 (this one) | $5.00 | not yet in `events.jsonl` | — |

**Delta, named: −$11.13 under the $32.00 planned for T01–T06, and −$16.13 under
the whole feature's $37.00 with this close's own attempt still to be recorded.**
The driver writes this close's `attempt_outcome` after the RESULT block, so the
figure above is everything measurable at close time and understates the feature
total by exactly one attempt. Against the gate's `cost_budget_usd: 50.00`, the
close began with **$29.13** of headroom.

**Every unit but T01 came in under.** Five of six landed between 39% and 61% of
their estimate on a single first-try attempt. The one overrun is T01, and it is
entirely the refused first attempt: $4.13 spent on an attempt the driver
rejected for a declared-but-unchanged `produces:` path, plus $3.68 on the
re-attempt that delivered it. Without the refusal T01 would have come in under
too. So the estimating was not pessimistic in the ordinary sense — **$11.13 of
the $16.13 surplus is simply that six units of straightforward, well-scoped work
each cost about half of a defensively-set floor**, and the remaining variance is
one guard refusal.

That is worth stating plainly rather than as a calibration complaint: a gate
budget summed from `planning-discipline.md` §5's floors plus one re-attempt of
the largest unit is *meant* to be defensive, and it behaved exactly as intended —
it absorbed a real refusal without halting, and the feature finished at 42% of
its gate budget. No change to the floors is indicated by one feature.

## Consumer-visible contract changes

Not `n/a`. Four consumer-visible additions and one behaviour change, all
inherited by a target repository on its next `specfuse upgrade`.

1. **A new declining reason and its label.** `REASON_CI_PENDING = "ci_pending"`
   joins `bug_lane.py`'s reason set and `DECLINE_LABELS` gains
   `bug-lane:ci-pending`, registered in `labels.py` for provisioning. A PR whose
   checks have not concluded at the poll deadline is declined under this reason
   instead of `ci_not_green`; it is a decline (fail closed, never a merge) whose
   escalation says "retry", not "red". A concluded run never reports it, so the
   guardrail's zero-issues predicate stays satisfiable. Consumers that treat the
   declining-reason set as closed — a dashboard, a label filter, an alert rule —
   see a ninth `REASON_*` constant and an eighth declining label.

2. **An optional `pr_number:` line in `/fix-bug`'s headless RESULT block.** The
   skill writes it on a `completed` outcome, naming the PR step 7 opened. It is
   **skill-local and optional**: `result-contract.md`'s format is unchanged, the
   driver ignores unknown RESULT lines, and a session that omits it still works
   through the existing list lookup. Consumers parsing that block gain a field;
   nothing they already parse changed.

3. **Two new `budgets:` keys in `.specfuse/agent-policy.yml`.**
   `item_timeout_minutes` (default 45) bounds one headless item invocation, and
   `ci_wait_minutes` (default 10, i.e. the existing `CI_WAIT_SECONDS = 600`)
   sets how long the lane waits for a CI conclusion. Both are optional and both
   fall back to their defaults when the file, the `budgets` block, or the key is
   absent, or the value is not a positive number — an existing policy file needs
   no edit.

4. **Per-item worktrees change what an `specfuse agent` run does to a
   repository.** This is the behaviour change, not an addition. Every item now
   runs in its own `git worktree` on `agent/<item_id>`, cut from the run's base
   commit; an item that ends with uncommitted edits has them committed under
   `wip/<item_id>` and named in the run summary; and **a run over a dirty
   starting tree now refuses to dispatch any item at all**, reporting the dirty
   paths. Operators who ran the agent over a working tree with local edits will
   see a refusal where they previously saw a run. New refs appear under
   `agent/*` and `wip/*`; nothing deletes them.

5. **`tokens spent` in a run summary is now a real number, so
   `budgets.max_tokens_per_run` can actually stop a run.** Previously every run
   reported `0` and the cap could never fire. An operator who set that key and
   never saw it trigger will now see runs stop with `STOP_CAP`. The key, its
   name and its semantics are unchanged — only its effect is, and the change is
   from "inert" to "enforced", which is worth an operator knowing before their
   next unattended run.

**`CHANGELOG.md`.** All five appear in `Unreleased` as four entries tracing
`FEAT-2026-0108` — three `added` (items 1, 2 and 3) and one `changed` covering
items 4 and 5, which are one story from an operator's point of view: what an
unattended run now does to their tree and when it now stops. Written through
`specfuse.loop.changelog.append_entry`, and `parse_changelog` reports the
document clean.

**This section requires explicit human acknowledgment**
(`close-discipline.md` §3). It is presented for that acknowledgment at gate
review; nothing in this close treats the list as acknowledged. The `not_met`
verdict means the terminal flips do not fire regardless.

## Lessons

One entry, appended to `.specfuse/LEARNINGS.md` under *FEAT-2026-0108/G1-CLOSE
— a criterion that injects the value it should compute*: **when a gate behaviour
spans a producer and a renderer split across two work units, at least one unit's
acceptance criterion must exercise the seam end to end and name the producer
call, not a constructed intermediate value.** T05 owned reading the PR number
and T06 owned rendering it; both passed, neither owned putting it on the
escalating return, and T06's criterion specified the injection that hid the gap.
The arming-time check is a sentence: for every criterion that constructs an
input another unit in the same gate is supposed to produce, name the unit that
produces it and confirm a criterion somewhere exercises that production.

Nothing else here generalizes. The driver-staleness restart prediction and the
`summarize_attempt_failure_classes` bucketing degradation are recorded above as
feature-specific findings; the latter is already a `LEARNINGS.md` rule from
`[FEAT-2026-0016/G3-CLOSE]` and is not repeated.

## Verdict

**`not_met`.** Five of the six behaviours in `GATE-01.md`'s definition of done
were demonstrated on fixtures in this session, each with a recorded exit status;
the sixth was demonstrated to fail, with the cause isolated to one unreached
call in `bug_lane_run.py`. The full suite reports `OK` on 3,683 tests and
`scripts/smoke-test.sh` exits 0 — every unit is individually green, which is
exactly the composite `close-discipline.md` §1 exists to catch. `FOLLOW-UPS.md`
carries one entry for the failed criterion, with the command, its exit code, the
root cause and the re-run condition. No terminal surface flips.
