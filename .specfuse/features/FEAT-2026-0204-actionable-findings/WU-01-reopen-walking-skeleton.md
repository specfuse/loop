---
id: FEAT-2026-0204/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - tests/test_monitor_finding_lifecycle_end_to_end.py
  - tests/test_monitor_finding_context_end_to_end.py
  - specfuse/monitor/issues.py
---

# T01 — a recurring fingerprint reopens its closed issue

**Objective.** The gate's `feature_oracle` goes from red to green for clause 1: a
fingerprint whose finding issue is closed within the lookup window is reopened with
one comment, never refiled.

**Context.** `FEAT-2026-0204/T01`, gate 1. **This unit is the walking skeleton**
(`/authoring-work-units` §14) and the only unit in the gate permitted to stub. Write
the oracle module **first**: `GATE-01.md`'s `feature_oracle` is appended to every
attempt's gate list, so it must exist before anything else lands. The oracle is two
modules: `tests/test_monitor_finding_lifecycle_end_to_end.py` (one class per lifecycle
clause; `DlqAcknowledgement` and `HeartbeatGrace` start as
`unittest.skip("owned by FEAT-2026-0204/T03")` / `("…/T04")`) and
`tests/test_monitor_finding_context_end_to_end.py` (classes `EveryFinding`,
`ErrorLogsContext`, `Http5xxContext`, `DlqContext`, `HeartbeatContext`,
`QueueStalledContext`, each skipped with a reason naming its owner, T05–T08, and each
asserting real section names from `PLAN.md`'s "Diagnostic context" so the owning unit
only removes the skip and makes it pass).

Today `issues._list_findings` (`specfuse/monitor/issues.py`) lists
`--state open` only, so `find_finding_issue` returns `None` for a fingerprint whose
issue is closed and `record_finding` files a new one (#3496 point 1; Backend#1042,
#1044, #1045). Widen the listing to open issues plus issues **closed within the last
90 days** (PLAN.md decision 3) — `gh issue list --state all` with a `closed:>=`
date from the injected `now`, or two listings merged; pick whichever keeps the
existing client-side `marker in body` check as the sole authority and keeps
`TruncatedListingError`'s "a full page is not proof of absence" guarantee. Carry each
row's `state` so `record_finding` can branch: a closed match runs
`gh issue reopen <n>` then `gh issue comment <n>` with the new occurrence count and
first/last seen in UTC; an open match keeps today's edit-and-throttle path. Rewrite
the module docstring's scope boundary to "never closes" and say why reopening is
allowed (PLAN.md decision 1).

`find_finding_issue` has two other callers: `autofix_state.has_prior_attempt` and
`record_attempt` (`specfuse/monitor/autofix_state.py:97`, `:122`). After this unit
they see closed issues too. That is the intended reading for `has_prior_attempt` (an
attempt recorded on a closed issue is still an attempt, so a reopened regression is
not auto-fixed twice — #3487 owns whether it should be), and `record_attempt` only
ever runs on an issue the agent just read as open. Keep both behaving as on HEAD for
open issues, and prove it with their existing tests.

Stubbable here, and only here: the comment's exact wording, and first-seen (T02 owns
recording it — this unit may print last-seen only).

**Acceptance criteria.**

1. `tests/test_monitor_finding_lifecycle_end_to_end.py::ClosedFindingReopens::test_closed_issue_is_reopened_not_refiled`
   fails on HEAD (absent module) and passes after: `run_cycle(dry_run=False)` over a
   stub transport yielding one `error-logs` row and a stub `gh` whose listing returns
   a **closed** issue carrying that row's fingerprint marker issues exactly one
   `gh issue reopen`, exactly one `gh issue comment`, and no `gh issue create`.
2. `test_open_issue_still_updates` and `test_new_fingerprint_still_files`: the open
   and absent cases issue the same `gh` calls they do on HEAD.
3. `test_listing_is_bounded`: the listing argv carries the 90-day bound derived from
   the injected `now`, and a closed match older than the bound is not returned.
4. `grep -rn '"issue", "close"\|issue close' specfuse/monitor` reports nothing, and
   the `issues.py` docstring no longer says the module never reopens.
5. `GATE-01.md`'s `feature_oracle` exits 0 at this unit's tree (skipped classes
   allowed, each naming its owning unit, T03–T08).

**Do not touch.** `specfuse/monitor/autofix_state.py` and `specfuse/loop/triage.py`
(their own `--state open` listings serve different questions). The finding-meta
reader (T02). Adapters and queries (T03–T08).

**Verification.** The narrow tier for `implementation`, with `tests` narrowed to this
unit's test module plus
`python3 -m unittest tests.test_monitor_issue_lifecycle tests.test_monitor_cli tests.test_monitor_one_issue_per_fingerprint tests.test_autofix_state tests.test_autofix_run -b`.

**Escalation triggers.** If no single listing shape can both include recently closed
issues and keep the truncation guarantee without a second `gh` call per run, stop and
escalate with the measured options rather than dropping the guarantee. If reopening
needs a permission the default `gh` token lacks on a consumer repo, escalate.
