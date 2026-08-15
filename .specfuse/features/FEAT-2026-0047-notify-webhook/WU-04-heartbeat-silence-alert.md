---
id: FEAT-2026-0047/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/loop/heartbeat.py
  - tests/test_heartbeat.py
  - plugins/specfuse/skills/attention/SKILL.md
produces_driver_helper: last_run_at, silence_check
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T08:25:52.471724+00:00
duration_seconds: 763.263
cost_usd: 1.268404
input_tokens: 71
output_tokens: 12587
---

# Alarm the silence — derive the last run from repo state and flag staleness

**Objective.** Create `specfuse/loop/heartbeat.py` deriving the agent's last-run
timestamp from repo state, exposing `silence_check(...)` that flags "no run in
M hours" and fires the same webhook, and surface the result in `/attention`.

**Context.** Correlation ID `FEAT-2026-0047/T04`. Depends on
`FEAT-2026-0047/T01` for the notifier. Independent of T02 and T03.

**A silent agent is indistinguishable from an idle one, and that is the bug.**
An agent that stalls, dies, or was never scheduled produces exactly the same
observable as an agent with nothing to do: nothing. This unit makes the
difference visible.

**Derive the timestamp; never store it.** The newest event across
`.specfuse/features/*/events.jsonl` **is** the last-run time. Per
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]`, a
written heartbeat file on an ephemeral runner is decorative — and here it would
also be redundant, because the events log already answers the question exactly.
A derived answer cannot drift from the thing it describes.

**Two surfaces, one function.** `silence_check` returns a verdict; what the
caller does with it differs:

- `/attention` calls it on open and prints the staleness line among its existing
  sections — no webhook, because a human is already looking.
- A scheduled invocation (FEAT-2026-0049's concern, not this WU's) calls it and
  posts through `post_notification` when stale.

**Do not add a scheduler.** This WU ships the check and the two call sites'
shapes. Nothing here decides when it runs.

**Skills are canonical in `plugins/specfuse/skills/`.** Edit
`plugins/specfuse/skills/attention/SKILL.md`, then run
`scripts/sync-scaffold.sh` to vendor into `.specfuse/skills/`.
`tests/test_skills_vendored_in_sync.py` fails if you edit only one copy.

**Load-bearing strings from T01, quoted verbatim:** `post_notification`;
`escalation.webhook_env`. New in this WU: `escalation.silence_hours` (int > 0,
default `24`), validated by `validate_agent_policy` the same way the other
`escalation.*` integers are.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_heartbeat.py::TestSilenceCheck::test_stale_when_no_events_within_window`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/heartbeat.py` defines
   `last_run_at(repo_root=None) -> float | None`, returning the newest event
   timestamp across `.specfuse/features/*/events.jsonl`, or `None` when there
   are no events at all.
3. `silence_check(*, now, repo_root=None, policy_path=None) -> dict` returns a
   verdict carrying at least `stale: bool`, `last_run_at`, and `hours_since`.
   `now` is injected — the module calls no clock directly.
4. A repo with a recent event is **not** stale; one whose newest event predates
   `escalation.silence_hours` **is**. A test covers the boundary at exactly the
   window.
5. **No events at all is reported distinctly**, not as stale-with-`hours_since:
   0` and not as healthy: a fresh repo that has never run is a different state
   from an agent that stopped, and conflating them either cries wolf on day one
   or hides a real death. A test asserts the distinct verdict.
6. A malformed or unparseable line in `events.jsonl` is skipped, not fatal, and
   does not make the repo look silent. A test covers a garbage line among valid
   ones.
7. `escalation.silence_hours` is added to the schema, defaults to `24`, and is
   validated as `int > 0` with an `ERROR: ` finding otherwise. The shipped
   example and this repo's live policy both carry it and validate clean.
8. `silence_check` performs **no** post itself — posting is the caller's choice.
   A test asserts no poster call is made from within it.
9. `plugins/specfuse/skills/attention/SKILL.md` gains a section instructing the
   skill to call `specfuse.loop.heartbeat.silence_check` on open and print the
   staleness line, explicitly **without** firing the webhook because a human is
   already reading. A test asserts the skill body names
   `specfuse.loop.heartbeat.silence_check` as an exact-match literal.
10. `scripts/sync-scaffold.sh` has been run and
    `.specfuse/skills/attention/SKILL.md` is byte-identical to the canonical
    copy — `python3 -m unittest tests.test_skills_vendored_in_sync -v` exits
    zero.
11. Reading `events.jsonl` is read-only: a test asserts no file under
    `.specfuse/features/` is written by any function in this module.
12. `python3 -m unittest tests.test_heartbeat -v` exits zero after this WU's
    edits.
13. `python3 -c "from specfuse.loop.heartbeat import last_run_at, silence_check"`
    exits zero.

**Do not touch.** Any `events.jsonl` — this module reads them and must never
write one; the driver owns that log. `specfuse/loop/notify.py` — T01 owns it.
`specfuse/loop/notify_sla.py` — T03 owns it. `.specfuse/skills/attention/`
directly — edit the canonical `plugins/` copy and let the sync script vendor it.
No scheduler, cron file, or workflow — FEAT-2026-0049 owns invocation.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 12, the sync check in 10, and
the symbol check in 13.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`events.jsonl` entries do not carry a parseable timestamp field usable for
"newest event" (report the actual envelope rather than inventing a second time
source); or `plugins/specfuse/skills/attention/SKILL.md` does not exist, meaning
FEAT-2026-0046 landed a different layout. If `specfuse/loop/heartbeat.py` is
absent from the files you edited, emit `status: blocked` — do not claim
complete.
