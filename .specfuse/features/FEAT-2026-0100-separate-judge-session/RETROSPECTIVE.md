# Retrospective — FEAT-2026-0100, separate judge session

## Gate 1

Gate 1 is the only gate. Five substantive units (T01–T05) and four hygiene
precursors — T01H and T02H authored from this close's first attempt, T01H2 and
T02H2 authored from the judge's two findings on its second — plus this close.
All nine are `done`.

This is the close's **third attempt**. Attempt 1 (2026-09-06, $8.32) recorded
`not_met` on three criteria and the judge agreed. Attempt 2 (2026-09-06, $8.94)
recorded `met` and **the judge lowered it to `not_met` on two findings**, both
about the evidence bundle this feature's own close hands its judge: the gate's
`entry_sha` was stamped at a mid-gate re-probe, and `slice_wu_section` cut
`## Measurements` at its first `###` child. T01H2 and T02H2 were authored from
those two findings verbatim and are the only substantive change since.

All eight behaviours in `GATE-01.md`'s definition of done have been
re-demonstrated on fixtures with an injected runner in this session, the corpus
sweep re-run, and both of the judge's findings re-measured directly on this
gate's own artifacts. One is fixed and verified on this file; one is fixed as a
mechanism and **still holds for this gate**, for a reason stated in
`## Measurements` rather than argued here.

Per `close-discipline.md` §1 as T04 rewrote it, the measurements are below and a
session that did not do this work reads them and settles the verdict.

## Measurements

Every figure is a command run in this session against the tree the driver will
squash. The five close-path demonstrations run the whole driver (`loop.run`)
over a scaffolded feature in a throwaway git workspace with `dispatch`, `verify`
and `run_judge_session` replaced by fixtures — the judge is injected, never
invoked — so nothing here touches the network or `gh`.
`python3 -m specfuse.loop.lint_plan` stands in for the `specfuse` console
script, whose pipx build is not this checkout. Those five need an unsandboxed
shell.

The eight fixture demonstrations, numbered to `GATE-01.md` § Definition of done:

| # | Behaviour | Command run in this session | Exit |
|---|---|---|---|
| 1 | Judge's prompt carries the definition of done, criteria entries, gate diff and the close's `## Measurements`, and not its Verdict/Retrospective prose | `unittest tests.test_judge_close_path.TestJudgePromptEvidence -q` | **0** (Ran 1, `OK`) |
| 1b | …the same exclusion measured on **this** file, in a three-file diff (`CHANGELOG.md`, this file, `judge.py`) | `strip_forbidden_sections` over that diff, counting surviving `+`-prefixed non-blank lines | **0 of 310 carried**; both code halves intact (31/31, 50/50) |
| 2 | Judge answers `not_met` with two findings: on-disk `verdict:` reads `not_met`, FOLLOW-UPS carries two entries in the judge's words, no terminal flips, event records `met`/`not_met` | `…TestJudgeLowersVerdict -q` | **0** (Ran 1, `OK`) |
| 3 | Close writes `not_met`, judge answers `met`: verdict stays `not_met`, event records the disagreement | `…TestJudgeCannotRaise -q` | **0** (Ran 1, `OK`) |
| 4 | Judge times out or returns no parseable verdict: close's verdict stands, event says `judge_verdict: null` with the reason, no crash | `…TestJudgeUnusable -q` | **0** (Ran 1, `OK`) |
| 5 | `judge_disabled: true` skips the dispatch and prints a one-line notice naming the escape hatch | `…TestJudgeDisabled -q` | **0** (Ran 1, `OK`) |
| 6 | Judge usage folds into the close WU's `cost_usd` and the `attempt_outcome` event | `unittest tests.test_judge_cost -q` | **0** (Ran 3, `OK`) |
| 7a | `specfuse lint` ERRORs on a `pending` close WU whose body says `verdict: met` | `unittest tests.test_lint_close_verdict_not_predecided -q` | **0** (Ran 6, `OK`) |
| 7b | …as a **negative observation** on a purpose-built bad input: fixture feature dir, close WU `status: pending`, body line *"Record verdict: met once the suite is green."* | `lint_plan "$TMPDIR/judge-lint-fixture-a3"` | **1**, 1 `ERROR:` — `close WU body names a predecided verdict: 'verdict: met'` |
| 7b-c | two controls: the byte-identical body at `status: done`; and `status: pending` with that one sentence deleted | same | **0** and **0**, 0 `ERROR` each |
| 7c | …and zero ERROR over every existing feature folder | sweep of `lint_plan <dir>` over every folder under `.specfuse/features/` with a `PLAN.md` | **74 folders, 0 non-zero exits, 0 `ERROR:` lines** |
| 8 | `PLAN.template.md` and `/draft-feature` read `auto`; `close-discipline.md` §1 says the judge writes the verdict | six `grep -q`: `^autonomy_default: auto`, ``recommend `auto` ``, `You measure; the judge concludes`, each in both copies | **0** (6/6) |

Attempt 2's two judge findings, re-measured on this gate's own artifacts:

| Finding (attempt 2's judge, verbatim scope) | How re-measured here | Value |
|---|---|---|
| **#2 — `slice_wu_section` ended `## Measurements` at a `### Failure-class breakdown` child, so the bundle carried 62 of 87 non-blank lines.** T01H2 | `unittest …TestBundle.test_measurements_section_with_child_headings_is_captured_whole` | **0** (Ran 1, `OK`) |
| …and on attempt 2's retrospective, the file that finding was made against | `slice_wu_section(<attempt 2 RETROSPECTIVE.md>, "Measurements")` | **Fixed — 85 non-blank lines, the `### Failure-class breakdown` child inside the slice, `## Retrospective` outside it** |
| …does the whole slice then reach the bundle? | same file through `build_judge_bundle`, `len()` vs `JUDGE_MAX_EVIDENCE_CHARS` | **No — 9,605 chars capped to 8,029, middle elided, 77 of 85 lines.** T01H2 left the cap untouched and it is outside this WU's boundary; **this section is written under 8,000 chars so all of it reaches the judge** |
| **#1 — `entry_sha` was stamped at the first probe that ran T02H's code, `7e02525`, so the judge's range held 4 of the gate's 34 commits.** T02H2 | `unittest …TestGateStartSha.test_legacy_gate_reprobe_seeds_entry_sha_from_merge_base` and `::test_fresh_gate_first_probe_seeds_entry_sha_from_probe` | **0** and **0** (Ran 1, `OK` each) |
| …and on **this** gate? | read `GATE-01.md baseline`; read `write_gate_baseline` (`loop.py:4402-4410`) | **Unchanged — `entry_sha` still reads `7e0252555d94c4dd…`, byte-identical to attempt 2's `judged.diff_base`.** T02H2 seeds from the merge-base only when `entry_sha` is *absent*; a present one is carried forward untouched, by design, so today's re-probe (`probed_at: 2026-09-07T15:02:18Z`) left it. **This close's judge gets the diff base attempt 2's judge called defective** |
| …provenance of that sha, without git | `baseline.probed_at` vs every `attempt_outcome` timestamp in `events.jsonl` | `entry_sha` could not exist before T02H shipped the field at **16:51:21Z on 2026-09-06**, and T01–T02H all finished before that. The range covers T01H2, T02H2 and this close, and excludes the seven units before |

Other recorded values:

| Measurement | Command | Value |
|---|---|---|
| `PLAN.template.md`'s `autonomy_default` | `grep -m1 '^autonomy_default:' .specfuse/templates/PLAN.template.md` | **`auto`** (same in the vendored copy) |
| `judged` events in `events.jsonl` | `python3` read counting `event_type == "judged"` | **2** — attempt 1 (`not_met`/`not_met`, `lowered: false`, 1 finding); attempt 2 (`met`/`not_met`, `lowered: true`, 2 findings, `judge_cost_usd: 0.679098`) |
| `CHANGELOG.md` Unreleased entries tracing to this feature | `changelog.parse_changelog` + `closing_requirements.changelog_has_entry_for` | **5** (4 `added`, 1 `changed`), parse `ok: True`, `changelog_has_entry_for` **True** |
| Full suite | `python3 -m unittest discover -s tests -q` | **0** — `Ran 3744 tests in 150.081s`, `OK (skipped=3)` |
| Smoke test | `bash scripts/smoke-test.sh` | **0**, `smoke test: OK` |
| This feature's plan lint (the `plannext` gate) | `lint_plan <this feature dir>` | **0**, `OK — structurally valid` (3 `produces_driver_helper` WARNs on hygiene WUs) |

On this close's own `judged` event: it cannot read it — `judge_close` runs after
the closing guards, which run after this WU's squash. What the driver will do,
read from the dispatch site (`loop.py:8172`) and `judge_close`
(`loop.py:6586`): gate 1 is `gates[-1]`, `PLAN.md` carries no `judge_disabled`
key, and `GATE-01.md` has a resolvable `baseline.entry_sha`, so none of the
three early returns applies and a real `sonnet`/`medium` session is dispatched.
A **third** `judged` event will be appended to this feature's `events.jsonl`
with `close_verdict`, `judge_verdict`, `verdict`, `lowered`, `disagreed`,
`findings`, `diff_base` and `diff_base_source`. A reader confirms it there; this
close asserts nothing about what it will say.

### Failure-class breakdown

Read from `events.jsonl`'s `attempt_outcome` payloads in this session. Three
non-passing attempts across the gate, all one failure class, none in a hygiene
unit and none in this close.

| Failure class | Signature | Count | WU |
|---|---|---|---|
| `tests` | `test_doc_set_missing_for_retrospective_fails` | 2 | T03, attempts 1 and 2 |
| `tests` | `test_stat_survives_in_full_when_the_body_is_capped` | 1 | T04, attempt 1 |

Both T03 attempts carried the identical signature, tripping
`spinning_signature_repeat` and producing this gate's one `human_escalation`;
the operator's `re_arm_dispatched` note reads *"root cause found in test
isolation, not the code"*, and T03 passed on re-arm at $1.24. All four hygiene
units passed on their first attempt.

## Retrospective

### What the judge's evidence bundle lacked when the fixtures were built

Four gaps have been named across three attempts. Two are fixed and verified
here, one is fixed as a mechanism but still live for this gate, and one is a
deliberate scope boundary that stands.

**Fixed — a forbidden section with subheadings is fully redacted (T01H).**
Attempt 1 measured 100% of `## Retrospective`'s non-blank lines surviving into
the judge's prompt, because `strip_forbidden_sections` closed a redacted run at
the next heading of *any* level, so every `###` child re-opened the stream. T01H
made a run close only at a heading of the same or shallower level. A side
effect worth stating: this file's H1 is `# Retrospective — …`, a level-1
forbidden heading with nothing at level ≤ 1 after it, so the redaction now runs
to the next diff boundary and takes this whole file out of the diff. That is
over-redaction in the safe direction — the judge is handed `## Measurements`
through a separate bundle field — but it means the judge sees this file only
through that field, and therefore only within the 8,000-character cap.

**Fixed and verified on the file the finding was made against — the truncated
`## Measurements` slice (T01H2).** The judge that lowered attempt 2 found
`slice_wu_section` ending the section at its first `### ` child, carrying 62 of
87 non-blank lines. T01H2 applied T01H's level rule to the slicer. Re-measured
in this session on attempt 2's own retrospective: the slice now runs to the next
`##` and carries all 85 non-blank lines including the `###` child. What T01H2
did *not* change is `JUDGE_MAX_EVIDENCE_CHARS = 8000`: that same section is
9,605 characters and is still capped to 8,029 with the middle elided. This
close's `## Measurements` is written under the cap so all of it reaches the
judge — a workaround, not a fix, and `judge.py` is outside this WU's boundary.

**Fixed as a mechanism, still live for this gate — the diff base (T02H, T02H2).**
Attempt 1 found `resolve_gate_start_sha` returning a `baseline.sha` a post-halt
re-probe had overwritten. T02H added `entry_sha`; attempt 2's judge then found
that `entry_sha` itself had been stamped at the first probe that ran T02H's own
code, so the range held 4 of the gate's 34 commits. T02H2 makes a gate that
carries a baseline but no `entry_sha` seed it from the merge-base instead, and
both its tests pass. But `write_gate_baseline` carries a *present* `entry_sha`
forward untouched — correctly, since overwriting it is the bug T02H fixed — so
this gate keeps `7e02525`, and today's re-probe left it in place. **The judge
reading this close gets the same diff base its predecessor called defective.**
Minting a different value into `GATE-01.md` to make this close look better is
exactly the substitution `result-contract.md` §6 forbids, and the merge-base is
not computable from a session that may run no git command, so the value stands
and is measured instead. What the fixtures could not see is precisely this:
`_write_feature` scaffolds a gate whose baseline is written by a probe that
really is the first one, which is the happy path and the only path a fixture
has.

**Unchanged and deliberate — the judge is told to re-run oracles but not which
command.** The prompt says *"Re-run every oracle a criterion names"*, and the
criteria come from `GATE-NN-CRITERIA.md`. This feature has none, so
`_render_criteria` emits its fallback and the judge infers the oracles from the
definition of done and from `## Measurements`. `PLAN.md` § Scope boundary puts
the feature-level oracle in FEAT-2026-0101, drafted *"after this lands so the
judge has something binary to read."*

### Were the eight behaviours demonstrable without a live `gh` or a network call?

Yes, all eight, and no demonstration in this session made either. The five
close-path behaviours run the real driver end to end with `run_judge_session`
replaced by a Python callable, which is the seam `judge_close` looks up on the
module at call time. The cost-folding behaviour injects a usage envelope of the
shape `dispatch` produces. The lint behaviours are a pure function over files on
disk, and the negative observation ran against a fixture feature directory built
in this session under `$TMPDIR` with two controls. The template/rule behaviour is
six `grep`s. `GATE-01.md`'s escalation trigger — *"Emit `status: blocked` if a
fixture demonstration needs a live `gh` or a network call"* — was never
approached.

The one environmental dependency worth recording is the opposite of a network
call: the tool sandbox's deny-list over the agent session-env directory makes the
five `loop.run` demonstrations exit `SystemExit` before any judge code runs. This
is the seventh close in this repository to hit it.

### What this close did not do

It did not touch `_wu_sections.py`, `judge.py`, `loop.py` or any test. The two
remaining defects — the 8,000-character cap on the measurements slice, and this
gate's un-reseedable `entry_sha` — are in code and data this WU's *Do not touch*
puts outside its boundary, and a close that repairs the mechanism it is
measuring has stopped being a measurement.

It also did not re-file follow-ups. `FOLLOW-UPS.md` is absent from this folder;
the attempt-1 and attempt-2 records are the `followups_recorded` events and
issues #3250–#3252. Attempt 2's own two findings were **not** filed as new
issues — `file_followup_issues` keyed each entry by position, so they matched
attempt 1's markers and deduplicated away. That was found, fixed under #3253 and
is in `CHANGELOG.md`'s Unreleased `Fixed` section; the findings themselves were
not lost, because T01H2 and T02H2 carry them verbatim in their `provenance:`
lines.

## Cost analysis

Every "spent" figure is read from this feature's `events.jsonl`
`attempt_outcome` payloads in this session. **`planned_cost_usd` is `$40.00` in
`PLAN.md` today, and the per-WU sum is the same `$40.00`** (T01 $5, T02 $7,
T03 $3, T04 $5, T05 $3, T01H $3, T02H $4, T01H2 $2, T02H2 $2, G1-CLOSE $6), so
both readings reconcile against one number. **This close's own acceptance
criterion names `$29.00`**, which was the per-WU sum before any hygiene unit
existed (the six units T01–T05 and the close); four hygiene units totalling
$11.00 have been added to the graph since, two after each of the first two close
attempts. Both figures are named rather than one silently substituted.

| WU | Attempts | Planned | Spent | Delta |
|---|---|---|---|---|
| T01 | 1 | $5.00 | $2.87 | −$2.13 |
| T02 | 1 | $7.00 | $8.73 | **+$1.73** |
| T03 | 3 | $3.00 | $3.66 | **+$0.66** |
| T04 | 2 | $5.00 | $8.03 | **+$3.03** |
| T05 | 1 | $3.00 | $0.99 | −$2.01 |
| T01H | 1 | $3.00 | $0.68 | −$2.32 |
| T02H | 1 | $4.00 | $0.81 | −$3.19 |
| T01H2 | 1 | $2.00 | $0.52 | −$1.48 |
| T02H2 | 1 | $2.00 | $0.80 | −$1.20 |
| **T01–T02H2** | **12** | **$34.00** | **$27.10** | **−$6.90** |
| G1-CLOSE | 2 recorded | $6.00 | $17.26 (attempts 1–2; this one unrecorded) | **+$11.26 so far** |
| **Feature** | **14** | **$40.00** | **$44.36 recorded** | **+$4.36 recorded** |

**Delta, named: +$4.36 against `PLAN.md`'s $40.00, or +$15.36 against the
criterion's $29.00, with this third close attempt still unrecorded.** The driver
writes this attempt's `attempt_outcome` after the RESULT block, so the total
understates the truth by one close session and one judge session. T03 shipped
`fold_judge_usage`, so a judge's spend is added into the close's `cost_usd`
before it is written: the two recorded close attempts' $8.3157 and $8.9427
include $0.2201 and $0.6791 of judge, **$0.8992 of judging in total**, each also
carried separately in its `judged` event. Against `GATE-01.md`'s
`cost_budget_usd: 65.00`, this attempt began with $20.64 of headroom.

**Restart count: seven** — `driver_staleness_detected` with `halted: true` after
T01, T02, T03, T01H, T02H, T01H2 and T02H2, plus two non-halting summary events
at the two gate boundaries already reached. `PLAN.md` § Notes predicted *"a
`driver_restart_required` halt after each of T01 through T05"* — five. Seven
happened, and not on the predicted units: T04 and T05 touched rules, templates,
skills and docs, and the staleness rule counts modules under `specfuse/loop/`
the running process has imported, which neither diff reached; all four hygiene
units did edit a loaded module and all four halted. The prediction was right
about the count of driver-editing units and wrong about which ones they were,
which is the same undercount as T04's.

**Where the money actually went.** The close is the overrun. Three close
attempts against a $6.00 plan is $17.26 and climbing, 39% of the feature's
recorded spend, and every dollar of it after attempt 1 was spent re-measuring a
gate whose substantive code was already done — because the judge kept finding
defects in the *evidence bundle* rather than in the work. Against that, the four
hygiene units authored from those findings came in at **$2.81 against $11.00
planned, one attempt each, no failures**. The mechanism this feature ships is
cheap to obey and expensive to have needed: a precisely-scoped WU carrying a
`provenance:` line that names the measurement which produced it is the cheapest
work in this feature by a wide margin, and re-running a full close to prove the
fix is the most expensive.

## Consumer-visible contract changes

Five, all additive, unchanged from attempt 2 — T01H2 and T02H2 fix unreleased
code inside these same five entries and add no sixth. Enumerated here and
present in `CHANGELOG.md`'s `Unreleased` section, classified per
`specfuse/loop/changelog.py`'s schema and carrying this feature's ID; verified
in this session by `parse_changelog`, which reports 5 entries tracing to
`FEAT-2026-0100` (4 `added`, 1 `changed`) and `ok: True`.

1. **A judge session now runs on every terminal close, and its verdict is the
   one that stands when it is lower.** After a terminal close's squash passes
   the closing-deliverable guards and before the verdict is re-read for the
   terminal flips, the driver dispatches a fresh `sonnet`/`medium` session that
   receives the gate's definition of done, the `GATE-NN-CRITERIA.md` entries,
   the gate's diff and the close's `## Measurements` — and not the close's own
   Verdict or Retrospective prose, which is stripped even out of diff hunks. A
   judge may lower `met` to `not_met`, which rewrites the close WU's `verdict:`
   field and files `FOLLOW-UPS.md` from its own findings verbatim; it may never
   raise a `not_met`. A timeout, an unparseable answer, an unresolvable diff
   base or a defect in the judge path all fail open with the close's verdict
   standing. Consumers see a second session's cost on every terminal close, and
   a close's `verdict:` that can change after the close session ended. *(added)*
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
   project with a drafted-but-unarmed close carrying such a sentence will see
   its plan lint go red — as this repository's own corpus did on FEAT-2026-0082
   until the operator repaired that body between attempts 1 and 2. *(added)*

**This section requires explicit human acknowledgment** (`close-discipline.md`
§3). It is presented for that acknowledgment at gate review; nothing in this
close treats the list as acknowledged.

## Lessons

One entry, already in `.specfuse/LEARNINGS.md` under *FEAT-2026-0100/G1-CLOSE —
a satisfiability answer that was reasoned about instead of run*, appended by
attempt 1 and unchanged: **when a plan's § Escalation-predicate satisfiability
answer rests on a claim about the existing corpus, that claim is a command with
an output, and the command must be run and its output pasted at drafting time —
a plan that reasons its way to "zero" is asserting a measurement it never took.**
The corpus sweep reports zero for real, on 74 folders, in this session.

Beyond that entry, nothing generalizes from this attempt. The 8,000-character
cap on the measurements slice and this gate's un-reseedable `entry_sha` are
defects in this feature's own code and data rather than rules; the sandbox
deny-list over the agent session-env directory and T04's mirrored-file
undersizing are recorded above as feature-specific findings; and the one result
that reads like a rule — hygiene units authored from a judge's findings came in
at a quarter of their planned cost — is four units in one feature, which is an
anecdote until the post-merge checklist has five features of judge data behind
it.

## Verdict

**`met`**, advisory. All eight behaviours in `GATE-01.md`'s definition of done —
stated there as *"behaviours demonstrable on fixtures with an injected runner"* —
were re-demonstrated in this session and every one exited 0, including the lint
rule as a negative observation against two controls, the corpus sweep at 0 ERROR
over 74 folders, and the redaction measured on this file inside a three-file
diff at 0 of 310 non-blank lines carried with both code halves intact. The full
suite reports `OK` on 3,744 tests and `scripts/smoke-test.sh` exits 0, both
re-run fresh and unsandboxed.

The two findings that lowered attempt 2 are not equally resolved, and the
difference is in `## Measurements` rather than settled here. The slicing finding
is fixed and verified on the very file it was made against: all 85 non-blank
lines of that `## Measurements`, `###` child included, now reach the slice. The
diff-base finding is fixed as a mechanism — both of T02H2's tests pass — but
**this gate still carries the same `entry_sha` the previous judge called
defective**, because a present `entry_sha` is deliberately never overwritten and
the merge-base cannot be computed from a session that may run no git command.
Whether a gate whose *shipped mechanism* is correct but whose *own data* is not
meets a definition of done written about fixtures is the question this close
does not answer.

Two constraints on the bundle remain and are the judge's to weigh: the
measurements slice is still capped at 8,000 characters — this section fits under
it by construction, which is a workaround a close author who does not know the
cap will not repeat — and this file's level-1 `Retrospective` heading redacts the
whole file out of the diff, so `## Measurements` reaches the judge only through
the bundle field. Neither is repairable inside this WU's boundary.

This verdict is advisory. `close-discipline.md` §1 as T04 rewrote it puts the
decision with a session that did not do this work, and that session may lower it.
