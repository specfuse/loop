---
feature_id: FEAT-2026-0204
title: Monitor findings a diagnosis can start from
slug: actionable-findings
branch: feat/FEAT-2026-0204-actionable-findings
roadmap_goal: A filed monitoring finding is never refiled, never a false alarm from a schedule that has not emitted yet, and carries everything a diagnosis needs without re-querying the telemetry backend
autonomy_default: auto
status: active
planned_cost_usd: 23.50
---

# Plan: Monitor findings a diagnosis can start from

The first real `specfuse monitor run` against a consumer's production workspace
(the first consumer's backend, 0.28.1, 2026-10-17) filed 16 issues for 7 distinct
findings, and the operator's report (#3496) groups what remains after #3486's
in-cycle dedupe into five points. Three hand diagnoses run the same day
(Backend#1014, #1016, #1019) each spent most of their effort re-deriving context the
finding could have carried: which endpoint, which stack frame, whether the request
still succeeded, what the dead-lettered message was, whether the host was up.

Two defects make findings wrong today, and one gap makes them expensive:

- **A closed finding is refiled.** `issues._list_findings` lists `--state open`
  only, so a fingerprint whose issue a human closed looks new on the next run and
  files a fresh issue that does not link to the old one; the diagnosis and the
  "reopen if…" note are lost (#3496 point 1).
- **A schedule that has never emitted a heartbeat reads as silent.** The
  `heartbeat` check compares the latest expected firing against the last heartbeat,
  with no notion of when heartbeats began, so every weekly schedule whose only
  expected firing predates emission files a guaranteed false `silent-schedule`
  (#3496 point 2; Backend#1019, #1020).
- **A finding carries one line of evidence.** `FailureArtifact` has a single
  `observed_text`, and the App Insights queries already project `OperationId` and
  `ParentId` and then drop them (#3496 points 3–5).

T01–T04 fix the two defects; T05–T08 make every check's finding carry what a
diagnosis needs. The operator's statement of that goal (2026-10-17): **gather as much
information as possible to run a diagnostic.**

## Decisions (interview, 2026-10-17)

Items marked *operator* were answered explicitly; items marked *recommendation*
were taken as proposed and confirmed with the skeleton.

1. **A recurring fingerprint reopens its closed issue** (*operator*), with one
   comment carrying the new occurrence count and first/last seen in UTC. It never
   files a second issue for a fingerprint that already has one, open or closed.
   This lifts half of `issues.py`'s stated scope boundary ("never closes an issue,
   reopens one, or transitions its state"): the monitor may now **reopen**, and
   still **never closes**. The boundary's reason — auto-closing on silence erases
   the evidence of an intermittent fault — is about closing, and stays intact. The
   module docstring is rewritten to say exactly that.
2. **`dlq` is a state, not an event** (*recommendation*). A dead-lettered message
   stays in the queue until someone resubmits or purges it, so it is "seen" on every
   run. The finding records the message ids it has seen; a closed `dlq` issue stays
   closed while every message in the queue is already recorded (closing it means
   "acknowledged, replay pending"), and a **new** message id reopens it with a
   comment naming the new message.
3. **Closed issues are searched within a bounded window** (*recommendation*): closed
   in the last 90 days. Including every closed finding would grow the listing without
   bound and trip `TruncatedListingError` at the 100-row limit within weeks. A
   fingerprint whose issue closed longer ago than the window is treated as new and
   files a fresh issue; after 90 quiet days that is the honest reading.
4. **Severity is out** (*operator*). Findings deliberately skip triage
   (`list_untriaged` flags them `already_structured`, and the triage provider skips
   them — FEAT-2026-0049 criterion 6), so a finding never gets a triage severity.
   Severity for findings belongs on the **diagnosis**, which sees the evidence T05–T08
   adds; that is FEAT-2026-0205.
5. **Labels `component:<name>` and `check:<type>`** (*operator*, from #3496 point 5
   minus severity), created on first use.
6. **Readable titles** (*operator*, #3496 point 4). The fingerprint leaves the title;
   it stays in the body marker, which `issues.py`'s docstring already names as the
   sole authority (the title prefix was only a search narrowing).
7. **One query per check stays the rule** (*recommendation*,
   `security-boundaries.md`). Every correlation T05–T08 add — exception to request,
   request to dependency, schedule to host liveness — is a KQL `join` inside the
   check's single query, never a second query built from a returned value. The
   reproduction KQL printed in a finding is **text for a human**, built from
   configuration plus the sample ids, and is never executed by the monitor.
9. **One gate** (*operator*, on the ceremony-proportionality rule,
   `docs/methodology.md` §6). Drafted first as two gates, on a misread threshold; the
   rule's threshold is 12 substantive units and this feature has 8, and nothing gate 1
   learns changes what gate 2 adds, so the second gate's intermediate close and
   `plan-next` bought nothing.
10. **Structured context on the artifact** (*recommendation*). `FailureArtifact`
   gains an ordered `context` mapping (section label → text) and `observed_at`,
   rendered after **Observed**, redacted by `redact_artifact`, and never read by
   `fingerprint_artifact`. Cramming everything into `observed_text`, as #3477 did for
   one check, would make five checks' evidence unaddressable by the renderer and the
   redaction pass.
8. **Autonomy `auto`** (*recommendation*). The feature edits the monitor and its
   tests, not the driver, so the judge session checks the terminal close; a wrong
   arm is cheap to undo because nothing here runs unattended until an operator
   schedules `monitor run`.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rnE 'reopen|"closed"|--state' specfuse/monitor specfuse/loop/escalation.py`,
  `grep -n '_META_TEMPLATE|_parse_meta' specfuse/monitor/issues.py`,
  `grep -n 'def _heartbeat_query' specfuse/monitor/providers/azure_app_insights.py`,
  and `grep -rn 'already_structured' specfuse`.
- **Verdict:** `found the finding-meta marker and its field-scan reader, extending; no reopen path anywhere, building new`
- **If reusing:** `specfuse/monitor/issues.py:101`, `_parse_meta` — already a
  `key=value` token scan, not a positional regex, so T02 extends it with new fields.
  **But it is not fail-closed:** `int(...)`/`float(...)` raise `ValueError` on a
  malformed value, which is the exact shape `[FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]`
  records (a reader called on every listed issue that raises out of a whole sweep).
  T02 fixes that as part of extending it. No module reopens an issue today; every
  `--state` in `specfuse/monitor` and `escalation.py` is `open`.

## Escalation-predicate satisfiability (§2)

n/a — this feature flips no severity and adds no validation rule; `monitoring.yml`'s
schema is unchanged.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0204/T01
        file: WU-01-reopen-walking-skeleton.md
        depends_on: []
      - id: FEAT-2026-0204/T02
        file: WU-02-finding-meta-fail-closed.md
        depends_on: [FEAT-2026-0204/T01]
      - id: FEAT-2026-0204/T03
        file: WU-03-dlq-acknowledgement.md
        depends_on: [FEAT-2026-0204/T02]
      - id: FEAT-2026-0204/T04
        file: WU-04-heartbeat-grace.md
        depends_on: [FEAT-2026-0204/T01]
      - id: FEAT-2026-0204/T05
        file: WU-05-finding-context-skeleton.md
        depends_on: [FEAT-2026-0204/T02]
      - id: FEAT-2026-0204/T06
        file: WU-06-http-5xx-context.md
        depends_on: [FEAT-2026-0204/T05]
      - id: FEAT-2026-0204/T07
        file: WU-07-dlq-context.md
        depends_on: [FEAT-2026-0204/T03, FEAT-2026-0204/T05]
      - id: FEAT-2026-0204/T08
        file: WU-08-heartbeat-queue-context.md
        depends_on: [FEAT-2026-0204/T04, FEAT-2026-0204/T05]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-2026-0204/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0204/T01, FEAT-2026-0204/T02, FEAT-2026-0204/T03, FEAT-2026-0204/T04, FEAT-2026-0204/T05, FEAT-2026-0204/T06, FEAT-2026-0204/T07, FEAT-2026-0204/T08]
```

## Diagnostic context (T05–T08)

Goal: **a finding carries everything a diagnosis needs without re-querying the
telemetry backend.** Drawn from the three hand diagnoses' "what the finding lacked"
notes and #3496 point 3; T05–T08 implement it and the context oracle asserts it.

- **Every finding:** readable title (decision 6); labels (decision 5); first/last
  seen in UTC; count within the harvest window as well as total occurrences; the
  `AppRoleInstance` set; a ready-to-run reproduction KQL (decision 7).
- **`error-logs`:** the top in-app stack frame from `Details.parsedStack`; the
  request (`OperationName`, joined to `AppRequests` on `OperationId` for the route
  and result code, since `OperationName` is empty for exceptions logged from
  middleware); the logger category and message template
  (`Properties.CategoryName`, `OriginalFormat`); a **client-abort flag** for a
  cancellation on a request that still returned 2xx (Backend#1014's whole
  diagnosis); 2–3 sample OperationIds.
- **`http-5xx`:** the correlated exception (type, message, top frame) and the failing
  or slowest dependency (`AppDependencies` target, type, result code), both joined on
  `OperationId`; duration; samples.
- **`dlq`:** message id, sequence number, subject, enqueued time, delivery count;
  `DeadLetterReason`/`Description`, or the `Exception.Message` and
  `Exception.StackTrace` application properties when the reason is empty
  (Backend#1016); body **shape** only (keys, never values); a peek command.
- **`heartbeat`:** the schedule's cron and timezone; the function's last execution
  from `AppRequests` and its result; the component's earliest heartbeat; whether the
  role sent any telemetry in the silent gap (Backend#1019's undetected 4-day outage).
- **`queue-stalled`:** oldest active message age and the subscription's last
  completed message, in addition to today's depth.
- **Redaction:** every new field passes `redact_artifact` before egress; stack
  frames carry file paths, messages carry identifiers. Samples are capped at 3.

## Scope boundary

**In:** reopen-on-recurrence and the bounded closed-issue lookup; the finding-meta
marker's new fields and its fail-closed reader; the `dlq` acknowledgement model;
`heartbeat` grace; per-check diagnostic context, titles and the two labels;
the docs that describe these behaviours.

**Out:**
- **Severity** on findings — FEAT-2026-0205 (decision 4).
- **Re-diagnosis of a reopened finding.** A reopened issue already carries a
  diagnosis, so `findings-diagnose` skips it, and `autofix` declines it as already
  attempted. Whether a regression after a fix should re-diagnose is #3487's question,
  and this feature makes it answerable (the reopen comment is the signal) without
  answering it.
- **Diagnosis triggered by `monitor run`** — #3488.
- **A component-level liveness check.** T08's heartbeat evidence *reports*
  whether the host was alive during a silent gap; a check that fires on a silent host
  with no schedules is a separate check type.
- **Auto-closing** anything (decision 1).
- Providers other than Azure App Insights and Azure Service Bus.

## Post-merge checklist

- **Live run against the first consumer's workspace.** Every in-loop oracle runs over
  stub transports and a stub `gh`. After release, run `specfuse monitor run` on
  the first consumer's backend and confirm: a closed finding that recurs is reopened, not
  refiled; the four weekly schedules read "pending first firing" until their first
  heartbeat; and a sample of finding bodies carries every section the Diagnostic context names for
  its check.
