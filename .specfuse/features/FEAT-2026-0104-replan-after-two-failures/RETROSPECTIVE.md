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
