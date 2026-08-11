---
open_questions:
  - "OQ-1: the findings gate is decided but not inserted — inserting it moves the terminal close from gate 3 to gate 4, which was outside G1-PLAN's boundary. G2-PLAN (WU-94) is drafted to own the restructure as its first acceptance criterion. Confirm that placement, or do the renumbering by hand before arming gate 2."
  - "OQ-2: T08 removes the `needs-human` label once it has parsed and acknowledged an operator's answer, before anything acts on that answer. That empties the human inbox on the strength of an acknowledgment comment. Confirm, or say the label stays until the chosen option is executed — one acceptance criterion changes either way."
---

# Gate 2 review — drafted by `G1-PLAN`, 2026-08-11

The operator's pre-arm review for gate 2 of `FEAT-2026-0049-specfuse-agent-runner`.
Flip each gate-2 WU from `status: draft` → `pending` only after working the two
open questions above and the Cross-surface contracts table below.

## What gate 1 proved

Gate 1 shipped the conductor's stopping properties with no action class attached,
in four substantive work units, first attempt each, for **$5.95 against a $36.00
budget**. It auto-closed on-plan (`evaluate_auto_close`, predicate=v1).

What it demonstrably established:

- **One agent per repo.** `acquire_agent_lock` takes `.specfuse/.agent.lock`,
  separate from the driver's `.specfuse/.loop.lock`, and a second agent refuses
  to start naming the holder's path rather than raising `BlockingIOError`
  (`run.py:61-74`, `AgentLockHeldError`).
- **One snapshot, no calls mid-decision.** `gather_snapshot` collects policy
  dials, `queue:`, open issues, open PRs, and feature-folder state into one
  frozen `AgentSnapshot`, issuing only non-mutating `gh ... list` reads, with a
  failed section landing as empty-plus-`*_error` rather than as a partial object
  that reads authoritative.
- **The loop terminates and says why.** `run_agent` drains, and every exit path
  produces exactly one machine-readable stop reason from a closed set
  (`drained` / `cap` / `pause`), with the run summary reporting *actual* elapsed
  minutes rather than the configured cap — so D3's accepted overshoot is visible
  instead of hidden.
- **A failing provider parks, it does not abort.** `provider.execute()` raising
  is caught, escalated for that item, and the run continues (`run.py:288-294`).
- **Priority is policy, not judgment.** `rules.bugs.preempt` decides bugs vs
  features and `queue:` order settles features among themselves; anything policy
  cannot place is escalated rather than guessed.

## What gate 1 deliberately did not prove

`GATE-01.md` says it plainly and it is worth repeating before arming: the
selector ran against an **empty provider registry**, so the gate could not show
that it picks *well* — only that it terminates, respects its budget, and stops
when told. Selection quality is gate 2's to demonstrate.

Two further gaps are not in `GATE-01.md`, because nothing in gate 1 could have
surfaced them. Both are now gate-2 work (T05):

1. **The selector's kind vocabulary is closed at two.** `_select_next`
   (`run.py:190-213`) ranks `KIND_BUG` and `KIND_FEATURE`; every other kind falls
   into `unresolved` and is parked with `unknown item kind`. That is correct
   behaviour for gate 1 — refusing to guess — but it means a gate-2 provider
   advertising any new kind would be escalated, never executed.
2. **`--max-tokens` cannot fire.** `RunBudget.record_tokens`
   (`budget.py:88`) has **no caller anywhere in the repo**
   (`grep -rn "record_tokens" specfuse/ tests/` returns only its definition), and
   `ActionOutcome` carries no spend field, so `may_start_next_item()` compares a
   counter that never leaves zero. With zero providers nothing spends, so gate 1
   could not have caught it. Gate 2 is where the agent starts invoking headless
   sessions that cost money, so the cap must become real before the providers
   land — otherwise the gate ships four spenders behind a cap that is decoration.

Also inherited: gate 1 auto-closed, so its per-criterion deferred-verification
list was never enumerated — **27 criteria across T01–T04** carry the
`specfuse:autoclose-debt` marker. `G2-CLOSE-INTERMEDIATE` (WU-93) is drafted to
reconcile them; that obligation is now on a work unit rather than in a comment.

## What gate 2 must therefore establish

That the loop **picks and acts**: that a real provider can be registered, ranked
by policy, executed, and reconciled; that the money it spends is counted against
the cap the operator set; and that the agent reads an operator's answer before
spending anything on work that answer might have overruled.

## The sizing decision

**Decision: split. Findings become their own gate; the feature is four gates.**

PLAN.md recorded the risk and named the split line in advance — "the natural
split is findings into their own gate" — and left the call to this unit with
evidence in hand. Three findings settled it.

**1. Drafting against real code grew the gate from five items to seven.** The
sketch was four providers plus answered escalations. Against the shipped
conductor it is: the selector seam (new — nothing can be selected without it),
the spend ledger (new — see above), bugs, triage, findings-diagnose,
findings-autofix, answered escalations. Two of those seven did not exist as
concepts when the gate was sketched, and both are prerequisites rather than
optional polish. Gate 1 ran four substantive WUs; seven is not the same gate.

**2. The findings pair is bigger than the sketch priced it.** The gate map reads
"findings-diagnose (`diagnose_cli`)", which implies a compose. It is not:

- `diagnose_cli.render_headless(raw)` *renders* a diagnosis body from analysis
  JSON. Its own docstring says it "produces a comment body; it does not post
  one, and shells out to nothing." It neither produces the analysis nor posts the
  result. A findings-diagnose provider therefore needs a headless analysis
  invoker **and** a posting path on top of the shipped function — the same shape
  as triage's classifier gap, but with a second half.
- `run_autofix` needs `monitoring_config` with named components plus an
  `Invoker`; resolving the component for a finding issue is provider work that
  does not exist yet.

**3. Findings cannot be dogfooded in this repository at all — the other classes
can.** `.specfuse/verification.yml`'s `monitoring-example-lint` gate says why, in
its own words: *"this repo is a CLI tool with no deployable components and will
never carry a real monitoring.yml."* `run_autofix` requires exactly that config.
So the findings providers can only ever be exercised against fixtures here, while
bugs, triage, and answered escalations can run against this repo's own live
issues. That is a materially different verification character, and it is a better
reason to draw a gate boundary than size alone: a gate whose definition of done
cannot be demonstrated on the repo it ships in should be reviewed as its own
claim, not folded into one that can.

**Against the split**, honestly: the four providers are a fan-out, not a chain —
none consumes another's output, so a late discovery in one cannot invalidate
another, which is the coupling a gate boundary usually exists to contain. And a
gate costs a full closing sequence (~$10.50 at the §5 floors) plus a human arming
halt. That argument is real; it is outweighed by point 3, and by the fact that
gate 2 is the first gate in which the agent spends money against a live repo —
the arming checkpoint is the operator's only look before it does, and a smaller
first acting gate is worth more than a saved closing sequence.

**What the split does not do here.** Inserting a findings gate ahead of the
features gate moves the terminal close from gate 3 to gate 4. Gate 3's work units
— including that close placeholder — are outside this unit's boundary, so the
insertion is *decided and recorded*, not performed. `G2-PLAN` (WU-94) owns it as
its first acceptance criterion, and OQ-1 puts it in front of the operator now
rather than at gate 3. Until it happens, PLAN.md's gate map reads three gates and
the plan of record is four; both documents say so.

**One WU was merged, and it is worth naming so the count is not read as a trim.**
The selector seam and the spend ledger were drafted separately and folded into
T05. Both edit the same function's plumbing in the same file, splitting them would
have made two WUs declare `produces: specfuse/agent/run.py` (a
`check_produces_satisfiability` warning) and serialised them for no benefit. T05
carries seven acceptance criteria as a result — above the 2–5 that
`/authoring-work-units` §6 calls typical, and the reason is recorded here rather
than hidden.

## Gate 2's work units

| WU | ID | What it does | Composes | $ |
|---|---|---|---|---|
| `WU-05-provider-seam.md` | T05 | Kind vocabulary, provider registry reachable from `main()`, spend ledger wired to `record_tokens` | — (agent-package plumbing) | 8.00 |
| `WU-06-bugs-provider.md` | T06 | Bug issues end to end | `loop.bug_lane_run.run_bug_lane` | 5.50 |
| `WU-07-triage-provider.md` | T07 | Untriaged issues classified and recorded | `loop.triage.list_untriaged` + `apply_triage` | 7.00 |
| `WU-08-answered-escalations.md` | T08 | Operator answers parsed and acknowledged | `loop.escalation` constants + renderer | 6.50 |
| `WU-93-gate-2-close-intermediate.md` | G2-CLOSE-INTERMEDIATE | Gate 2 retro/lessons/docs + gate-1 auto-close debt | — | 4.50 |
| `WU-94-gate-2-plan-next.md` | G2-PLAN | The gate restructure, then the findings gate | — | 6.00 |

Sum **$37.50**; `GATE-02.md`'s `cost_budget_usd: 45.50` is that plus one
re-attempt of the largest (T05, $8.00), per `planning-discipline.md` §5.

`depends_on`: T06, T07, and T08 each depend on T05 alone — they are independent
of each other and can be dispatched in any order once the seam lands. The closing
pair depends on all four.

**Selection order**, decided in T05 rather than per-provider, because priority is
policy and a per-provider guess is how it stops being policy: answered
escalations first (an answer may cancel work already queued); then bugs and
features exactly as gate 1 ranks them, `rules.bugs.preempt` unchanged; then
triage last (classification prepares work for a later run rather than closing
any, so under a cap the agent should spend its remaining items acting). If the
operator wants triage first, that is a policy dial for a later feature, and T05's
escalation trigger tells the session to stop rather than mint an
`agent-policy.yml` key for it.

## Default and severity check (`planning-discipline.md` §4)

**No drafted gate-2 WU flips a default or a severity.** Checked per WU, not
assumed:

- **T05** adds constants, a registry function, and a spend field. `--max-tokens`,
  `--max-minutes`, and `--max-items` keep their `None` (unbounded) defaults;
  `rules.bugs.preempt` keeps its `False` safe default and its existing tiers; no
  check changes severity.
- **T06** calls `run_bug_lane`, which evaluates `evaluate_merge_guardrails` and
  honours `rules.bugs.automerge` internally. The provider passes `policy_path`
  through and reads no dial itself.
- **T07** passes `snapshot.triage_auto` to `apply_triage(auto=...)` and is
  explicitly forbidden from re-implementing the low-confidence→`question`
  downgrade. The dial's meaning is unchanged.
- **T08** writes a comment and removes a label at runtime. Neither is a default
  or a severity in the codebase; the label lifecycle is OQ-2.

**The one change that comes closest, stated rather than buried.** T05 makes
`--max-tokens` enforce a real number for the first time. That is not a default
flip — the default stays `None`/unbounded — but it *is* a behaviour change for
anyone who passed `--max-tokens` under gate 1's build and observed no
enforcement. Since gate 1 registers no providers, no such run can have done
anything but drain immediately, so the blast radius is zero. Recorded because
"nothing flips" claims should name their nearest miss.

No §4 runtime probe is therefore required to arm this gate.

## Cross-surface contracts (`/authoring-work-units` §8)

Values the drafted WUs name that live in code the WUs do not own. Verify each
against its source before arming; none was invented by this draft, and each WU's
`Do not touch` forbids re-spelling it locally.

| Value | Authoritative source | Used by | Checked |
|---|---|---|---|
| `run_bug_lane(runner, repo, issue_number, *, working_dir, policy_path, now)` → `BugLaneResult(outcome, reason, pr_number)` | `specfuse/loop/bug_lane_run.py:284` | T06 | ☐ |
| Outcomes `merged` / `declined` / `refused` / `could_not_proceed`; the lane self-escalates on the last two | `bug_lane_run.py:62-67`, `:306-308` | T06 | ☐ |
| `IssueSummary.triage_category` populated from the body's triage marker | `specfuse/agent/state.py:157-169` | T06, T07 | ☐ |
| `list_untriaged(...)` rows carry `already_structured` | `specfuse/loop/triage.py:211` | T07 | ☐ |
| `apply_triage(..., auto=True)` downgrades non-`high` confidence to `question` | `specfuse/loop/triage.py:126` | T07 | ☐ |
| `triage.CATEGORIES` / `route_for` / `label_for` — `ValueError` on an unknown category | `specfuse/loop/triage.py:69-88` | T07 | ☐ |
| `NEEDS_HUMAN_LABEL` = `needs-human` | `specfuse/loop/escalation.py:17` | T08 | ☐ |
| Escalation marker `<!-- specfuse:escalation id=... -->` | `specfuse/loop/escalation.py:44` | T08 | ☐ |
| The `Reply with a number` numbered-answers section and its two-option invariant | `escalation.py:97-103`, `validate_escalation_body` | T08 | ☐ |
| `PARKED_LABEL` = `escalation-parked`, never removed by the agent | `specfuse/loop/notify_sla.py:40` | T08 | ☐ |
| `autofix_invoke.build_invocation` / `classify_outcome` as the headless-invoker *shape precedent* (read, not imported) | `specfuse/monitor/autofix_invoke.py:32,53` | T07 | ☐ |

## Risks to weigh before arming

- **The provider protocol itself survived contact.** T04's escalation trigger
  asked whether defining `ActionProvider` before its first consumer would produce
  something gate 2 has to redesign. Drafting four real providers against it: the
  three verbs (`advertise` / `execute` / `reconcile`) fit all four action classes
  unchanged, and `handled_ids` correctly prevents a re-advertising provider from
  stalling the run. What needs extending is the *ranking table* and the
  *outcome record*, both additive and both T05's job. That is an extension, not a
  redesign, so this unit did not escalate.
- **A provider reads outside the snapshot.** T08 must fetch issue comments
  itself (`gh issue view --json comments`) because `state._read_issues` requests
  only `number,title,labels,body`. Read-only, and the same shape
  `autofix_run._read_finding_issue` uses, but it does soften "the selector reads
  a value, not a call." The alternative — extending T02's snapshot — is a gate-1
  surface change and was left out of bounds deliberately.
- **Triage ranks last, so a tight `--max-items` never triages.** Deliberate (see
  the selection order above) and reversible by policy, but it means a repo whose
  issues are all untriaged will look drained to a capped run. Worth knowing
  before the first live run.
- **T07 introduces a second headless-invocation surface** (`triage_invoke.py`)
  alongside `autofix_invoke.py`. Two invokers with the same shape and no shared
  base is a duplication the next feature may want to fold; it is not worth
  building an abstraction for two.
