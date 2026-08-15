---
id: FEAT-2026-0047/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - specfuse/loop/notify_escalation.py
  - tests/test_notify_escalation.py
produces_driver_helper: notify_new_escalation
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T07:25:51.033742+00:00
duration_seconds: 616.604
cost_usd: 0.706789
input_tokens: 31
output_tokens: 7826
---

# Post a one-liner and a link when a needs-human issue is filed

**Objective.** Create `specfuse/loop/notify_escalation.py` exposing
`notify_new_escalation(...)`: when an escalation issue is filed, send a
one-liner and its link to the configured channel.

**Context.** Correlation ID `FEAT-2026-0047/T02`. Depends on
`FEAT-2026-0047/T01` for the notifier.

**Do not modify `escalation.py`.** FEAT-2026-0046 owns the escalation contract —
`emit_escalation`, `render_escalation_body`, `validate_escalation_body`, and the
idempotency guarantee that a second call for the same correlation ID returns the
existing issue rather than filing a duplicate. This WU adds a **separate,
callable notification step** that a caller invokes after `emit_escalation`
returns. Wrapping or patching `emit_escalation` would make the notifier able to
break escalation filing, which PLAN.md assumed decision 4 forbids.

**Import the constants; do not retype them:** `NEEDS_HUMAN_LABEL`,
`CATEGORY_LABELS`, and the correlation-marker template from
`specfuse.loop.escalation`. A second copy of the label string is drift waiting
to happen.

**The message is a one-liner and a link. Nothing else.** No issue body, no
option text, no diagnosis. The channel is a loudspeaker; the audit trail is the
issue. A message that reproduces the body invites people to answer in chat,
where the answer is lost — which is the exact failure this feature's
notify-only design avoids.

**Load-bearing strings from T01, quoted verbatim:** module
`specfuse/loop/notify.py`; entry point
`post_notification(message, *, policy_path=None, poster=None) -> bool`; config
keys `escalation.webhook_env`, `escalation.provider`.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_notify_escalation.py::TestNotifyNewEscalation::test_posts_one_liner_and_link`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/notify_escalation.py` defines
   `notify_new_escalation(correlation_id, *, repo, issue_number, category, summary, policy_path=None, poster=None) -> bool`.
3. The rendered message contains the issue link, the category, and a summary
   truncated to one line — and a test asserts it contains **no** newline beyond
   the link line, so an issue body cannot leak into chat by accident.
4. `NEEDS_HUMAN_LABEL` and `CATEGORY_LABELS` are **imported** from
   `specfuse.loop.escalation`; a test asserts the imported objects are the same
   ones (identity check), so a future edit there cannot leave this module
   behind.
5. An unknown category is rejected before posting, matching
   `render_escalation_body`'s own behavior, with no post made.
6. `specfuse/loop/escalation.py` is **unmodified** by this WU — `git diff
   --stat` shows no change to it, and `tests/test_escalation*.py` passes
   untouched.
7. With no webhook configured, `notify_new_escalation` returns `False`, makes no
   poster call, and does not raise — the default state of this repo.
8. A poster that raises causes `notify_new_escalation` to return `False` without
   propagating, so a failed notification can never prevent or undo an
   escalation.
9. Every payload passes through T01's redaction path — a test with a redactable
   token in the summary asserts it is absent from the posted message.
10. `python3 -m unittest tests.test_notify_escalation -v` exits zero after this
    WU's edits.
11. `python3 -c "from specfuse.loop.notify_escalation import notify_new_escalation"`
    exits zero.

**Do not touch.** `specfuse/loop/escalation.py` — criterion 6 makes this
checkable; if notification genuinely cannot be added without editing it, that is
an escalation, not a license. `specfuse/loop/notify.py` — T01 owns it; call it.
The re-ping and parking rules — T03 owns them; this WU posts once, on filing.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 10 and the symbol check in 11.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`escalation.py` does not expose the constants named in this WU's Context; or a
criterion here would require editing `escalation.py`. If
`specfuse/loop/notify_escalation.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
