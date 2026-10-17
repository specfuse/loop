# Retrospective — FEAT-2026-0204 gate 1 close

## Measurements

All commands below were run fresh in this session from the repository root, exit
codes read directly. HEAD was `3a5deb0b8dc3e1be3c40008da17b0a8586a7c1bd` with this
close's own working-tree edits (`docs/concepts/monitoring-runners.md`,
`CHANGELOG.md`, this file, `FOLLOW-UPS.md`, `LEARNINGS-pending.md`,
`GATE-01-CRITERIA.md`) uncommitted. This session may not run git, so the tree
state is HEAD plus those edits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end tests.test_monitor_finding_context_end_to_end -v -b`
(exit 0): `Ran 27 tests in 0.016s` / `OK`, with every class below running (none skipped):

```
ClosedFindingReopens      4 tests    DlqAcknowledgement   4 tests    HeartbeatGrace    1 test
EveryFinding              5 tests    ErrorLogsContext     3 tests    Http5xxContext    4 tests
DlqContext                2 tests    HeartbeatContext     3 tests    QueueStalledContext 1 test
```

### No surviving skip

`grep -n 'unittest.skip' tests/test_monitor_finding_context_end_to_end.py tests/test_monitor_finding_lifecycle_end_to_end.py`
reports nothing (exit 1, no output). No oracle class is hollow.

### Nothing in the monitor closes an issue

`grep -rn '"issue", "close"\|issue close' specfuse/monitor` reports nothing (exit 1).
The `specfuse/monitor/issues.py` docstring now reads "This module never closes an
issue … It does reopen one", the sentence T01 rewrote.

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate, and this session was told
not to run it. The driver's recorded results in `events.jsonl`:

- 2026-10-17T16:03:12Z `broad_run_result` `ok: false`: `tests` failed with
  `FAILED (failures=1, skipped=4)`, the failure
  `test_monitor_cli.TestAllCheckTypesDispatch.test_all_six_check_types_reach_their_adapter`;
  `coverage` followed (`no_gate_marker`, a consequence of the red `tests` run).
  Repaired in `ab4c8b1` ("give the dispatch test's heartbeat stub a history").
- 2026-10-17T16:17:35Z `broad_run_result` `ok: true`, `failing: []`, on the tree
  recorded in `GATE-01.md`'s `broad_run:` block.

### Per-criterion oracles (30 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 30

Each criterion's oracle was re-run this attempt; per-entry command, `kind` and
`state` are in `GATE-01-CRITERIA.md`. All 30 exit 0: T01#1–#3, #5; T02#1–#4;
T03#1–#4; T04#1–#5; T05#1–#3; T06#1–#3; T07#1–#3; T08#1–#3, plus the two grep
criteria T01#4 and T08#3 (a "reports nothing" criterion is satisfied by `grep`
exit 1, so those two oracles are written `! grep …`).

Two substitutions, stated rather than hidden:

- **T02#4** names the reopen comment and the body as ISO-8601 UTC with `first_seen`
  unchanged. Its oracle is the whole `tests.test_monitor_finding_meta` module (11
  tests), which holds `test_update_keeps_first_seen` and
  `test_reopen_keeps_first_seen_and_comments_iso`; no narrower node covers both
  halves.
- **T07#3** is two checks joined: `tests.test_service_bus_dlq_adapter` (exit 0) and
  `grep -nE "\.(receive_messages|complete_message|abandon_message|dead_letter_message|defer_message)\(" specfuse/monitor/providers/azure_service_bus.py`
  reporting nothing. The module's only receiver calls are `get_subscription_receiver`
  and `peek_messages`.

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
| 4. a target preceding the earliest heartbeat is not silent; a missed firing after emission still is | `HeartbeatGrace.test_target_before_first_heartbeat_is_not_silent`; `test_heartbeat_adapter.TestHeartbeatGrace` (3 tests) | proven |
| 5. an unreadable finding-meta reads as absent, never raises | `test_monitor_finding_meta.TestFailClosed`, `TestCycleSurvivesMalformedMeta` | proven |
| 6. readable title, `component:`/`check:` labels, run summary, no fingerprint change | `EveryFinding.test_readable_title_labels_and_run_summary`, `test_each_label_is_created_once_before_first_use`, `test_fingerprint_unchanged_by_context` | proven |
| 7. each check's finding carries the sections `PLAN.md` names, one query each, schema-clean, redacted | the five context classes, `test_secret_in_context_value_is_redacted_in_body` | **not proven**: two sections the plan names are not rendered (below) |

### Sections a rendered fixture finding carries, against `PLAN.md` "Diagnostic context"

Every finding also carries a readable title, the two labels, `Occurrences`, `First
seen`, `Last seen`, `Seen this run` (count, first, last, UTC) and `Instances`
(`EveryFinding`); the Reproduce text is a section of the checks that name it below.

| check | plan names | a fixture finding carries | missing |
| --- | --- | --- | --- |
| `error-logs` | top in-app frame; request with route and result code; logger category and template; client-abort flag; 2–3 sample ids | Where, Request, Logger, Likely client abort, Samples, Reproduce | none |
| `http-5xx` | correlated exception (type, message, top frame); failing or slowest dependency; duration; samples | Exception, Where, Dependency, Duration, Samples, Reproduce | none |
| `dlq` | message id, sequence number, subject, enqueued time, delivery count; reason/description, or `Exception.Message`/`StackTrace` when blank; body shape only; peek command | Message (all five fields), Dead-letter or Exception, Body shape, Peek it | none |
| `heartbeat` | cron and timezone; last execution and result; **the component's earliest heartbeat**; whether the role sent telemetry in the gap | Schedule (cron, dialect, timezone, expected firing), Last run, Host last seen, Host silent | **earliest heartbeat** |
| `queue-stalled` | oldest active message age; **the subscription's last completed message**; depth | Queue (oldest active message age, depth, `stall_after`), Where | **last completed message** |

Neither missing section is recorded as deliberately dropped by any unit or by
`PLAN.md`. `WU-08`'s Objective and criteria name Schedule, Last run, Host last seen,
Host silent and the oldest age, and name neither of these two. The earliest
heartbeat is computed (`first_heartbeat`, `azure_app_insights.py:748`) and used for
the grace test, then not put in `context`. The last completed message would need a
new broker read the `QueueStalled` transport protocol does not have. The close's
escalation trigger applies, so the verdict is `not_met` and `FOLLOW-UPS.md` carries
both.

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
| G1-CLOSE | 5.00 | not recorded | 1 in progress | — |

`PLAN.md` plans 23.50 across all nine units; the eight implementation units spent
$3.84 of their $18.50 (21%), every unit between 15% and 30% of its plan. The
close's own cost is not in `events.jsonl` while it is running (its
`attempt_outcome` is written when the driver ends the attempt), so it is not
reconciled here. `GATE-01.md` sets `cost_budget_usd: 36.00`; recorded spend is
$3.84. The `ab4c8b1` repair of the dispatch test was made outside a work unit and
has no event.

### Failure-class breakdown

One off-plan event, class `tests`: the 16:03Z broad run. T04 made a silent
schedule need an earlier heartbeat to evaluate; `tests/test_monitor_cli.py`'s
`TestAllCheckTypesDispatch` stubbed the heartbeat transport with rows lacking one,
and T04's `produces:` and verification did not name that file (only T01's verification ran `tests.test_monitor_cli`), so T04's narrow tier never ran it.
The `coverage` failure was its shadow.

## Deferred verification

1. **The live run on the first consumer's backend** (`PLAN.md` Post-merge
   checklist). Every in-loop oracle runs over stub transports and a stub `gh`. After
   release, `specfuse monitor run` on the consumer's backend must show: a closed
   finding that recurs is reopened, not refiled; the four weekly schedules read
   "pending first firing" until their first heartbeat; a sample of finding bodies
   carries every section the Diagnostic context names for its check. Checked as the
   one `specfuse:post-merge` issue filed at close.
2. **The real `AppDependencies`/`AppRequests` joins and `arg_max` reductions.** The
   KQL passes the checked-in workspace schema reference
   (`tests.test_app_insights_query_schema_check`) and the query's shape is asserted
   (`test_query_reduces_joined_tables_to_one_row_per_operation`), but nothing in the
   loop executes it against a workspace. Where checked: the same live run, item 1.
3. **The real Service Bus peek and runtime properties.** `dlq` and `queue-stalled`
   context is built from stub messages shaped like Backend#1016 (including
   `bytes`-keyed application properties); the SDK's actual object shapes are not
   exercised. Where checked: the live run, on a subscription with a dead-lettered
   message.
4. **`gh issue reopen` and `gh label create --force` against GitHub.** The stub
   `gh` records argv; whether GitHub accepts it and a reopened issue keeps its
   diagnosis comment is not observed. Where checked: the live run's first recurrence.
5. **The 90-day listing bound under real volume.** `test_listing_is_bounded` proves
   the bound is derived from `now`; whether a busy repository stays under the
   100-row `TruncatedListingError` is not. Where checked: the live run's issue list.
6. **The two missing sections.** Not verified because not built: `FOLLOW-UPS.md`
   entries 1 and 2. Re-run condition stated there.

## Consumer-visible contract changes

Enumerated across T01–T08 for acknowledgment; each is also in `CHANGELOG.md`
`Unreleased` (`Added` ×1, `Changed` ×1, `Fixed` ×2, all FEAT-2026-0204).

- **Changed — a recurring closed finding is reopened, not refiled.** An issue
  closed within 90 days is reopened with one comment (count, first/last seen UTC);
  older closes file a new issue. The monitor reopens and never closes; the
  `issues.py` boundary sentence moved from "never reopens" to "never closes".
- **Changed — `dlq` closing now means "acknowledged".** A closed `dlq` issue whose
  recorded message ids cover the queue stays closed with no write; an unrecorded id
  reopens it naming that message. The finding-meta marker gains `first_seen` and
  `messages` fields (a marker written by an earlier version still parses).
- **Changed — issue titles and labels.** The fingerprint-bearing `[monitor:` prefix leaves
  the title (now `<component>: <failure class> in <where>`); issues carry
  `component:<name>` and `check:<type>` labels, created on first use. A consumer
  filtering on the old title prefix must filter on the marker or the labels. No
  fingerprint changed, so nothing is refiled.
- **Added — per-check diagnostic context** in the issue body, as the table above
  lists, with a Reproduce query and Peek it command that are text only.
- **Fixed — a schedule not yet emitting no longer files `silent-schedule`.**
- **Fixed — a malformed finding-meta value no longer aborts a run.**

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## Retrospective

**What went well.** The walking skeleton did its job: both oracle modules existed
before any unit, every later class was a skip naming its owner, and each owner
removed exactly its own, so no unit failed on a missing module and the final tree
has no hollow class. The fail-closed discipline held: T02's `TestFailClosed` calls
the reader directly. Fingerprint independence was tested in three places (message
id, `context`, `observed_at`) and nothing refiled. All eight units passed on attempt
1 at 21% of plan.

**What didn't.** The plan's "Diagnostic context" is an enumerated list that the
feature's own goal ("gather as much information as possible") rests on, and two of
its items never reached a unit: T08's body restated the heartbeat and queue-stalled
requirements from memory, not from the list, so its criteria were all met while the
plan's list was not. The oracle asserts what the unit criteria name, so it could not
see the gap; only this close's per-check comparison did. The broad run also caught
a dispatch test that T04's behaviour change broke and no unit's `produces:` covered.

**Open follow-ups (not blockers to the merge of what is built).** The two missing
sections; the live run; and the Service Bus context shapes in deferred item 3.
