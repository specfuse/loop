<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0047, notify webhook + heartbeat-silence self-alert

Terminal close of a single-gate feature. Correlation ID
`FEAT-2026-0047/G1-CLOSE`, attempt 1, `auto_close_disabled: true` — this close
re-runs oracles per `close-discipline.md` §1, which makes it load-bearing
(#189).

**Verdict: `partially_met`.** Every oracle this close ran is green and all three
security claims hold, re-tested in this session from the shipped code. One
acceptance criterion is genuinely unmet rather than merely unverifiable here:
T04's criterion 9 required both a `/attention` skill section naming
`specfuse.loop.heartbeat.silence_check` **and** a test asserting that literal.
The section shipped; the test does not exist. Three further criteria are
unverifiable in this environment. All four are recorded below with `kind:`
classifications and re-run conditions.

## Gate 1 — what shipped

Four substantive work units, all `done` on their first attempt, zero re-arms.
Four new importable modules in the wheel, plus one schema change:

- **`specfuse/loop/notify.py`** (T01) — `post_notification(message, *,
  policy_path=None, poster=None, now=None) -> bool` and
  `resolve_webhook_url(policy_path=None) -> str | None`, plus three pure payload
  adapters (`discord_payload`, `slack_payload`, `teams_payload`). Fire-and-forget:
  a poster that raises, times out, or returns non-2xx yields `False` and never
  propagates. Every adapter routes its message through
  `specfuse.monitor.redaction.redact_text`.
- **The `escalation.webhook` → `escalation.webhook_env` rename** (T01) in
  `specfuse/loop/agent_policy.py`, with `escalation.provider`
  (`discord`|`slack`|`teams`|`none`) added alongside. `webhook` is now an
  unknown key; a literal URL in `webhook_env` is an `ERROR: ` finding, enforced
  by the same `^[A-Za-z_][A-Za-z0-9_]*$` shape `lint_monitoring` already uses
  for credentials. Both `.specfuse/agent-policy.yml` and
  `.specfuse/agent-policy.yml.example` migrated in the same unit, both with an
  **empty** value.
- **`specfuse/loop/notify_escalation.py`** (T02) — `notify_new_escalation(...)
  -> bool`, a separate step a caller invokes *after* `emit_escalation` returns.
  `specfuse/loop/escalation.py` was not modified; `NEEDS_HUMAN_LABEL` and
  `CATEGORY_LABELS` are imported, and a test asserts object identity.
- **`specfuse/loop/notify_sla.py`** (T03) — `sla_sweep(runner, repo, *, now,
  policy_path=None, poster=None) -> list`, `PARKED_LABEL = "escalation-parked"`,
  and the `<!-- specfuse:sla-repinged at={at} -->` marker. The re-ping count is
  re-derived from the issue's comment list on every call — no stored counter, so
  an ephemeral runner cannot lose it. Parked is a label; nothing here ever
  closes an issue.
- **`specfuse/loop/heartbeat.py`** (T04) — `last_run_at(repo_root=None) -> float
  | None` and `silence_check(*, now, repo_root=None, policy_path=None) -> dict`.
  The newest event across `.specfuse/features/*/events.jsonl` **is** the
  last-run time; it is derived, never stored. A repo with no events at all is a
  distinct verdict (`no_events: True`, `hours_since: None`), not
  stale-with-zero-hours. `escalation.silence_hours` (int > 0, default 24) added
  to the schema; `plugins/specfuse/skills/attention/SKILL.md` gained a
  *Check for silence* section, vendored to `.specfuse/skills/`.

## Oracles re-run fresh in this session

`close-discipline.md` §1. Every command below was run in this close session with
its exit code read directly, not inherited from a producing WU's self-report.
The runner did **not** stop at the first failure — each gate's code was captured
independently.

### The full `code` gate set from `.specfuse/verification.yml`

The gate list was derived from `verification.yml` at run time
(`python3 -m specfuse.loop.gate_commands .specfuse/verification.yml`), the same
way `scripts/smoke-test.sh` and CI derive it, so this table cannot drift from
what CI runs. This WU's criterion 1 enumerates ten gates; **all sixteen** in the
file were run.

| # | Gate | Command | Exit |
|---|---|---|---|
| 1 | `tests` | `python3 -m unittest discover -s tests -v -b` | **0** |
| 2 | `lint` | `ruff check specfuse .specfuse/scripts tests scripts` | **0** |
| 3 | `security` | `bandit -r specfuse .specfuse/scripts -ll` | **0** |
| 4 | `coverage` | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** |
| 5 | `leak-scan` | `python3 .specfuse/scripts/leak_scan.py --all` | **0** |
| 6 | `agent-policy-example-lint` | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml` | **0** |
| 7 | `event-type-gate` | `python3 .specfuse/scripts/event_type_gate.py` | **0** |
| 8 | `roadmap-link-gate` | `python3 .specfuse/scripts/roadmap_link_gate.py` | **0** |
| 9 | `arm-sweep-gate` | `python3 .specfuse/scripts/arm_sweep_gate.py` | **0** |
| 10 | `monitoring-example-lint` | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** |
| 11 | `leak-scan-hook` | `bats tests/leak_scan_hook.bats` | **0** |
| 12 | `sync-scaffold-bats` | `bats tests/sync_scaffold.bats` | **0** |
| 13 | `sync-scaffold-symlinks-bats` | `bats tests/sync_scaffold_symlinks.bats` | **0** |
| 14 | `init-sh-shim-bats` | `bats tests/init_sh_shim.bats` | **0** |
| 15 | `init-skills-bats` | `bats tests/init_skills_idempotent.bats` | **0** |
| 16 | `hookspath-conflict-bats` | `bats tests/hookspath_conflict.bats` | **0** |

Salient numbers from those runs: **2758 tests, OK (3 skipped)**; **coverage
TOTAL 93%** against a `--fail-under=90` floor; `leak-scan: clean` (gitleaks
8.30.1 plus the denylist scan); bandit **0 medium, 0 high**.

**The set was run twice in this session, and the table above is the second
run** — the one against the tree as this close leaves it, including this close's
own edits to `.specfuse/roadmap.md`, `CHANGELOG.md`, `GATE-01-CRITERIA.md`,
`RETROSPECTIVE.md` and `LEARNINGS-pending.md`. That distinction matters here
rather than being pedantry: three of these gates read exactly those files.
`roadmap-link-gate` parses the link graph this close extended (0 errors, 4
pre-existing warnings unrelated to this feature, which by design do not fail the
gate); `event-type-gate` validates every feature's `events.jsonl`; and the
`tests` gate contains the corpus sweep that reads the annotated
`GATE-01-CRITERIA.md`. A close that only re-ran the gates *before* writing its
artifacts would not have checked its own output. The first run — mid-session,
against the tree as dispatched — was also 16/16 green, with identical test and
coverage numbers.

### The two gates the driver escalated on at gate entry are green

The driver halted this gate with `human_escalation` /
`preexisting_gate_failure` at `2026-08-10T08:55:58Z`, naming two failing gates
in the baseline probe against sha `e0ec497`:

- `tests`, signature
  `test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings`;
- `coverage`.

Both were re-run in this session and both exit **0**. The `tests` signature is
the corpus sweep in `tests/test_lint_closing_criteria.py`, which asserts that no
feature folder in this repo produces a `close-l` / `close-intermediate-f`
finding. It was red because a killed close attempt had left annotated per-criterion
state in `GATE-01-CRITERIA.md`; commit `1c87eb0` dropped that state, and the test
was already green when this session opened
(`python3 -m unittest tests.test_lint_closing_criteria.TestCorpusSweepStaysClean`
→ `Ran 1 test … OK`). This close re-annotated the artifact — 53 entries, each
with `oracle`, `kind`, `state`, `attempt` — and the corpus sweep is green
against the annotated artifact, which is the state that matters.

### Per-WU scoped runs and symbol checks

| Oracle | Result | Exit |
|---|---|---|
| `python3 -m unittest tests.test_notify -v` | Ran 18 tests, OK | **0** |
| `python3 -m unittest tests.test_notify_escalation -v` | Ran 7 tests, OK | **0** |
| `python3 -m unittest tests.test_notify_sla -v` | Ran 17 tests, OK | **0** |
| `python3 -m unittest tests.test_heartbeat -v` | Ran 10 tests, OK | **0** |
| `python3 -m unittest tests.test_agent_policy_schema -v` | Ran 29 tests, OK | **0** |
| `python3 -m unittest discover -s tests -p "test_escalation*.py" -v` | Ran 16 tests, OK | **0** |
| `python3 -m unittest tests.test_skills_vendored_in_sync -v` | Ran 4 tests, OK | **0** |
| `python3 -m unittest tests.test_attention_skill_structure tests.test_attention_nonwriting_guard -v` | Ran 5 tests, OK | **0** |
| `python3 -c "from specfuse.loop.notify import post_notification, resolve_webhook_url"` | — | **0** |
| `python3 -c "from specfuse.loop.notify_escalation import notify_new_escalation"` | — | **0** |
| `python3 -c "from specfuse.loop.notify_sla import sla_sweep, PARKED_LABEL"` | — | **0** |
| `python3 -c "from specfuse.loop.heartbeat import last_run_at, silence_check"` | — | **0** |

### Signature and identity checks

`inspect.signature` over each shipped symbol, compared against the string its WU
declared as load-bearing. All six match; two carry additive divergences worth
recording:

- `post_notification(message, *, policy_path=None, poster=None, now=None) -> bool`
  — T01 declared no `now` parameter. The addition is what makes quiet hours
  testable without a clock, and it is keyword-only with a default, so it is
  purely additive.
- `silence_check(*, now: float, ...)` — `now` is **epoch seconds**, not a
  `datetime`, while `sla_sweep`'s `now` is a `datetime`. Both WUs wrote `now`
  with no type, so neither diverged from its declaration, but the two injected
  clocks in one feature now disagree on units. Recorded as a consumer-visible
  detail below rather than fixed here; a close verifies, it does not implement.

Identity assertions (constants imported, never retyped), all `True`:
`notify_escalation.NEEDS_HUMAN_LABEL is escalation.NEEDS_HUMAN_LABEL`;
`notify_escalation.CATEGORY_LABELS is escalation.CATEGORY_LABELS`;
`notify_sla.NEEDS_HUMAN_LABEL is escalation.NEEDS_HUMAN_LABEL`;
`notify_sla.PARKED_LABEL == "escalation-parked"`.

## The security posture, re-tested from shipped code

The feature's entire security posture is that the webhook URL lives in the
environment and touches nothing else. All three claims were re-tested in this
session against the shipped modules — not read from source, and not inherited
from T01's report. The harness was written and run **outside the repository
tree**, deliberately: it constructs a URL-shaped literal, and a file carrying
one has no business in a committed tree. Its checks and outputs are reproduced
below; the reproduction recipe is in
[What the loop did NOT verify](#what-the-loop-did-not-verify).

Every check below is a **negative observation** where one is possible — the rule
seen rejecting a purpose-built bad input — per `verification-discipline.md` §3.

### Security claim 1 re-tested — the config surface refuses to hold a credential

| Check | Input | Observed | Verdict |
|---|---|---|---|
| 1a | a policy carrying `escalation.webhook: ""` | `["ERROR: unknown 'escalation.webhook' key", "ERROR: missing 'escalation.webhook_env' key"]` | **PASS** |
| 1b | a policy carrying a literal `https://…` URL in `escalation.webhook_env` | `ERROR: 'escalation.webhook_env' must be an environment-variable NAME, not a value (got '…')` | **PASS** |
| 1c | `webhook_env: "SPECFUSE_NOTIFY_WEBHOOK"` (conforming) | `[]` — zero findings | **PASS** |
| 1c | `webhook_env: ""` (this repo's own state) | `[]` — zero findings | **PASS** |

The two 1c rows are the satisfiability control PLAN.md § *Escalation-predicate
satisfiability* promised: the rule reports **zero** on an input already in its
intended final state, including the empty-value case this repo actually ships.
The rename is a rename and not a deprecation — the old spelling is rejected, not
tolerated.

### Security claim 2 re-tested — the resolved URL escapes into nothing

A fake webhook URL carrying a unique sentinel token was placed in the
environment and named by `webhook_env`, and a poster that raises was injected.

| Check | Observed | Verdict |
|---|---|---|
| precondition | `resolve_webhook_url` returned the URL — so the leak assertions below are **not vacuous** | **PASS** |
| 2a | the raising poster did not propagate; nothing was raised into the caller | **PASS** |
| 2b | return value is `False`; the sentinel is absent from its `repr` | **PASS** |
| 2c | captured root-logger output was exactly `notify: poster raised an exception` — the sentinel is absent, and the string `https` does not appear at all | **PASS** |
| 2d | the URL **did** reach the injected poster as the POST target | **PASS** |
| 2e | the built payload was `{"text": "escalation filed"}` — no URL | **PASS** |
| 2f | the same through `notify_new_escalation`: no raise, returns `False`, no sentinel in the log | **PASS** |
| 2g | with the named environment variable unset, `resolve_webhook_url` returns `None` | **PASS** |
| 2h | an unknown escalation category raises `ValueError` **before** any post — zero poster calls recorded | **PASS** |
| 2h' | that rejection message carries no URL | **PASS** |

2d is what makes 2b, 2c and 2e load-bearing: the URL was resolved and used, and
still appeared in no return value, no exception text, and no log line. The
notifier's failure log is a fixed string with no interpolation, which is why it
cannot leak.

### Security claim 3 re-tested — this repo's own policy holds no credential

| Check | Observed | Verdict |
|---|---|---|
| 3a | `.specfuse/agent-policy.yml` → `escalation.webhook_env == ""` | **PASS** |
| 3b | the live policy has no `escalation.webhook` key at all; keys are `assignee, provider, quiet_hours, silence_hours, sla_hours, webhook_env` | **PASS** |
| 3c | `escalation.provider == "none"` | **PASS** |
| 3d | `validate_agent_policy` over the live policy → zero findings | **PASS** |
| 3e | `leak-scan` over the whole tree → `leak-scan: clean` (gitleaks 8.30.1) | **PASS** |

This close did not add a URL to any policy file to exercise a path, and
`.specfuse/agent-policy.yml`'s `webhook_env` is untouched, per this WU's **Do
not touch**.

## The composite oracle

The feature-level assertion no individual WU could make: that the four units
compose. One simulated escalation, an injected poster and an injected fake `gh`
runner, an issue filed 30 hours before `now` against `sla_hours: 24`.

| Check | Observed | Verdict |
|---|---|---|
| 5a | filing produces **exactly one** post; `notify_new_escalation` returns `True` | **PASS** |
| 5a' | the post is a one-liner carrying the issue link: `[needs-human:blocked-wu] <summary> — https://github.com/<owner>/<repo>/issues/42` | **PASS** |
| 5b | the first sweep past the window returns `[{"number": "42", "action": "repinged"}]` | **PASS** |
| 5b' | that re-ping is **exactly one** additional post — 2 total | **PASS** |
| 5b'' | one `<!-- specfuse:sla-repinged at=… -->` comment was written | **PASS** |
| 5c | the second sweep returns `[{"number": "42", "action": "parked"}]` | **PASS** |
| 5c' | post count is **still 2** — no double re-ping | **PASS** |
| 5c'' | labels are `["needs-human", "escalation-parked"]` — parked was added, needs-human was not removed | **PASS** |
| 5c''' | no argv reaching the runner contained `close` on any path — the parked issue stays open | **PASS** |
| 5c'''' | a **third** sweep still parks and still posts nothing | **PASS** |
| 5d | with `webhook_env: ""`: **no post at all**, on any path — `notify_new_escalation` returns `False` and the recorder saw zero payloads | **PASS** |
| 5d' | …and the SLA bookkeeping still works without a channel: re-ping then park | **PASS** |

No double re-ping and no post with an empty `webhook_env` — the two escalation
triggers this criterion guards against did not fire. 5d' is the property that
matters most for an operator who never configures a webhook: the queue stays
coherent with no channel at all.

## Solo-drafting decision audit

This feature was **drafted solo, with no operator interview**, on operator
instruction (2026-08-09), alongside FEAT-2026-0044 and FEAT-2026-0048. PLAN.md
§ *Assumed decisions* lists eight decisions for veto at PR review. All eight,
audited against what the implementation actually did:

**1. Single gate, single terminal close.** **Validated.** Four substantive WUs,
all `done` on attempt 1, zero re-arms, no `blocked` outcome, and the substantive
half came in at 42% of its planned spend. Nothing about the run suggests the
ceremony was too thin — and this close, the one load-bearing session, is where
the only unmet criterion surfaced, which is the ceremony earning its cost.

**2. The config holds an environment-variable NAME, not a URL.** **Validated,
and it is the decision that carried the feature.** Re-tested above from the
shipped code: the old key is rejected, a literal URL is an `ERROR: `, and both
conforming shapes report zero. See § *The `webhook_env` rename* below for what
changing a same-night schema actually cost.

**3. Provider support is a payload adapter, chosen by an explicit `provider:`
key rather than sniffed.** **Validated as a design, lightly exercised as code.**
Three pure adapters exist and are unit-tested for envelope shape, and the
explicit key means no code path parses the URL. But **the roadmap row's phrase
"provider swap = URL change" is not what shipped**: a provider swap is a URL
change *and* a `provider:` change. That divergence is a direct consequence of
this decision and is the right trade — but the row promised the simpler thing,
and the roadmap detail section is corrected accordingly.

**4. The notifier is fire-and-forget and never fatal.** **Validated hard.** All
three failure modes (raise, timeout, non-2xx) return `False` without
propagating, covered by `tests.test_notify` and re-tested at two call layers by
this close's security claim 2. The reliability ordering PLAN.md wanted — the
issue is the system of record, the notification is a courtesy — holds by
construction: `notify_new_escalation` is a separate step invoked *after*
`emit_escalation` returns, so it cannot wrap or fail the filing path.

**5. Every payload is redacted before it leaves the process.** **Validated
structurally, but currently close to vacuous.** `redact_text` is applied in all
three adapters and a test asserts a redactable token is absent from the payload.
The strain: by decision 3's sibling constraint the message is *only* a one-liner
and a link, so there is almost nothing for redaction to remove. The decision is
right, but its value today is as a standing guard against a future message that
carries body text — not as a filter doing work now. Worth saying plainly so a
reader does not read "redaction is applied" as "redaction has been exercised
against real body text."

**6. The last-run timestamp is derived, never stored.** **Validated.**
`last_run_at` globs `.specfuse/features/*/events.jsonl` and returns the newest
timestamp; `test_does_not_write_any_events_file` asserts the module writes
nothing under `.specfuse/features/`. Malformed lines are skipped rather than
fatal. One strain worth recording: the derivation is a full scan of every event
in every feature with no index, and this repository already carries 50+ feature
folders. Irrelevant at today's size, and cheaper than the class of bug a stored
timestamp on an ephemeral runner produces — but it is O(all history), and the
decision's rationale did not mention that cost.

**7. SLA re-pings exactly once, then parks.** **Validated by the composite
oracle** — one re-ping, park on sweeps 2 and 3, post count never exceeds 2.
Strain: "exactly once" is derived from a marker living in the issue's comment
list, so the guarantee is exactly as durable as GitHub's comment history, and
every test exercises it through a fake runner. If a comment is deleted, the
issue re-pings again. That is the correct trade against a disk-backed counter on
an ephemeral runner, and it is the trade `monitor/autofix_state.py` already
makes — but it is a trade, not an absolute.

**8. Quiet hours suppress the post, never the issue.** **Unexercised against the
real path.** `post_notification` honours `quiet_hours` and returns `False`
without calling the poster, and `tests.test_notify` covers the suppressed and
unsuppressed cases. But "never the issue" is a property of code this feature
never wrote: nothing here files an issue, and `escalation.py` was not modified.
The decision holds **by construction** — suppression happens inside the notifier,
downstream of filing — rather than by any test that files an issue during quiet
hours. Coverage confirms the shallowness: `_in_quiet_hours` lines 102 and 106 are
uncovered, meaning a **malformed** `quiet_hours` string and a **non-wrapping**
window (`09:00-17:00`) are both untested; only the midnight-wrapping form is
exercised.

**Summary: five validated (1, 2, 4, 6, 7), two validated-but-strained (3, 5),
one unexercised (8).** None was contradicted by the implementation. The two
strains and the one unexercised decision are all in the same direction — the
feature's *outbound* half is far better verified than its *configured* half,
which is the same finding § *The whole configured path is untested* records
below.

## The `webhook_env` rename against a same-night schema

T01 changed a field FEAT-2026-0044 had shipped hours earlier
(`escalation.webhook` → `escalation.webhook_env`), with no compatibility shim.

**What it cost, measured.** Four edits: the key in
`.specfuse/agent-policy.yml`, the key in `.specfuse/agent-policy.yml.example`,
the schema key set and validator in `specfuse/loop/agent_policy.py`, and the
tests. No consumer code changed, because there was no consumer — FEAT-2026-0044
shipped the field and FEAT-2026-0047 is its first and only reader. T01 landed
the rename and the example's migration in the same unit, so no intermediate tree
failed its own gate, which is the expand→migrate→contract ordering
`[FEAT-2026-0069/G1]` records as the only one satisfiable under the preflight
baseline probe. T01 came in at $1.81 against a $4.50 plan — the rename was not
where the money went.

**One piece of residue.** `CHANGELOG.md`'s `Unreleased` section still carries
FEAT-2026-0044's entry describing `escalation.webhook_env`'s predecessor
alongside the rest of that schema. This close does **not** edit that entry:
rewriting a shipped changelog entry to match a later rename hides that the
rename happened. Instead the rename is appended as its own `### Breaking` entry
tracing to FEAT-2026-0047, so a reader of `Unreleased` sees both the original
shape and the correction, in order.

**Did the rename-without-shim call hold up? Yes — and the reason it held is
narrower than it looks.** Both features sit in the *same* unreleased section:
no tagged release ever carried `escalation.webhook`, so no consumer outside this
repository could have adopted it. That is what made the no-shim call cheap. A
shim would have meant accepting both spellings indefinitely, and the old
spelling is precisely the unsafe one — a permanent second door into the failure
mode the feature exists to close. The generalisable form of the call is *"rename
without a shim while the key is still unreleased; after a tagged release, the
same rename needs a reader that accepts both shapes."* It would **not** have
been the right call one release later.

## The whole configured path is untested against a real provider

Stated plainly, because green tests must not read as "notifications work":
**no notification produced by this feature has ever reached a real Discord,
Slack, or Teams channel.** Every test injects a poster, by design — PLAN.md's
"No test may perform a real HTTP request" is a deliberate constraint, since a
test that reached the network would be both flaky and, with a real URL, a leak.

Coverage measures exactly how much of the configured path is unexercised.
`coverage report --show-missing` over the feature's modules:

```
specfuse/loop/heartbeat.py              47      5    89%   53, 71-72, 75, 82
specfuse/loop/notify.py                 77      8    90%   65, 102, 106, 111-121
specfuse/loop/notify_escalation.py      14      0   100%
specfuse/loop/notify_sla.py             62      0   100%
```

`notify.py` lines **111–121 are `_default_poster` in its entirety** — the
`urllib.request` call, the JSON body, the `Content-Type` header, the 10-second
timeout, the status read. That function is the *only* code in this feature that
would ever touch a real provider, and it has **zero** coverage. Everything green
above it is green with a fake in its place.

What this means concretely, and what it does not:

- **What is proven:** the message shape, the payload envelopes, the redaction
  call, the never-fatal contract, the quiet-hours gate, the SLA once-then-park
  rule, and the no-op-on-empty behaviour — all against an injected poster.
- **What is not proven:** that any of the three payload envelopes is *accepted*
  by the provider it names; that `_default_poster` serialises, addresses, and
  times out correctly; that a real incoming-webhook URL round-trips from the
  environment through to a delivered message. The three adapters were written
  from each provider's documented envelope, and no response from any provider
  has ever been observed.
- **The other two uncovered regions** are narrower but real: `heartbeat.py`
  71–72, 75 and 82 are `_resolve_silence_hours`' fallbacks (absent policy file,
  non-mapping `escalation`, invalid `silence_hours`), so the default-24
  behaviour is untested; `notify.py` 102 and 106 are the malformed-`quiet_hours`
  and non-wrapping-window branches noted in decision 8 above.

The first live post is an operator-deferred oracle. It is listed in
[What the loop did NOT verify](#what-the-loop-did-not-verify) with the exact
condition that would settle it.

## Consumer-visible contract changes

`close-discipline.md` §3. Eight items, enumerated across all four producing WUs.
Every one is also appended to `CHANGELOG.md`'s `Unreleased` section, classified,
carrying this feature's `FEAT-2026-0047` trace. **This section blocks on
explicit human acknowledgment** — recorded as D1 below.

1. **BREAKING — `escalation.webhook` is renamed to `escalation.webhook_env`, and
   its value is now an environment-variable NAME rather than a URL.** The old
   spelling is an `ERROR: unknown 'escalation.webhook' key`, not a warning and
   not a silent acceptance; a policy carrying it fails
   `agent-policy-example-lint`. A literal `https://` value in the new key is an
   `ERROR: ` finding. Any project that copied `escalation.webhook` from
   FEAT-2026-0044's example must rename the key and move the URL into the
   environment. Migration is one line. **The URL must not be committed.**
2. **NEW — `escalation.provider`**, one of `discord` | `slack` | `teams` |
   `none`. Optional; absent is valid and behaves as `none`. An unrecognised
   value is an `ERROR: ` finding. **A provider swap is now a two-line change**
   (the environment's URL *and* this key), not the "URL change" the roadmap row
   promised — the provider is declared, never sniffed from the URL, because
   sniffing a bearer credential means parsing it.
3. **NEW — `escalation.silence_hours`**, int > 0, default 24. Optional; a zero,
   a negative, or a non-int is an `ERROR: ` finding. Consumed by
   `heartbeat.silence_check`.
4. **NEW label — `escalation-parked`.** Added by `notify_sla.sla_sweep`
   alongside `needs-human`, which is never removed. A repository whose label
   registry does not carry it will have the label created or the edit rejected
   by `gh`, depending on its settings; the sweep's parking decision is derived
   from the marker, not the label, so a failed label write degrades the UI
   swatch and not the behaviour.
5. **NEW published marker — `<!-- specfuse:sla-repinged at={epoch_seconds} -->`,
   written as an issue comment.** This is the authoritative record that an
   escalation has already been re-pinged, and its idempotency key. **Once an
   issue carries one, changing this format orphans that issue** — it would scan
   as never-re-pinged forever and be re-pinged on every sweep. Treat the format
   as frozen; a future change needs a reader accepting both shapes, not an edit.
6. **CHANGED — the `/attention` skill gains a *Check for silence* section**, in
   the published plugin and vendored to `.specfuse/skills/`, so any project
   upgrading its scaffold gains the new behaviour: `/attention` calls
   `specfuse.loop.heartbeat.silence_check` on open and prints a staleness line.
   It explicitly does **not** fire the webhook — a human is already reading the
   output.
7. **NEW public module — `specfuse.loop.notify`**, shipped in the wheel;
   nothing previously occupied that import path. Public surface:
   `post_notification`, `resolve_webhook_url`, `discord_payload`,
   `slack_payload`, `teams_payload`. The contract a consumer depends on is that
   it **never raises and never fails a gate**: every failure and every no-op
   returns `False`, so `False` means "did not post", not "error". A caller that
   needs to distinguish the two must ask `resolve_webhook_url` itself.
8. **NEW public modules — `specfuse.loop.notify_escalation`,
   `specfuse.loop.notify_sla`, and `specfuse.loop.heartbeat`**, shipped in the
   wheel; none previously occupied its import path. Public surface:
   `notify_new_escalation`; `sla_sweep` and `PARKED_LABEL`; `last_run_at` and
   `silence_check`. `notify_new_escalation` is the one function here that
   **does** raise — `ValueError` on an unknown category, before any post,
   matching `render_escalation_body`'s own behaviour.

**One asymmetry a consumer should know about, short of a contract change:** the
two injected clocks in this feature disagree on units.
`notify_sla.sla_sweep(now=...)` takes a `datetime`;
`heartbeat.silence_check(now=...)` takes **epoch seconds** as a float. Both are
new in this feature, both are keyword-only, and neither WU's declaration
specified a type, so neither diverged from its plan. A caller wiring both — which
is exactly what FEAT-2026-0049 will do — must convert between them. Recorded
rather than fixed: this close verifies, it does not implement.

## Cost analysis

Actuals read from `.specfuse/features/FEAT-2026-0047-notify-webhook/events.jsonl`
(`task_completed` payloads, `cumulative_cost_usd`, which folds in any re-arm
cycles). **Every WU has `re_arm_count: 0` and `attempts_lifetime: 1`**, so
`cost_usd` and `cumulative_cost_usd` are equal throughout — there were no re-arm
cycles on this feature.

| WU | Planned | Actual | Delta | Variance | Attempts | Duration |
|---|---:|---:|---:|---:|---:|---:|
| T01 — notifier + `webhook_env` | $4.50 | $1.812547 | −$2.687453 | **−59.7%** | 1 | 871s |
| T02 — notify on escalation | $3.00 | $0.706789 | −$2.293211 | **−76.4%** | 1 | 617s |
| T03 — SLA re-ping and park | $3.50 | $2.469086 | −$1.030914 | −29.5% | 1 | 1482s |
| T04 — heartbeat silence alert | $4.00 | $1.268404 | −$2.731596 | **−68.3%** | 1 | 763s |
| **Substantive subtotal** | **$15.00** | **$6.256826** | **−$8.743174** | **−58.3%** | 4 | 3733s |
| G1-CLOSE (this WU) | $5.00 | *stamped by the driver at exit* | — | — | 1 | — |
| **Feature planned total** | **$20.00** | — | — | — | | |

**Gate 1 against its budget.** `GATE-01.md` carries `cost_budget_usd: 24.50`.
Substantive spend is $6.256826, leaving **$18.24 of the gate budget unspent
before this close's own cost**. The close would have to cost more than $18.24 —
3.6× its $5.00 plan — to breach the gate budget. For calibration, the comparable
close on FEAT-2026-0044 (same day, same shape, `opus`/`high`, also
`auto_close_disabled`) cost $8.73 against the same $5.00 plan. At that rate this
feature lands near **$15.0 against a $20.00 plan and a $24.50 gate budget** —
inside both. This close cannot report its own actual: the driver stamps
`cost_usd` into this WU's frontmatter after the session ends.

**Feature total against PLAN.md's $20.00.** $20.00 planned, $6.26 spent on
implementation, one close outstanding. The feature will come in under plan
unless this close costs more than $13.74.

### Why three WUs came in more than 50% under plan

**T01 (−59.7%).** T01 was planned as the expensive unit: a new module, three
adapters, a schema rename, and an example migration, all in one WU to avoid an
intermediate red tree. It came in at 40% of plan because the two things that
usually make a foundation WU expensive were both already answered before
dispatch. The convention to copy was named exactly
(`lint_monitoring._ENV_VAR_NAME_RE`, with its rationale comment), and the
directory layout to copy was named exactly (`specfuse/monitor/providers/`) —
PLAN.md's existing-mechanism table did that search at plan time and recorded the
verdicts, so the session spent no turns rediscovering them. The estimate priced
in a search the plan had already paid for.

**T02 (−76.4%), the largest variance in the feature.** T02 is 14 statements of
shipped code: a URL formatter, a category guard, a one-line message, and a
delegation to `post_notification`. Its plan priced it as a peer of the other
three units. It is not one — it is the thinnest possible seam between two
modules that already existed, and the WU body's constraints ("import the
constants, do not retype them"; "a one-liner and a link, nothing else") removed
essentially all of the design latitude that costs turns. The lesson is not that
the estimate was careless but that **a WU whose whole job is to compose two
finished modules should be priced against its own statement count, not against
its siblings.** It also finished with 100% coverage, which is what 14 statements
under seven tests looks like.

**T04 (−68.3%).** T04 bundled a new module, a schema key, a skill edit, and a
sync-script run — four surfaces, which is what the $4.00 estimate priced. Three
of the four turned out to be near-mechanical: `silence_hours` follows the
validation shape `sla_hours` already had; the skill edit is one prose section;
and `scripts/sync-scaffold.sh` is a single invocation. Only `last_run_at` and
`silence_check` were genuine design, and PLAN.md's assumed decision 6 had
already settled the one real question (derive, do not store) with the precedent
citation attached. **T04 also carries this feature's one unmet criterion**
(criterion 9's missing guard test), and it is worth noting that the cheapest of
the three under-spends is where the gap is — see D2. The under-spend and the gap
are plausibly the same fact: the skill edit was treated as the mechanical part
of the WU, and its falsifiable half was dropped with it.

**The common cause.** All three under-spends came from the same place: a plan
that had already done the searching. PLAN.md's existing-mechanism table and
verb-check table cost real tokens at plan time and were repaid four times over.
The counter-lesson is that estimates written *alongside* such a table should be
priced against the post-search work, not the pre-search work — otherwise the
plan pays twice and the budget reads as slack.

### Failure-class breakdown

(no non-passing attempts in scope)

Every `attempt_outcome` event in this feature's `events.jsonl` reads
`outcome: passed` with `failure_class: null` and `failure_signature: null`, on
attempt 1, for all four substantive WUs. There is one non-attempt failure event
worth naming so this section is not read as "nothing went wrong": a
`human_escalation` with `reason: preexisting_gate_failure` at
`2026-08-10T08:55:58Z`, which halted gate 1 on two failing baseline gates
(`tests` and `coverage`). That is a gate-entry probe result, not a WU attempt,
so it is not a failure class; both gates are green in this session and the
reconciliation is in § *The two gates the driver escalated on at gate entry are
green* above.

Four driver-side `driver_staleness_detected` halts also appear — one after each
substantive WU — because every WU in this feature modified a file the driver
itself imports (`agent_policy.py`, `notify.py`, `notify_escalation.py`,
`labels.py`, `notify_sla.py`, `heartbeat.py`). Each required a driver restart
and cost wall-clock, not attempts: the gaps between `task_completed` and the
next `task_started` are 15, 20, 5 and 17 minutes respectively, roughly 57
minutes of the run. Expected for a feature that ships modules into the driver's
own package, and recorded here because it is invisible in the cost column.

## Documentation

`.specfuse/roadmap.md`'s FEAT-2026-0047 detail section gained a **What shipped**
section describing the delivered shape, including the two places the delivered
shape diverges from the row's original Goal prose: the key is
`escalation.webhook_env` (the Goal says `escalation.webhook`, written before the
security correction), and a provider swap is a URL change *plus* a `provider:`
change (the Goal says "provider swap = URL change"). **The Goal prose itself is
left as authored** — it is the row's original promise, and rewriting it to match
the outcome would erase the fact that the promise moved.

**The row and the detail agree, and both stay `active`.** The row's Status
column reads `active` and the detail section reads `**Status: active.**`. That
is correct and deliberate for a hedged verdict: on `partially_met` the driver
leaves every terminal surface un-flipped (gate `awaiting_review`, roadmap row
`active`, `PLAN.md` `active`), and this close does not write `PLAN.md`'s
`status` — `fire_terminal_flips` owns that, gated on the verdict.

`CHANGELOG.md`'s `Unreleased` section gained seven entries tracing to
FEAT-2026-0047 — one `Breaking`, five `Added`, one `Changed` — carrying the same
eight items as § *Consumer-visible contract changes*. Seven entries for eight
items because item 8's three sibling modules share one entry; item 7,
`specfuse.loop.notify`, has its own. `parse_changelog` reports **zero findings**
over the edited file. This is the same enumeration, written once and placed
where a consumer reads it, not a second write.

## Lessons promoted

**Nothing generalizes into `.specfuse/LEARNINGS.md` from this close** — not
because nothing was learned, but because this feature runs
`autonomy_default: auto`, and under `auto` a closing WU that touches
`.specfuse/LEARNINGS.md` fails `assert_learnings_staged_under_auto` (reason
`learnings_not_staged`). No human read this gate before the close dispatched, so
a lesson written straight into the planning-context file would compound into
every future feature unreviewed. Three candidate lessons are staged in this
feature's `LEARNINGS-pending.md` for the operator to promote, narrow, or reject
at PR review:

1. **The config holds a name, the environment holds the value** — the
   convention, its enforcement shape, and the boundary of where it applies.
2. **A criterion of the form "X ships AND a test asserts X" needs its two halves
   verified separately** — the gate set proves neither half, which is how T04#9
   passed four green gates with only one half delivered.
3. **Price a composition WU against its own statement count, not against its
   siblings** — from T02's −76.4% variance.

This is the second time the staging mechanism has fired in this repository;
FEAT-2026-0044's close was the first, three hours earlier.

## Hedged-verdict follow-up record

Four entries, one per acceptance criterion this close could not settle as `met`.
Each gives the criterion verbatim, why it is unmet here, the exact re-run
condition that would upgrade it, and its `kind:`. This section and
[What the loop did NOT verify](#what-the-loop-did-not-verify) describe the same
material; this one carries the classification.

### D1 — Human acknowledgment of the consumer-visible contract-change list

- **Criterion, verbatim** (`close-discipline.md` §3): "The close enumerates
  every consumer-visible addition, removal, or rename the feature makes across
  ALL its producing WUs — API surface, generated models, published schemas, CLI
  flags, whatever contract consumers depend on — and **blocks on explicit human
  acknowledgment of the list**."
- **Why unmet here:** the enumeration exists and is complete (eight items, above,
  and in `CHANGELOG.md`'s `Unreleased`), but an agent cannot supply the
  acknowledgment it is collecting. `operator-escalation.md` names writing the
  human's own justification for them as a failure the rule exists to prevent.
  Item 1 is a **breaking rename**, which is the item class that most needs a
  real read.
- **Re-run condition that would upgrade this:** the operator reads the eight items
  at this feature's PR and acknowledges them — which for this feature is the
  same read that discharges the solo-drafting veto checkpoint over the eight
  assumed decisions, so it is one review, not two.
- **kind:** `acceptance-discharged`

### D2 — T04 criterion 9's guard test does not exist

- **Criterion, verbatim** (T04 acceptance criterion 9):
  "`plugins/specfuse/skills/attention/SKILL.md` gains a section instructing the
  skill to call `specfuse.loop.heartbeat.silence_check` on open and print the
  staleness line, explicitly **without** firing the webhook because a human is
  already reading. A test asserts the skill body names
  `specfuse.loop.heartbeat.silence_check` as an exact-match literal."
- **Why unmet here:** the **first half shipped** — `grep -qF
  'specfuse.loop.heartbeat.silence_check'` exits 0 against both
  `plugins/specfuse/skills/attention/SKILL.md` and the vendored
  `.specfuse/skills/attention/SKILL.md`, and the section correctly instructs the
  skill not to fire the webhook. The **second half did not**:
  `grep -rl 'heartbeat.silence_check' tests/` returns nothing (exit 1). No test
  in this repository asserts that literal. This is not a limitation of the close
  environment — it is a deliverable that was not delivered, which is why the
  verdict is `partially_met` rather than `met_locally`, and why `T04#9` is
  recorded `state: fail` in `GATE-01-CRITERIA.md`. It is the exact failure mode
  the criterion's second half exists to prevent: prose passes every automated
  code gate trivially, so without a falsifiable assertion the section can be
  edited away and nothing goes red. `tests/test_attention_skill_structure.py`
  already exists for this purpose — FEAT-2026-0046 wrote it to make the same
  skill's other required sections falsifiable — so the guard has an obvious home
  and was simply not added to it. **This close does not add it:** a close
  verifies, it does not implement, and writing the missing assertion here would
  mean the close both produces and blesses the same deliverable.
- **Re-run condition that would upgrade this:** a follow-up work unit adds the
  assertion to `tests/test_attention_skill_structure.py` — one line, in the
  shape that file's existing literal checks already use —  and
  `python3 -m unittest tests.test_attention_skill_structure` exits 0 with the
  literal asserted, verified by deleting the SKILL.md section and observing the
  test go red. Then `T04#9` flips to `state: pass` and this entry clears.
- **kind:** `externally-verifiable-later` — classified for the ceiling it
  implies, which is the load-bearing half: real rework exists and would raise
  the verdict, so the operator has a genuine choice between accepting the hedge
  and asking for the one-line fix first. It is not `routed-finding`, which would
  claim another surface already owns it, and it is emphatically not `inherent`.
  The "external" condition here is a follow-up WU rather than a different
  machine.

### D3 — `specfuse/loop/escalation.py` is unmodified by T02, by diff

- **Criterion, verbatim** (T02 acceptance criterion 6):
  "`specfuse/loop/escalation.py` is **unmodified** by this WU — `git diff
  --stat` shows no change to it, and `tests/test_escalation*.py` passes
  untouched."
- **Why unverifiable here:** the criterion names `git diff --stat` as its
  oracle, and a work-unit session runs no `git` at all (`result-contract.md`
  rule 1, `never-touch.md` §3). The pre-dispatch `diff-stat` oracle capture is
  truncated to a byte budget — it shows 14 of 69 changed paths — so it cannot
  answer the question either. **The second half was verified:**
  `python3 -m unittest discover -s tests -p "test_escalation*.py" -v` ran clean
  in this session (16 tests, OK, exit 0), which is the behavioural proof that
  `escalation.py`'s semantics survived; and the identity assertions above show
  `notify_escalation` imports its constants from that module rather than
  shadowing them. Only the diff-shaped half is open.
- **Re-run condition that would upgrade this:**
  `git diff --stat main -- specfuse/loop/escalation.py` returning empty output,
  run by anyone with git access — the PR's own changed-files list answers it at
  review.
- **kind:** `externally-verifiable-later`

### D4 — The red half of the four red-test-first criteria

- **Criterion, verbatim** (T01#1, and identically T02#1, T03#1, T04#1):
  "`tests/test_notify.py::TestPostNotification::test_no_webhook_configured_is_noop`
  exists and **fails on HEAD before this WU runs**."
- **Why unverifiable here:** the assertion is about a tree state that no longer
  exists. Re-running each named test today proves the *green* half and can never
  prove the red half, because the module the test imports is now present.
  Reaching the red state requires checking out each WU's parent commit, which is
  a `git` operation this session may not perform. All four named tests exist and
  pass — `tests.test_notify` (18), `tests.test_notify_escalation` (7),
  `tests.test_notify_sla` (17), `tests.test_heartbeat` (10), all exit 0 — so the
  entries are recorded `pass` in `GATE-01-CRITERIA.md` on the strength of the
  half that is assertable.
- **Re-run condition that would upgrade this:** check out each work unit's
  parent commit and run the named test nodeid, expecting a failure — e.g.
  `git checkout 9e8ab8e && python3 -m unittest
  tests.test_notify.TestPostNotification.test_no_webhook_configured_is_noop`.
  Cheap, but it needs git.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** Three of the four entries are
`externally-verifiable-later`, so by
`closing_requirements.verdict_ceiling_for_kinds` **rework exists**: D2 is a
one-line test, and D3 and D4 are git-shaped checks any environment permitted to
run `git` can settle in seconds. That leaves D1, whose discharge *is* the
operator accepting the verdict. The operator therefore has a real choice between
accepting `partially_met` now at PR review and asking for D2's missing guard
first. **D2 is the one worth asking for** — it is the only entry describing work
that does not exist yet, and the only one whose absence lets a shipped
deliverable regress silently.

## What the loop did NOT verify

Six entries. The first four are the hedged-verdict follow-up record above,
restated with where each actually gets checked; the last two are scope notes
rather than unmet criteria.

1. **Human acknowledgment of the consumer-visible contract-change list (D1).**
   *Where it actually gets checked:* the operator's read of this feature's PR —
   the same read that is this feature's solo-drafting veto checkpoint over the
   eight assumed decisions.
2. **T04 criterion 9's guard test (D2).** *Where it actually gets checked:*
   nowhere, currently. That is the finding. Until a test asserts the literal,
   the `/attention` staleness section is prose that passes every code gate
   trivially and can be deleted without going red. It gets checked when a
   follow-up WU adds the assertion to `tests/test_attention_skill_structure.py`,
   which then runs in the `tests` gate on every CI run.
3. **`specfuse/loop/escalation.py` unmodified, by diff (D3).** *Where it
   actually gets checked:* the PR's changed-files list, or `git diff --stat main
   -- specfuse/loop/escalation.py` run by anyone with git access. The
   behavioural half is already checked by `tests/test_escalation*.py`, which
   runs in the `tests` gate on every CI run.
4. **The red half of the four red-test-first criteria (D4).** *Where it actually
   gets checked:* nowhere automatically, by construction — a red-test-first
   claim is verified once, by the producing session, at the moment it is true.
   The durable protection is that all four tests exist and are wired into the
   `tests` gate, so a regression that would have made them red again fails CI.
5. **A live post to a real Discord / Slack / Teams webhook — the feature's
   central promise — was never made.** Every test injects a poster, and
   `notify.py`'s `_default_poster` (lines 111–121, the entire `urllib` call) has
   **zero** coverage. Nothing in this repository proves that any of the three
   payload envelopes is accepted by the provider it names, or that a real
   incoming-webhook URL round-trips from the environment to a delivered message.
   This is not an oversight to be fixed in CI: PLAN.md forbids a test that
   performs a real HTTP request, because such a test would be flaky and, with a
   real URL, a leak. **Green tests here do not mean "notifications work"; they
   mean "everything up to the socket is correct."** *Where it actually gets
   checked:* the first operator who sets `escalation.webhook_env` to a real
   variable name, exports a real webhook URL, sets `escalation.provider`, and
   triggers one escalation — an operator-deferred oracle by design. That single
   run settles all three adapters' envelopes only for the provider used; the
   other two remain unproven.
6. **This close's own security harness is not in the repository and does not run
   in CI.** It was written to `$TMPDIR` and run from there deliberately: it
   constructs a URL-shaped literal with a sentinel token, and committing that
   file would put a URL-shaped string into the tree that `leak-scan` and the
   pre-commit structural scan exist to keep out. All of its assertions are
   reproduced above with their observed outputs. *Where it actually gets
   checked:* the durable subset already lives in the `tests` gate —
   `tests/test_notify.py::TestPostNotification::test_url_never_leaves_process_on_poster_exception`
   is the committed form of security claim 2, and
   `tests/test_agent_policy_schema.py`'s `test_old_webhook_key_is_error`,
   `test_webhook_env_url_shaped_is_error`, `test_webhook_env_name_shaped_is_valid`
   and `test_webhook_env_empty_is_valid` are the committed form of claim 1. What
   is *not* committed is the composite oracle (§ *The composite oracle*), which
   crosses three modules and has no single WU that owns it; it is reproducible
   from this document.

**No predecessor auto-close debt.** This feature has one gate and no
`<!-- specfuse:autoclose-debt -->` marker anywhere in its folder; nothing
auto-closed here and there is no deferred close to reconcile.

## Verdict

**`partially_met`.**

Everything the feature set out to build exists, all sixteen `code` gates are
green, all three security claims hold under re-test from the shipped code, and
the composite oracle shows the four units composing correctly — one post on
filing, one re-ping, a park, and silence when no webhook is configured. That is
the case for `met`.

It is not `met` because T04's acceptance criterion 9 asked for two things and
one of them was not delivered: the `/attention` staleness section shipped, and
the test that would keep it from being silently deleted does not exist. That is
an unmet deliverable, not an environment limitation, which is what separates
`partially_met` from `met_locally` here. Three further criteria — the diff-shaped
half of T02#6, the red half of the four red-test-first criteria, and the human
acknowledgment §3 requires — are unverifiable in this session and are recorded
above with their re-run conditions.

The honest one-line summary: **the notifier is built and the credential cannot
escape, but nothing here has ever posted to a real channel, and one guard that
was asked for is missing.**

## Hedged verdict accepted

- **Accepted verdict:** `partially_met`
- **Operator reason (verbatim):** "accepting since D2, D3 and D4 are verified with the final validation coming later with a real webhook"
- **Contract-change list:** acknowledged by the operator at PR review (#1411), discharging D1.
- **Recorded:** 2026-08-10T11:42:35+00:00

The verdict ceiling at acceptance time was **rework exists** — D2, D3, and D4 are
`externally-verifiable-later`. Unlike the sibling features accepted the same morning,
**every entry that named rework has had that rework done** before acceptance:

- **D2** was a genuine gap when the close ran. `tests/test_attention_silence_section.py`
  was authored at the operator's direction, asserts the entry-point literal, the
  no-webhook rule, and vendored-copy sync, and was verified falsifiable (3 of 5
  assertions fail against a sabotaged skill body).
- **D3** — `git diff --stat main -- specfuse/loop/escalation.py` returns empty.
- **D4** — `git cat-file -e <parent>:<test path>` fails for all four of
  `test_notify.py`, `test_notify_escalation.py`, `test_notify_sla.py`, and
  `test_heartbeat.py`, confirming the red half.

The entries below are still carried forward **verbatim and open**: accepting a hedge
records what was shipped with known-open items, it does not mark them done.

**Outstanding beyond the follow-up record, and the operator's stated reason for
accepting anyway:** no message has ever been sent to a real Discord/Slack/Teams
endpoint — every test injects a poster. Recorded in full under § *The whole configured
path is untested against a real provider*. Channel selection and webhook configuration
were routed into the `agent-policy.yml` interview-skill issue (**#1417**), including the
constraint that the interview must collect an environment-variable name and never a
pasted URL.

### Follow-ups carried forward, verbatim and open

### D1 — Human acknowledgment of the consumer-visible contract-change list

- **Criterion, verbatim** (`close-discipline.md` §3): "The close enumerates
  every consumer-visible addition, removal, or rename the feature makes across
  ALL its producing WUs — API surface, generated models, published schemas, CLI
  flags, whatever contract consumers depend on — and **blocks on explicit human
  acknowledgment of the list**."
- **Why unmet here:** the enumeration exists and is complete (eight items, above,
  and in `CHANGELOG.md`'s `Unreleased`), but an agent cannot supply the
  acknowledgment it is collecting. `operator-escalation.md` names writing the
  human's own justification for them as a failure the rule exists to prevent.
  Item 1 is a **breaking rename**, which is the item class that most needs a
  real read.
- **Re-run condition that would upgrade this:** the operator reads the eight items
  at this feature's PR and acknowledges them — which for this feature is the
  same read that discharges the solo-drafting veto checkpoint over the eight
  assumed decisions, so it is one review, not two.
- **kind:** `acceptance-discharged`

### D2 — T04 criterion 9's guard test does not exist

- **Criterion, verbatim** (T04 acceptance criterion 9):
  "`plugins/specfuse/skills/attention/SKILL.md` gains a section instructing the
  skill to call `specfuse.loop.heartbeat.silence_check` on open and print the
  staleness line, explicitly **without** firing the webhook because a human is
  already reading. A test asserts the skill body names
  `specfuse.loop.heartbeat.silence_check` as an exact-match literal."
- **Why unmet here:** the **first half shipped** — `grep -qF
  'specfuse.loop.heartbeat.silence_check'` exits 0 against both
  `plugins/specfuse/skills/attention/SKILL.md` and the vendored
  `.specfuse/skills/attention/SKILL.md`, and the section correctly instructs the
  skill not to fire the webhook. The **second half did not**:
  `grep -rl 'heartbeat.silence_check' tests/` returns nothing (exit 1). No test
  in this repository asserts that literal. This is not a limitation of the close
  environment — it is a deliverable that was not delivered, which is why the
  verdict is `partially_met` rather than `met_locally`, and why `T04#9` is
  recorded `state: fail` in `GATE-01-CRITERIA.md`. It is the exact failure mode
  the criterion's second half exists to prevent: prose passes every automated
  code gate trivially, so without a falsifiable assertion the section can be
  edited away and nothing goes red. `tests/test_attention_skill_structure.py`
  already exists for this purpose — FEAT-2026-0046 wrote it to make the same
  skill's other required sections falsifiable — so the guard has an obvious home
  and was simply not added to it. **This close does not add it:** a close
  verifies, it does not implement, and writing the missing assertion here would
  mean the close both produces and blesses the same deliverable.
- **Re-run condition that would upgrade this:** a follow-up work unit adds the
  assertion to `tests/test_attention_skill_structure.py` — one line, in the
  shape that file's existing literal checks already use —  and
  `python3 -m unittest tests.test_attention_skill_structure` exits 0 with the
  literal asserted, verified by deleting the SKILL.md section and observing the
  test go red. Then `T04#9` flips to `state: pass` and this entry clears.
- **kind:** `externally-verifiable-later` — classified for the ceiling it
  implies, which is the load-bearing half: real rework exists and would raise
  the verdict, so the operator has a genuine choice between accepting the hedge
  and asking for the one-line fix first. It is not `routed-finding`, which would
  claim another surface already owns it, and it is emphatically not `inherent`.
  The "external" condition here is a follow-up WU rather than a different
  machine.

### D3 — `specfuse/loop/escalation.py` is unmodified by T02, by diff

- **Criterion, verbatim** (T02 acceptance criterion 6):
  "`specfuse/loop/escalation.py` is **unmodified** by this WU — `git diff
  --stat` shows no change to it, and `tests/test_escalation*.py` passes
  untouched."
- **Why unverifiable here:** the criterion names `git diff --stat` as its
  oracle, and a work-unit session runs no `git` at all (`result-contract.md`
  rule 1, `never-touch.md` §3). The pre-dispatch `diff-stat` oracle capture is
  truncated to a byte budget — it shows 14 of 69 changed paths — so it cannot
  answer the question either. **The second half was verified:**
  `python3 -m unittest discover -s tests -p "test_escalation*.py" -v` ran clean
  in this session (16 tests, OK, exit 0), which is the behavioural proof that
  `escalation.py`'s semantics survived; and the identity assertions above show
  `notify_escalation` imports its constants from that module rather than
  shadowing them. Only the diff-shaped half is open.
- **Re-run condition that would upgrade this:**
  `git diff --stat main -- specfuse/loop/escalation.py` returning empty output,
  run by anyone with git access — the PR's own changed-files list answers it at
  review.
- **kind:** `externally-verifiable-later`

### D4 — The red half of the four red-test-first criteria

- **Criterion, verbatim** (T01#1, and identically T02#1, T03#1, T04#1):
  "`tests/test_notify.py::TestPostNotification::test_no_webhook_configured_is_noop`
  exists and **fails on HEAD before this WU runs**."
- **Why unverifiable here:** the assertion is about a tree state that no longer
  exists. Re-running each named test today proves the *green* half and can never
  prove the red half, because the module the test imports is now present.
  Reaching the red state requires checking out each WU's parent commit, which is
  a `git` operation this session may not perform. All four named tests exist and
  pass — `tests.test_notify` (18), `tests.test_notify_escalation` (7),
  `tests.test_notify_sla` (17), `tests.test_heartbeat` (10), all exit 0 — so the
  entries are recorded `pass` in `GATE-01-CRITERIA.md` on the strength of the
  half that is assertable.
- **Re-run condition that would upgrade this:** check out each work unit's
  parent commit and run the named test nodeid, expecting a failure — e.g.
  `git checkout 9e8ab8e && python3 -m unittest
  tests.test_notify.TestPostNotification.test_no_webhook_configured_is_noop`.
  Cheap, but it needs git.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** Three of the four entries are
`externally-verifiable-later`, so by
`closing_requirements.verdict_ceiling_for_kinds` **rework exists**: D2 is a
one-line test, and D3 and D4 are git-shaped checks any environment permitted to
run `git` can settle in seconds. That leaves D1, whose discharge *is* the
operator accepting the verdict. The operator therefore has a real choice between
accepting `partially_met` now at PR review and asking for D2's missing guard
first. **D2 is the one worth asking for** — it is the only entry describing work
that does not exist yet, and the only one whose absence lets a shipped
deliverable regress silently.

## What the loop did NOT verify

