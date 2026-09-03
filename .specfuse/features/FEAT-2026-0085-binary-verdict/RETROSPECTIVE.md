# Retrospective — FEAT-2026-0085, binary verdict

## Gate 1

Gate 1 is the only gate. Five substantive units (T01–T05) and this close, all
serial because every unit edits `specfuse/loop/`. All five are `done`; the five
behaviours in `GATE-01.md`'s definition of done were demonstrated on fixtures in
this session and the three oracles were re-run fresh. **Verdict: `met`.**

This close is the first one bound by the rule T05 wrote. It is therefore also a
test of that rule: the verdict below is `met` because every criterion was
demonstrated, not because the alternative was expensive.

## Measurements

Every "after" figure below is a command run in this session, not a claim
inherited from a producing WU. Every "before" figure is `PLAN.md` § Notes'
recorded baseline, taken before T01 ran. `__pycache__` / `*.pyc` are excluded
from all greps: they are gitignored build artifacts this session's own Python
runs created.

| Measurement | Command run in this session | Before | After |
|---|---|---|---|
| `VERDICT_VALUES` size | `python3 -c "from specfuse.loop import closing_requirements as c; print(sorted(c.VERDICT_VALUES))"` | 4 members | **2** — `frozenset({"met", "not_met"})` |
| `LEGACY_VERDICT_VALUES` size | same | did not exist | **2** — `frozenset({"met_locally", "partially_met"})`, read-only |
| Files naming `met_locally` | `grep -rl "met_locally" specfuse/ plugins/ docs/ .specfuse/rules .specfuse/templates tests/` | 38 files | **12** files |
| Files naming `met_locally` or `partially_met` | `grep -rl "met_locally\|partially_met" specfuse/ plugins/ docs/ .specfuse/rules .specfuse/templates tests/` | not measured at baseline | **14** files |
| … of those, in `.specfuse/rules`, `.specfuse/templates`, `.specfuse/skills`, `plugins/` | `grep -rl "met_locally\|partially_met" .specfuse/rules .specfuse/templates .specfuse/skills plugins/` | (not isolated) | **0** files (`grep` exit 1) |
| … of those, in `specfuse/` | `grep -rl "met_locally\|partially_met" specfuse/` | (not isolated) | **3** files — exactly the legacy-tolerance surface `GATE-01.md` names |
| … of those, in `docs/` | `grep -rl "met_locally\|partially_met" docs/` | (not isolated) | **1** file — `docs/methodology.md`, all hits inside § Migrating a hedged close |
| Test files referencing hedge machinery | `grep -rlE "met_locally\|partially_met\|HEDGED_VERDICT_VALUES\|FOLLOW_UP_KIND\|verdict_ceiling_for_kinds\|accept.hedged.close\|Hedged-verdict follow-up" tests/` | 22 files | **10** files |
| Closing requirements in the registry for `wu_type: close` | `python3 -c "from specfuse.loop import closing_requirements as c; print(sorted(r.id for r in c.CLOSING_REQUIREMENTS['close']))"` | included `close-g`, `close-j` | **11** — `close-g` and `close-j` gone, `close-m` added |
| Standing hedged closes in this repository | `grep -l "^verdict: met_locally\|^verdict: partially_met" .specfuse/features/*/WU-9*.md` | 6 | **6** (unchanged by design — legacy values stay readable) |
| … same, counting `PLAN.md` copies of the field | `grep -rl "^verdict: met_locally\|^verdict: partially_met" .specfuse/features/` | 8 | **8** |
| Feature folders reporting a lint ERROR | `for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done \| grep -c "^ERROR"` | 0 | **0** across 73 folders |

### The 6 standing hedged closes, listed

| File | `verdict:` | `type:` |
|---|---|---|
| `FEAT-2026-0016-attempt-outcome-rearm-contract/WU-90-gate-3-close.md` | `met_locally` | `close` |
| `FEAT-2026-0018-auto-close-predicate/WU-90-gate-3-close.md` | `met_locally` | `close` |
| `FEAT-2026-0020-public-readiness-prep/WU-90-gate-1-close-intermediate.md` | `partially_met` | `close-intermediate` |
| `FEAT-2026-0024-hashed-denylist-leak-guard/WU-90-gate-1-close-intermediate.md` | `partially_met` | `close-intermediate` |
| `FEAT-2026-0032-windows-native/WU-92-gate-2-close.md` | `partially_met` | `close` |
| `FEAT-2026-0039-monitoring-schema/WU-92-gate-2-close.md` | `met_locally` | `close` |

Plus two `PLAN.md` files (`FEAT-2026-0016`, `FEAT-2026-0018`) carrying the same
retired value in a feature-level `verdict:` field. All eight are `status: done`
and none reports a new lint error — verified above: the corpus-wide sweep is
zero ERROR with T01's narrowing in place, which is the satisfiability claim
`PLAN.md` § Escalation-predicate satisfiability made before arming.

### The five fixture demonstrations

Scripts are throwaway drivers in `$TMPDIR/close-demos/`, written and run in this
session; they call the real functions on temp-directory fixtures. Two
sub-behaviours (`halt_for_human_unit`'s no-dispatch seam, and the terminal-close
guards after an auto-closed predecessor) run `git` internally, which a dispatched
session may not; those are demonstrated by the repo's own end-to-end tests,
invoked by nodeid in this session and recorded with their own exit status.

| # | Behaviour from `GATE-01.md` | Command run in this session | Exit |
|---|---|---|---|
| 1 | A close writing `met_locally` is refused naming the two legal values; `not_met` without `FOLLOW-UPS.md` is refused; `not_met` with one entry per failed criterion passes, flips nothing, and files one issue per entry through an injected runner carrying the label and the entry body verbatim | `python3 $TMPDIR/close-demos/demo1_verdict.py` | **0** (26 checks) |
| 1′ | same, via the repo's own suite | `python3 -m unittest tests.test_binary_verdict tests.test_followups_artifact tests.test_terminal_flips` | **0** (41 tests, `OK`) |
| 2 | An auto-closed gate's stub carries no `deferred:` line and no `autoclose-debt` marker; a terminal close after an auto-closed predecessor needs no "What the loop did NOT verify" section | `python3 $TMPDIR/close-demos/demo2_autoclose.py` | **0** (20 checks) |
| 2′ | same, incl. the git-based terminal-close guards | `python3 -m unittest tests.test_autoclose_stub_states_what_passed tests.test_autoclose_deferral_visibility tests.test_dispatch_skeleton` | **0** (24 tests, `OK`) |
| 3 | A `type: human` unit halts the driver without a dispatch and prints the six-part brief; `done` + `evidence:` lets the next unit dispatch; `done` without `evidence:` is a lint ERROR | `python3 $TMPDIR/close-demos/demo3_human.py` | **0** (20 checks) |
| 3′ | the no-dispatch seam, end to end | `python3 -m unittest tests.test_human_work_unit` | **0** (4 tests, `OK`) |
| 4 | `grep -rl "met_locally\|partially_met"` names zero files in the scaffold surfaces and only the legacy-tolerance surface elsewhere | `python3 $TMPDIR/close-demos/demo4_grep.py` | **0** (13 checks) |
| 5 | The full suite is green and `specfuse lint` reports the same ERROR count as before this gate | `python3 -m unittest discover -s tests -q` | **0** — `Ran 3620 tests in 144.410s / OK (skipped=1)` |
| 5 | | `bash scripts/smoke-test.sh` | **0** — `smoke test: OK` |
| 5 | | `for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done` | **0 ERROR** across all 73 feature folders |

Every row above was re-run after this close wrote `RETROSPECTIVE.md`,
`CHANGELOG.md` and `.specfuse/LEARNINGS.md`, so the exit statuses are the state
of the tree the driver will squash, not the state before the close's own edits.
The four demo scripts, the full suite, `scripts/smoke-test.sh`, the corpus lint
sweep and `specfuse lint --closing` were all re-run at that point and all
reported the same result.

What demonstration 1 asserted about the issue filing, specifically, because it is
the part a reading of the source cannot establish: two `### `-headed entries
produced exactly two `gh issue create` invocations; each argv carried
`--label specfuse:follow-up`; each `--body` compared **equal** to the entry text
`parse_followup_entries` returned, byte for byte; each `--title` carried its
`FEAT-…-followup-N` correlation id; a `followups_recorded` event was written with
`filed: 2, unfiled: 0`; and a second call against a runner that reports the issues
as already open filed nothing new. Across the same fixture, `fire_terminal_flips`
returned `[]` and the gate stayed `awaiting_review`, `PLAN.md` stayed `active`,
and the roadmap row stayed `active`.

Two notes on where the suite ran. The first full-suite run, inside the sandbox,
reported 91 errors sharing one signature —
`PermissionError … '<HOME>/.claude/session-env'`, raised by the
driver's own `require_session_env_writable` preflight, whose message says
"re-run outside the sandbox". That is a report about the sandbox, not about the
repository (`result-contract.md` §7); the run recorded above is the unsandboxed
re-run. Separately, `specfuse lint` here means
`python3 -m specfuse.loop.lint_plan`, not the `specfuse` on `PATH`: that binary
warns it is measuring the installed pipx build rather than this checkout.

### Failure-class breakdown

Ten dispatched attempts across T01–T05; **five did not pass**, read directly from
`events.jsonl` in this session.

| Outcome | `failure_class` | Count | Signature |
|---|---|---|---|
| `blocked` | (none — agent-reported) | 2 | T01: AC3 vs. the vendored mirror; T02: the fifth reader of the debt marker |
| `files_changed_mismatch` | `files_changed_mismatch` | 1 | `tests/test_hedged_kind_contract.py` declared, unchanged |
| `deliverable_missing` | `guard_refusal` | 1 | `assert_declared_deliverables` — `tests/test_autoclose_stub_states_what_passed.py` |
| `failed` | `tests` | 1 | `test_run_does_not_flip_on_not_met_verdict` |

These are *recorded* attempts, and the count is a lower bound on real cost: the
driver's own helper cannot produce this table. `summarize_attempt_failure_classes(feature_dir, gate_n=1)`
returns `(no non-passing attempts in scope)` for this feature, because it buckets
by `_gate_number_from_wu_id`, which resolves `G<n>-CLOSE` ids and returns `None`
for substantive ids like `FEAT-2026-0085/T01` — every one of the five is silently
filtered out. That is the degradation `[FEAT-2026-0016/G3-CLOSE]` already records
in `LEARNINGS.md`; this feature is its second observation, and the table above was
built by reading `events.jsonl` directly rather than trusting the helper.

## Retrospective

### Which of the 42 standing hedged closes in the field this repository owns, and what the migration note would have each do

This repository owns **6 of the 42** — the table above. `docs/methodology.md`
§ Migrating a hedged close offers two routes; applied per close, and using the
note's own `kind:` translation table:

- **`FEAT-2026-0016/G3-CLOSE` (`met_locally`) → Route B.** The hedge covered two
  scope-deferred items the retrospective names: predicate v2, explicitly left to
  a future feature by `PLAN.md` § Scope OUT, and the `_gate_number_from_wu_id`
  gate-bucketing degradation. The first was never an acceptance criterion (old
  `kind: inherent` — the note says delete it from the criteria and say so); the
  second is a real, still-open defect and is the one `FOLLOW-UPS.md` entry this
  migration would write. This close re-observed it, above.
- **`FEAT-2026-0018/G3-CLOSE` (`met_locally`) → Route A.** The single open item
  is "one event observation in a future feature's gate close" — a terminal gate
  landing on-plan, the close WU's dispatch skipped, an `auto_close_decision`
  event with `auto: true` at the in-loop call site. That re-run condition is
  reachable today against any on-plan terminal gate since closed, so the note
  says run it, read the exit, edit `verdict:` to `met`, and fire the flips with
  `specfuse run --recheck-verdict FEAT-2026-0018`.
- **`FEAT-2026-0032/G2-CLOSE` (`partially_met`) → Route B, then `PLAN.md`.** Every
  open item is "unverified on real Windows (post-merge manual)" — old
  `kind: externally-verifiable-later`, needing an environment the loop does not
  have. The note routes that to a `## Post-merge checklist` line in `PLAN.md`,
  filed as one `specfuse:post-merge` issue, and *not* to an acceptance criterion.
- **`FEAT-2026-0039/G2-CLOSE` (`met_locally`) → split across all three channels.**
  This is the only one of the six carrying a full `## Hedged-verdict follow-up
  record`, and its four entries land in three different places under the new rule:
  FU-1 (an operator must run `/derive-monitoring` against a real project and
  confirm the discovered components) is old `kind: acceptance-discharged` and
  becomes a `type: human` unit placed before the close; FU-4 bundles into it.
  FU-2 (the "before" measurement of the `code` gate set, unreachable because a
  close cannot run `git`) is a `FOLLOW-UPS.md` entry, and its own stated durable
  fix — have the driver record the gate-set result at dispatch time — is the
  better repair. FU-3 (the provider-agnostic boundary, which holds only if
  FEAT-2026-0040 ships without patching it) is `kind: externally-verifiable-later`
  in another feature: a `FOLLOW-UPS.md` entry linking 0040.
- **`FEAT-2026-0020/G1-CLOSE-INTERMEDIATE` and
  `FEAT-2026-0024/G1-CLOSE-INTERMEDIATE` (both `partially_met`) → neither route
  applies, and that is a gap in the note.** Both are `close-intermediate` WUs on
  features whose *terminal* closes have long since landed (0024's `G2-CLOSE` is
  `verdict: met`; 0020's `G2-CLOSE` carries no `verdict:` field at all). Route A
  ends in `--recheck-verdict`, which fires **terminal** flips; there are none to
  fire for an intermediate gate, and the feature is already `done`. Route B ends
  in a feature-level `FOLLOW-UPS.md` the driver would file issues from — for work
  that closed months ago. The note's finder,
  `grep -l … .specfuse/features/*/WU-9*.md`, matches `WU-90-gate-1-close-intermediate.md`
  just as readily as a terminal close, so an operator following it lands on two
  files with no instruction that fits. The honest answer for both is **leave
  them**: they are sealed history, they are readable, they produce no lint error,
  and 0024's retrospective already records the operator's own upgrade to `met`
  in prose. The note should say so — that is the one thing this close would
  change about T05's migration section, and it is recorded here rather than
  fixed, because `docs/` is this WU's *Do not touch*.

Read together, the six are the survey's proportions in miniature: two would have
been a `type: human` unit or a post-merge line, one is a genuine unfinished
follow-up, one is discharge-and-record, and two should never have carried a
verdict field the migration reads at all.

### Was the `human` unit's brief printable from real unit text?

**Yes.** `format_human_unit_brief` was rendered in this session against a real
work-unit file read from disk — `WU-04-human-work-unit-type.md`, this feature's
own T04 — with no fixture text substituted. All six headings from
`escalation.py`'s `_PART_HEADINGS` appear, in order, as the only `## ` headings
in the output. Part 3 carried that unit's `**Objective.**` verbatim; the unit's
1,111-character acceptance-criteria block was quoted verbatim; the headline
carried the real WU id and title; parts 1 and 3 named the real done-set and the
real remaining set from run state; part 5 offered three options each with `Pros:`
and `Cons:`; part 6 recommended one. Nothing in the brief was a placeholder
(`TODO` / `TBD` / `<fill` all absent).

The qualification worth stating: **no `type: human` unit exists anywhere in the
corpus yet**, so "real unit text" here means a real implementation unit's
sections, which is exactly the text a human unit carries — `lint_plan`'s
`HUMAN_REQUIRED_SECTIONS` is `{Objective, Context, Acceptance criteria}`, a
subset of what every unit already writes. The brief has never been printed by an
actual halt on a real feature. The mechanism is verified; the first field use is
still ahead of it, and the sensible place to find out is FEAT-2026-0039's FU-1,
which is the corpus's clearest candidate for the first one.

### What this feature does not fix, said once

A close can still write `met` on a feature that is not wired end to end. Making
the verdict binary removes the polite way to avoid saying so; it does not add an
oracle that would catch it. That is the feature oracle's job, and it comes after
the judge — unchanged from `PLAN.md` § Notes.

### Three stale prose references this close found and did not fix

Named rather than silently carried, and none of them fails `GATE-01.md`'s grep
bullet, which is scoped to the two retired verdict values:

- `.specfuse/rules/operator-escalation.md:131` still offers
  "`/accept-hedged-close`'s reason line" as a live example of a field recording
  why a human accepted something. The skill no longer exists. (Line 150's mention
  is past-tense provenance and is correct as written.)
- `docs/dev/leak-scan-content-action.md:93` refers to
  `## What the loop did NOT verify`, a heading T02 retired.
- `tests/test_derive_monitoring_discovery.py:475,951` — two comments referring to
  the same retired heading.

All three are in this WU's *Do not touch* (rules, docs, tests — T01–T05 own
them). They are inert, not wrong-in-effect, and each is a one-line edit for
whoever next opens the file.

## Cost analysis

`planned_cost_usd` is declared per-WU and sums to **$35.00**, which is also
`PLAN.md`'s feature-level figure: T01 $8, T02 $4, T03 $6, T04 $6, T05 $6, and
this close $5.

| WU | Attempts | Planned | Spent | Delta |
|---|---|---|---|---|
| T01 | 3 | $8.00 | $19.67 | **+$11.67** |
| T02 | 3 | $4.00 | $5.13 | +$1.13 |
| T03 | 2 | $6.00 | $6.82 | +$0.82 |
| T04 | 1 | $6.00 | $11.09 | **+$5.09** |
| T05 | 1 | $6.00 | $7.33 | +$1.33 |
| **T01–T05** | **10** | **$30.00** | **$50.03** | **+$20.03 (+67%)** |
| G1-CLOSE | 1 (this one) | $5.00 | not yet in `events.jsonl` | — |

**Delta, named: +$20.03 over the $30.00 planned for T01–T05, and +$15.03 over the
whole feature's $35.00 with this close's own attempt still to be recorded.** The
driver writes this close's `attempt_outcome` after the RESULT block, so the
figure above is the complete picture of everything measurable at close time and
understates the feature total by exactly one attempt.

Where the overrun is: **T01 alone is 58% of it.** Its first attempt ($6.52) ended
`blocked` on the vendored-mirror contradiction and was discarded on re-arm; the
re-armed attempt 1 ($5.92) was refused for a declared-but-unchanged path; only
attempt 2 ($7.23) passed. T04 is the second-largest at +$5.09 and is a plain
estimate miss, not rework — one attempt, passed first try, on the largest new
mechanism in the feature (a work-unit type, a run-loop halt seam, a six-part
brief renderer, and a lint rule). The remaining three units together are +$3.28,
which is estimating noise. Two of the three units estimated at $6 came in over,
and the one estimated at $8 came in at $19.67; the calibration lesson is not
"raise the estimates" but "a unit whose criterion is a repo-wide grep has an
unbounded blocked-attempt tail", which is this close's one `## Lessons` entry.

**Restart count, named: 4** `driver_restart_required` halts — after T01, T02,
T03 and T04, each emitted as a `driver_staleness_detected` event with
`halted: true`. `GATE-01.md` § Arming discipline predicted **five**, one per
unit, on the reasoning that every unit edits `specfuse/loop/`. T05 did not
produce one: its writes landed in `specfuse/loop/data/` (shipped rules, docs and
templates) and in `docs/`, `plugins/` and `.specfuse/`, none of which is driver
code the running process has already imported. The prediction was one restart too
pessimistic, for a reason worth keeping: *shipped data under the driver package
is not driver code*.

Two further halts, neither a restart:

- **The baseline halt.** Before any unit was dispatched, the gate-entry probe
  reported three pre-existing failures on the integration branch
  (`test_real_tree_is_clean_on_all_four_invariants`, the coverage gate, and a
  `roadmap-link-gate` ERROR about this feature's own `**Status: planned.**`
  marker). Zero work units were dispatched and zero dollars were spent; the halt
  was cleared out of band before T01 started.
- **The budget halt.** After T05 passed, cumulative gate spend of $50.03 crossed
  the then-declared $45.00 gate budget and the driver halted in front of this
  close with `gate_budget_exceeded`. The operator reopened gate 1 at
  `cost_budget_usd: 60.00` and re-probed the baseline clean. This close runs with
  $9.97 of headroom under the reopened budget.

Two re-arms, both recorded with a reason: T01 ("AC3 rescoped to Python files,
mirror is T05's") and T02 ("spec widened to include the lint reader"). Both
re-arms followed an agent-reported `blocked` that was correct — in each case the
work unit as written could not be satisfied without violating its own *Do not
touch*, and the agent said so instead of guessing. Those two blocks cost $7.64
between them and are the cheapest line items in this feature: the alternative was
three attempts each spent working around a boundary.

## Consumer-visible contract changes

Not `n/a`. **Every consumer of this scaffold is affected** — the contract is the
loop itself, so a target repository inherits all of the following on its next
`specfuse upgrade`, whether or not it has ever hedged a close.

1. **`VERDICT_VALUES` is narrowed from four members to two**, `met` and
   `not_met`. `assert_verdict_well_formed` (`close-d`) refuses a retired value on
   any close dispatched from now on, with a message that names both legal values
   *and* `docs/methodology.md` § Migrating a hedged close, rather than only
   reporting "not in `VERDICT_VALUES`". **Reading a retired value still works**:
   `LEGACY_VERDICT_VALUES` keeps `load_wu` and `recheck_terminal_verdict` parsing
   the 42 standing hedged closes, and `lint_plan` validates `verdict` only on a
   non-`done` close, so no standing feature reports a new error. This is a
   breaking change to what a close may **write**, not to what the loop can read.
2. **`close-j` is removed.** FEAT-2026-0059's requirement that every entry in a
   hedged-verdict follow-up record carry a `kind:` from a closed four-value set
   goes with the record it validated. A close that used to fail this lint now has
   nothing to fail.
3. **`close-g` is removed.** The auto-close debt reconciliation check
   (`assert_autoclose_debt_reconciled`) is gone, along with
   `build_autoclose_debt_enumeration`, the `## What the loop did NOT verify`
   deferral heading, the `specfuse:autoclose-debt` marker, and `lint_plan`'s
   `check_autoclose_debt_prediction`. An auto-closed gate's `RETROSPECTIVE.md`
   stub now states what the driver's gates proved — one line per substantive unit
   naming the gate set it passed — instead of re-listing every acceptance
   criterion as debt. A terminal close after an auto-closed predecessor no longer
   owes a deferral section.
4. **`close-m` is added.** A close whose `verdict:` is `not_met` must carry
   `FOLLOW-UPS.md` in its feature folder with at least one `### `-headed entry;
   an absent file or an entry-less one is refused as
   `closing_deliverable_missing`, pre-squash and by `specfuse lint --closing`.
5. **`FOLLOW-UPS.md` is a new artifact with a new contract.** One `### ` entry per
   failed criterion, carrying the criterion verbatim, the evidence, and the re-run
   condition. After the close passes, the driver files one tracked issue per entry
   and writes the number back; `gh` being absent or failing leaves the file itself
   as the record and the driver never deletes or rewrites it.
6. **`type: human` is a new work-unit type.** The driver never dispatches one: it
   halts in front of it, flips the unit to `blocked_human`, prints the six-part
   operator brief, and disables auto-close for that gate. The operator marks it
   `done` with `evidence:` (`/unblock-wu --done --evidence "…"`) and the run
   resumes. A `done` `human` unit with no non-empty `evidence:` is a **lint
   ERROR**. A `human` unit carries three mandatory sections, not five.
7. **`/accept-hedged-close` is removed**, with no replacement and no path that
   softens a verdict to get past `/wrap-feature`'s refusal. `--recheck-verdict`
   stays as the one out-of-band caller of `fire_terminal_flips` and is how a
   migrated close gets its flips.
8. **Two new labels**, both registered in `labels.py`: `specfuse:follow-up` (one
   issue per `FOLLOW-UPS.md` entry, on `not_met`) and `specfuse:post-merge` (one
   issue for `PLAN.md`'s optional `## Post-merge checklist` section, on `met`).

`close-discipline.md` §2, `docs/methodology.md` §3, the glossary, the lifecycle
diagram and `WU.template.md` are rewritten to match.

**Reconciliation with `CHANGELOG.md`.** The same eight items appear in
`Unreleased` under two entries, both tracing `FEAT-2026-0085`: T05's `breaking`
entry covers items 1, 4, 5, 6, 7 and 8, and this close appended a `changed` entry
covering items 2 and 3 — the auto-close stub change and the removal of `close-g`
and `close-j` — which T05's entry did not carry. Writing it is
`close-discipline.md` §3's own instruction to the close ("also append it to
`CHANGELOG.md`'s `Unreleased` section"), and the omission is precisely the shape
`[FEAT-2026-0058/G1-CLOSE/a-close-wus-do-not-touch-must-permit-its-own-binding-obligations]`
warns about: `close-k` fires only on a **missing** trace, never on an
**incomplete** enumeration, so a partial list passes clean and looks identical to
a complete one. `parse_changelog` reports the document clean with both entries
classified and traced.

**This section requires explicit human acknowledgment** (`close-discipline.md`
§3). It is presented for that acknowledgment at gate review; nothing in this
close treats the list as acknowledged.

## Lessons

One entry, appended to `.specfuse/LEARNINGS.md` under
*FEAT-2026-0085/G1-CLOSE — grep-shaped criteria and vendored mirrors*: **a "zero
matches under `<path>`" acceptance criterion must be scoped to the paths the WU
is authorized to edit, and a canonical file and its byte-synced vendored mirror
are one editable unit that belongs to one WU.** T01 and T02 both blocked on that
shape, $7.64 and two re-arms between them, and the entry gives the arming-time
check: intersect the grep's path set with the WU's authorized touch-set and write
the intersection into the criterion.

Nothing else here generalizes. The migration-note gap for `close-intermediate`
WUs and the `_gate_number_from_wu_id` bucketing degradation are recorded above as
feature-specific findings; the latter is already a `LEARNINGS.md` rule from
`[FEAT-2026-0016/G3-CLOSE]` and is not repeated.

## Verdict

**`met`.** All five behaviours in `GATE-01.md`'s definition of done were
demonstrated on fixtures in this session, each with a recorded exit status; the
full suite reports `OK` on 3,620 tests, `scripts/smoke-test.sh` exits 0, and
`specfuse lint` over every feature folder reports zero ERROR — the same count as
before this gate. No `FOLLOW-UPS.md` is written, because no criterion failed.
