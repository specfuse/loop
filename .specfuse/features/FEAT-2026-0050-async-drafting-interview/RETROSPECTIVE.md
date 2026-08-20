## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0050
- predicate_version: v1
- gate_total_cost: $4.30
- gate_budget: $27.00
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 2's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=19 predicate=v1 -->

- **FEAT-2026-0050/T01** (`WU-01-question-set-builder.md`)
  - deferred: `tests/test_drafting_questions.py::TestBuildQuestionSet::test_elicitation_questions_carry_no_options`
  - deferred: Every question in a built set carries `kind` ∈ {`elicitation`, `decision`},
  - deferred: Every `decision` question carries at least two options **and** a
  - deferred: The builder reads the roadmap entry, a LEARNINGS slice, and at least one
  - deferred: The module issues no `gh` and no `git` subprocess — asserted structurally
  - deferred: `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
- **FEAT-2026-0050/T02** (`WU-02-post-question-issue.md`)
  - deferred: `tests/test_drafting_question_issue.py::test_each_question_carries_its_own_marker`
  - deferred: The body is produced by calling `escalation.render_escalation_body` — asserted
  - deferred: The issue carries `needs-human` and `drafting-needed`, and no other category
  - deferred: Elicitation questions render open — no numbered options — and decision
  - deferred: Rendering issues no `gh` command: the function returns a body and a label
  - deferred: `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
- **FEAT-2026-0050/T03** (`WU-03-answer-gate.md`)
  - deferred: `tests/test_drafting_answer_gate.py::test_unanswered_elicitation_forces_fallback`
  - deferred: An unanswered **decision** question yields the agent's recommendation as the
  - deferred: Answers bind by T02's per-question marker, not by position: a reply answering
  - deferred: Round two re-asks **only** unanswered elicitation questions; answered
  - deferred: A hard cap of two rounds: a third round is never posted, and reaching the cap
  - deferred: The fallback outcome is the **existing** `drafting-needed` escalation, not a
  - deferred: `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`

> **Reconciled at the terminal close.** All 19 criteria above were re-verified
> in the `G2-CLOSE` session against the working tree at `ac80f64`. Every one is
> green; none was carried forward. The per-criterion evidence is in
> § Gate 1's auto-close debt, reconciled below.

## Gate 2 — drafting from answers

Gate 2 asked whether an answered question issue can produce a drafted feature
folder without a live human. What it decided: the interview now instructs the
reply shape its own parser accepts (T04), `/draft-feature` documents a mode in
which answers rather than presence authorize a write (T05), a `draft_ready`
answer set produces exactly one headless invocation and a `fallback` set
produces none (T06), and `FeatureProvider`'s `needs_drafting` branch dispatches
that invocation instead of escalating when it is handed a `draft_ready` result
(T07).

What it did **not** decide is the thing the feature was funded for, and it is
recorded as a headline rather than a footnote: **the path is not wired
end-to-end, and nothing has ever travelled it.** See § Did the feature remove
the bottleneck below.

Four implementation work units, four first-attempt passes, zero blocked
attempts, zero driver refusals. Full `code` gate set re-run fresh in this close
session: 16 of 16 green.

### Oracles re-run fresh (`close-discipline.md` §1)

Every command below was executed in this close session with its exit code read
directly from the process; none is inherited from a producing WU's self-report.
The list is the full `code` set from `.specfuse/verification.yml` in
declaration order, run from the repository root via `./scripts/smoke-test.sh`
against the working tree as it stands at this attempt.

| # | gate | command | exit |
|---|---|---|---|
| 1 | tests | `python3 -m unittest discover -s tests -v -b` | 0 |
| 2 | lint | `ruff check specfuse .specfuse/scripts tests scripts` | 0 |
| 3 | security | `bandit -r specfuse .specfuse/scripts -ll` | 0 |
| 4 | coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | 0 |
| 5 | leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | 0 |
| 6 | agent-policy-example-lint | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && … .specfuse/agent-policy.yml` | 0 |
| 7 | event-type-gate | `python3 .specfuse/scripts/event_type_gate.py` | 0 |
| 8 | roadmap-link-gate | `python3 .specfuse/scripts/roadmap_link_gate.py` | 0 |
| 9 | arm-sweep-gate | `python3 .specfuse/scripts/arm_sweep_gate.py` | 0 |
| 10 | monitoring-example-lint | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | 0 |
| 11 | leak-scan-hook | `bats tests/leak_scan_hook.bats` | 0 |
| 12 | sync-scaffold-bats | `bats tests/sync_scaffold.bats` | 0 |
| 13 | sync-scaffold-symlinks-bats | `bats tests/sync_scaffold_symlinks.bats` | 0 |
| 14 | init-sh-shim-bats | `bats tests/init_sh_shim.bats` | 0 |
| 15 | init-skills-bats | `bats tests/init_skills_idempotent.bats` | 0 |
| 16 | hookspath-conflict-bats | `bats tests/hookspath_conflict.bats` | 0 |

`tests`: `Ran 3433 tests in 109.470s / OK (skipped=1)`. `coverage`: the same
3433 tests, `TOTAL 11127 stmts / 712 miss / 94%`, over the gate's
`--fail-under=90`. `leak-scan`: `gitleaks 8.30.1 / leak-scan: clean`.
`event-type-gate`: `no validation errors across 63 events.jsonl file(s), 1570
event(s) checked`. `roadmap-link-gate` exits 0 with two pre-existing advisories
on FEAT-2026-0011 and FEAT-2026-0052 — neither is this feature's row, and both
are WARN, not error. The scaffold-integrity layer the same script runs first —
`lint_plan` on the bundled example feature and a driver dry-run — also exits 0.
Script exit: `SMOKE EXIT=0`, `smoke test: OK`.

Plus the two commands this work unit's own **Verification** section names:

| command | exit |
|---|---|
| `specfuse lint --closing` | 0 |
| `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview` | 0 (`OK — … is structurally valid.`) |

**Environment note.** The gate set was run **outside** the session sandbox, as
this unit's Verification section requires. Under the sandbox, pip
build-dependency resolution and the tests that shell out to `git` over the
network go falsely red; the exit codes above are the honest ones, and they are
the same environment (`oracle_env: macos_local`) every producing WU ran in.

### Failure-class breakdown

(no non-passing attempts in scope)

Nine dispatched sessions across both gates (T01–T03, G1-PLAN, T04–T07, and this
close), every one passing on attempt 1. No `blocked` RESULT, no driver-refused
attempt, no re-arm. `G1-CLOSE-INTERMEDIATE` was never dispatched at all — the
auto-close predicate took it, which is the origin of the debt reconciled below.

## Did the feature remove the bottleneck it was filed for?

**No — and nothing has been drafted through this path.** The measurable claim
`WU-92` names is: *a `drafting-needed` queue entry reaches a drafted folder
without an interactive session.* That has never happened. It has not happened
once, in this repository or anywhere else, and the reason is not "we ran out of
time to try" — **it cannot happen with the code as it stands**, because two
seams in the chain are unconnected. Both were found by reading the shipped tree
in this session, not inferred:

**Seam 1 — nothing posts the question issue.** `render_question_issue` returns
a body and a label set and issues no `gh` command, by T02's own acceptance
criterion 5. That is correct for the unit. But no production caller exists:

```
grep -rn "render_question_issue\|build_question_set_for_feature" specfuse/ --include="*.py"
-> hits only inside specfuse/agent/drafting_questions.py itself
```

So the interview is renderable and has never been rendered anywhere an operator
could see it.

**Seam 2 — the real agent run never asks the answer gate.**
`FeatureProvider.__init__` takes an injectable `answer_gate` and defaults it to
`self._fallback_answer_gate`, which returns `OUTCOME_FALLBACK` unconditionally.
`specfuse/agent/run.py`'s `default_providers` (line 648) constructs
`FeatureProvider` with `repo`, `runner`, `policy_path`, `features_root`,
`stream_driver_output` and `reporter` — and **no `answer_gate`**. So in every
real run, `_dispatch_drafting` takes the fallback branch on the first line and
`needs_drafting` still escalates exactly as it did before this feature.

```
grep -rn "answer_gate" specfuse/ --include="*.py"
-> 5 hits, all in specfuse/agent/providers/feature.py; none in run.py
```

That default is deliberate and is documented in the constructor's own comment
("no answers exist anywhere yet to read, so `needs_drafting` still escalates
every time (D3)"). It is the safe default. It is also the reason the headline
benefit is unmeasured: **D3's "worst case is status quo" is, at this commit,
the *only* case.**

**This is a planning gap, not a work-unit failure.** Neither gate's Definition
of Done ever named "post the issue" or "inject the gate in
`default_providers`". Gate 1's DoD stops at "an operator reply is parsed back
to per-question answers"; gate 2's stops at "`FeatureProvider` dispatches that
path on `needs_drafting`", which T07 satisfies *when handed a `draft_ready`
result*. Every unit did what it was asked. The composition was never assigned
to anyone, so it was never built, and the feature's own gate structure could
not detect that — which is the generalizable lesson staged in
`LEARNINGS-pending.md`.

FEAT-2026-0080 closed `met_locally` on this exact distinction and recorded it;
this close makes the same call for the same reason, one notch lower, because
here the mechanism is not merely unproven outside the repo — it is unreachable
inside it.

## Was a real operator reply ever observed, and in what shape?

**No. None was observed, and the parser remains unvalidated against a human.**

`GATE-02-REVIEW.md` § Runtime probe recorded this at gate 2's arming: no issue
was ever posted, so no reply was ever received, so every reply shape in this
feature is **designed, not observed**. That statement is still true at close,
and it follows directly from seam 1 above — with no production caller for
`render_question_issue`, there is no issue for an operator to reply to.

What *is* measured is the in-tree round-trip between the two halves, re-run
fresh in this session:

- an operator-copyable answer template rendered into the body binds every
  question id back through `parse_reply_answers`
  (`test_template_block_parses_back_to_every_question`, exit 0);
- a bare-number reply — the shape every other `needs-human` issue instructs —
  still binds nothing and still yields `fallback`
  (`test_bare_number_reply_still_binds_nothing_and_falls_back`, exit 0).

The second is the property worth keeping: the round-trip **fails closed**. A
mis-shaped reply leaves elicitation unanswered and D1 falls back; it does not
bind an answer to the wrong question. That is the design behaving well against
a synthetic reply, and it is not evidence about a human. Reporting the parser
as validated would be the failure `GATE-01.md`'s arming discipline names, so it
is reported as unvalidated.

## Gate 1's auto-close debt, reconciled

`RETROSPECTIVE.md` carried `<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03
criteria=19 -->`. Gate 1 auto-closed at `evaluate_auto_close`, so no session
ever enumerated which of those 19 criteria were actually checked. All 19 were
re-verified in this session, each against a scoped oracle whose exit code was
read directly. **19 of 19 green; none carried forward.**

| WU | criterion | oracle | exit |
|---|---|---|---|
| T01 | 1 — elicitation carries no options (negative observation) | `unittest tests.test_drafting_questions.TestBuildQuestionSet.test_elicitation_questions_carry_no_options …test_an_elicitation_question_rejects_manufactured_options` | 0 (2 tests) |
| T01 | 2 — every question carries kind/id/text | `…TestBuildQuestionSet.test_every_question_has_kind_id_and_text` | 0 |
| T01 | 3 — decisions carry ≥2 options and a recommendation naming one | `…test_decision_questions_carry_options_and_a_recommendation …test_a_decision_the_builder_cannot_recommend_on_is_rejected …test_a_decision_recommendation_must_name_one_of_its_own_options` | 0 (3 tests) |
| T01 | 4 — reads roadmap/LEARNINGS/exemplar; set mentions the named surface | `…test_question_set_mentions_a_surface_named_in_the_roadmap_entry …TestBuildQuestionSetForFeature` | 0 (3 tests) |
| T01 | 5 — module issues no `gh`/`git` subprocess (structural) | `…test_module_issues_no_gh_or_git_subprocess` | 0 |
| T01 | 6 — `lint_plan` on this feature dir | `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview` | 0 |
| T02 | 1 — each question carries its own marker | `unittest tests.test_drafting_question_issue.RenderQuestionIssueTests.test_each_question_carries_its_own_marker` | 0 |
| T02 | 2 — body produced by `render_escalation_body`, hand-rolled body fails | `…test_body_is_produced_by_render_escalation_body …test_hand_rolled_body_fails_the_same_check` | 0 (2 tests) |
| T02 | 3 — `needs-human` + `drafting-needed` and no other category | `…test_labels_are_needs_human_and_drafting_needed_only` | 0 |
| T02 | 4 — elicitation renders open, decisions render options + recommendation | `…test_elicitation_questions_render_open_with_no_options …test_decision_questions_render_options_with_recommendation_named` | 0 (2 tests) |
| T02 | 5 — rendering issues no `gh` command | `…test_renders_no_gh_command` | 0 |
| T02 | 6 — `lint_plan` on this feature dir | same as T01 #6 | 0 |
| T03 | 1 — unanswered elicitation forces fallback | `unittest tests.test_drafting_answer_gate.UnansweredElicitationForcesFallbackTests` | 0 |
| T03 | 2 — unanswered decision defaults to the recommendation + records an assumption | `…UnansweredDecisionDefaultsTests` | 0 (2 tests) |
| T03 | 3 — answers bind by marker, not by position | `…BindByQuestionIdNotPositionTests` | 0 (3 tests) |
| T03 | 4 — round two re-asks only unanswered elicitation | `…RoundTwoReasksOnlyUnansweredElicitationTests` | 0 (2 tests) |
| T03 | 5 — hard cap of two rounds; cap reached ⇒ fallback | `…HardCapOfTwoRoundsTests` | 0 (2 tests) |
| T03 | 6 — fallback equals `FeatureProvider`'s existing payload (D3) | `…FallbackMatchesFeatureProviderTests` | 0 |
| T03 | 7 — `lint_plan` on this feature dir | same as T01 #6 | 0 |

**What the debt reconciliation does and does not buy.** It establishes that
gate 1's units delivered what their criteria said, which auto-close asserted
but never checked. It does not establish that gate 1's *gate-level* claim — "the
agent can post the interview and read the operator's reply" — holds in a real
run; no criterion in T01–T03 ever asserted a posted issue, so no amount of
re-verification here reaches it. That gap is seam 1 above, and it is carried in
the hedged-verdict record, not in this table.

## Cost analysis

Reconciled against `PLAN.md`'s `planned_cost_usd: 46.00` and each gate's
`cost_budget_usd`. Every figure is the `cost_usd` the driver wrote to
`events.jsonl`; nothing is estimated.

### Gate 1 — budget $27.00

| WU | type | planned | actual | attempts |
|---|---|---|---|---|
| T01 question-set builder | implementation | $4.00 | $1.396823 | 1 |
| T02 post question issue | implementation | $3.50 | $1.009557 | 1 |
| T03 answer gate | implementation | $4.50 | $1.893161 | 1 |
| G1-CLOSE-INTERMEDIATE | close-intermediate | $6.00 | $0.00 | 0 — auto-closed, never dispatched |
| G1-PLAN | plan-next | $9.00 | $6.368013 | 1 |
| **gate 1** | | **$27.00** | **$10.667554** | 4 dispatched sessions |

Gate 1 landed at **40% of its budget**. The auto-close predicate accounts for
$6.00 of the $16.33 underspend by simply not running a session — and that
saving is what created the 19-criterion debt this close spent real money
reconciling, so it is a deferral, not a discount.

### Gate 2 — budget $25.00

| WU | type | planned | actual | attempts |
|---|---|---|---|---|
| T04 reply-shape round-trip | implementation | $3.00 | $1.302884 | 1 |
| T05 answers-supplied mode | implementation | $3.50 | $1.003346 | 1 |
| T06 drafting invocation | implementation | $3.00 | $1.133740 | 1 |
| T07 provider dispatch | implementation | $3.50 | $1.379538 | 1 |
| G2-CLOSE (this session) | close | $6.00 | recorded by the driver at exit | 1 |
| **gate 2, implementation only** | | **$13.00** | **$4.819508** | 4 |

### Feature total

| | planned | actual (excl. this close) |
|---|---|---|
| **FEAT-2026-0050** | **$46.00** | **$15.487062** — 34% |

**Four observations worth carrying, all of them about estimating rather than
about this feature:**

1. **Every implementation estimate was 2.5–3.5× the actual.** Seven
   implementation WUs, planned $25.00, spent $8.12. The estimates were not
   individually wrong so much as uniformly padded — a per-unit ratio of ~0.32
   with almost no variance (0.29–0.40), which is a systematic bias, not noise.
2. **`plan-next` was the only estimate close to right.** $9.00 planned,
   $6.37 actual (71%). `PLAN.md` argued that number up from the $6.00 floor on
   `[FEAT-2026-0069/G2-CLOSE]`'s evidence and was nearly right; the same
   reasoning applied to implementation units would have made them *worse*.
   `planning-discipline.md` §5's warning — a floor is a distribution question —
   cuts both ways.
3. **Cheap WUs are what a first-attempt-pass gate looks like.** Nine sessions,
   nine passes, zero refusals. The 28%-of-spend-on-refused-attempts figure
   `planning-discipline.md` §5 reports does not appear anywhere in this
   feature's ledger, and the padding sized to absorb it went unspent.
4. **Underspend is not the good news it looks like here.** $30 of unspent
   budget bought a feature whose headline benefit is unmeasured. The gate that
   would have caught that — one asserting an end-to-end drafted folder — was
   never drafted, and no budget line existed for it to overrun.

## Consumer-visible contract changes

Five additions, no removals, no renames, no breaking changes. Every one is
additive: no existing signature changed shape, and no existing caller needs
editing.

1. **New module `specfuse/agent/drafting_questions.py`** — `build_question_set`,
   `build_question_set_for_feature`, `load_roadmap_entry`,
   `render_question_issue`. Builds the `/draft-feature` interview as a
   classified question set and renders it as a `needs-human` issue body plus a
   label set. Renders only; posts nothing.
2. **New module `specfuse/agent/drafting_answers.py`** — `parse_reply_answers`,
   `evaluate_answer_gate`, `fallback_escalation`, `AnswerGateResult`,
   `Assumption`, `OUTCOME_DRAFT_READY` / `OUTCOME_FALLBACK`, `MAX_ROUNDS`.
   Parses an operator reply back to per-question answers and applies D1.
3. **New module `specfuse/agent/drafting_invoke.py`** — `build_invocation`,
   `read_result`. Same `(argv, prompt)` idiom as `triage_invoke`,
   `diagnose_invoke` and `autofix_invoke`; runs no subprocess.
4. **`FeatureProvider.__init__` gains a keyword-only `answer_gate` parameter**,
   defaulting to a fallback-only reader. Existing callers are unaffected —
   `default_providers` passes nothing and gets today's behaviour.
5. **`/draft-feature` gains a documented `## Answers-supplied mode`** on both
   skill surfaces (canonical and vendored, byte-identical). This is the
   operator-facing change: the skill now states that answers, not a live human,
   authorize a write, and that a folder drafted this way lands `status: planned`
   and unarmed.

**Human acknowledgment.** Item 5 is the one a human must sign off on, and that
signature was collected at arming rather than here: `GATE-02-REVIEW.md`
§ Open question 1 carries the recorded answer of 2026-08-16 — *"Accepted as
drafted — the recommendation, i.e. the second option's constraint"* — which is
the `status: planned` and unarmed constraint now written into T05's criterion 3
and into the shipped section. Items 1–4 are internal to the agent runner and
change no published contract. This close carries no further acknowledgment
request; the feature's terminal verdict is hedged, so the operator reads this
list again when deciding whether to accept it.

## Hedged-verdict follow-up record

Verdict: `partially_met`. Two criteria are unmet. Both are the same shape — a
mechanism that is built, tested, and unreachable — and both are upgradeable.

### The feature has not removed the bottleneck it was filed for

**Criterion, verbatim (`WU-92` acceptance criterion 3):** *"Whether the feature
actually removed the bottleneck it was filed for. The measurable claim: a
`drafting-needed` queue entry reaches a drafted folder without an interactive
session."*

**Why it is unmet here.** Not an environment limit — a wiring gap. No
production code calls `render_question_issue`, so no question issue is ever
posted; and `default_providers` constructs `FeatureProvider` without an
`answer_gate`, so `_dispatch_drafting` takes the fallback branch on every real
run. Both are quoted with their greps in § Did the feature remove the
bottleneck. The three modules and the skill mode are green in isolation and
connected to nothing.

**Exact re-run condition that would upgrade this to `met`.** A follow-up
feature closes the two seams — a caller that posts the rendered issue, and an
`answer_gate` injected in `default_providers` that reads the reply from that
issue's comments — after which a `specfuse-agent` run over a `queue:` holding
one undrafted `planned` feature produces a drafted feature folder, and the run's
`events.jsonl` shows `needs_drafting` resolving to a completed drafting
dispatch rather than an escalation. That run, and its resulting folder, is the
evidence.

- **kind:** `externally-verifiable-later`

### No real operator reply has ever been observed

**Criterion, verbatim (`WU-92` acceptance criterion 4):** *"Whether a real
operator reply was ever observed, and in what shape."*

**Why it is unmet here.** It is answerable — the answer is "none, ever" — but
the property gate 2's parsing criteria were drafted to hold cannot be checked:
with no issue posted (seam 1), there is nothing for an operator to reply to.
Every reply shape in this feature is designed. The round-trip is proven against
a synthetic reply and fails closed on a mis-shaped one; neither observation is
about a human.

**Exact re-run condition that would upgrade this to `met`.** One real
`drafting-needed` question issue posted to the repository, one operator reply,
and that reply's verbatim text fed to `parse_reply_answers` with the resulting
bindings recorded. If it binds every question, the parser is validated; if it
does not, the recorded shape is what the next iteration is drafted against —
which is the evidence `GATE-01.md`'s arming discipline asked for and never got.

- **kind:** `externally-verifiable-later`

**Verdict ceiling.** Both entries are `externally-verifiable-later`, so
`verdict_ceiling_for_kinds` reads *rework exists* — `met` is reachable, and the
operator has a real choice between accepting the hedge now and waiting for the
follow-up work above. This is not a case where accepting is the only move.

## What the loop did NOT verify (terminal — gates 1 and 2)

**Per-criterion deferred-verification list: (nothing — every acceptance
criterion was verified in-loop).**

All 39 acceptance criteria across the feature's seven implementation work units
were verified in this close session against oracles whose exit codes were read
directly: gate 1's 19 (the `specfuse:autoclose-debt` marker's T01–T03, table
above — the marker is hereby reconciled) and gate 2's 20 (T04–T07, recorded
per-criterion in `GATE-02-CRITERIA.md` with oracle, kind, state and attempt).
Nothing is carried forward.

**That empty list is a statement about criteria, not about the feature.** Two
feature-level claims are unverified and are recorded in § Hedged-verdict
follow-up record above rather than here, because no work unit's acceptance
criteria ever asserted them:

- that a `drafting-needed` queue entry reaches a drafted folder without an
  interactive session — never observed, and unreachable at this commit;
- that a real operator reply parses back to per-question answers — no real
  reply has ever existed.

The gap between "every criterion green" and "the feature worked" is exactly the
distance between those two lists, and it is the reason this feature closes
`partially_met` rather than `met`.

## Hedged verdict accepted

**Accepted verdict:** `partially_met`

**Operator reason (verbatim):** "This will have to be tested with a real
feature"

**Recorded at:** 2026-08-17T11:47:22Z

**Computed ceiling at acceptance:** `rework exists` — both entries below carry
`kind: externally-verifiable-later`, so in-repo rework *can* raise this verdict.
The operator accepted now rather than waiting for the named re-run condition.

Both follow-ups below are carried forward **open**. Accepting the hedge ships
the feature with them outstanding; it does not discharge either one.

### Carried forward 1 — the feature has not removed the bottleneck it was filed for

**Criterion, verbatim (`WU-92` acceptance criterion 3):** *"Whether the feature
actually removed the bottleneck it was filed for. The measurable claim: a
`drafting-needed` queue entry reaches a drafted folder without an interactive
session."*

**Why it is unmet here.** Not an environment limit — a wiring gap. No
production code calls `render_question_issue`, so no question issue is ever
posted; and `default_providers` constructs `FeatureProvider` without an
`answer_gate`, so `_dispatch_drafting` takes the fallback branch on every real
run. Both are quoted with their greps in § Did the feature remove the
bottleneck. The three modules and the skill mode are green in isolation and
connected to nothing.

**Exact re-run condition that would upgrade this to `met`.** A follow-up
feature closes the two seams — a caller that posts the rendered issue, and an
`answer_gate` injected in `default_providers` that reads the reply from that
issue's comments — after which a `specfuse-agent` run over a `queue:` holding
one undrafted `planned` feature produces a drafted feature folder, and the run's
`events.jsonl` shows `needs_drafting` resolving to a completed drafting
dispatch rather than an escalation. That run, and its resulting folder, is the
evidence.

- **kind:** `externally-verifiable-later`

### Carried forward 2 — no real operator reply has ever been observed

**Criterion, verbatim (`WU-92` acceptance criterion 4):** *"Whether a real
operator reply was ever observed, and in what shape."*

**Why it is unmet here.** It is answerable — the answer is "none, ever" — but
the property gate 2's parsing criteria were drafted to hold cannot be checked:
with no issue posted (seam 1), there is nothing for an operator to reply to.
Every reply shape in this feature is designed. The round-trip is proven against
a synthetic reply and fails closed on a mis-shaped one; neither observation is
about a human.

**Exact re-run condition that would upgrade this to `met`.** One real
`drafting-needed` question issue posted to the repository, one operator reply,
and that reply's verbatim text fed to `parse_reply_answers` with the resulting
bindings recorded. If it binds every question, the parser is validated; if it
does not, the recorded shape is what the next iteration is drafted against —
which is the evidence `GATE-01.md`'s arming discipline asked for and never got.

- **kind:** `externally-verifiable-later`
