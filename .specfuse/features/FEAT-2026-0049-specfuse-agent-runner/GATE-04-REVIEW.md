---
open_questions:
  - "OQ-1: `rules.features.wip_limit` is validated by agent_policy.py and read by no shipped code. T12 is drafted to be its first consumer, capping how many distinct features one run advances, taking them in `queue:` order, with entries that are already done consuming no slot. Confirm, or say the limit counts something else (open feature PRs, features `active` in the repo regardless of the queue) — T12's criterion 4 and T14's criterion 6 change either way."
  - "OQ-2: `rules.features.gate_review` (`human` | `auto`, plus the per-feature `overrides` map) is likewise validated and unread. T14 is drafted so `human` escalates an awaiting-review halt with a `gate-review` needs-human issue, and `auto` records the halt in the run summary and files nothing — because the agent cannot arm a gate, and arming is `/arm-gate`'s job. Confirm, or say `auto` should escalate too, which makes the dial inert for v1. T14's criterion 6 changes either way."
  - "OQ-3: after T14, a bare `specfuse-agent run` dispatches the loop driver against the `queue:` top unattended. That is the largest blast-radius change this feature makes, and it is drafted with no opt-in flag — registered in `default_providers()` like every other provider, on the grounds that D4 (`autonomy_default: auto`) and the roadmap goal both already say so. Confirm, or say feature advancement must be opt-in, which adds a CLI flag and a consumer-visible surface. T14's criterion 7 changes either way."
---

# Gate 4 review — drafted by `G3-PLAN`, 2026-08-11

## Open questions — decided by the AGENT, not the operator (2026-08-11T05:55:32Z)

**The operator was asleep.** Standing authorization of 2026-08-10 to arm gate 3
unattended, given after being told any operator-owned question would be decided
by the agent and marked as such. Gate 4 was armed under the same authorization
and the same caveat. **None of these has been reviewed by the operator.**

- **OQ-1 — confirmed as drafted.** `rules.features.wip_limit` caps how many
  distinct features one run advances, in `queue:` order, with already-done
  entries consuming no slot. Verified the claim: the key is validated at
  `agent_policy.py:383` and read by nothing. The deciding argument against the
  alternative reading (count open feature PRs) is that `budgets.max_open_prs`
  already exists and already counts exactly that — making `wip_limit` a second
  name for it would leave the repo with two keys for one quantity.
- **OQ-2 — confirmed as drafted.** `rules.features.gate_review: human` escalates
  an awaiting-review halt as a `gate-review` needs-human issue; `auto` records
  the halt in the run summary and files nothing. Verified: the dial is validated
  at `agent_policy.py:376` and read by nothing (every other `gate_review` hit in
  the tree is `gate_review_filename`, an unrelated helper). Reasoning: the agent
  cannot arm a gate — arming is `/arm-gate`'s job and requires judgment. If
  `auto` escalated too, the dial would be inert, which is the outcome to avoid
  when the whole feature exists to make declared policy real.
- **OQ-3 — confirmed as drafted, and this is the one to review first.** After
  T14, a bare `specfuse-agent run` dispatches the loop driver against the
  `queue:` top unattended, with **no opt-in flag**. This is the largest
  blast-radius change the feature makes.

  Reasoning for confirming rather than adding a flag: the roadmap goal funds
  exactly this — *"operator-launched, run-to-drain … pick the highest-value
  action under policy (bugs preempt per rules; queue top for features)"* — so
  requiring a flag would contradict the approved goal, not merely narrow it. The
  blast radius is bounded by machinery already built and tested: the agent lock,
  the item-boundary caps, and the PAUSE marker.

  **The agent nonetheless recommends the operator review this specific decision
  before merge.** It is the one call made overnight where the safe option
  (opt-in) and the funded option (as drafted) diverge, and it was resolved toward
  the funded one. Reversing it means adding a CLI flag and a consumer-visible
  surface — T14's criterion 7.

The operator's pre-arm review for the terminal gate of
`FEAT-2026-0049-specfuse-agent-runner`. Flip each gate-4 WU from `status: draft`
→ `pending` only after answering the three open questions above and checking the
Cross-surface contracts table below.

## What gate 3 proved

Gate 3 shipped the findings seam and both findings providers in three
substantive work units, first attempt each, for **$4.94 against a $38.50
budget** — 12.8% of the gate's budget and 24% of its own planned sum. It is also
the first gate of this feature whose close was forced to run rather than
auto-closing, and that close is what discharged gate 1's and gate 2's accumulated
auto-close debt (27 and 30 criteria).

What it demonstrably established:

- **The provider protocol took two more implementers without changing.**
  `advertise` / `execute` / `reconcile` still fit; neither findings provider
  needed a fourth verb. Five providers across two gates now satisfy the protocol
  T04 defined before it had a single consumer. **This is why this unit drafted
  rather than escalated** — `G3-PLAN`'s first escalation trigger fires only if
  the protocol failed to survive the findings pair, and `RETROSPECTIVE.md`
  § "What actually happened" records that it did.
- **Composition without modification held for a fifth and sixth class.** No file
  under `specfuse/monitor/` was edited; `render_headless` and `run_autofix` were
  consumed as they shipped.
- **The selector's vocabulary reached six kinds** with a ranking exercised as a
  whole (`test_full_kind_ordering_with_findings_inserted`), not per provider.
- **The "shipped function is not an action class" gap is now a pattern, not an
  anecdote.** `diagnose_invoke.py` is the third module built to the shape
  `autofix_invoke.py` established, after `triage_invoke.py`.

## What gate 3 deliberately did not prove

- **`reconcile` has still never done anything — across five providers.** All five
  return `None`. Gate 2's review named gate 4's feature provider as the verb's
  last chance to earn its place; gate 3's retrospective went further, saying the
  sample is now large enough to read the protocol as "two verbs and a hook nobody
  has needed." See § "The `reconcile` verdict" below.
- **The spend ledger still counts zeros.** No provider anywhere sets
  `ActionOutcome.spend`; `--max-tokens` is wired end to end and cannot fire on
  real work. Two gates old now, and gate 4 adds a sixth spender.
- **Nothing has ever run unattended.** Every behaviour in gates 1–3 was proven by
  test against injected runners. No `specfuse-agent run` has executed against
  this repository's live issues, so the cost, the failure modes and the operator
  experience of a real run remain unmeasured. Gate 4 does not change that, and
  the terminal verdict must say so rather than implying otherwise.
- **Gate 3's own criteria were met against fixtures, not live surfaces.** Ten
  criteria are enumerated individually in `RETROSPECTIVE.md`
  § "Gate 3 — the criteria met only against fixtures", each with the live
  condition that would close it. All are `kind: externally-verifiable-later`.
- **Two clauses are structurally unreconcilable in any close session.** The
  red-before-green half of eleven criteria (T01#1 … T11#1) and the four
  no-file-under-`specfuse/loop/`-was-edited diff claims (T06#2, T07#2, T10#2,
  T11#2) both need `git`, and a closing session runs no `git` command by
  contract. Gate 3's close named them individually and told `G4-CLOSE` to carry
  them as `kind: inherent` rather than deferring them again.

## What gate 4 must therefore establish

That the agent advances a feature: that it reads the `queue:` top, invokes the
driver **as a subprocess**, reads what came back correctly enough to tell six
different halts apart, escalates the ones a human owns, parks the ones it cannot
work, and moves to the next entry — all without the driver changing, and without
drafting anything.

And one thing no earlier gate had to establish: that **the agent can be pointed
at the loop itself without becoming part of it.** Gates 1–3 built a conductor
over GitHub issues and monitoring findings; gate 4 is the first where the thing
being driven is the same machinery driving the work. The subprocess invariant is
the whole of that separation.

## Gate 4's work units

| WU | ID | What it does | Composes | $ |
|---|---|---|---|---|
| `WU-12-queue-workability.md` | T12 | Five dispositions for a queue entry; `wip_limit` / `gate_review` readers | `loop.agent_policy` + T02's `FeatureSummary` | 5.50 |
| `WU-13-driver-invoke.md` | T13 | `specfuse run` as a subprocess; six halt classes | the driver, as a subprocess and nothing else | 6.00 |
| `WU-14-feature-provider.md` | T14 | Advertise the queue, execute, escalate, switch | T12 + T13 + `loop.escalation` | 6.50 |
| `WU-92-gate-4-close.md` | G4-CLOSE | Terminal close: three gates' deferrals, verdict, changelog | — | 5.00 |

Sum **$23.00**; `GATE-04.md`'s `cost_budget_usd: 29.50` is that plus one
re-attempt of the largest (T14, $6.50), per `planning-discipline.md` §5.

`depends_on`: T12 and T13 each depend on nothing and can be dispatched in either
order — they produce different modules with no shared `produces:` path and
neither imports the other. T14 depends on both. This is a **fan-in**, where gates
2 and 3 both used a fan-out, and the reason is that here the provider genuinely
consumes both seams *in code*: `select_workable` decides what to advertise and
`advance_feature` decides what the outcome is.

**On the estimates.** Gate 3's review deliberately declined to correct downward
on two gates of evidence, on the grounds that shrinking a padding rule from an
outlier is the failure `planning-discipline.md` §5 names. There are now eleven
substantive work units across three gates, every one a first-attempt pass, with
actual spend of $5.95 / $6.66 / $4.94 against planned sums of $29.50 / $39.50 /
$20.50 — a distribution, not an outlier. The estimates above are corrected
modestly (roughly 10-15% below gate 3's comparable units) rather than to the
observed median of about $1.50: the gate budget's one-re-attempt headroom is
sized off the largest estimate, and collapsing the estimates would collapse the
headroom with them. `G4-CLOSE` stays at the §5 `close` floor of $5.00 even though
this close has more to reconcile than any before it, because §5 is explicit that
a closing-WU retry is a defect to diagnose rather than a cost to budget for.

## Halt classification — the decision, and the evidence it needs no driver change

`G3-PLAN`'s second escalation trigger fires if classifying the driver's halt
needs the driver to report something it does not currently report. It does not,
and this is the evidence, read from the shipped source rather than assumed.

`specfuse.loop.loop.run` returns exactly three exit codes, and the code alone is
ambiguous in both directions that matter:

| rc | Returned at | What it can mean | Disambiguated by |
|---|---|---|---|
| `0` | `loop.py:7414` | a gate completed and awaits review | `GATE-NN.md` `status`, `PLAN.md status` |
| `0` | `loop.py:6096` | every gate already `passed` | `PLAN.md status` |
| `0` | `loop.py:6127` | `--prepare-only` stopped early | not reachable — the agent passes no such flag |
| `2` | `loop.py:6185` | the gate holds `draft` work units | the exit code alone |
| `1` | `loop.py:7260` | a work unit blocked after its attempts | a `human_escalation` row appended to `events.jsonl` |
| `1` | `loop.py:6109` | another driver holds the tree lock | no such row; `stderr` carries the message |
| `1` | `loop.py:6059`, `:7437` | malformed `verification.yml`; bookkeeping commit rejected | same |

Every disambiguator is a file the agent already reads or a stream the subprocess
already returns. The one place the exit code lies by omission — all gates
`passed` while `PLAN.md` is not `done` — is documented in the driver's own
comment (`loop.py:6089-6091`) as meaning the terminal flips were withheld, so
T13 classifies it `HALT_AWAITING_REVIEW` rather than `HALT_FEATURE_DONE`.

**Consequence for arming:** if a reviewer finds a halt this table cannot place,
that is a plan change and not a gate-4 work unit, and T13's escalation trigger
says so in the WU.

## Decisions taken here

Recorded so the operator reviews them once rather than finding them inside three
work units. None is an open question — none is a policy the operator owns.

**D-1 — the subprocess runs `specfuse run`, and the command is a parameter, not
a flag.** `GATE-04.md` names `specfuse run`; T13 defaults to it and takes the
command as a keyword argument so tests can inject one. No CLI flag is added.
**The consequence worth knowing, in this repository specifically:** `specfuse
run` delegates to `specfuse.loop.loop:main` inside the *installed* suite
(currently 0.11.0), so a dogfood run here drives the installed driver, not the
working tree's. That is the second half of #1040, and it is correct for every
target project — a project does not run the driver from a checkout. Adding a
`--driver-command` flag would be a new consumer-visible surface for a
this-repo-only concern.

**D-2 — the agent never pre-judges whether a gate is armed.** T12 classifies an
unarmed feature `WORKABLE`; the driver's exit code `2` is the authority. A second
copy of the arm predicate inside the agent is exactly the drift
`/authoring-work-units` §8 exists to prevent, and it would go stale the first
time `arm_eval` changes. The price is one cheap driver invocation per unarmed
feature per run, which dispatches nothing.

**D-3 — the two unused escalation categories are used, not extended.**
`escalation.py:21` already declares `drafting-needed` and `gate-review`; every
shipped provider uses `blocked-wu` and nothing has ever used those two. Gate 4 is
their first consumer. No category is minted.

**D-4 — `HALT_BLOCKED` carries an escalation payload.** The driver writes the
`human_escalation` event and the work unit's frontmatter and files **no** GitHub
issue — verified: `emit_escalation` appears nowhere in `loop.py`. This is the
mirror image of `providers/bugs.py:89-93`, where the bug lane files its own issue
and the provider deliberately passes `escalation=None`. Getting it backwards
produces either a silent block or a duplicate issue, so it is stated rather than
inferred.

## The `reconcile` verdict

Gate 2's review named this gate's provider as the verb's last chance to earn its
place. **T14 is drafted to return `None` like the five before it**, and that is a
decision, not an oversight: the feature provider's post-execution work — filing
the escalation, recording spend — is already done by the loop between `execute`
and the next iteration, and inventing a use for `reconcile` to justify the verb
would be worse than reporting it honestly. `G4-CLOSE` therefore inherits a
finding it can state plainly: across six providers and four gates, `reconcile`
was called every time and did nothing every time, and a future feature should
either delete the verb or name the case that needs it.

## Default and severity check (`planning-discipline.md` §4)

**No drafted gate-4 WU flips a default or a severity.** Checked per WU against
the drafted criteria, not assumed — and therefore **no §4 runtime probe is
required to arm this gate**, and none was run.

- **T12** adds a new module and two policy readers. Both readers take the
  conservative value when the policy is absent or the key is missing —
  `wip_limit` defaults to `1` and `gate_review` to `"human"`, matching
  `.specfuse/agent-policy.yml.example`'s own shipped values. It adds a public
  alias in `state.py` and changes no behaviour reachable from `gather_snapshot`.
- **T13** reads exit codes and frontmatter. It changes no default, no severity,
  and nothing about what a halt *is* — only about what the agent calls it.
  `GATE-04.md`'s arming discipline asks specifically whether any WU "changes what
  a halt means rather than only reading it": it does not. The driver's behaviour
  on every one of the seven rows above is untouched.
- **T14** registers a provider and reads two dials. `KIND_FEATURE` already ranks
  at tier 1 in `_select_next` and its ranking is unchanged; `rules.bugs.preempt`
  keeps its `False` safe default and its existing tier values;
  `--max-tokens` / `--max-minutes` / `--max-items` keep their `None` (unbounded)
  defaults.

**The two changes that come closest, stated rather than buried.**

1. **Two validated-but-inert dials become load-bearing at once.**
   `rules.features.gate_review` and `rules.features.wip_limit` are enforced by
   `agent_policy.py:371-411` and read by no shipped code; T12 is their first
   consumer. This is the same shape as gate 3's `diagnose:` dial and it is not a
   default flip — the values come from the operator's own `agent-policy.yml`. It
   is OQ-1 and OQ-2 rather than a footnote for one reason gate 3's equivalent did
   not have: **the blast radius here is not zero.** This repository's live
   `.specfuse/agent-policy.yml` really does set `gate_review: human`,
   `wip_limit: 1` and `queue: [FEAT-2026-0049]`, so the first `specfuse-agent
   run` after this gate lands would attempt to advance *this feature*.
2. **What `specfuse-agent run` does changes shape, not degree.** Before T14 the
   command could file bug PRs, triage issues, answer escalations, post
   diagnoses and fire autofixes. After it, the same command dispatches the gate
   driver, which commits. No default value changes and no severity is raised, so
   §4's probe is not triggered — but it is the largest single expansion of what
   an unattended run can do, which is why it is OQ-3.

## Cross-surface contracts (`/authoring-work-units` §8)

Values the drafted WUs name that live in code the WUs do not own. Verify each
against its source before arming; none was invented by this draft, and each WU's
`Do not touch` forbids re-spelling it locally.

| Value | Authoritative source | Used by | Checked |
|---|---|---|---|
| Exit codes `0` / `1` / `2` and their return sites | `specfuse/loop/loop.py:6059, 6096, 6109, 6127, 6185, 7260, 7414, 7437` | T13 | ☐ |
| `human_escalation` event type and its `reason` payload field | `loop.py:6631, 6663, 7176, 7242` | T13 | ☐ |
| `--feature` accepts a bare `FEAT-YYYY-NNNN` as well as a directory name | `loop.py:7692` | T13 | ☐ |
| `specfuse run` delegates to `specfuse.loop.loop:main` and returns its code unchanged | umbrella `specfuse/cli.py` `DELEGATED_COMMANDS` + `_delegate` | T13 | ☐ |
| The driver files **no** needs-human issue on a blocked WU | absence of `emit_escalation` in `loop.py` | T14 | ☐ |
| `CATEGORY_LABELS` includes `drafting-needed` and `gate-review` | `specfuse/loop/escalation.py:21` | T14 | ☐ |
| `emit_escalation` is idempotent per correlation id | `escalation.py:185` and its docstring | T14 | ☐ |
| `GATE_REVIEW_VALUES` = `{human, auto}`; `wip_limit` is `int >= 1`; `overrides` is a `FEAT-ID -> human\|auto` map | `specfuse/loop/agent_policy.py:55, 371-411` | T12 | ☐ |
| A `queue:` entry is a bare `FEAT-YYYY-NNNN`, validated against the roadmap | `agent_policy.py:225`; `.specfuse/agent-policy.yml` | T12, T14 | ☐ |
| `FeatureSummary(feature_id, status, gates)` and `features_errors` keyed by directory name | `specfuse/agent/state.py:83-106, 237` | T12 | ☐ |
| `PLAN.md status` vocabulary — `planned` / `active` / `blocked` / `deferred` / `done` / `abandoned`, all six | `lint_plan.py:53` (`VALID_FEATURE_STATUS`) | T12 | ☐ |
| A feature item's `queue_key` must be in `snapshot.queue` or it is escalated | `specfuse/agent/run.py:228-235` | T14 | ☐ |
| `handled_ids` suppresses a re-advertised `item_id` | `run.py:213` | T14 | ☐ |
| `EscalationPayload`'s six parts and its two-option minimum | `run.py:97-111`; `escalation.render_escalation_body` | T14 | ☐ |

## Risks to weigh before arming

- **The queue top is this feature.** `.specfuse/agent-policy.yml` reads
  `queue: [FEAT-2026-0049]`. After T14 lands, a `specfuse-agent run` in this
  working tree would take the agent lock, read that queue, and invoke `specfuse
  run` on the feature the agent is being built inside. T14's escalation trigger
  forbids editing the policy file to dodge it and requires fixture folders in the
  tests, but the hazard is real for anyone who runs the command by hand during
  the gate. It is also the sharpest illustration of why the subprocess invariant
  is not stylistic.
- **The snapshot is now decisively not a snapshot.** Gate 3's review called this
  "more aspiration than description" with three providers reading live state;
  T14 makes it four, and it is the first that reads live state *because its own
  execute changed it*. The fix — extending T02's snapshot — is a gate-1 surface
  change and stays out of bounds. `G4-CLOSE` should say so plainly rather than
  keep calling it a snapshot.
- **A sixth spender that reports zero.** `advance_feature` launches the most
  expensive subprocess this agent can launch, and like every provider before it
  will report `spend=0` unless a token count can be recovered from the driver's
  output. `--max-tokens` remains wired and unfireable. The driver does write cost
  into WU frontmatter (`write_cost_to_wu`), so unlike the earlier five this
  provider has a plausible spend source — but reading it is not drafted, and
  claiming a measured zero would be the thing T11's trigger refused.
- **`--max-items` now counts gates, not features.** Because the item id carries
  the advance point, a single feature advancing four gates consumes four items.
  An operator who sets `--max-items 3` expecting three features gets one. This is
  the honest reading of D3's item-boundary rule and it is what makes a cap able
  to stop between gates at all, but it is the flag semantics most likely to
  surprise on a first live run — worth agreeing with explicitly at arming.
- **A feature that escalates still costs a driver invocation** on every run until
  a human clears it, because nothing persists across runs. `emit_escalation`'s
  idempotence stops the duplicate issue, not the duplicate invocation. For an
  `awaiting_review` halt that is one cheap exit-0 call; for a `blocked` feature
  the driver may re-dispatch the blocked WU. Confirm this is acceptable, or
  narrow T12's `BLOCKED` disposition to cover it.
- **No gate-4 WU touches `specfuse/loop/`**, so unlike gate 1 this gate takes no
  driver-restart halt (`driver_edit.DRIVER_MODULE_PREFIXES`). Stated because it
  is a change from gate 1's cost model, not because anything must be done.
- **The arm predicate will not clear this gate on its own.** `PLAN.baseline.json`
  snapshots 7 work units totalling $34.50; everything drafted after baselining
  counts as added, so `arm_eval`'s drift-cap and budget-projection classes have
  fired since gate 2. Gates 2 and 3 were both armed by hand for the same reason.
  This is the predicate working on a feature baselined before three of its four
  gates were planned, not a new signal about gate 4.

## Three lint WARNs that are correct to leave standing

`specfuse lint` on this folder exits 0 and prints three WARNs, one per drafted
work unit:

```
WARN: WU-1{2,3,4}-*.md: implementation WU mentions driver wiring (['loop.py'])
but `produces_driver_helper` frontmatter is empty.
```

`detect_driver_wiring` (`lint_plan.py:116-140`) fires on the literal `loop.py`
anywhere in a WU body, on the premise that a WU naming the driver is wiring
something into it. **Gate 4 inverts that premise**: it is the one gate whose
whole job is to *read* the driver — its exit codes, its `human_escalation`
events, its `--feature` flag — while every WU's `Do not touch` forbids editing a
single file under `specfuse/loop/`. The citations are the evidence that no driver
change is needed, and removing them to silence the WARN would make the work units
strictly worse.

**Do not "fix" this by declaring a `produces_driver_helper` value.** These units
produce no driver symbol, so any value would be false — and a declared driver
surface colliding with their own Do-not-touch section is an **ERROR** under
`check_produces_boundary`, turning an advisory WARN into an un-armable WU. Leave
all three standing and read them as noise on this gate specifically.

## The terminal close, sharpened

`WU-92-gate-4-close.md` was drafted by `G1-PLAN` against a guess at what this
feature would build, and renumbered once. This unit set its `depends_on` to
`[T12, T13, T14]` and sharpened its criteria against what actually shipped:

- **Its deferral section must name gate 1, gate 2 *and* gate 3.** Gates 1 and 2
  carry `specfuse:autoclose-debt` markers (27 and 30 criteria), which
  `assert_autoclose_debt_reconciled` requires by name in the **last**
  `## What the loop did NOT verify` section in `RETROSPECTIVE.md`. Gate 3 carries
  no marker — its close ran — but gate 3's own deferral section *stops being the
  record* the moment gate 4 appends its own, which the gate-3 close said in
  writing. The criterion now says all three, and says the guard checks it after
  dispatch so a mismatch costs a full re-attempt.
- **The oracles re-run fresh, in-session** (`close-discipline.md` §1), including
  the gate-4 modules scoped — the close inherits nothing from a producing WU's
  self-report.
- **The consumer-visible enumeration is pre-populated** rather than rediscovered
  from the diff: the `specfuse-agent` console script, the
  `--max-minutes` / `--max-tokens` / `--max-items` / `--repo` / `--policy` /
  `--features-root` / `--monitoring-config` flags, and the behaviour change to
  `default_providers()` that makes an unattended run dispatch the gate driver.
  That last one is a change to an existing command, not an addition, and is the
  entry most likely to be missed.
- **The hedged-verdict kinds are named in advance** where gate 3's close already
  decided them: gate 3's ten fixture-only criteria as
  `externally-verifiable-later`, and the eleven red-before-green halves plus the
  four diff claims as `inherent`, because a close session runs no `git` command
  by contract and no future close can discharge them either.

**A note on the lint WARN.** `G3-PLAN`'s brief said `specfuse lint` currently
WARNs that `WU-92`'s body never instructs reconciling the auto-close debt. It
does not: `check_autoclose_debt_prediction` (`lint_plan.py:911`) fires only on a
marked gate the close's body never names as `gate N`, and `WU-92`'s criterion 2
already named gates 1 and 2 verbatim. `specfuse lint` on this feature folder
prints `OK` and no WARN, before and after this unit's edits. The sharpening above
was still worth doing — the criterion was one gate out of date — but it closed a
staleness, not a live warning.
