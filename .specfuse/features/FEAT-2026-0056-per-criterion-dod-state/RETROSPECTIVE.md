## Gate 1

Gate 1 of FEAT-2026-0056 set out to make per-criterion close state **recorded** and
**linted**, and it did: `specfuse/loop/criteria_state.py` defines the entry schema and
its parser/renderer (T01), `precreate_dispatch_skeleton` seeds `GATE-NN-CRITERIA.md`
on every `close` / `close-intermediate` dispatch through a hoisted
`extract_wu_criteria` shared with `build_autoclose_debt_enumeration` (T02),
`closing_requirements.py` declares `close-l` / `close-intermediate-f` and
`lint_closing.py` implements `check_criteria_state_well_formed` (T03), and
`close-discipline.md` §5 documents the narrow/broad oracle contract while the roadmap's
benefit paragraph was re-baselined to what the design can reach (T04). Four work units,
five attempts, $6.99 against a $12.50 plan for those units.

Every oracle is green. The composite checks this close is here to run are not, and the
two findings below are the substance of this gate's record. Neither is a defect *inside*
a producing unit — each is a gap *between* two of them, which is the class no producing
unit's acceptance criteria can reach.

### Oracle re-runs (close-discipline §1)

Re-run fresh in this session, exit codes read directly. Commands are prefixed with the
project venv's interpreter; the gate declarations in `.specfuse/verification.yml` write
them as bare `python3`.

The full `code` gate set:

```
$ python3 -m unittest discover -s tests -v -b
Ran 2411 tests in 107.185s
OK (skipped=3)
EXIT=0

$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
EXIT=0

$ bandit -r specfuse .specfuse/scripts -ll
	Total issues (by severity):  Undefined: 0  Low: 92  Medium: 0  High: 0
EXIT=0

$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
TOTAL                                               7726    502    94%
EXIT=0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
EXIT=0

$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 53 events.jsonl file(s), 1244 event(s) checked
EXIT=0
```

The remaining `code` entries, run for completeness rather than because a producing
unit's criteria named them: `roadmap_link_gate.py` EXIT=0 (0 errors, 8 warnings, none
new), `arm_sweep_gate.py` EXIT=0 (14 evaluable features swept clean),
`lint_monitoring.py` EXIT=0, and all six `bats` suites EXIT=0.

The per-unit oracles named in T01–T04's own acceptance criteria:

```
$ python3 -c "from specfuse.loop.criteria_state import ORACLE_KINDS, CRITERION_STATES, parse_criteria_state, render_criteria_state, criterion_id_for"     # T01 c7
EXIT=0

$ python3 -c "from specfuse.loop.loop import extract_wu_criteria, _precreate_criteria_state_stub"                                                          # T02 c9
EXIT=0

$ python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"                                                                    # T03 c11
EXIT=0

$ python3 -m unittest discover -s tests -v -b -k debt                                                                                                     # T02 c3
Ran 5 tests in 0.007s
OK
EXIT=0

$ bash scripts/sync-scaffold.sh                                                                                                                           # T04 c6
Scaffold data already in sync (26 files checked).
EXIT=0
$ diff specfuse/loop/data/rules/close-discipline.md .specfuse/rules/close-discipline.md          -> EXIT=0
$ diff specfuse/loop/data/templates/GATE.template.md .specfuse/templates/GATE.template.md        -> EXIT=0
$ diff specfuse/loop/data/templates/WU.template.md .specfuse/templates/WU.template.md            -> EXIT=0

$ python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0056-per-criterion-dod-state                                                         # T04 c10
OK — .specfuse/features/FEAT-2026-0056-per-criterion-dod-state is structurally valid.
EXIT=0
```

**T03's corpus sweep had to be re-run with a different command than the one on record,
and that is itself a finding.** `GATE-01.md`'s arming baseline and T03's criterion-10
sweep both invoke the `specfuse-lint` console script from the project venv. That script
resolves `specfuse.loop` from the **installed** distribution in `site-packages`
(version 0.7.1), not from the working tree — it has no `close-l`, no
`close-intermediate-f`, and no `criteria_state` module at all. So the sweep that was
offered as evidence the severity flip is satisfiable never executed the requirement it
was measuring. The shims under `.specfuse/scripts/` path-insert the repo root and do
resolve from source, so the sweep re-run below is against the code under test:

```
$ for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done   # non-zero exits only
### .specfuse/features/FEAT-2026-0001-health-endpoint/ (exit 1)
  - plan-next-a: GATE-02-REVIEW.md absent or empty
### .specfuse/features/FEAT-2026-0036-adopt-ruff-016/ (exit 1)
  - close-a: RETROSPECTIVE.md absent or empty in feature dir
  - close-b: no LEARNINGS.md additions and no 'nothing generalizes' note
  - close-d: verdict frontmatter field is absent
### .specfuse/features/FEAT-2026-0056-per-criterion-dod-state/ (exit 1)
  - close-intermediate-b: no LEARNINGS.md additions and no 'nothing generalizes' note
```

The conclusion T03 reached is correct — **zero findings attributable to `close-l` or
`close-intermediate-f` across the corpus** — and it is unchanged from `GATE-01.md`'s
baseline except that this feature's own `close-intermediate-a` is now satisfied. But it
was correct for a reason nobody checked: no feature in `.specfuse/features/` carries a
criteria artifact, so the requirement's `applies_when` gate short-circuits before any
code that could differ between the two package copies is reached. The finding set would
have been identical had T03 shipped nothing at all. See finding 2 for why that premise
expires the moment the driver restarts.

### The feature-level question — does a close dispatched today receive a seeded artifact?

**Answer: no, this close did not. The shipped code does. The two facts are both true and
the gap between them is finding 1.**

This session's own feature folder contains no `GATE-01-CRITERIA.md`. It contains a
`RETROSPECTIVE.md` pre-created at dispatch, so `precreate_dispatch_skeleton` ran — it
ran the retrospective stub and not the criteria stub, which are consecutive statements
in the same function.

Run against a temporary copy of this exact feature folder, through the real entrypoint,
with the real `FEAT-2026-0056/G1-CLOSE-INTERMEDIATE` work unit loaded by `load_wu` from
the `PLAN.md` graph:

```
WU: FEAT-2026-0056/G1-CLOSE-INTERMEDIATE type: close-intermediate
artifact before: False
artifact after : True
entries: 41
ids: ['T01#1', 'T01#2', 'T01#3', 'T01#4', 'T01#5'] ... ['T04#8', 'T04#9', 'T04#10']
states set: ['unverified'] kinds set: ['None']
```

Forty-one entries, seeded from this gate's own four substantive work units, every one
`state: unverified` with `oracle` / `kind` / `proved_at_sha` / `attempt` absent — exactly
T02's criterion 6. So the composite works in the tree. It did not work in this dispatch.

#### Finding 1 — the driver process that dispatched this close predates the code that seeds the artifact

The driver for this feature is `.specfuse/scripts/loop.py --prepare`, and
`ps -eo pid,lstart,etime,command` shows that process started at 23:40:21 UTC — the same
minute as `GATE-01.md`'s `baseline.probed_at` of 23:40:22. T02, which added
`_precreate_criteria_state_stub`, completed at 00:05:04. Python caches modules in
`sys.modules` at first import, so the `precreate_dispatch_skeleton` in that process's
memory is the pre-T02 function object with no criteria-stub call site in it. Every
in-process check — the unit tests, the symbol imports, the composite above — runs in a
fresh interpreter and reports the new behaviour correctly.

This is a **recurrence of an already-promoted lesson**, not a new one:
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` states the rule, and its rule (b)
— check the driver process's start time against the wiring unit's `started_at` before
writing anything else — is the step that produced this diagnosis in one command. What the
recurrence adds is that the lesson was already in `LEARNINGS.md` when this gate was
planned, and gate 1 was planned anyway with a driver-module `produces:` in T02 and a
close armed to observe it, with no restart step in the gate. The lesson is not missing;
it is not being consumed at plan time. That belongs in gate 2's plan as a step, not in
`LEARNINGS.md` as a second copy of a rule that is already there.

Consequence for the feature: **gate 2's consumer will read an artifact that the same
driver run never wrote.** If gate 2 is planned to be dispatched by the process now
running, its skip policy will find no state to skip on and will silently do nothing —
which looks exactly like "the cache did not help", not like "the cache was never
written". G1-PLAN should treat a driver restart between T02-class wiring and any unit
that observes it as a planned gate step.

#### Finding 2 — a freshly seeded artifact is born failing its own lint, 41 findings deep

The seeded artifact from the composite run above, untouched, linted with the
working-tree lint:

```
$ python3 .specfuse/scripts/lint_plan.py <temp copy of this feature folder> --closing
FAIL — 42 unmet closing requirement(s):
  - close-intermediate-b: no .specfuse/LEARNINGS.md additions ...
  - close-intermediate-f: T01#1: missing kind: — would fail check_criteria_state_well_formed after squash
  - close-intermediate-f: T01#2: missing kind: — would fail check_criteria_state_well_formed after squash
  ... (41 × close-intermediate-f, one per seeded criterion)
```

T02's criterion 6 requires every seeded entry to omit `kind:`. T03's criterion 6 requires
a missing `kind:` to be exactly one blocking finding. Each unit is right in isolation and
each shipped its own passing test. Composed, they mean: **from the instant the driver is
restarted, every `close` and `close-intermediate` dispatch in this repo starts with a red
`specfuse-lint --closing` and stays red until the close session hand-annotates a `kind:`
and a `state:` for every acceptance criterion of every substantive work unit in its
gate** — 41 of them for this gate. Gate 1 shipped no mechanism to fill them in, because
filling them in is a close-session behaviour and no unit in gate 1 owned it.

`PLAN.md`'s escalation-predicate analysis asked the right question ("what does the rule
report on an input already in its intended final state? **Zero**") and answered it for
the *final* state. Nothing asked what it reports on the *initial* state the driver itself
creates, and that is the state every close now begins in. `GATE-01.md`'s arming
condition — "the finding set is unchanged from the baseline" — was satisfiable only
because the stale driver never produced an artifact for the sweep to find.

This is a design question for the operator and for gate 2, and it is deliberately not
fixed here: `specfuse/` is outside this work unit's boundary, and a fix nobody reviewed
is worse than a finding somebody reads. Three shapes are available to gate 2 and the
choice is not this session's to make — seed entries with a `kind` the close may correct;
narrow `applies_when` so the requirement fires only once a close has begun recording; or
give the close a helper that fills the artifact from the oracles it already ran.

**This close did not create `GATE-01-CRITERIA.md` in this feature folder.** No acceptance
criterion asks it to, creating one would be simulating a driver action rather than
observing it, and the observation above is precisely that doing so turns criterion 10
(`specfuse-lint --closing` exits 0) red. The absence is reported, not papered over.

### The re-arm property, observed rather than asserted

`tests/test_loop_criteria_skeleton.py::test_criteria_artifact_survives_rearm_fold`
exercises **the real fold path**: it calls `loop.fold_cumulative_on_rearm(close_wu,
loop.Backend())` — the production function at `specfuse/loop/loop.py:1829` with the
production backend, no stub, no stand-in — after seeding through the real
`precreate_dispatch_skeleton`, and asserts the parsed entries are identical across it.
The driver's only call site for that function is `loop.py:5893`, on the re-arm branch of
the dispatch loop. So the property T02 claims is the property T02 tests.

**The property is true and it is not the one that protects the artifact.** The fold
rewrites work-unit frontmatter; the artifact is a separate file, so no frontmatter
operation could ever have touched it — the test can only pass. The path that *does*
destroy it is the per-attempt reset. `untracked_before` is snapshotted once per work
unit at `loop.py:5890`, outside the attempt loop that begins at `loop.py:5952`;
`precreate_dispatch_skeleton` runs inside each attempt, at `loop.py:3357`. So on attempt
1 the artifact is created *after* the snapshot, and a failing attempt's
`reset_preserving_events(head_before, events_path, untracked_before)` hands it to
`_clean_attempt_untracked` as a file that appeared since the snapshot. Executing that
function's real decision rule and unlink loop against a real filesystem:

```
criteria artifact still present after attempt reset: False
events.jsonl still present after attempt reset:      True
```

`events.jsonl` is preserved by an explicit carve-out. The criteria artifact has none. It
is untracked until the close's own passing attempt commits it, so through every failed
attempt of a close — which is the entire scenario this feature exists to make cheaper —
the recorded state is deleted and re-seeded blank. `[FEAT-2026-0053/G2-CLOSE]` is the
precedent the plan cited, and it applies more exactly than the plan expected: the guard
was keyed on the wrong path, and the wrong path was the one that could not fail.

This is a third finding for gate 2 to design against, alongside finding 2. It does not
change any gate 1 acceptance criterion's verdict — T02's criterion 8 asks for the fold
test and got a correct one.

### Failure-class breakdown

| failure_class | count | work units | attempt cost |
| --- | --- | --- | --- |
| `produces_not_in_diff` | 1 | `FEAT-2026-0056/T04` (attempt 1) | $0.94 |

One non-passing attempt in the gate, excluding this close's own. T04 spent attempt 1
editing `.specfuse/roadmap.md` and its own work-unit file while leaving all three paths
in its `produces:` list — the canonical `close-discipline.md` and the two templates —
untouched. The driver's produces-vs-diff guard refused it, and attempt 2 made the
declared edits and passed. The work unit's body warned about exactly this ("**Canonical
copy first, then propagate**", with the reason spelled out), which is worth noting: the
prose was there, correct, and did not prevent the failure. The guard did. $0.94 of the
gate's $6.99 — 13.5% — went to the refused attempt, and it bought the correct file set on
the retry.

### What gate 1 did for cost: nothing, by design

**Gate 1 shipped no cost saving, and none was expected.** Nothing reads the recorded
state to skip work until gate 2; the artifact is written and linted, and no close is
cheaper for it. This gate's own spend must not be read as evidence for or against the
feature's savings claim in either direction — the mechanism that saves money has not
shipped. `GATE-01.md` says this ("Gate 1 makes no close cheaper — that is the intended
shape, not an omission") and it is repeated here because a cost table in a retrospective
invites exactly that misreading.

Separately, and more consequentially: **the roadmap's benefit paragraph was re-baselined
by T04 because the original claim assumed a mechanism `PLAN.md` rejects.** The row
claimed the feature "roughly halves close cost on multi-attempt gates". That number was
reachable only through diff-derived test selection, which `PLAN.md` rejected on the
grounds that it builds a second, weaker definition of the tests gate alongside
`verification.yml`. This repository's `tests` gate is
`python3 -m unittest discover -s tests -v -b` — 2411 tests, one command, no diff
awareness. It is a `broad` oracle by the contract this gate just documented, so it
re-runs on every close attempt and is excluded from the saving by construction. What
oracle-kind invalidation can actually save is the per-criterion agent reasoning, the
regeneration, and the scenario matrix. T04 rewrote the paragraph to say that and to name
the suite as the excluded oracle. The claim is now smaller and true.

## Cost analysis

Two independent totals, computed separately and compared:

| work unit | planned | actual | attempts | delta |
| --- | --- | --- | --- | --- |
| `T01` criteria-state schema | $3.00 | $0.599546 | 1 | −$2.40 (−80%) |
| `T02` pre-create the artifact | $4.00 | $2.093737 | 1 | −$1.91 (−48%) |
| `T03` criteria-state lint | $3.00 | $2.313287 | 1 | −$0.69 (−23%) |
| `T04` rules, templates, re-baseline | $2.50 | $1.983739 | 2 | −$0.52 (−21%) |
| **producing units** | **$12.50** | **$6.990309** | 5 | **−$5.51 (−44%)** |
| `G1-CLOSE-INTERMEDIATE` (this unit) | $4.50 | not yet stamped | 1 in progress | — |
| `G1-PLAN` | $6.00 | not dispatched | — | — |
| **gate plan / budget** | **$23.00** / $29.00 | **$6.99 to date** | | |

**Frontmatter total: $6.990309.** Summing `cost_usd` across the four `done` work units'
frontmatter.

**`events.jsonl` total: $6.990309.** Summing `cost_usd` across every `attempt_outcome`
payload in the feature's event log — five attempts, including T04's refused attempt 1 at
$0.943193. Summing the four `task_completed` payloads instead gives the same
$6.990309.

**Divergence: $0.000000 (0.00%).** The two surfaces agree exactly, and they agree for a
checkable reason rather than by luck: `re_arm_count` is 0 on every unit in this gate, so
no cycle was ever folded into a `cumulative_*` accumulator and the per-cycle frontmatter
field is still the whole story. `events.jsonl` is the only surface that survives a
re-arm — that property was not exercised here, so this gate's agreement is not evidence
the reconciliation would hold on a re-armed unit. T04's two attempts do exercise the
weaker property: its frontmatter `cost_usd` of $1.983739 and `duration_seconds` of
1191.003 are the sums across both attempts, not attempt 2 alone.

Against the $29.00 gate budget: $6.99 spent, 24% consumed, with $10.50 of planned close
spend still ahead. Projected gate total is roughly $17.49 — about 60% of budget — and
even a three-attempt close would land inside it. The producing units came in 44% under
plan, which is a plan-side signal worth carrying to G1-PLAN: the two units estimated
highest (T02 at $4.00, T03 at $3.00) were the two that actually did structural work, and
they were the closest to their estimates. T01 at 20% of plan was a pure-data module with
no wiring, and it was over-estimated by the same reasoning that over-estimated the rest.

## What the loop did NOT verify

Deferred-verification list, per acceptance criterion 5. Every criterion across T01–T04
was re-verified in this session except the four below.

**D1 — T01 c1, T02 c1, T03 c1: the red-test-first observation.**
*Criteria, in substance:* the named test "exists and **fails on HEAD before this WU's
edits**", with the failing output recorded.
*Why not verified here:* the property is historical. It is a claim about the tree as it
stood before each unit's edits, and it is unobservable from a tree in which those edits
have landed. Reproducing it would require reverting the source, which this unit may not
do — `specfuse/` is outside its boundary and it may not run git.
*Where it actually gets checked:* each producing unit's own attempt, whose RESULT block
recorded the failing output, and the driver's produces-vs-diff guard, which independently
refuses a unit whose declared source went untouched. The post-condition half of each
criterion — that the test passes now — is verified here: all 2411 tests pass.

**D2 — T04 c8 and c9: the roadmap edit is confined to FEAT-2026-0056's section.**
*Criteria, verbatim:* the `**Why.**` and `**Goal.**` paragraphs "are byte-identical to
their state before this WU — verified with `git diff .specfuse/roadmap.md`", and
"`git diff --stat .specfuse/roadmap.md` shows changes confined to the FEAT-2026-0056
section".
*Why not verified here:* both oracles are `git` invocations, and this work unit is
forbidden from running any git command — the driver owns that surface. There is no
non-git substitute: the property is a diff against a commit.
*Where it actually gets checked:* T04's own attempt-2 RESULT block, and the squash commit
for T04, which a reviewer can read directly. `roadmap_link_gate.py` passes here with 0
errors, which confirms the roadmap's link graph is intact but says nothing about which
section changed.

**D3 — the seeded-artifact-to-lint interaction over more than one gate shape.**
*Criterion:* none — this is a gap in the criteria, recorded because finding 2 exists.
*Why not verified here:* the 41-finding observation was made against one gate of one
feature. Whether the count and shape hold for a gate with a different substantive-unit
mix, or for a `close` rather than a `close-intermediate`, is unmeasured.
*Where it actually gets checked:* gate 2, which must design against finding 2 and will
need the measurement to choose between the three remedies named above.

**D4 — the artifact's survival across a genuine multi-attempt close.**
*Criterion:* T02 c8 asks for survival across `fold_cumulative_on_rearm`, and that is
verified. The broader property — that recorded state survives a *failed attempt* — is
not asserted by any criterion in gate 1.
*Why not verified here:* observing it end-to-end requires a close that actually fails an
attempt with state already recorded, which cannot be staged from inside a close session
that may not run git or drive the driver. The deletion rule itself **was** observed (see
the re-arm section); what is unobserved is the full driver loop reaching it.
*Where it actually gets checked:* the first real multi-attempt close after the driver is
restarted — or, better, a gate 2 test that drives `reset_preserving_events` with a
dispatch-time snapshot and asserts the artifact survives.

## Consumer-visible contract changes — awaiting operator acknowledgment

Enumerated per `close-discipline.md` §3, across T01–T04. This section is a real
enumeration and not the exemption line: there are five items, one of which changes the
outcome of a command every scaffold consumer runs. Each is appended to `CHANGELOG.md`'s
`Unreleased` section, classified and traced to `FEAT-2026-0056`.

> The exemption line is quoted nowhere in this section on purpose.
> `closing_requirements.consumer_visible_section_is_na` classifies a §3 section by
> substring — it returns true for any body containing "n/a" and "no consumer-visible
> contract change" — so a close that writes "this is **not** *(the exemption line)*",
> the natural way to say it and the phrasing at least one prior close in this repo used,
> is read as an exempt close. For a terminal `close` that suppresses `close-k`, the
> requirement that a real enumeration must reach `CHANGELOG.md`, and the lint stays
> green while a contract change ships unlisted. Observed in this session: the first
> draft of this section tripped it, and rewording the sentence flipped the classifier
> back. Not fixed here — `specfuse/` is outside this unit's boundary and the code is
> FEAT-2026-0064's, not this gate's — and recorded for whoever owns that surface.

**1. A new blocking `specfuse-lint --closing` finding: `close-l` /
`close-intermediate-f` (breaking, headline).** A close whose gate carries a
`GATE-NN-CRITERIA.md` now fails the closing lint for every entry with a missing or
unrecognized `kind:`, a missing or unrecognized `state:`, or a `broad` entry reading
`state: pass` with an `attempt:` that is not the current one. The requirement is gated on
`applies_when="criteria_artifact_present"`, so a feature with no artifact lints exactly as
it did before — which is every feature in every tree today. **The gate opens the moment
the driver that seeds the artifact is running**, and from that point every close session
must annotate every acceptance criterion of its gate or its closing lint is red. See
finding 2: this is the item that most needs a human decision, and the operator should
read that finding before acknowledging this list.

**2. `GATE-NN-CRITERIA.md` appears in close and close-intermediate sessions
(added, behavioural).** `precreate_dispatch_skeleton` now writes a new file into the
feature folder at dispatch for `close` and `close-intermediate` work units, seeded from
the gate's substantive units' acceptance criteria and additive across re-dispatches — an
existing entry is never rewritten, a new criterion is appended `unverified`, and a
criterion that has disappeared is left in place rather than deleted. It remains a no-op
for `plan-next` and every other work-unit type. Anything that enumerates a feature
folder's contents, or asserts on its file list, will see the new file.

**3. A new `applies_when` value, `criteria_artifact_present`
(added, registry contract).** `closing_requirements.Requirement` accepts a sixth
`applies_when` value alongside `always`, `verdict_met`, `verdict_hedged`,
`failures_present`, and `autoclose_debt_marker`, and its docstring enumerates it. Any
downstream consumer that switches exhaustively on `applies_when` — a custom lint, a
reporting script — gains a case it does not handle.

**4. `specfuse/loop/criteria_state.py`, a new importable module shipped in the wheel
(added).** Public surface: `ORACLE_KINDS` (`narrow`, `broad`), `CRITERION_STATES`
(`pass`, `fail`, `unverified`), `CriterionStateEntry`, `parse_criteria_state`,
`render_criteria_state`, and `criterion_id_for`. Additive as an import path; nothing
previously occupied it.

**5. `close-discipline.md` §5, and the two templates that point at it
(changed, vendored documentation).** The rule gains
`## 5. Per-criterion state and the narrow/broad oracle contract`, placed between §4 and
the project-local split, and `GATE.template.md` and `WU.template.md` each carry a
one-line pointer to it. All three files are vendored: `specfuse upgrade` overwrites the
`.specfuse/` copy in every downstream project, so the new section arrives without any
consumer action. Documentation only — no behaviour rides on it.

Not a contract change, and named here so the absence is on record rather than assumed:
`extract_wu_criteria` was hoisted out of `build_autoclose_debt_enumeration`, and that
function's output is unchanged — its five scoped regression tests pass unmodified.

**Human acknowledgment of this list has not been obtained, and this close is blocked on
it.** `close-discipline.md` §3 requires explicit human acknowledgment, and a dispatched
work-unit session has no human to ask; `operator-escalation.md` is explicit that the
acknowledgment must come from the human and that an agent drafting it has removed the
signature it was collecting. The enumeration is complete and the changelog entries are
written, so the acknowledgment is the only outstanding act. Item 1 is the one that needs
a real decision rather than a nod.

## Lessons

Two lessons are promoted to `.specfuse/LEARNINGS.md`, and two further candidates were
considered and deliberately not promoted.

**Promoted.** *State designed to outlive a retry must be tested against every path that
destroys it, and the path named in the plan is rarely the dangerous one.* Written up in
`LEARNINGS.md` under `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]`.
It generalizes past this feature: any artifact whose value is that it persists across
attempts has a set of destroyers — a fold, a reset, a clean, a regeneration — and a test
that covers one of them reads as coverage of all of them.

**Promoted.** *A console-script entry point and a source checkout are two different
programs; a sweep that measures "the corpus is clean" must name which one it ran.*
Written up as `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]`.
This is not specific to this feature or this repo — it applies to any project that both
ships a CLI and dogfoods it from source.

**Not promoted — already in `LEARNINGS.md`.** The stale-driver-module finding is
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`, entry and rules intact, and its
diagnostic rule (b) is what produced finding 1 in a single command. Adding a second entry
saying the same thing would dilute a file that is loaded whole into every planning
session. The recurrence is recorded in finding 1 instead, where it belongs — as evidence
that the gap is at plan time, not in the rule.

**Not promoted — restates this feature's design.** "A close should record which oracle
proved which criterion" is what FEAT-2026-0056 *is*. A lesson that only names the
feature's own thesis teaches a future work unit nothing it would not read in the plan.
