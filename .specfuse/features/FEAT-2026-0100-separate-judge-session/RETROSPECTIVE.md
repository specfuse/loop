# Retrospective — FEAT-2026-0100, separate judge session

## Gate 1

Gate 1 is the only gate. Five substantive units (T01–T05) and this close. All
five are `done`. All eight behaviours in `GATE-01.md`'s definition of done were
exercised on fixtures with an injected runner, in this session, and every
fixture demonstration exited 0. **Two of the eight are nonetheless measurably
false on this gate's own artifacts**, which the fixtures were not shaped to
catch:

- **Behaviour 7** — the new lint rule does report `ERROR` on a `pending` close
  WU whose body says `verdict: met`, and it does *not* report zero `ERROR` over
  every existing feature folder: the sweep over all 74 returns one.
- **Behaviour 1** — the judge's prompt does carry the definition of done, the
  criteria, a diff and the close's `## Measurements`, and it does *not* exclude
  the close's `## Retrospective` prose: every non-blank line of that section
  survives redaction inside the diff. Separately, the diff it carries is not the
  gate's — the re-probed `baseline.sha` narrows it to 4 lines against the
  gate's real 3,687.

`GATE-01.md`'s own test is *"If all five units are `done` and any behaviour
above cannot be demonstrated, this gate is not done."* Two behaviours, measured
in this session, are not true on this tree.

This close does not decide what that means. Per `close-discipline.md` §1 as T04
rewrote it, the measurements are below and the judge — a session that did not do
this work — reads them and settles the verdict. This is the first close in this
repository the judge will see, and it did not know that when it started
measuring.

## Measurements

Every figure below is a command run in this session against the tree the driver
will squash. The five close-path demonstrations run the whole driver
(`loop.run`) over a scaffolded feature in a throwaway git workspace with
`dispatch`, `verify` and `run_judge_session` all replaced by fixtures — the
judge is injected, not invoked — so no demonstration touches the network or
`gh`. `python3 -m specfuse.loop.lint_plan` is used rather than the `specfuse`
console script: the installed pipx build is not this checkout, and it says so
itself in a warning.

The five `loop.run` demonstrations require an unsandboxed shell.
`require_session_env_writable` probes `~/.claude/session-env` before every run
and the tool sandbox denies writes there (`PermissionError: [Errno 1] Operation
not permitted`), which fails every one of them with `SystemExit` before any
judge code executes. Sandboxed, all five are false red; unsandboxed, all five
pass. That is a property of where the suite ran, not of the tree.

### The eight fixture demonstrations

Numbered to match the eight bullets of `GATE-01.md` § Definition of done, in
order.

| # | Behaviour (`GATE-01.md` § Definition of done) | Command run in this session | Exit |
|---|---|---|---|
| 1 | The judge's prompt carries the definition of done, the `GATE-NN-CRITERIA.md` entries, the gate's diff and the close's `## Measurements`, and not the close's `## Verdict` / `## Retrospective` prose | `python3 -m unittest tests.test_judge_close_path.TestJudgePromptEvidence -q` | **0** (Ran 1, `OK`) |
| 1b | …the same exclusion, measured directly on *this* close's `RETROSPECTIVE.md` rendered as a diff hunk | `python3` call to `specfuse.loop.judge.strip_forbidden_sections` over this file in `+`-prefixed diff form, counting surviving non-blank lines per section | **`## Verdict`: 0% of its non-blank lines survive (correct). `## Retrospective`: 100% survive — NOT excluded** (see below) |
| 2 | Judge answers `not_met` with two findings: on-disk `verdict:` reads `not_met`, `FOLLOW-UPS.md` carries two entries in the judge's words, no terminal surface flips, `judged` event records `close_verdict: met` / `judge_verdict: not_met` | `python3 -m unittest tests.test_judge_close_path.TestJudgeLowersVerdict -q` | **0** (Ran 1, `OK`) |
| 3 | Close writes `not_met`, judge answers `met`: the verdict stays `not_met`, the `judged` event records the disagreement | `python3 -m unittest tests.test_judge_close_path.TestJudgeCannotRaise -q` | **0** (Ran 1, `OK`) |
| 4 | Judge times out or returns no parseable verdict: the close's verdict stands, the event says `judge_verdict: null` with the reason, the run does not crash | `python3 -m unittest tests.test_judge_close_path.TestJudgeUnusable -q` | **0** (Ran 1, `OK`) |
| 5 | `judge_disabled: true` in PLAN frontmatter skips the dispatch and prints a one-line notice naming the escape hatch | `python3 -m unittest tests.test_judge_close_path.TestJudgeDisabled -q` | **0** (Ran 1, `OK`) |
| 6 | The judge's usage is folded into the close WU's `cost_usd` and the `attempt_outcome` event; the cost analysis can see it | `python3 -m unittest tests.test_judge_cost -q` | **0** (Ran 3, `OK`) |
| 7a | `specfuse lint` reports `ERROR` on a `pending` close WU whose body says `verdict: met` | `python3 -m unittest tests.test_lint_close_verdict_not_predecided -q` | **0** (Ran 6, `OK`) |
| 7b | …the same, as a negative observation on a purpose-built bad input (fixture feature dir, close WU `status: pending`, body line *"Record verdict: met once the suite is green"*) | `python3 -m specfuse.loop.lint_plan "$TMPDIR/judge-lint-fixture"` | **1** — emits `ERROR: …/WU-90-close.md: close WU body names a predecided verdict: 'verdict: met'`. Positive control: the identical body with `status: done` exits **0** with zero `predecided` hits |
| 7c | …and zero `ERROR` over every existing feature folder | sweep of `python3 -m specfuse.loop.lint_plan <dir>` over all 74 folders under `.specfuse/features/` holding a `PLAN.md` | **1 folder non-zero, 1 `ERROR` line — NOT zero** (see below) |
| 8 | `PLAN.template.md` and `/draft-feature`'s autonomy recommendation read `auto`; `close-discipline.md` §1 says the judge writes the verdict | `grep -q "^autonomy_default: auto" .specfuse/templates/PLAN.template.md && grep -q "^autonomy_default: auto" specfuse/loop/data/templates/PLAN.template.md && grep -q 'recommend `auto`' .specfuse/skills/draft-feature/SKILL.md && grep -q 'recommend `auto`' plugins/specfuse/skills/draft-feature/SKILL.md && grep -q "You measure; the judge concludes" .specfuse/rules/close-discipline.md && grep -q "You measure; the judge concludes" specfuse/loop/data/rules/close-discipline.md` | **0** (all six surfaces present) |

### The corpus sweep, in full

| Measurement | Command | Value |
|---|---|---|
| Feature folders swept | `for d in .specfuse/features/*/; do [ -f "$d/PLAN.md" ] \|\| continue; …` | **74** |
| Folders exiting non-zero | same sweep | **1** |
| `ERROR:` lines across all folders | same sweep, `grep -c 'ERROR:'` | **1** |

The single line, verbatim:

```
ERROR: .specfuse/features/FEAT-2026-0082-async-drafting-wiring/WU-90-gate-1-close.md: close WU body names a predecided verdict: 'the verdict is' — the judge writes the verdict in its own session; see PLAN.md § Escalation-predicate satisfiability.
```

The rule is behaving exactly as T05 built it. What is false is the corpus claim
made about it. `PLAN.md` § Escalation-predicate satisfiability says *"`done`
closes are skipped as sealed history, so FEAT-2026-0082's pre-decided hedge,
which is `done`, does not fire it."* FEAT-2026-0082's close WU is
`status: pending`, `attempts: 0`; the feature is `status: planned` and has never
been dispatched. The rule fires on `pending`, so it fires here.

This is not a close-time regression. The file has one commit in its history
(`78c0a94`, the feature's drafting commit); `git show
303f1d7:.specfuse/features/FEAT-2026-0082-async-drafting-wiring/WU-90-gate-1-close.md`
— T05's own commit — carries the same `status: pending` and the same sentence.
The sweep would have failed on the tree T05 reported `done` on. T05's fourth
acceptance criterion was *"`python3 -m specfuse.loop.lint_plan` over every folder
under `.specfuse/features/` reports zero ERROR from this rule"*, and its
escalation trigger was *"Emit `status: blocked` if the corpus sweep reports an
ERROR on a non-`done` close; paste the sentence, do not widen the skip."*
`GATE-01.md` § Arming discipline asked for the same sweep at arm time and its
`## Reflection notes` is still the unedited placeholder.

### Other recorded values

| Measurement | Command | Value |
|---|---|---|
| `PLAN.template.md`'s `autonomy_default` | `grep -m1 '^autonomy_default:' .specfuse/templates/PLAN.template.md` | **`auto`** (identically in `specfuse/loop/data/templates/PLAN.template.md`) |
| `judged` events in this feature's `events.jsonl` | `python3` read of `events.jsonl`, counting `event_type == "judged"` | **0 at the time this section was written** |
| Full suite | `python3 -m unittest discover -s tests -q` | **0** — `Ran 3734 tests`, `OK (skipped=3)` |
| Smoke test | `bash scripts/smoke-test.sh` | **0** — `smoke test: OK` |
| This feature's own plan lint (the `plannext` gate) | `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0100-separate-judge-session` | **0** |

**On the `judged` event.** This close cannot read its own. `judge_close` runs
after the closing-deliverable guards, which run after this WU's squash, and the
`judged` event is appended after that — all of it downstream of this session.
What the driver will do, from `loop.py` (the dispatch site guarded by `if gate
is gates[-1]`): gate 1 is `gates[-1]` for this feature, `PLAN.md` carries no
`judge_disabled` key, and `GATE-01.md` carries a `baseline.sha`, so the three
early returns in `judge_close` do not apply and a real `sonnet`/`medium` session
is dispatched. Exactly one `judged` event will be appended to
`.specfuse/features/FEAT-2026-0100-separate-judge-session/events.jsonl`,
carrying `close_verdict` (this close's `verdict:` as read off disk),
`judge_verdict`, `verdict`, `lowered`, `disagreed`, `findings`, `diff_base` and
`diff_base_source`. A reader of this retrospective can confirm it there; this
close asserts nothing about what it will say.

### Failure-class breakdown

Read from `events.jsonl`'s `attempt_outcome` payloads in this session. Three
non-passing attempts across the gate, all one failure class.

| Failure class | Signature | Count | WU |
|---|---|---|---|
| `tests` | `test_doc_set_missing_for_retrospective_fails` | 2 | T03, attempts 1 and 2 |
| `tests` | `test_stat_survives_in_full_when_the_body_is_capped` | 1 | T04, attempt 1 |

Both T03 attempts carried the identical signature, which tripped
`spinning_signature_repeat` and produced this gate's one `human_escalation`. The
operator's `re_arm_dispatched` note records the disposition: *"root cause found
in test isolation, not the code"* — and T03 passed on the re-armed attempt at
$1.24 without the production change the two spinning attempts had been reaching
for. `test_doc_set_missing_for_retrospective_fails` is not a judge test; it is a
doc-set invariant that T03's edits perturbed through import order.

Three `driver_staleness_detected` halts (after T01, T02 and T03), each requiring
an operator resume. `PLAN.md` § Notes predicted *"a `driver_restart_required`
halt after each of T01 through T05"* — five. Three happened. T04 and T05 touched
rules, templates, skills, docs and `lint_plan.py`; the staleness rule counts
modules under `specfuse/loop/` the running process has imported, and neither
unit's diff reached one that was loaded.

## Retrospective

### What the judge's evidence bundle lacked when the fixtures were built

Three things, two of them serious. Both serious ones are invisible from the
fixtures and visible the moment the bundle is built against this gate's own
artifacts — which is the composite `close-discipline.md` §1 says only the
close's fresh re-run catches.

**A `## Retrospective` section with subheadings is not redacted at all.**
`strip_forbidden_sections` opens a redacted run at a heading whose first word is
`verdict` or `retrospective`, and closes it at *the next heading of any level*.
A `##` sibling closing the run is the intended behaviour and is what
`test_redaction_stops_at_the_next_ordinary_heading` pins. A `###` **child**
closes it too — so every subsection under `## Retrospective` re-opens the stream
and is carried into the judge's prompt verbatim. Measured on this file, rendered
as a `+`-prefixed diff hunk exactly as it will reach the bundle:

| Section | Surviving redaction |
|---|---|
| `## Verdict` (no subheadings) | **0% of its non-blank lines** — correctly stripped |
| `## Retrospective` (with `###` subsections) | **100%** — every line carried |

Stated as proportions rather than line counts on purpose: the absolute counts
move every time this file is edited, and this file is the input to its own
measurement. The proportions do not — the section is either redacted or it is
not, and `## Retrospective` is not.

The prompt's own instruction to the judge — *"Do not open `RETROSPECTIVE.md`.
Its closing sections carry the other session's own opinion of its work; reading
them is how a judge stops being one"* — is therefore asking the judge not to
read something the prompt has already handed it. `TestJudgePromptEvidence`
passes because its fixture retrospective's `## Verdict` has no subheadings, so
the one section it asserts on is the one shape the implementation handles. The
two most recent retrospectives in this repository (FEAT-2026-0108,
FEAT-2026-0085) both use `###` subsections under `## Retrospective`; so does
this one. Filed as a follow-up.

**The gate diff the judge will actually receive is a rounding error.**
`resolve_gate_start_sha` prefers `GATE-NN.md`'s `baseline.sha`, whose docstring
says the driver wrote it *"at gate entry, before any unit was dispatched, which
is exactly the boundary the judge's diff wants."* That is not what the field
holds on a gate that halted. `GATE-01.md`'s `baseline.sha` is
`7f50a473b99f0483eb71a390bea995cf1a6af689`, `probed_at`
`2026-09-06T13:26:04Z` — the baseline probe re-ran on the last driver resume, ten
hours after T01 started, and overwrote the gate-entry value. Measured in this
session:

| Range | `git diff --stat …` |
|---|---|
| `7f50a47..HEAD` — what `resolve_gate_start_sha` returns | **1 file changed, 2 insertions(+), 2 deletions(-)** (`GATE-01.md` itself) |
| `64dde90..HEAD` — merge-base with `main`, the gate's real footprint | **34 files changed, 3677 insertions(+), 10 deletions(-)** |

So the judge for this close will be handed a four-line diff of the gate file's
own frontmatter, plus whatever this close's squash adds, as "the gate diff". The
fixtures could not see this: `_write_feature` scaffolds a gate whose baseline is
written once and never re-probed, which is the happy path. Every feature that
takes a `driver_staleness_detected` halt — and this one predicted five — gets the
degraded bundle. Filed as a follow-up.

**The judge is told to re-run oracles but is not told which command.** The prompt
says *"Re-run every oracle a criterion names"*, and the criteria come from
`GATE-NN-CRITERIA.md`. This feature has no `GATE-01-CRITERIA.md`, so
`_render_criteria` emits its fallback — *"No per-criterion state was recorded for
this gate. Judge from the definition of done, the diff, and the measurements
below."* — and the judge is left to infer the oracles from the definition of done
and from this section. That is a known and deliberate boundary rather than a
defect: `PLAN.md` § Scope boundary puts the feature-level oracle in
FEAT-2026-0101, drafted *"after this lands so the judge has something binary to
read."* Worth naming here because it is what the judge's `not_met`-if-unverified
rule collides with first.

Nothing else was missing. The in-diff redaction is real rather than vacuous as
far as it goes — the close's `RETROSPECTIVE.md` is inside the gate diff, so its
prose arrives in a diff hunk and `strip_forbidden_sections` has to catch it
there, which `TestJudgePromptEvidence` asserts by requiring `RETROSPECTIVE.md`
to be present in the prompt while `## Verdict` is absent from it. It is that
assertion's *scope* that is too narrow: one `##` section with no children, and
the only shape the child-heading defect above does not reach.

### Were the eight behaviours demonstrable without a live `gh` or a network call?

Yes, all eight, and no demonstration in this session made either. The five
close-path behaviours run the real driver end to end with `run_judge_session`
replaced by a Python callable, which is the seam `judge_close` looks up on the
module at call time. The cost-folding behaviour injects a usage envelope of the
same shape `dispatch` produces. The lint behaviours are a pure function over
files on disk. The template/rule behaviour is six `grep`s. `GATE-01.md`'s
escalation trigger — *"Emit `status: blocked` if a fixture demonstration needs a
live `gh` or a network call"* — was never approached.

The one environmental dependency worth recording is the opposite of a network
call: the tool sandbox's deny-list over `~/.claude/session-env` makes the five
`loop.run` demonstrations fail with `SystemExit` before any judge code runs. This
is the fifth close in this repository to hit it.

### What this close did not do

It did not fix FEAT-2026-0082's close body. The one-line rewrite that would clear
the corpus sweep is obvious and tempting, and it is another feature's work unit:
this WU's *Do not touch* limits it to its own close record, and 0082's close body
also still says *"the verdict is hedged"*, a shape FEAT-2026-0085 retired — so the
right repair is a review of that close's whole body by whoever arms 0082, not a
phrase swap by a close trying to turn its own sweep green.

## Cost analysis

`planned_cost_usd` is `$29.00` at the feature level, and the per-WU sum is the
same `$29.00` (T01 $5, T02 $7, T03 $3, T04 $5, T05 $3, G1-CLOSE $6), so both
readings reconcile against one number. Every "spent" figure is read from this
feature's `events.jsonl` `attempt_outcome` payloads in this session.

| WU | Attempts | Planned | Spent | Delta |
|---|---|---|---|---|
| T01 | 1 | $5.00 | $2.87 | −$2.13 |
| T02 | 1 | $7.00 | $8.73 | **+$1.73** |
| T03 | 3 | $3.00 | $3.66 | **+$0.66** |
| T04 | 2 | $5.00 | $8.03 | **+$3.03** |
| T05 | 1 | $3.00 | $0.99 | −$2.01 |
| **T01–T05** | **8** | **$23.00** | **$24.29** | **+$1.29 (+5.6%)** |
| G1-CLOSE | 1 (this one) | $6.00 | not yet in `events.jsonl` | — |
| **Feature** | **9** | **$29.00** | **$24.29 recorded** | **−$4.71 recorded** |

**Delta, named: −$4.71 against $29.00, with this close's own attempt still
unrecorded.** The driver writes this attempt's `attempt_outcome` after the RESULT
block, so the feature total above understates the truth by exactly one attempt —
and, for the first time in this repository, by one *judge* session too:
FEAT-2026-0100/T03 shipped `fold_judge_usage`, so the judge's spend is added into
this close's `cost_usd` and into its `attempt_outcome` payload before either is
written, and appears separately as `judge_cost_usd` on the `judged` event.
Against `GATE-01.md`'s `cost_budget_usd: 40.00`, this attempt began with $15.71
of headroom.

**Restart count: three**, one each after T01, T02 and T03, against `PLAN.md`'s
prediction of five. Each cost an operator resume and no dollars.

**Where the +$1.29 overrun on the substantive units came from — one spin and one
mis-sized unit.** T03's two spinning attempts cost $2.42 and produced nothing;
the re-armed third attempt cost $1.24 and passed, which is roughly what the unit
was planned at. Strip the spin and T01–T05 come in at $21.87 against $23.00. The
other half of the story is T04: planned $5.00 for rules, templates, two skill
copies, two docs copies and their vendored mirrors, it spent $8.03 across two
attempts. A unit whose diff spans twelve files in six mirrored pairs is not a
$5.00 unit, and the mirroring is the part that is easy to under-count at planning
time.

## Consumer-visible contract changes

Five, all additive. Enumerated here and appended to `CHANGELOG.md`'s
`Unreleased` section in the same pass, classified per
`specfuse/loop/changelog.py`'s schema and carrying this feature's ID.

1. **A judge session now runs on every terminal close, and its verdict is the one
   that stands when it is lower.** After a terminal close's squash passes the
   closing-deliverable guards and before the verdict is re-read for the terminal
   flips, the driver dispatches a fresh `sonnet`/`medium` session that receives
   the gate's definition of done, the `GATE-NN-CRITERIA.md` entries, the gate's
   diff and the close's `## Measurements` — and not the close's own `## Verdict`
   or `## Retrospective` prose, which is stripped even out of diff hunks. A judge
   may lower `met` to `not_met`, which rewrites the close WU's `verdict:` field
   and files `FOLLOW-UPS.md` from the judge's own findings verbatim; it may never
   raise a `not_met`. A timeout, an unparseable answer, an unresolvable diff base
   or a defect in the judge path all fail open with the close's verdict standing.
   Consumers see a second session's cost on every terminal close, and a close's
   `verdict:` that can change after the close session ended. *(added)*
2. **A new `judged` event type in `events.jsonl`.** One per terminal close,
   emitted for every outcome including the ones where no judge ran, carrying
   `gate`, `close_verdict`, `judge_verdict`, `verdict`, `lowered`, `disagreed`,
   `findings`, `reason`, and — when a diff base resolved — `diff_base` and
   `diff_base_source`, plus `usage` and `judge_cost_usd` when the session
   returned an envelope. Anything consuming `events.jsonl` sees a new
   `event_type`. *(added)*
3. **A new `judge_disabled` PLAN.md frontmatter key.** `judge_disabled: true`
   skips the dispatch and prints a one-line notice naming the key. One reader,
   no other behaviour; absent or false is the default and no existing `PLAN.md`
   needs an edit. *(added)*
4. **`autonomy_default: auto` is what a drafted feature now recommends.**
   `PLAN.template.md` ships `auto` and `/draft-feature`'s autonomy decision
   recommends it. Existing `PLAN.md` files are untouched and keep whatever they
   declare; only newly drafted features get the new default. *(changed)*
5. **One new `ERROR`-level plan-lint rule.** `lint_close_verdict_not_predecided`
   refuses a `close` WU whose body names the verdict it expects
   (`verdict: met`, `the verdict is`, `record met`, the retired `hedged verdict`
   and siblings), at `ERROR` when the WU is `pending`/`ready`, at `WARN` when
   `draft`, skipped when `done`. Matches only outside fenced code blocks. A
   project with a drafted-but-unarmed close carrying such a sentence will see its
   plan lint go red — as this repository's own corpus sweep does, on
   FEAT-2026-0082. *(added)*

**This section requires explicit human acknowledgment** (`close-discipline.md`
§3). It is presented for that acknowledgment at gate review; nothing in this
close treats the list as acknowledged.

## Lessons

One entry, in `.specfuse/LEARNINGS.md` under *FEAT-2026-0100/G1-CLOSE — a
satisfiability answer that was reasoned about instead of run*: **when a plan's
§ Escalation-predicate satisfiability answer rests on a claim about the existing
corpus, that claim is a command with an output, and the command must be run and
its output pasted at drafting time — a plan that reasons its way to "zero" is
asserting a measurement it never took.** `PLAN.md` § Escalation-predicate
satisfiability answered §2's mandatory question with *"FEAT-2026-0082's
pre-decided hedge, which is `done`, does not fire it"*; 0082's close WU is
`status: pending`, so it fires, and the one-line `git show` that would have
settled it costs nothing. The claim then survived two more surfaces that were
built to catch it — `GATE-01.md` § Arming discipline asked for the sweep in
writing and its `## Reflection notes` is still the placeholder, and T05 carried
the sweep as its fourth acceptance criterion and a matching `blocked` escalation
trigger, and reported `done` at one attempt. Three chances, one unrun command,
and the first thing in the feature able to see it was this close's fresh re-run
of the same oracle.

Nothing else here generalizes. The re-probed `baseline.sha` truncating the
judge's diff is a defect in this feature's own code, filed as a follow-up rather
than a rule; the sandbox deny-list over `~/.claude/session-env` and T04's
mirrored-file undersizing are recorded above as feature-specific findings.

## Verdict

**`not_met`.** All eight behaviours in `GATE-01.md`'s definition of done were
exercised on fixtures with an injected runner in this session and every fixture
demonstration exited 0. Two of the eight are false on this gate's own artifacts
anyway, each measured directly rather than inferred:

- **Behaviour 7.** The lint rule does report `ERROR` on a `pending` close WU
  whose body says `verdict: met` — demonstrated twice, once as a negative
  observation on a purpose-built bad input with a passing positive control. It
  does not report zero `ERROR` over every existing feature folder: the sweep
  over all 74 returns one, on a `pending` close that was already in the tree
  when T05 reported `done` against the same criterion.
- **Behaviour 1.** The prompt does not exclude the close's `## Retrospective`
  prose — every non-blank line of that section survives redaction inside the
  diff, because a `###` child heading closes the redacted run the same way a
  `##` sibling does.
  And the diff it carries is not the gate's: the re-probed `baseline.sha`
  narrows it to 4 lines against the gate's real 3,687.

`FOLLOW-UPS.md` carries one entry per failed criterion: the corpus sweep, the
diff base, and the child-heading redaction gap.

The full suite reports `OK` on 3,734 tests and `scripts/smoke-test.sh` exits 0,
both re-run fresh and unsandboxed.

This verdict is advisory. `close-discipline.md` §1 as T04 rewrote it puts the
decision with a session that did not do this work, and this is the first close
this repository submits to it — which means the mechanism's first real test is
whether it agrees, disagrees, or finds something in the evidence above that this
close read wrong.
