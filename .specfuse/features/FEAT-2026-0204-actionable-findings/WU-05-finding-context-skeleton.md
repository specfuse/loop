---
id: FEAT-2026-0204/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/monitor/artifact.py
  - specfuse/monitor/issues.py
  - specfuse/monitor/cli.py
  - specfuse/monitor/redaction.py
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_monitor_finding_context_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:48:53.647641+00:00
duration_seconds: 194.293
cost_usd: 0.90173
input_tokens: 46
output_tokens: 25028
---

# T05 — a finding has a readable title, labels, and an `error-logs` body a diagnosis can start from

**Objective.** The context half of the oracle goes green for `error-logs`: a finding
renders a readable title, `component:`/`check:` labels, a "when and where" section,
and the `error-logs` evidence a diagnosis needs, without changing any fingerprint.

**Context.** `FEAT-2026-0204/T05`. PLAN.md decisions 5–7 and the "Diagnostic context"
section. T01 created `tests/test_monitor_finding_context_end_to_end.py` with one
skipped class per check type, each naming its owning unit; this unit removes the
skip on `ErrorLogsContext` and on `EveryFinding`.

**The model (decided at draft time, PLAN.md decision 9).** `FailureArtifact` gains
`context: Optional[Mapping[str, str]]` (ordered; each key a section label, each value
text) and `observed_at: Optional[str]` (the row's timestamp). `fingerprint_artifact`
must **not** read either. `redact_artifact` redacts every context value.
`issues._render_body` renders context after **Observed** as `**<label>:**` lines
(multi-line values in a fenced block).

**Per finding, every check.** In `run_cycle`, #3495's per-cycle fingerprint set
becomes a per-cycle aggregate: for each fingerprint, the count of rows this cycle,
first and last `observed_at`, and the set of `AppRoleInstance` values; the first
artifact carries them into the body as "Seen this run" (count, first, last, UTC) and
"Instances". The title becomes `<component>: <failure class> in <where>` when the
context names a location (e.g. the top frame's type), else
`<component>: <failure class>` — no fingerprint (PLAN.md decision 6). Labels
`component:<name>` and `check:<type>` are added on create, creating each label once
per run with `gh label create --force` before first use.

**`error-logs` evidence**, from the **one** query (`_error_logs_query`), extended
with joins inside it: the top in-app frame (first `Details[0].parsedStack` entry whose
assembly is not a framework one — define "framework" as a short prefix list in the
module, `System.`/`Microsoft.`), the request (`AppRequests` joined on `OperationId`:
route `Name` and `ResultCode`), the logger category and template
(`Properties.CategoryName`, `Properties.OriginalFormat`), `AppRoleInstance`, and a
**client-abort flag** set when the exception type is
`TaskCanceledException`/`OperationCanceledException` and the joined request returned
2xx (Backend#1014). Up to 3 sample OperationIds. A "Reproduce" section prints a KQL
query built from the component name and the samples — text only, never executed
(PLAN.md decision 7).

**Acceptance criteria.**

1. `tests/test_monitor_finding_context_end_to_end.py::ErrorLogsContext` and
   `::EveryFinding` (skipped by T01, naming this unit) have their skips removed and
   pass: from fixture rows modelled on Backend#1014 (two cancellations, 200 responses,
   two instances), one issue is created whose title has no `[monitor:` prefix, whose
   labels include `component:web-api` and `check:error-logs`, and whose body carries
   Seen this run (count 2, first, last), Instances, Where (top frame), Request
   (route + 200), Logger (category + template), Likely client abort, Samples, and
   Reproduce.
2. `test_fingerprint_unchanged_by_context`: two artifacts differing only in `context`
   and `observed_at` have the same `fingerprint_artifact`.
3. `_error_logs_query` passes `schema_violations` with no new findings, the adapter
   issues exactly one `run_query`, and a secret-shaped string placed in a context value
   is redacted in the rendered body.

**Do not touch.** The fingerprint model. Other adapters (T06–T08). The finding-meta
marker (T02).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_app_insights_adapters tests.test_app_insights_query_schema_check tests.test_monitor_issue_lifecycle tests.test_monitor_one_issue_per_fingerprint tests.test_monitor_finding_lifecycle_end_to_end -b`.

**Escalation triggers.** If `Details[0].parsedStack` is not reachable in KQL without
`mv-expand` over every exception (cost), stop and escalate with the measured query
rather than dropping the frame. If `gh label create` needs a permission the default
token lacks, escalate rather than silently skipping labels.
