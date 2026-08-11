---
open_questions:
  - "OQ-1: findings-autofix is drafted to rank at the bug tier and honour `rules.bugs.preempt` — the dial an operator may already have set for bugs alone would then also let a monitoring autofix jump the feature queue. Confirm, or say findings get their own priority, which means minting a new `agent-policy.yml` key and is a plan change rather than a WU. T09's criterion 4 changes either way."
  - "OQ-2: the `diagnose:` dial in monitoring.yml (`manual` / `auto`) is validated by the linter and read by no shipped code. T10 is drafted to be its first consumer and to skip components whose dial is not `auto`. Confirm, or say the agent diagnoses every finding regardless of the dial — T10's criterion 6 changes either way."
---

# Gate 3 review — drafted by `G2-PLAN`, 2026-08-11

## Open questions — decided by the AGENT, not the operator (2026-08-11T04:09:30Z)

**The operator was asleep.** They gave standing authorization on 2026-08-10 to
arm gate 3 unattended, after being told explicitly that any operator-owned
question would be decided by the agent and marked as such. These are those
decisions. **Neither has been reviewed by the operator.** Both align with the
drafted criteria, so no criterion text changed — reversing either means editing
the WU, not just this note.

- **OQ-1 — confirmed as drafted: findings-autofix ranks at the bug tier and
  honours `rules.bugs.preempt`.** Reasoning: `run_autofix` invokes headless
  `/fix-bug`; a monitoring autofix *is* a bug fix, so the bugs dial governing it
  is coherent rather than accidental. The alternative mints a new
  `agent-policy.yml` key, which is a schema change plus validator work — a plan
  change, disproportionate to the distinction it draws. **Accepted consequence:**
  an operator who set `preempt: true` for bugs alone now also lets a monitoring
  autofix jump the feature queue. If that is not wanted, T09 criterion 4 is the
  place to change it.
- **OQ-2 — confirmed as drafted: T10 honours the `diagnose:` dial and skips
  components not set to `auto`.** Verified the review's claim: `diagnose:` is a
  required, enum-validated component field (`lint_monitoring.py:192`) that no
  shipped code reads. Honouring it makes a declared-but-inert surface real, which
  is this feature's whole premise — read policy, do not guess intent. Ignoring it
  would make a validated dial meaningless and would spend money diagnosing
  findings for components whose operator chose `manual`.

The operator's pre-arm review for gate 3 of `FEAT-2026-0049-specfuse-agent-runner`.
Flip each gate-3 WU from `status: draft` → `pending` only after answering the two
open questions above and checking the Cross-surface contracts table below.

## The restructure, done

`G1-PLAN` decided to split the findings classes into their own gate and could not
place it: inserting a gate ahead of the features gate moves the terminal close,
and gate 3's work units were outside its boundary. That insertion is now made.

| Was | Is |
|---|---|
| gate 3 — the agent advances features (`GATE-03.md`) | gate 4 (`GATE-04.md`) |
| `FEAT-2026-0049/G3-CLOSE` in `WU-92-gate-3-close.md` | `FEAT-2026-0049/G4-CLOSE` in `WU-92-gate-4-close.md` |
| — | gate 3 — the agent diagnoses and autofixes findings (`GATE-03.md`, new) |

**No history was rewritten to do it.** The renumbering touched exactly two files:
the features gate, whose status was `open` and which had never been dispatched,
and its terminal close placeholder, whose status was `draft`. No `done` work
unit's frontmatter and no `passed` gate file was edited. The close WU's
acceptance criteria are unchanged — only the gate number it names, and the name
of the `plan-next` WU that will sharpen it (`G2-PLAN` → `G3-PLAN`), which would
otherwise have been left factually wrong.

Gates 1, 2 and 3 are now non-terminal (`close-intermediate` + `plan-next`); gate
4 is terminal (single `close`).

## What gate 2 proved

Gate 2 shipped the provider seam and three action providers in four substantive
work units, first attempt each, for **$6.66 against a $45.50 budget**. It
auto-closed on-plan (`evaluate_auto_close`, predicate=v1).

What it demonstrably established:

- **The loop picks and acts.** `default_providers()` (`run.py:381`) returns three
  real providers reachable from `main()`, and `_select_next` ranks them by policy
  rather than by registration order.
- **The kind vocabulary opened to four**, with `KIND_TRIAGE` and
  `KIND_ESCALATION_ANSWER` joining bugs and features, and the selection order
  settled once — answers first, then bugs and features per `rules.bugs.preempt`,
  then triage.
- **`--max-tokens` enforces a real number.** `ActionOutcome` carries a `spend`
  field and `run_agent` feeds it to `RunBudget.record_tokens` (`run.py:329`),
  which had no caller at all when gate 2 was drafted.
- **Composition without modification held for three classes.** Bugs go through
  `run_bug_lane`, triage through `list_untriaged` + `apply_triage`, answers
  through `escalation`'s constants and renderer. No driven surface was edited.
- **The gap between "a shipped function" and "an action class" is real and
  repeatable.** `apply_triage` records a decision but makes none, so T07 built
  `triage_invoke.py` to the shape `autofix_invoke.py` established. That is the
  second instance of the same pattern, and gate 3 makes it the third.

**The provider protocol survived contact.** T04's escalation trigger asked whether
defining `ActionProvider` before its first consumer would produce something a
later gate has to redesign. Four real providers later, the three verbs
(`advertise` / `execute` / `reconcile`) still fit unchanged, and this unit found
nothing in the findings pair that needs a fourth. `EscalationPayload` and
`ActionOutcome.spend` were additive extensions, exactly as predicted. This is why
this unit drafted rather than escalated.

## What gate 2 deliberately did not prove

- **`reconcile` has never done anything.** All three shipped providers implement
  it as `return None` (e.g. `providers/triage.py:172`). The verb is in the
  protocol and is called by the loop, but no provider has yet had post-execution
  work to do. Gate 3 does not change that — neither findings provider needs it
  either — so the verb remains unexercised, and gate 4's feature provider is the
  last chance for it to earn its place. If it does not, that is a finding for the
  terminal retrospective, not a defect.
- **The spend ledger counts zeros.** `record_tokens` has a caller now, but every
  shipped provider returns `ActionOutcome` with the default `spend=0`: none of
  them recovers a token count from the headless session it launches. So
  `--max-tokens` is wired end to end and still cannot fire on real work. T11's
  second escalation trigger names this rather than letting gate 3 add a fourth
  provider that reports zero silently.
- **Nothing ran unattended.** Every gate-2 behaviour was proven by test, against
  injected runners. No `specfuse-agent run` has executed against this repo's live
  issues, so the cost, the failure modes, and the operator experience of an
  actual run are all still unmeasured.
- **The per-criterion deferred-verification list was never enumerated — twice
  over.** Gate 1 auto-closed (27 criteria, T01–T04) and `WU-93` was drafted to
  reconcile that debt; `WU-93` then auto-closed as well (30 criteria, T05–T08).
  **Both `specfuse:autoclose-debt` markers in `RETROSPECTIVE.md` are still open.**
  `G3-CLOSE-INTERMEDIATE`'s criterion 3 carries the obligation now, and
  `G3-PLAN`'s criterion 4 makes the terminal close instruct it explicitly —
  `specfuse lint` already WARNs that `WU-92`'s body does not.

## What gate 3 must therefore establish

That the agent handles work it can only see through a config this repository does
not have: that a finding issue can be diagnosed and that a diagnosed finding can
be autofixed, both by composing the shipped monitoring functions unmodified, and
that both classes take their place in the selector's ranking without disturbing
the four already there.

And, unavoidably, it must establish the *shape* of a claim this feature has not
had to make before — one proven entirely against fixtures. See below.

## What cannot be proven here, precisely

**This is the reason findings became their own gate**, and it deserves to be
stated exactly rather than as "no live components".

`run_autofix` requires a `monitoring_config` with named components.
`.specfuse/verification.yml`'s `monitoring-example-lint` gate explains why this
repo will never supply one, in its own words: *"this repo is a CLI tool with no
deployable components and will never carry a real monitoring.yml, so a gate
pointed at a live file would fail permanently on an absent file or pass vacuously
forever."* No `monitoring.yml` means no harvester run, which means no
`monitoring-finding` issue has ever been filed here. Both gate-3 providers
therefore advertise an empty list against this repo's live state — correctly, and
that emptiness is itself untestable as a live signal.

**The gate's definition of done is still reachable.** It is deferred, not
unreachable, and the distinction is load-bearing:

- Every criterion in T09, T10 and T11 is met with an injected `runner` and a
  fixture config. That is not a weaker substitute invented for this gate — it is
  the same oracle the shipped function is already held to: `tests/test_autofix_run.py`
  verifies `run_autofix` itself with `_monitoring_config(dial)` returning
  `{"components": [{"name": ..., "autofix": dial}]}` (`:44`). Holding the caller
  to the standard its callee is held to is not a lowered bar.
- The composition, the parse and render path, the decline paths, the escalation
  shapes, the ranking, and the idempotence checks are all fully provable this
  way, because none of them depends on a component existing.

**What is left unproven, itemised, and what would close each:**

| Unproven | What would close it |
|---|---|
| That a real harvester-filed finding issue's body parses to a component name this reader resolves | One `specfuse monitor run` against a repo with a real `monitoring.yml`, producing one real finding issue |
| That a headless analysis session actually returns the five fields `parse_analysis` requires, at a usable rate | One live `specfuse-agent run` against such a repo, with the escalation count on `AnalysisParseError` read afterwards |
| That `decide` reaches `FIRE` on real diagnosis text, rather than declining everything as `unreadable_input` | The same run, with `decide`'s reason distribution read from the run summary |
| That the end-to-end diagnose → autofix handoff works *within one run* (T09's ranking argument depends on it) | The same run, on a repo with at least two findings |

The right home for these at close time is a `kind: externally-verifiable-later`
entry per `close-discipline.md` §2 — a real run in a monitoring-configured repo is
a nameable condition, not an inherent impossibility. **Do not attempt to close the
gap by inventing a `.specfuse/monitoring.yml` for this repository**: it would make
the `monitoring-example-lint` gate's stated reasoning false and would be a fixture
masquerading as a live surface, which is worse than an honest deferral.

## Gate 3's work units

| WU | ID | What it does | Composes | $ |
|---|---|---|---|---|
| `WU-09-findings-seam.md` | T09 | Two kinds and their ranking; the monitoring-config reader; `--monitoring-config` | — (agent-package plumbing over `loop._miniyaml`) | 6.50 |
| `WU-10-findings-diagnose-provider.md` | T10 | Undiagnosed findings analysed, rendered, posted | `monitor.diagnose_cli.render_headless` | 7.50 |
| `WU-11-findings-autofix-provider.md` | T11 | Diagnosed findings decided, recorded, fired, labelled | `monitor.autofix_run.run_autofix` | 6.50 |
| `WU-95-gate-3-close-intermediate.md` | G3-CLOSE-INTERMEDIATE | Gate 3 retro/lessons/docs + the two open auto-close debts | — | 4.50 |
| `WU-96-gate-3-plan-next.md` | G3-PLAN | Gate 4, and sharpening the terminal close | — | 6.00 |

Sum **$31.00**; `GATE-03.md`'s `cost_budget_usd: 38.50` is that plus one
re-attempt of the largest (T10, $7.50), per `planning-discipline.md` §5.

`depends_on`: T10 and T11 each depend on T09 alone — they are independent of each
other and can be dispatched in either order once the seam lands. The closing pair
depends on all three. This is the same fan-out shape gate 2 used, and for the
same reason: neither provider consumes the other's output *in code*, only at
runtime through GitHub.

**Each provider names its shipped function and asserts it is consumed unmodified.**
T10 composes `diagnose_cli.render_headless`; T11 composes
`autofix_run.run_autofix` and passes `autofix_invoke` as its `invoker`. Both WUs'
`Do not touch` sections forbid every file under `specfuse/monitor/` outright, and
both carry an escalation trigger that fires if the composition turns out to
require a change to the driven surface.

**Why T09 exists as a separate unit**, given `GATE-02-REVIEW.md` argued for
*merging* the seam into one WU there. The reasoning is the same and lands the
other way: T05's seam and ledger both edited the same function's plumbing, so
splitting them would have made two WUs declare the same `produces:` path and
serialised them for nothing. Here the seam produces a **new module**
(`monitoring_read.py`) that both providers import, so splitting costs no shared
`produces:` path and buys the thing that mattered in gate 2 — the providers
become thin. T10 and T11 each land one module plus one registry line.

## The ranking decision, and why it is in the review

Both new kinds must be placed in `_select_next`, and priority is policy. Recorded
here so the operator reviews one decision rather than two provider details:

| Kind | Tier | Reasoning |
|---|---|---|
| `escalation-answer` | −1 | unchanged — an answer may cancel queued work |
| `bug` | 0 / 2 | unchanged — `rules.bugs.preempt` |
| **`finding-autofix`** | **0 / 2, with bugs** | `autofix_invoke.build_invocation` launches `/fix-bug`; a fired autofix *is* a bug-lane run reached by a different route. Ranking it elsewhere gives the same work two priorities depending on who noticed it. **OQ-1.** |
| `feature` | 1 | unchanged — `queue:` order |
| **`finding-diagnose`** | **3, ahead of triage** | prepares work rather than closing it, so behind everything that acts — but ahead of triage, because it is the only preparatory class that can unlock acting work *in the same run*: T11 reads comments live at `advertise()`, so a diagnosis posted at iteration 3 is visible at iteration 4 |
| `triage` | 3, sub-rank 1 | position relative to every existing kind unchanged; the sub-rank replaces an ordering that would otherwise depend on provider registration order |

## Default and severity check (`planning-discipline.md` §4)

**No drafted gate-3 WU flips a default or a severity.** Checked per WU, not
assumed:

- **T09** adds two constants, two ranking branches, one new module, and one CLI
  flag. `--max-tokens` / `--max-minutes` / `--max-items` keep their `None`
  (unbounded) defaults; `--monitoring-config` defaults to the documented
  conventional path and an absent file is a normal state, not an error;
  `rules.bugs.preempt` keeps its `False` safe default and its existing tier
  values.
- **T10** posts a comment. It changes no default and no severity; the body it
  posts is `diagnosis.render`'s, unaltered.
- **T11** calls `run_autofix`, which evaluates `autofix.decide` and applies
  `AUTOFIX_FAILED_LABEL` internally. The provider re-decides nothing:
  `CONFIDENCE_THRESHOLD`, `FIX_SCOPES`, `DAILY_CAP` and the fingerprint rate
  limit are all read by the driven surface, and criterion 4 asserts the provider
  holds no copy.

**The two changes that come closest, stated rather than buried.**

1. **`rules.bugs.preempt` gains a second meaning.** An operator who set it for
   bugs alone would find it also lets a monitoring autofix jump the feature
   queue. The default is unchanged and the dial's *value* is unchanged — but its
   *scope* is not, which is why it is OQ-1 rather than a footnote. Blast radius
   in this repo: zero, since no finding issue can exist here.
2. **The `diagnose:` dial becomes load-bearing for the first time.**
   `lint_monitoring.py` validates it (`DIAGNOSE_VALUES` at `:43`) and no shipped
   code reads it. T10 is drafted as its first consumer, gating advertisement on
   `auto`. That is not a default flip — the value comes from the operator's own
   `monitoring.yml` — but a previously inert setting becoming behaviour is
   exactly the class of change §4 exists to surface, so it is OQ-2. This is the
   same shape as gate 2's nearest miss, where `--max-tokens` became enforceable
   for the first time.

**No §4 runtime probe is therefore required to arm this gate.** If arming review
answers OQ-1 or OQ-2 in a way that turns either into a real flip, that WU may not
be armed on "mechanical, nothing design-open" and needs the local probe first.

## Cross-surface contracts (`/authoring-work-units` §8)

Values the drafted WUs name that live in code the WUs do not own. Verify each
against its source before arming; none was invented by this draft, and each WU's
`Do not touch` forbids re-spelling it locally.

| Value | Authoritative source | Used by | Checked |
|---|---|---|---|
| `FINDING_LABEL` = `monitoring-finding` | `specfuse/monitor/issues.py:54` | T10, T11 | ☐ |
| `**Component:** <name>` line in a finding-issue body | `specfuse/monitor/issues.py:137` (`_render_body`) | T09 | ☐ |
| Finding marker `<!-- specfuse:finding fingerprint=... -->` — read by `run_autofix`, never written by the agent | `issues.py:60`, read at `autofix_run.py:55` | T11 | ☐ |
| `diagnosis.parse(body)` as the only "is it diagnosed?" test; marker prefix never spelled locally | `specfuse/monitor/diagnosis.py:33,106` | T10, T11 | ☐ |
| `render_headless(raw)` → body; `AnalysisParseError` on bad input | `specfuse/monitor/diagnose_cli.py:88,30` | T10 | ☐ |
| The five required analysis fields `root_cause` / `evidence` / `candidate_fix` / `confidence` / `fix_scope`, and `FIX_SCOPES` | `diagnose_cli.py:27`, `diagnosis.py:31` | T10 | ☐ |
| `run_autofix(*, runner, invoker, repo, finding_issue_number, monitoring_config, component)` → `AutofixRunResult(decision, reason, outcome)`, `outcome is None` when nothing fired | `specfuse/monitor/autofix_run.py:164,78` | T11 | ☐ |
| Decisions `FIRE` / `ROUTE_TO_HUMAN` / `DECLINE` and the `REASON_*` strings | `specfuse/monitor/autofix.py:43-58` | T11 | ☐ |
| `AUTOFIX_FAILED_LABEL` = `auto-fix-attempted-failed`, applied by `run_autofix`, never by the provider | `specfuse/monitor/autofix_state.py:64` | T11 | ☐ |
| `autofix_invoke` passed as `run_autofix`'s `invoker=`, exactly as `autofix_run.main` does | `autofix_run.py:235` | T11 | ☐ |
| Component schema keys `components[].name` / `.diagnose` / `.autofix`; `DIAGNOSE_VALUES` = `{manual, auto}` | `specfuse/loop/lint_monitoring.py:43,60` | T09, T10 | ☐ |
| `_miniyaml.parse` as the monitoring-config reader | `autofix_run.py:230-231` | T09 | ☐ |
| `gh issue comment <n> --repo <r>` as the in-package comment shape | `specfuse/agent/providers/answers.py:207` | T10 | ☐ |
| `build_invocation` / result-reader split as the headless-invoker shape | `specfuse/agent/triage_invoke.py:29,62` | T10 | ☐ |

## Risks to weigh before arming

- **Two providers now read outside the snapshot.** T08 already did it for issue
  comments; T10 and T11 both do it again, and per finding per loop iteration.
  Read-only, and the same shape `autofix_run._read_finding_issue` uses, but "the
  selector reads a value, not a call" is now more aspiration than description.
  The fix — extending T02's snapshot to carry comments — is a gate-1 surface
  change and stays out of bounds; the honest move at gate 4's close is to say so
  rather than to keep calling it a snapshot.
- **`--max-tokens` still cannot fire, and gate 3 adds two more spenders.** Both
  findings providers launch headless sessions and, like the three before them,
  will report `spend=0` unless the invoker can recover a token count. T11's
  escalation trigger refuses to report zero as if it were measured, which is the
  most this gate can honestly do; making the cap real needs a spend source that
  no shipped invoker has.
- **A findings-heavy repo starves triage entirely.** Findings-diagnose now sits
  ahead of triage, which already ranked last. A repo with more findings than
  `--max-items` will never triage anything. Deliberate and reversible by policy —
  same trade-off gate 2 accepted for triage — but the failure mode compounds.
- **`DECLINE` reported as completed.** T11 maps a declined autofix to a completed
  item, so a run against a repo with `autofix: "off"` everywhere reports items
  completed having changed nothing. The alternative turns a working safety dial
  into an alarm; the reason string is in the run summary either way. Worth
  agreeing with explicitly at arming, because it is the row of T11's outcome
  table most likely to surprise on a first live run.
- **A new consumer-visible surface lands here.** `specfuse-agent` gains a
  `--monitoring-config` flag. `G4-CLOSE`'s contract-change enumeration and the
  `CHANGELOG.md` `Unreleased` entry must carry it alongside the console script
  itself; it is recorded here so the terminal close does not have to rediscover
  it from the diff.
- **The arm predicate will not clear this gate on its own.** `arm_eval`'s
  drift-cap and budget-projection classes have been fired since gate 2 was
  drafted — `PLAN.baseline.json` snapshots 7 work units totalling $34.50, and
  everything drafted after baselining counts as added. Gate 2 was armed by hand
  for the same reason. This is the predicate working on a feature baselined
  before two of its four gates were planned, not a new signal about gate 3.
