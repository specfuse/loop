---
feature_id: FEAT-2026-0047
title: Notify webhook (pluggable provider) + heartbeat-silence self-alert
slug: notify-webhook
branch: feat/FEAT-2026-0047-notify-webhook
roadmap_goal: Make escalations push instead of waiting to be pulled — a one-liner and a link to whatever channel the operator configured — and make agent silence itself alarmed, so a stalled or dead agent announces rather than simply stopping.
autonomy_default: auto
status: planned
planned_cost_usd: 20.00
---

# Plan: Notify webhook + heartbeat-silence self-alert

Escalations must push, not wait to be pulled. Answers still belong in the
GitHub escalation issue ([FEAT-2026-0046](../../roadmap.md#feat-2026-0046)), so
this stays deliberately trivial: **notify-only**. No bot hosting, no reply
parsing in chat, no provider lock-in.

And a silent agent is itself a failure mode. An agent that stalls, dies, or is
never scheduled looks exactly like an agent with nothing to do. This feature
makes that difference observable.

Drafted **solo, without an operator interview**, on operator instruction
(2026-08-09), alongside [FEAT-2026-0044](../../roadmap.md#feat-2026-0044) and
[FEAT-2026-0048](../../roadmap.md#feat-2026-0048). § *Assumed decisions* records
every choice for veto at PR review.

## Scope boundary

**IN.** A webhook notifier with per-provider payload adapters; the
`escalation.webhook_env` config surface and its validation; posting on new and
re-pinged needs-human issues; the SLA re-ping-once-then-park rule; and a
heartbeat-silence self-alert derived from repo state.

**OUT — inbound anything.** No bot, no slash commands, no reply parsing, no
webhook *receiver*. The channel is a loudspeaker; the audit trail stays on
GitHub. This is the single constraint that keeps the feature small, and
widening it is a different feature.

**OUT — scheduling.** Nothing here decides when the heartbeat check runs.
FEAT-2026-0049 owns invocation; `/attention` surfaces the staleness on open.

**OUT — the escalation body and its contract.** FEAT-2026-0046 owns
`render_escalation_body` and `validate_escalation_body`. This feature reads
issues; it does not restate or re-render their bodies.

**OUT — notifying on anything other than escalations and silence.** No per-WU
progress pings, no cost alerts, no PR notifications. A channel that reports
everything gets muted, and a muted channel is worse than none.

## Assumed decisions (drafted without an interview — operator veto at PR review)

1. **Single gate, single terminal `close`.** Four substantive WUs, at the
   ceremony-proportionality threshold (`docs/methodology.md` §6).
2. **The config holds an environment-variable NAME, not a URL — and this is a
   change to what FEAT-2026-0044 shipped hours earlier.** See § *The security
   correction* below. This is the most consequential assumed decision here.
3. **Provider support is a payload adapter, not an integration.** Discord,
   Slack, and Teams all accept an incoming-webhook POST; only the JSON envelope
   differs. Adapters are pure functions from a neutral message to a provider
   payload, chosen by an explicit `provider:` key rather than sniffed from the
   URL — sniffing a secret-bearing URL means reading it, and the code should
   handle it as little as possible.
4. **The notifier is fire-and-forget and never fatal.** A failed webhook post
   logs and returns; it never raises into the caller, never blocks an
   escalation from being filed, and never fails a gate. The GitHub issue is the
   system of record; the notification is a courtesy. A notifier that can break
   the escalation path inverts the reliability ordering.
5. **Every payload is redacted before it leaves the process.** `redact_text`
   from `monitor/redaction.py` is applied to any body-derived text. An outbound
   channel is the one place where a leak is irreversible — it is cached and
   indexed by a third party the moment it lands.
6. **The last-run timestamp is derived, never stored.** The newest event across
   `.specfuse/features/*/events.jsonl` *is* the timestamp. Per
   `[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]`, a
   written heartbeat file on an ephemeral runner is decorative; and the events
   log already answers the question exactly.
7. **SLA re-pings exactly once, then parks.** Unbounded re-pinging trains the
   operator to mute the channel, which defeats the feature. One re-ping, then
   the item is parked and the queue continues — the roadmap row's own wording.
8. **Quiet hours suppress the post, never the issue.** During quiet hours the
   needs-human issue is still filed; only the outbound message is withheld. A
   config that could delay an escalation's *record* would be a safety
   regression dressed as a courtesy.

## The security correction

FEAT-2026-0044's T01 shipped `escalation.webhook: ""` into
`.specfuse/agent-policy.yml` — **a committed file**. An incoming-webhook URL is
a bearer credential: anyone holding it can post to the channel. And
`lint_monitoring`'s credential-key pattern
(`key|token|secret|password|credential|connection_string`) does **not** match
`webhook`, so nothing in the repo would have stopped an operator pasting a live
Discord URL into git, and the `leak-scan` gate's secret detection is not
guaranteed to recognise every provider's URL shape.

This feature renames the key to **`escalation.webhook_env`** and requires its
value to be an environment-variable *name*, enforced with the same
`_ENV_VAR_NAME_RE` shape `monitoring.yml` already uses for credentials. The URL
itself is read from the environment at post time and never written to config,
logs, events, or a rendered payload.

**This is a consumer-visible contract change against a schema that shipped the
same night.** It is defensible precisely because nothing consumes the key yet —
FEAT-2026-0044 shipped the field, FEAT-2026-0047 is its first and only reader —
so the migration cost is one line in an example file. T01 owns the rename and
must not leave both spellings accepted.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -n "^[A-Z_]\+ = \|^def " specfuse/loop/escalation.py`
  - `grep -n "_CREDENTIAL_KEY_RE\|_ENV_VAR_NAME_RE" -A20 specfuse/loop/lint_monitoring.py`
  - `ls specfuse/monitor/providers/`
  - `grep -n "^def " specfuse/monitor/redaction.py`
  - `grep -rn "webhook" --include='*.py' specfuse/`
- **Verdict:** `no notifier exists — building new; four surrounding mechanisms found and reused.`

The last grep returns nothing: there is no outbound notification of any kind in
this repo today. The rest each returned a mechanism to reuse:

| Surface this feature needs | Existing mechanism | Verdict |
|---|---|---|
| Env-var-name-not-value config convention | `lint_monitoring._ENV_VAR_NAME_RE` + `_check_credentials` | **copy the shape and the rationale** — T01 |
| Redaction before text leaves the process | `monitor/redaction.redact_text` | **import and call** — T01 |
| Provider-adapter directory layout | `specfuse/monitor/providers/` (`azure_*`) | **copy the layout** — T01 |
| The needs-human issue surface to watch | `loop/escalation.NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`, `_CORRELATION_MARKER_TEMPLATE` | **import the constants; do not retype the label** — T02/T03 |
| Policy reader for `escalation.*` | `loop/agent_policy.load_policy` (FEAT-2026-0044) | **call directly** — T01 |
| The inbox that already sweeps needs-human | `/attention` skill (FEAT-2026-0046) | **extend with one section** — T04 |

**Genuinely new:** the notifier itself, the three payload adapters, the SLA
re-ping bookkeeping, and the staleness derivation.

**Roadmap-row verb check**
(`[FEAT-2026-0045/G1-CLOSE/verb-check-table-earns-its-cost]`):

| Verb from the row | Mechanism it assumes | Backed? |
|---|---|---|
| "post a one-liner + link to the configured channel" | an HTTP POST path | **no** — nothing posts anywhere today; T01 builds it. The one genuinely-new verb. |
| "on new/re-pinged needs-human issues" | a needs-human issue surface | **yes** — FEAT-2026-0046 shipped the label, marker, and idempotent filing |
| "provider swap = URL change" | payload adapters per provider | **partly** — the `providers/` layout exists as precedent; no HTTP adapters do. Assumed decision 3 makes the provider explicit rather than sniffed. |
| "unanswered escalation past the configured window re-pings once" | a readable filing timestamp per escalation | **yes** — the correlation marker plus GitHub's own issue timestamps |
| "records a last-run timestamp (repo-derivable)" | derivable repo state | **yes** — `.specfuse/features/*/events.jsonl` timestamps; assumed decision 6 |

5 verbs, 3 backed, 1 partly, 1 genuinely new and scoped to T01.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature raises one existing check's strictness: `validate_agent_policy`
will reject a literal URL in `escalation.webhook_env`.

- **What does the rule report on an input already in its intended final state?**
  **Zero.** A conforming policy file carries an env-var *name*
  (`SPECFUSE_NOTIFY_WEBHOOK`) or an empty string, and both pass. An empty value
  is explicitly valid and means "no webhook configured" — the feature must
  degrade to no-op, not to a finding, because this repo itself ships no webhook.
- The only input that fires is a pasted URL, which is exactly the authoring slip
  the check exists to catch.

T01 must land the rename **and** the shipped example's migration in the same WU,
so no intermediate tree fails its own gate — the expand→migrate→contract
ordering `[FEAT-2026-0069/G1]` records as the only one satisfiable under the
preflight baseline probe.

## Task graph

```yaml
# Single terminal gate: 4 substantive WUs, at the ceremony-proportionality
# threshold (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0047/T01
        file: WU-01-notifier-and-webhook-env.md
        depends_on: []
      - id: FEAT-2026-0047/T02
        file: WU-02-notify-on-escalation.md
        depends_on: [FEAT-2026-0047/T01]
      - id: FEAT-2026-0047/T03
        file: WU-03-sla-reping-and-park.md
        depends_on: [FEAT-2026-0047/T02]
      - id: FEAT-2026-0047/T04
        file: WU-04-heartbeat-silence-alert.md
        depends_on: [FEAT-2026-0047/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0047/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0047/T01
          - FEAT-2026-0047/T02
          - FEAT-2026-0047/T03
          - FEAT-2026-0047/T04
```

T04 depends only on T01 (it needs the notifier, not the escalation wiring), so
it is independent of the T02→T03 chain. T03 depends on T02 because the re-ping
rule is a refinement of the posting path, not a separate one.

## Notes

- **This repo ships no webhook.** `escalation.webhook_env` stays empty in
  `.specfuse/agent-policy.yml` throughout, and every code path must no-op
  cleanly on an empty value. That is also the only configuration the CI gates
  ever see, so the no-op path is the one with real test coverage — T01's
  criteria make the configured path testable with an injected poster rather
  than a live URL.
- **No test may perform a real HTTP request.** Every poster is injected. A test
  that reaches the network would be both flaky and, with a real URL, a leak.
- FEAT-2026-0049 is the consumer of all four deliverables and is `blocked` until
  this feature, FEAT-2026-0044, and FEAT-2026-0048 are all `done`. Clearing that
  block is a human flip, not an automatic consequence.
