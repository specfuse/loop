---
id: FEAT-2026-0047/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - specfuse/loop/notify_sla.py
  - tests/test_notify_sla.py
produces_driver_helper: sla_sweep, PARKED_LABEL
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T07:56:01.777855+00:00
duration_seconds: 1482.221
cost_usd: 2.469086
input_tokens: 5667
output_tokens: 27647
---

# Re-ping an unanswered escalation exactly once, then park it

**Objective.** Create `specfuse/loop/notify_sla.py` exposing `sla_sweep(...)`:
find open needs-human issues past the SLA window, re-ping each **once**, and
park anything already re-pinged so the queue continues.

**Context.** Correlation ID `FEAT-2026-0047/T03`. Depends on
`FEAT-2026-0047/T02`.

**Exactly once is the whole rule.** Unbounded re-pinging trains the operator to
mute the channel, and a muted channel is worse than no channel — the feature
would then be actively harmful rather than merely absent. The roadmap row's
wording is the contract: *"unanswered escalation past the configured window
re-pings once, then the item is parked and the queue continues."*

**The re-ping count must live where the work lives, not on disk.** Per
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]`: the
runner is a GitHub Actions container today and an AKS CronJob tomorrow, so a
disk-backed "already re-pinged" flag disappears silently and every sweep
re-pings every issue forever, while code review sees a rate limiter. Store the
state as an HTML-comment marker on the issue and re-derive it on every read —
the same shape `monitor/autofix_state.py` and `monitor/issues.py` already use.

**Marker convention**, fixed here: `<!-- specfuse:sla-repinged at={at} -->`,
written as an issue comment. Follows the existing `<!-- specfuse:… -->` prefix
family.

**Parked is a label, not a close.** A parked escalation stays **open** — it is
still awaiting a human, and closing it would destroy the queue it represents.
`PARKED_LABEL = "escalation-parked"` is added alongside the existing
`needs-human` label, never replacing it.

**Load-bearing strings from T01/T02, quoted verbatim:** `post_notification`;
`escalation.sla_hours`; `NEEDS_HUMAN_LABEL` imported from
`specfuse.loop.escalation`.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_notify_sla.py::TestSlaSweep::test_repings_once_then_parks`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/notify_sla.py` defines
   `sla_sweep(runner, repo, *, now, policy_path=None, poster=None) -> list`,
   returning one record per issue acted on. `now` is injected — the module calls
   no clock directly, so the test is deterministic.
3. `PARKED_LABEL = "escalation-parked"` is a module-level constant, and
   `NEEDS_HUMAN_LABEL` is **imported** from `specfuse.loop.escalation` (identity
   check in a test), never retyped.
4. An issue younger than `escalation.sla_hours` is untouched: no post, no
   marker, no label. A test covers the boundary at exactly the window.
5. An issue past the window with **no** re-ping marker is re-pinged once: one
   post, one `<!-- specfuse:sla-repinged at={at} -->` comment. A test asserts
   exactly one of each.
6. An issue past the window that **already** carries the marker is parked: the
   `escalation-parked` label is added, and **no** second post is made. A test
   asserts the post count is zero on this path.
7. The re-ping count is re-derived from issue comments on every call, with no
   stored counter — a test asserts two successive sweeps over the same fixture
   produce the same decisions and no additional posts.
8. A parked issue stays **open** — a test asserts no close command reaches the
   runner on any path.
9. A malformed or unparseable marker is ignored rather than fatal, and does not
   cause a double re-ping. A test covers a garbage marker alongside a valid one.
10. With no webhook configured, the sweep still parks correctly and makes no
    poster call — the labeling is independent of the channel, so an operator
    without a webhook still gets a coherent queue.
11. Every GitHub access goes through the injected `runner`; a test exercises
    every path with a fake runner and no network.
12. `python3 -m unittest tests.test_notify_sla -v` exits zero after this WU's
    edits.
13. `python3 -c "from specfuse.loop.notify_sla import sla_sweep, PARKED_LABEL"`
    exits zero.

**Do not touch.** `specfuse/loop/escalation.py` — import its constants, do not
edit it. `specfuse/loop/notify.py` and `notify_escalation.py` — T01 and T02 own
them. `monitor/autofix_state.py` — read it for the marker shape, do not import
it (different artifacts, different counts). Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 12 and the symbol check in 13.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
issue creation timestamps are not reliably readable through the runner, so "past
the window" cannot be decided mechanically (guessing here would re-ping
correct-state issues); or the `escalation-parked` label collides with an
existing label in the repo's registry. If `specfuse/loop/notify_sla.py` is
absent from the files you edited, emit `status: blocked` — do not claim
complete.
