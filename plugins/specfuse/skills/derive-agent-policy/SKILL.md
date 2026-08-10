---
name: derive-agent-policy
description: "Interactively draft a target project's `.specfuse/agent-policy.yml` `rules`, `budgets`, and `escalation` blocks by proposing what repo evidence can answer and asking the operator everything else. Drafts; never auto-writes. Triggers: /derive-agent-policy, derive the agent policy, fill in agent-policy.yml, draft the escalation block."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Derive agent policy (interactive)

This skill is `derive-verification`'s and `derive-monitoring`'s sibling for the
operator's own dials: where those two drafts prove a change correct and notice a
deployed component misbehaving, this skill drafts `.specfuse/agent-policy.yml`'s
`rules`, `budgets`, and `escalation` blocks — the operator's priorities for what
the loop works on, how hard it can spend, and where it escalates. It combines
**evidence `propose_policy_defaults` extracts from the repo's own history** with
**a small batched round of questions only the operator can answer**, and produces
a candidate policy file. The output is always *proposed*; the operator reviews it
block by block before anything lands on disk. Posture mirrors `plan-next`: draft,
then arm.

**Run interactively.** The skill's whole value is the batched question round in
Step 2 (`gate_review`, `wip_limit`, `preempt`, `min_severity`, `automerge`, and
the whole `escalation` block), so it needs an operator it can ask. A
non-interactive `[gap]` fallback is documented below for when no human is
reachable (CI, a dispatched session, no stdin) — it is a degraded mode, not the
intended path. Piping `PROMPT.md` via `claude -p < PROMPT.md` consumes stdin and
silently degrades to gap-mode; use an interactive `claude` session and ask it to
run this skill instead.

The companion `PROMPT.md` is what the operator pipes to `claude -p` or pastes
into a session. This SKILL.md is the method that prompt operationalizes — read
it as the contract.

## Why this exists

`.specfuse/agent-policy.yml` shipped once full of values an agent chose and
never explained — the failure `[FEAT-2026-0039]` shipped, and the reason
`propose_policy_defaults` (`specfuse/loop/policy_proposals.py`) exists: it
proposes only what a repository's own history and structure can answer, and
every proposal carries the evidence it came from. This skill is the interview
that turns those proposals — plus the fields no repo evidence can ever answer —
into a filled-in, operator-reviewed policy file.

The single guarantee the skill makes: **every drafted `rules`/`budgets` value
traces to `propose_policy_defaults`'s evidence, or to a question the operator
explicitly answered; every `escalation` value comes from the operator, never
from a guess.** No silent invention.

## Hard rules

- **Draft, do not write.** The produced YAML is printed and discussed with the
  operator, block by block. It lands at `.specfuse/agent-policy.yml` only after
  the operator explicitly accepts each block, and only if the existing file is
  absent or backed up. This matches `plan-next`'s "drafts but never arms"
  posture — see `docs/methodology.md` §7.
- **Staged per-block accepts, never one blanket yes.** Present `rules`,
  `budgets`, and `escalation` as three separate accept/edit/reject decisions,
  in that order. A blanket accept would let an operator wave through the
  `escalation` block — the one with a credential-shaped field — without
  actually reading it.
- **Proposed values are not asked values, and the prose must not blur them.**
  `budgets.max_tokens_per_run`, `budgets.max_items_per_day`,
  `budgets.max_open_prs`, and `rules.bugs.test_paths` are the four fields
  `propose_policy_defaults` can derive from repo evidence — present each with
  its evidence string and let the operator disagree. Every other field —
  `rules.bugs.preempt`, `rules.bugs.min_severity`, `rules.bugs.automerge`,
  `rules.features.gate_review`, `rules.features.wip_limit`, and the whole
  `escalation` block — is **asked**, because no repo evidence answers it.
  Presenting an invented value as evidence-backed is the failure
  `[FEAT-2026-0039]` shipped; this skill exists not to repeat it.
- **Where `propose_policy_defaults` proposes nothing, present the shipped
  default and say plainly that it is a default.** `propose_policy_defaults`
  omits a key entirely when the repo carries no evidence for it — a repo with
  no `events.jsonl` gets no `max_tokens_per_run` proposal, not a plausible-
  looking guess dressed as one. When that happens, this skill still shows the
  operator a value to react to (`.specfuse/agent-policy.yml.example`'s shipped
  default) but labels it explicitly as a default, never as though the repo
  suggested it — the same distinction the Hard Rule above draws between
  proposed and asked, applied to the case where even a proposal attempt came
  back empty.
- **The webhook question collects an environment-variable name, never a URL.**
  `escalation.webhook_env` is validated against `^[A-Za-z_][A-Za-z0-9_]*$` — an
  incoming-webhook URL is a bearer credential, and that pattern exists
  precisely so one cannot be entered as a committed file. Ask *"what
  environment variable holds your webhook URL?"*, never *"what's your webhook
  URL?"*. If a drafted answer fails that shape (contains `:`, `/`, `.`, or
  starts with a digit), re-prompt and explain why — never write it and let
  `validate_agent_policy` catch it later. This is the one constraint this
  skill must never lose: an interview that prompts for the URL hand-feeds the
  credential the validator exists to refuse, in the one flow an operator
  trusts most.
- **An unset `webhook_env` is a silent no-op — say so.** `resolve_webhook_url`
  returns `None`, and every escalation post is skipped, whenever the named
  environment variable is unset at runtime — indistinguishable from "no
  webhook configured" unless this skill's report says so explicitly. Tell the
  operator that leaving `webhook_env` empty, or naming a variable they never
  export, means escalations are posted nowhere and nothing errors.
- **Never invent an `invariant`-shaped value or a business judgment.**
  `min_severity`, `gate_review`, `wip_limit`, `preempt`, `automerge`, and every
  `escalation` field are the operator's call about their own team and repo. The
  skill asks; it never proposes a plausible-sounding default for these and
  presents it as inferred.
- **The draft must validate.** The closing step tells the operator to run
  `validate_agent_policy(".specfuse/agent-policy.yml")` (or the CLI wrapper
  around it). A non-empty finding list means the draft is wrong, not the
  validator — the validator is gate 1's shipped oracle, never loosened to fit
  a draft.
- **Key ownership is disjoint: one writer per key block, not per file.**
  This skill owns `rules`, `budgets`, and `escalation` in
  `.specfuse/agent-policy.yml`. It must never write `queue` — that key
  belongs to `/groom-backlog` alone. (The older phrasing, "one writer per
  config file," no longer holds: `/groom-backlog` and this skill both write
  `.specfuse/agent-policy.yml`, so the invariant that stays true is per key
  block, not per file.) If asked to touch `queue:`, say so and stop rather
  than reaching into `/groom-backlog`'s surface.

## The method (in strict order)

This ordering is the whole point. Propose from evidence first, ask only what
evidence cannot answer, and never blur the two.

### Step 1 — Evidence gathering via `propose_policy_defaults`

Call `propose_policy_defaults(repo_root)` from `specfuse/loop/policy_proposals.py`
against the target repo. It returns a dict keyed by exactly the four fields in
scope — `max_tokens_per_run`, `max_items_per_day`, `max_open_prs`, `test_paths`
— each present only when the repo carries evidence for it, and each shaped as
`{value, evidence}`. Read the evidence string verbatim into the draft; it names
the exact `events_stats.collect` aggregate, gate-command scan, or `gh pr list`
count that produced the value. A key **absent** from the returned dict means the
repo has no evidence for it — that is a first-class outcome, not a bug, and this
skill must present the shipped default in its place, labeled as a default (see
Hard Rules).

Do not re-derive any of this by hand — `propose_policy_defaults` already reads
`events_stats.collect`, `gate_commands.iter_code_gates`, and (when a `runner` is
supplied) `gh pr list --state open`. This skill's evidence-gathering step is
calling that function once, not re-implementing its heuristics.

### Step 2 — Ask the operator — only for what evidence cannot resolve

Every field below has zero repo evidence by construction — a business or team
judgment, not a fact the tree could carry. Batch them into **one round**,
grouped by block, presented together with a one-line explanation of what each
controls:

**`rules.bugs`:**
1. `preempt` (bool) — do bugs jump the feature queue?
2. `min_severity` (`low`|`medium`|`high`|`critical`) — floor for the bug lane
   to act automatically.
3. `automerge` (`"off"`|`"on"`) — may the bug lane merge without a human
   review?

**`rules.features`:**
4. `gate_review` (`human`|`auto`) — does a gate boundary wait for a human, or
   arm itself?
5. `wip_limit` (int ≥ 1) — how many features in flight at once?

**`escalation`** (asked last, once the operator has the shape of the other two
blocks in view):
6. `provider` (`discord`|`slack`|`teams`|`none`).
7. `webhook_env` — **the environment-variable NAME holding the webhook URL,
   never the URL itself.** Validate against `^[A-Za-z_][A-Za-z0-9_]*$` before
   drafting it; re-prompt on failure with the reason. Explain that leaving it
   empty, or naming an unexported variable, means escalations post nowhere and
   nothing errors (`resolve_webhook_url` returns `None` silently).
8. `assignee` (str, may be empty).
9. `quiet_hours` (str, `"HH:MM-HH:MM"` or empty).
10. `sla_hours` (int > 0).
11. `silence_hours` (optional int > 0; defaults to 24 if left unanswered —
    present that default plainly as a default, per the Hard Rules).

**Forbidden questions** — anything `propose_policy_defaults` already answered.
Asking "what's your coverage token budget?" after Step 1 already returned a
`max_tokens_per_run` proposal with evidence is a skill bug, not a
clarification — present the proposal and ask only whether the operator wants
to override it.

**Non-interactive fallback.** If the skill runs where the operator cannot
answer (CI invocation, dispatched session, no stdin), it still produces a
draft — every would-be question becomes an explicit `[gap]` line in the
reconciliation report, and every `escalation` field is left at its safest
value (`provider: none`, `webhook_env: ""`) rather than guessed. Silence is
never permission to invent a severity floor, a gate-review dial, or a webhook
target.

### Step 3 — Output

Three artifacts, in this order, and the draft is only ever written to
`.specfuse/agent-policy.yml` after all three blocks below are individually
accepted:

#### 3a. The proposed `rules` block

```yaml
rules:
  bugs:
    preempt: true                # ASKED — Q1
    min_severity: low            # ASKED — Q2
    automerge: "off"             # ASKED — Q3
    test_paths:                  # PROPOSED from evidence, or shipped default
      - tests/
  features:
    gate_review: human           # ASKED — Q4
    wip_limit: 1                 # ASKED — Q5
  triage:
    auto: false                  # shipped default; not in this skill's scope to ask
```

Present it and stop. Accept, edit, or reject as a unit before moving to 3b.

#### 3b. The proposed `budgets` block

```yaml
budgets:
  max_tokens_per_run: <value>    # PROPOSED from evidence, or shipped default
  max_open_prs: <value>          # PROPOSED from evidence, or shipped default
  max_items_per_day: <value>     # PROPOSED from evidence, or shipped default
```

Every value here traces to `propose_policy_defaults`'s evidence string
(reproduced in the reconciliation report) or, where that function returned no
proposal, to `.specfuse/agent-policy.yml.example`'s shipped default — labeled
as a default in the report, never presented as though the repo suggested it.
Accept, edit, or reject as a unit before moving to 3c.

#### 3c. The proposed `escalation` block

```yaml
escalation:
  webhook_env: ""                 # ASKED — Q7; env-var NAME only, validated
                                   # against ^[A-Za-z_][A-Za-z0-9_]*$; never a URL
  provider: none                  # ASKED — Q6
  assignee: ""                    # ASKED — Q8
  quiet_hours: ""                 # ASKED — Q9
  sla_hours: 24                   # ASKED — Q10
  silence_hours: 24               # ASKED — Q11, or shipped default if unanswered
```

Present it last, and separately — this is the block with the credential-shaped
field. Accept, edit, or reject as a unit. Re-validate `webhook_env` against the
env-var-name pattern before showing the final block; if it fails, re-prompt
rather than draft it.

#### 3d. The reconciliation report

```
# Reconciliation report for <repo-name>

## Evidence inventory (propose_policy_defaults)
- max_tokens_per_run: <evidence string, or "no proposal — no events.jsonl / no passing implementation attempts">
- max_items_per_day: <evidence string, or "no proposal">
- max_open_prs: <evidence string, or "no proposal — no `gh` runner supplied">
- test_paths: <evidence string, or "no proposal">

## Asked (no repo evidence exists for these)
- Q1 preempt → A: <answer>
- Q2 min_severity → A: <answer>
- Q3 automerge → A: <answer>
- Q4 gate_review → A: <answer>
- Q5 wip_limit → A: <answer>
- Q6 provider → A: <answer>
- Q7 webhook_env → A: <answer> (validated against ^[A-Za-z_][A-Za-z0-9_]*$)
- Q8 assignee → A: <answer>
- Q9 quiet_hours → A: <answer>
- Q10 sla_hours → A: <answer>
- Q11 silence_hours → A: <answer, or "shipped default 24 used">

## Shipped defaults presented as defaults (not proposals)
- <field>: <value> — no repo evidence; `.specfuse/agent-policy.yml.example`'s default

## Webhook note
- <"webhook_env left empty / unexported: escalations will post nowhere and
  nothing will error" OR "webhook_env resolves at runtime via <name>">

## Recommended next step
- Review each of the three blocks above. If all three are accepted, merge
  them into `.specfuse/agent-policy.yml` (preserving `version`, `queue`, and
  `rules.triage` as they already stand), then run
  `validate_agent_policy(".specfuse/agent-policy.yml")` and confirm the
  finding list is empty.
```

## Review mode — an existing `.specfuse/agent-policy.yml`

**Entry condition.** This skill is one skill with two entry conditions, not two
skills — the questions in Step 2 above are the same questions; only the
starting state differs. Before doing anything else, check whether
`.specfuse/agent-policy.yml` **exists** in the target repo:

- **Absent** (or unreadable) → run the bootstrap interview documented above:
  Step 1 evidence gathering, Step 2 the batched ask, Step 3 the staged draft.
  This is gate 1's shipped path.
- **Exists** → run review mode, described below. An existing file is read and
  corrected, never clobbered on the strength of a proposal alone.

Review mode calls `review_agent_policy(repo_root)` from
`specfuse/loop/policy_review.py`. It reads the live
`.specfuse/agent-policy.yml`, composes `propose_policy_defaults` for the
evidence-backed half, and returns a per-key readout for the same four in-scope
fields Step 1 above proposes from evidence: `budgets.max_tokens_per_run`,
`budgets.max_items_per_day`, `budgets.max_open_prs`, and
`rules.bugs.test_paths`. Do not re-derive this comparison by hand — call the
function once and present its output.

### The readout, per key

For each of the four keys, `review_agent_policy` returns an entry carrying:

- **`current`** — the value read from the live file (or its absence).
- **`proposal`** — what `propose_policy_defaults` returns for this key today
  (value plus evidence string), or unavailable.
- **`baseline`** — the shipped default: `agent_policy.DEFAULT_TEST_PATHS` for
  `rules.bugs.test_paths`, `.specfuse/agent-policy.yml.example`'s literal
  value for the three `budgets` keys.
- **`classification`** — the provenance verdict: `matches_baseline`,
  `differs_from_baseline`, `absent_from_file`, or `baseline_unavailable`.

Present all four parts for every key — current, proposal, baseline, and
classification — not just the current value and a verdict. An operator who
sees only the classification cannot tell *why* a key was flagged.

### Provenance is a hint, not a claim

A `matches_baseline` classification is a **hint, not a claim**, and the
readout must say so in those words. A value equal to the shipped baseline
**may never have been** deliberately chosen — but an operator who deliberately
picked that exact value looks identical from this comparison alone; the two
are not distinguishable from the file. Never present a `matches_baseline`
entry as "this was never decided."

The asymmetry runs the other way too, and the readout must state it: a value
that **differs** from the shipped baseline reliably means someone touched it.
That direction is not lossy. Present `differs_from_baseline` with more
confidence than `matches_baseline` — the former is evidence of a decision, the
latter only a possibility of one.

### Measured vs. converted proposals are not the same and must not read alike

T04's `proposal.kind` field distinguishes two kinds of evidence-backed number,
and the readout must carry the distinction at the point the operator reads
it — not only in a source comment:

- **`measured`** — `rules.bugs.test_paths` is the only measured value of the
  four. It comes straight from repo evidence (`gate_commands.iter_code_gates`
  scanning actual test-path usage) with no interpretive step in between.
- **`converted`** — `budgets.max_tokens_per_run`, `budgets.max_items_per_day`,
  and `budgets.max_open_prs` are converted: `propose_policy_defaults` derives
  them from raw evidence (`events_stats.collect` aggregates, `gh pr list`
  counts) through an assumption about how to turn that evidence into a budget
  number. Name the assumption behind each converted value in the readout
  itself, alongside the number — an operator reading only the number cannot
  tell it rests on an assumption they might disagree with, separately from
  disagreeing with the number.

Do not present all four keys alike. An operator must be able to disagree with
a converted value's *assumption* independently of disagreeing with its
*number*; a readout that renders `measured` and `converted` identically takes
that away.

### Output — the same staged per-block accept, applied to corrections

Review mode's corrections use the same staged per-block accept contract the
bootstrap draft uses in Step 3 above — never one blanket yes. Present
corrections to `rules`, then `budgets`, then `escalation`, as three separate
accept/edit/reject decisions, in that order, even though review mode is
correcting an existing file rather than drafting a fresh one:

1. **`rules`** — `rules.bugs.test_paths`'s readout (current, proposal,
   baseline, classification, `measured`).
2. **`budgets`** — `max_tokens_per_run`, `max_items_per_day`, `max_open_prs`
   readouts (current, proposal, baseline, classification, each `converted`
   with its assumption named).
3. **`escalation`** — out of `review_agent_policy`'s scope (it reads only the
   four in-scope keys above); if the operator wants `escalation` reviewed too,
   fall back to the bootstrap Step 2 ask for that block, staged the same way.

Never merge a correction into `.specfuse/agent-policy.yml` without the
operator's explicit per-block accept — the same rule the bootstrap draft
follows.

## Escalation framing (binding — `.specfuse/rules/operator-escalation.md`)

Whenever this skill halts for a human decision — a `webhook_env` answer that
fails the env-var-name pattern, an ambiguous evidence readout, a block the
operator must accept, edit, or reject — present it in the six parts that rule
requires, in plain English, **before** any correlation ID, guard name, or
finding-prefix jargon: what has been done so far; what the issue is about; what
decision is needed and why; why it did not resolve automatically; the options
with their pros and cons; and a recommendation.

Never author the operator's own justification. Where a field records *why a
human decided something* — an accepted severity floor, a chosen `gate_review`
dial — that text comes from them.

## What this skill does NOT do

- It does not write `.specfuse/agent-policy.yml` to disk on its own. It is an
  authoring aid; the operator merges the accepted draft themselves, one block
  at a time.
- It does not compute or propose `queue:` — that is `/groom-backlog`'s surface
  entirely; this skill never reads or writes it. It owns `rules`, `budgets`,
  and `escalation`; `queue` is the one key block it must never write.
- It does not re-implement `propose_policy_defaults`'s heuristics. It calls the
  function once and reads its `{value, evidence}` output.
- It does not extend `.specfuse/agent-policy.yml`'s schema. If drafting reveals
  a field the schema does not define, the skill stops and reports the need — it
  never invents a new key.
- It does not modify `specfuse/loop/policy_proposals.py`,
  `specfuse/loop/agent_policy.py`, or `.specfuse/agent-policy.yml.example`. If
  applying this skill reveals that those need to change, the skill stops and
  reports the need — it never edits them as part of its work.
- It does not accept a webhook URL under any name. A pasted URL is re-prompted,
  never drafted, regardless of which field the operator tried to put it in.
- It does not auto-run from `init.sh`. `init.sh` stays deterministic and
  agent-free; the closing instructions point at this skill as an optional next
  step.

## Version

**v0.1.** First cut of the agent-policy interview: `rules`/`budgets`/`escalation`
proposal-and-ask, staged per-block accepts. Expected to grow once the loop has
run this skill against a project whose `events.jsonl` history is deep enough to
exercise every `propose_policy_defaults` branch.
