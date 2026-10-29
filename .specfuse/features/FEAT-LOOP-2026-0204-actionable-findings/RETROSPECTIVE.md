# Retrospective — FEAT-LOOP-2026-0204 gate 1 close

This is the second close of gate 1. The first (2026-10-17 16:21Z) judged `not_met`
on two missing diagnostic sections and filed #3504 and #3505; commit `d9667f9`
discharged both and fixed three defects found by rendering real findings against
the first consumer's workspace, then re-armed the close. Everything below was
re-measured this session.

## Measurements

All commands were run fresh in this session from the repository root, exit codes
read directly. HEAD was `3b002bcd28928c16a40b1819a715e3f046837f10` with this close's
own working-tree edits (`CHANGELOG.md`, `docs/concepts/monitoring-runners.md`, this
file, `LEARNINGS-pending.md`, `GATE-01-CRITERIA.md`, the `verdict` field of
`WU-90-gate-1-close.md`) uncommitted. This session may not run git, so the tree
state is HEAD plus those edits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end tests.test_monitor_finding_context_end_to_end -v -b`
(exit 0): `Ran 29 tests` / `OK`, every class running, none skipped:

```
ClosedFindingReopens   4    DlqAcknowledgement          4    HeartbeatGrace             1
EveryFinding           5    ErrorLogsContext            3    Http5xxContext             4
DlqContext             2    HeartbeatContext            3    QueueStalledContext        1
DlqExceptionPrefersAppFrames 1    DlqFirstSeenIsTheEnqueuedTime 1
```

(The last two classes are the oracle's additions in `d9667f9`; the first close ran 27.)

### No surviving skip

`grep -n 'unittest.skip' tests/test_monitor_finding_context_end_to_end.py tests/test_monitor_finding_lifecycle_end_to_end.py`
reports nothing (exit 1, no output). No oracle class is hollow.

### Nothing in the monitor closes an issue

`grep -rn '"issue", "close"\|issue close' specfuse/monitor` reports nothing (exit 1).
The `specfuse/monitor/issues.py` docstring reads "This module never closes an
issue … It does reopen one", the sentence T01 rewrote.

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate. Its recorded results in
`events.jsonl`:

- 16:03:12Z `ok: false`: `tests` failed with `test_monitor_cli.TestAllCheckTypesDispatch`
  (a heartbeat stub with no history, after T04); `coverage` followed (`no_gate_marker`).
  Repaired in `ab4c8b1`.
- 16:17:35Z `ok: true`.
- 16:33:37Z `ok: false`, `tests` failed with
  `test_lint_closing_criteria.TestCorpusSweepStaysClean.test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings`:
  that test lints every feature in the repo, and at that moment this feature's
  close had just been re-armed, so it reported `close-b`/`close-c`/`close-d`/`close-l`
  for the in-flight close. Same tree hash as the next run; no code was changed
  between them. `coverage` followed.
- 16:43:32Z `ok: true`, `failing: []`, on the tree recorded in `GATE-01.md`'s
  `broad_run:` block. `Ran 4627 tests`, `OK (skipped=4)`.

### Per-criterion oracles (30 criteria, `GATE-01-CRITERIA.md`)

carried forward: 29 criteria, re-measured: 1

29 criteria (T01#1–#4, T02#1–#4, T03#1–#4, T04#1–#5, T05#1–#3, T06#1–#3,
T07#1–#3, T08#1–#3) were carried forward from attempt 1, proved at
`3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd`. Their modules are unchanged in intent;
as a cross-check this session also ran `tests.test_app_insights_query_schema_check`,
`tests.test_heartbeat_adapter`, `tests.test_service_bus_dlq_adapter` and
`tests.test_monitor_finding_meta` together (exit 0, `Ran 41 tests`, `OK (skipped=1)`).

Re-measured: **T01#5**, the `feature_oracle` above, exit 0; its `proved_at_sha` in
`GATE-01-CRITERIA.md` is now `3b002bcd28928c16a40b1819a715e3f046837f10`.

### One query per check

Each context class asserts `len(transport.queries) == 1` after the cycle
(`ErrorLogsContext.test_sections_present`, `Http5xxContext.test_sections_present`,
`HeartbeatContext.test_sections_present`) and every query passes
`schema_violations` (`test_query_has_no_schema_violations` for `error-logs` and
`http-5xx`, `HeartbeatContext.test_query_is_one_bounded_schema_clean_query`). The
`dlq` and `queue-stalled` checks read the broker, not a query.

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. closed → one reopen + one comment, no create; open updates; new files one | `ClosedFindingReopens` (4 tests), incl. `test_closed_issue_is_reopened_not_refiled`; T02's `test_reopen_keeps_first_seen_and_comments_iso` for count and UTC | proven |
| 2. nothing closes an issue | the `grep` above, exit 1 | proven |
| 3. closed `dlq` with covered ids stays closed; a new id reopens naming it | `DlqAcknowledgement.test_closed_dlq_with_covered_ids_stays_closed`, `test_unseen_message_id_reopens_naming_it`; `test_fingerprint_ignores_message_id` | proven |
| 4. a target preceding the earliest heartbeat is not silent; a missed firing after emission still is | `HeartbeatGrace.test_target_before_first_heartbeat_is_not_silent`; `test_heartbeat_adapter.TestHeartbeatGrace` | proven |
| 5. an unreadable finding-meta reads as absent, never raises | `test_monitor_finding_meta.TestFailClosed`, `TestCycleSurvivesMalformedMeta` | proven |
| 6. readable title, `component:`/`check:` labels, run summary, no fingerprint change | `EveryFinding.test_readable_title_labels_and_run_summary`, `test_each_label_is_created_once_before_first_use`, `test_fingerprint_unchanged_by_context` | proven |
| 7. each check's finding carries the sections `PLAN.md` names, one query each, schema-clean, redacted | the five context classes; `test_secret_in_context_value_is_redacted_in_body`; the table below | proven |

### Sections a rendered fixture finding carries, against `PLAN.md` "Diagnostic context"

Every finding also carries a readable title, the two labels, `Occurrences`, `First
seen`, `Last updated`, `Seen this run` (count, first, last, UTC) and `Instances`
(`EveryFinding`).

| check | plan names | a fixture finding carries | missing |
| --- | --- | --- | --- |
| `error-logs` | top in-app frame; request with route and result code; logger category and template; client-abort flag; 2–3 sample ids; reproduction KQL | Where, Request, Logger, Likely client abort, Samples, Reproduce | none |
| `http-5xx` | correlated exception (type, message, top frame); failing or slowest dependency; duration; samples | Exception, Where, Dependency, Duration, Samples, Reproduce | none |
| `dlq` | message id, sequence number, subject, enqueued time, delivery count; reason/description, or `Exception.Message`/`StackTrace` when blank; body shape only; peek command | Message (all five fields), Dead-letter or Exception (app frames first, with a count of omitted framework frames), Body shape, Peek it | none |
| `heartbeat` | cron and timezone; last execution and result; the component's earliest heartbeat; whether the role sent telemetry in the gap | Schedule (cron, dialect, timezone, expected firing), Last run, Host last seen, Host silent, Earliest heartbeat | none |
| `queue-stalled` | oldest active message age, in addition to depth | Queue (oldest active message age, depth, `stall_after`), Where | none |

The first close found two gaps. Both are discharged and recorded: the earliest
heartbeat is now rendered (`context["Earliest heartbeat"]`,
`azure_app_insights.py:940`; `HeartbeatContext.test_sections_present` asserts
`**Earliest heartbeat:** 2026-10-10T00:00:00Z`), and `PLAN.md`'s "Diagnostic
context" is amended to drop the subscription's last completed message with its
reason (Service Bus runtime properties carry no completion time, and reading one
from messages would mean receiving them), which `docs/concepts/monitoring-runners.md`
repeats. So no check's finding lacks a section the plan names without a recorded
reason, and the escalation trigger does not apply.

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's
`planned_cost_usd`; no figure is estimated. Every unit passed on attempt 1.

| unit | planned (USD) | actual (USD) | attempts | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 2.50 | 0.4421 | 1 | 76 |
| T02 | 2.00 | 0.3172 | 1 | 70 |
| T03 | 2.50 | 0.5230 | 1 | 151 |
| T04 | 2.00 | 0.2941 | 1 | 78 |
| T05 | 3.00 | 0.9017 | 1 | 194 |
| T06 | 2.00 | 0.4272 | 1 | 72 |
| T07 | 2.00 | 0.3894 | 1 | 60 |
| T08 | 2.50 | 0.5448 | 1 | 116 |
| T01–T08 | 18.50 | 3.8395 | 8 | 817 |
| G1-CLOSE, first attempt (incl. judge fold) | 5.00 | 1.7830 | 1 | 246 |
| **recorded total** | 23.50 | **5.6225** | 9 | 1063 |

`PLAN.md` plans 23.50; the nine recorded attempts spent $5.62 (24%), and
`GATE-01.md` sets `cost_budget_usd: 36.00`. This close's own attempt is not in
`events.jsonl` while it runs (its `attempt_outcome` is written when the driver ends
the attempt), so it is not reconciled here and the total above excludes it. The
`ab4c8b1` and `d9667f9` repairs were made outside a work unit and have no event.

### Failure-class breakdown

Two off-plan events, both class `tests`, both at the broad run:

1. 16:03Z: T04 made a silent schedule need an earlier heartbeat to evaluate;
   `tests/test_monitor_cli.py`'s `TestAllCheckTypesDispatch` stubbed the heartbeat
   transport without one, and T04's `produces:` did not name that file, so its
   narrow tier never ran it. `coverage` failed as its shadow.
2. 16:33Z: a corpus sweep test linting the in-flight, just-re-armed close. Same tree
   as the passing 16:43Z run; a re-arm-timing artifact, not a code defect.

## Deferred verification

1. **The live run on the first consumer's backend** (`PLAN.md` Post-merge
   checklist). Every in-loop oracle runs over stub transports and a stub `gh`. After
   release, `specfuse monitor run` on the consumer's backend must show: a closed
   finding that recurs is reopened, not refiled; the four weekly schedules read
   "pending first firing" until their first heartbeat; a sample of finding bodies
   carries every section the Diagnostic context names for its check. Checked as the
   one `specfuse:post-merge` issue filed at close.
2. **The `AppDependencies`/`AppRequests` joins and `arg_max` reductions at
   production volume.** The KQL passes the checked-in workspace schema reference
   and its shape is asserted, and `d9667f9`'s opt-in live render showed both
   queries resolve against the consumer's workspace, but that run was manual and
   outside the loop and nothing in the loop executes the query. Where checked: the
   live run, item 1.
3. **The real Service Bus peek and runtime properties.** `dlq` and `queue-stalled`
   context is built from stub messages shaped like Backend#1016 (including
   `bytes`-keyed application properties); the SDK's actual object shapes are not
   exercised in-loop. Where checked: the live run, on a subscription with a
   dead-lettered message.
4. **`gh issue reopen` and `gh label create --force` against GitHub.** The stub
   `gh` records argv; whether GitHub accepts it and a reopened issue keeps its
   diagnosis comment is not observed. Where checked: the live run's first recurrence.
5. **The 90-day listing bound under real volume.** `test_listing_is_bounded` proves
   the bound is derived from `now`; whether a busy repository stays under the
   100-row `TruncatedListingError` is not. Where checked: the live run's issue list.

## Consumer-visible contract changes

Enumerated across T01–T08 and `d9667f9` for acknowledgment; each is also in
`CHANGELOG.md` `Unreleased` (`Added` ×1, `Changed` ×1, `Fixed` ×2, all FEAT-LOOP-2026-0204).

- **Changed — a recurring closed finding is reopened, not refiled.** An issue
  closed within 90 days is reopened with one comment (count, first/last seen UTC);
  older closes file a new issue. The monitor reopens and never closes; the
  `issues.py` boundary sentence moved from "never reopens" to "never closes".
- **Changed — `dlq` closing now means "acknowledged".** A closed `dlq` issue whose
  recorded message ids cover the queue stays closed with no write; an unrecorded id
  reopens it naming that message. The finding-meta marker gains `first_seen` and
  `messages` fields (a marker written by an earlier version still parses).
- **Changed — issue titles, labels and the body's time lines.** The fingerprint-bearing
  `[monitor:` prefix leaves the title (now `<component>: <failure class> in <where>`);
  issues carry `component:<name>` and `check:<type>` labels, created on first use. A
  consumer filtering on the old title prefix must filter on the marker or the
  labels. The body's `**Last seen:**` line is now `**Last updated:**`, and `First
  seen` is the earliest occurrence the run's rows show rather than the harvest time.
  No fingerprint changed, so nothing is refiled.
- **Added — per-check diagnostic context** in the issue body, as the table above
  lists, with a Reproduce query and Peek it command that are text only.
- **Fixed — a schedule not yet emitting no longer files `silent-schedule`.**
- **Fixed — a malformed finding-meta value no longer aborts a run.**

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## Documentation pass

`docs/concepts/monitoring-to-fix.md` does not exist at this tree, so the pass
updated `docs/concepts/monitoring-runners.md`, as the unit allows. Its "What a
finding is, and how its issue is kept" section describes reopen-not-refile with the
"reopens, never closes" boundary, `dlq` acknowledgement, heartbeat grace, and a
per-check "What a finding contains" table. This session corrected one sentence
(first seen / last updated) to match `d9667f9`. That file is not in
`tests/test_scaffold_data_in_sync.py`'s docs manifest and has no copy under
`specfuse/loop/data/docs/`, so there is no shipped copy to keep byte-identical;
`tests.test_scaffold_data_in_sync` passes. `CHANGELOG.md`'s Unreleased section had
a stale sentence saying the earliest heartbeat and last completed message were not
shown; it now states what is shown and why the last completed message is not, and
`tests.test_changelog_schema`, `test_changelog_append_only` and
`test_changelog_collection` pass.

## Retrospective

**What went well.** The walking skeleton did its job: both oracle modules existed
before any unit, every later class was a skip naming its owner, and each owner
removed exactly its own, so no unit failed on a missing module and the final tree
has no hollow class. The fail-closed discipline held: T02's `TestFailClosed` calls
the reader directly. Fingerprint independence was tested in three places (message
id, `context`, `observed_at`) and nothing refiled. All eight units passed on attempt
1 at 21% of plan. The not-met verdict did its job too: the first close's per-check
table caught two missing sections the oracle could not see, and each was resolved
with a test or a recorded reason rather than a hedge.

**What didn't.** The plan's "Diagnostic context" is an enumerated list that the
feature's own goal rests on, and two of its items never reached a unit: T08's body
restated the heartbeat and queue-stalled requirements from memory, not from the
list. The oracle asserts what the unit criteria name, so only the close's
comparison saw the gap. Separately, no in-loop test could see that two queries did
not parse in the real workspace, that "First seen" was the harvest time, or that a
`dlq` exception's handler frame was cut off; all three surfaced only when real
findings were rendered by hand after the first close. The broad run also caught a
dispatch test T04's behaviour change broke and no unit's `produces:` covered.

**Open follow-ups (not blockers).** The live run and the Service Bus context
shapes in Deferred verification. `FOLLOW-UPS.md` (#3504, #3505) is the first
close's record and is discharged by `d9667f9`; the driver owns that file and it is
left as written.
