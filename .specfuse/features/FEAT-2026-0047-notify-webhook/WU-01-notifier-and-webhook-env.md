---
id: FEAT-2026-0047/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
produces:
  - specfuse/loop/notify.py
  - tests/test_notify.py
produces_driver_helper: post_notification, resolve_webhook_url
---

# The notifier, its payload adapters, and the `webhook_env` security correction

**Objective.** Create `specfuse/loop/notify.py` — three provider payload
adapters and a fire-and-forget `post_notification` — and rename
`escalation.webhook` to `escalation.webhook_env`, enforcing that its value is an
environment-variable **name** rather than a URL.

**Context.** Correlation ID `FEAT-2026-0047/T01`. Foundation WU: T02, T03, and
T04 all call this module.

**The security correction is the reason this WU is first.** FEAT-2026-0044
shipped `escalation.webhook: ""` into `.specfuse/agent-policy.yml` — a
**committed file**. An incoming-webhook URL is a bearer credential: anyone
holding it can post to the channel. `lint_monitoring`'s credential-key pattern
(`key|token|secret|password|credential|connection_string`) does **not** match
`webhook`, so nothing in this repo would stop an operator pasting a live Discord
URL into git.

So: the config holds a **name**, the environment holds the **value**.

**Copy the convention and the rationale from
`specfuse/loop/lint_monitoring.py`.** Read `_CREDENTIAL_KEY_RE`,
`_ENV_VAR_NAME_RE`, and `_check_credentials` before writing. `_ENV_VAR_NAME_RE`
is `^[A-Za-z_][A-Za-z0-9_]*$` and its comment explains precisely why it is a
structural shape check and not a secret detector — the same reasoning applies
here, and a URL trips it on `:`, `/`, and `.`.

**Rename, do not deprecate.** Accept `webhook_env` only. Nothing consumes
`webhook` yet — this WU is its first and only reader — so a compatibility
shim would be permanent cost for zero migration. Land the rename **and** the
example's migration in this same unit so no intermediate tree fails its own
gate (`[FEAT-2026-0069/G1]`: expand → migrate → contract is the only ordering
satisfiable under the preflight baseline probe).

**Provider is explicit, never sniffed.** Add `escalation.provider` with values
`discord` | `slack` | `teams` | `none` (default `none`). Sniffing the provider
from the URL would mean parsing a secret; the code should touch it as little as
possible.

**Fire-and-forget, never fatal.** A failed post logs and returns; it never
raises into the caller and never fails a gate. The GitHub issue is the system of
record — a notifier that can break the escalation path inverts the reliability
ordering.

**Redact before anything leaves the process.** Apply
`specfuse.monitor.redaction.redact_text` to every body-derived string in a
payload. An outbound channel is the one place a leak is irreversible.

**Load-bearing strings fixed here and quoted verbatim by T02, T03, T04:**

- module: `specfuse/loop/notify.py`
- entry point: `post_notification(message, *, policy_path=None, poster=None) -> bool`
- URL resolver: `resolve_webhook_url(policy_path=None) -> str | None`
- config keys: `escalation.webhook_env`, `escalation.provider`,
  `escalation.quiet_hours`, `escalation.sla_hours`
- provider values: `discord`, `slack`, `teams`, `none`

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_notify.py::TestPostNotification::test_no_webhook_configured_is_noop`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/notify.py` defines
   `post_notification(message, *, policy_path=None, poster=None) -> bool`,
   returning `False` (no-op, no error) when no webhook is configured.
3. `resolve_webhook_url(policy_path=None) -> str | None` reads the env-var
   *name* from `escalation.webhook_env` and returns `os.environ`'s value for it,
   or `None` when the key is empty, absent, or the variable is unset. A test
   covers all four.
4. **The resolved URL never leaves the process except as the POST target.** A
   test asserts it appears in no return value, no exception message, and no
   logged string — construct a fake poster, raise inside it, and assert the URL
   is absent from the captured log and the raised text.
5. Three pure adapter functions exist, one per provider, each mapping a neutral
   message to that provider's JSON payload. A test asserts each produces the
   documented envelope shape and that an unknown provider yields no payload and
   no post.
6. `redact_text` from `specfuse.monitor.redaction` is applied to every
   body-derived string before it enters a payload. A test passes a message
   containing a redactable token and asserts it is absent from the payload.
7. **Never fatal:** a poster that raises, times out, or returns a non-2xx
   status causes `post_notification` to return `False` without propagating. A
   test covers all three.
8. Quiet hours suppress the post and nothing else: with `quiet_hours` covering
   the passed-in time, `post_notification` returns `False` and no poster call is
   made. A test asserts the caller is unaffected.
9. `escalation.webhook` is **renamed** to `escalation.webhook_env` in
   `specfuse/loop/agent_policy.py`'s schema, and `webhook` is rejected as an
   unknown key. A test asserts the old spelling produces an `ERROR: ` finding.
10. `validate_agent_policy` emits an `ERROR: ` finding when `webhook_env`'s
    value is not env-var-name-shaped, using the `_ENV_VAR_NAME_RE` shape. A test
    asserts a pasted `https://` URL is rejected and that
    `SPECFUSE_NOTIFY_WEBHOOK` and `""` are both accepted.
11. `escalation.provider` is validated against the four permitted values; an
    unknown value is an `ERROR: ` finding.
12. `.specfuse/agent-policy.yml.example` and this repo's live
    `.specfuse/agent-policy.yml` are both migrated to `webhook_env` in **this**
    WU, both keep an **empty** value, and both validate clean.
13. `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml`
    exits zero, and the `agent-policy-example-lint` gate passes.
14. No test performs a real HTTP request — every poster is injected. A test
    asserts the module makes no network call under the default no-op path.
15. `python3 -m unittest tests.test_notify -v` exits zero after this WU's edits.
16. `python3 -c "from specfuse.loop.notify import post_notification, resolve_webhook_url"`
    exits zero.

**Do not touch.** `specfuse/loop/escalation.py` — T02 wires the call; this WU
ships the notifier only. `specfuse/monitor/redaction.py` — import and call, do
not modify. `specfuse/loop/lint_monitoring.py` — read for the convention, do not
edit or import. Any real webhook URL — this repo ships none and must not gain
one. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 15, the live-policy lint in 13,
and the symbol check in 16.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`specfuse/loop/agent_policy.py` does not exist or does not carry
`escalation.webhook` (meaning FEAT-2026-0044 did not land, or landed a
different schema — report the actual shape, do not adapt silently); or the
rename cannot be landed together with the example migration without an
intermediate red tree. **Never** commit a real webhook URL to satisfy a test.
If `specfuse/loop/notify.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
