# Where the monitoring cycle runs — the `runner` dial and its surfaces

`.specfuse/monitoring.yml` gives every component a `runner` dial: `local`,
`gh-actions`, or `in-cluster`. The dial says *where that component's
diagnose/autofix cycle executes* — it is a routing decision, not a feature
flag, and it does not gate any code path inside the cycle itself. This
document covers the two surfaces FEAT-2026-0040 ships and states plainly
what is still missing.

What happens to a finding after it is filed — diagnosis, the autofix decision,
the fix — and which processes must be scheduled for it is in
[`monitoring-to-fix.md`](monitoring-to-fix.md).
`specfuse monitor run` does not diagnose anything itself: when it files or
updates findings for a component set to `diagnose: auto`, its summary prints one
line saying those findings wait for `specfuse agent run` (specfuse-agent).

## The two shipped surfaces

**Local.** An operator, or a cron entry on a machine they control, runs
`specfuse monitor run`. This is the recommended starting point — the
schema's own `monitoring.yml.example` advises starting every component at
`runner: local` before loosening any dial. Nothing extra to install — the
`specfuse` suite already carries it (`pipx install specfuse`, which
hard-depends on the `specfuse-loop` distribution this CLI ships in). The CLI
reads `.specfuse/monitoring.yml` from the current working directory the same
way on this surface as any other.

**GitHub Actions.** A shipped, scheduled workflow template runs the same
cycle in CI. It lives at
`specfuse/loop/data/workflows/specfuse-monitor.yml` in the `specfuse-loop`
distribution — this is a *template*, not a workflow this repository runs
itself (this repository is a CLI tool with no deployable components and
will never carry a real `monitoring.yml`; see `verification.yml`). To use
it in a consumer project:

1. Copy `specfuse-monitor.yml` into that project's own `.github/workflows/`.
   You already have it if `specfuse` is installed — it ships inside the
   `specfuse_loop` package data, so
   `python -c "import specfuse.loop, pathlib; print(pathlib.Path(specfuse.loop.__file__).parent / 'data/workflows/specfuse-monitor.yml')"`
   prints its path. It is also readable from this repository's
   `specfuse/loop/data/workflows/`.
2. Add the secrets it references — one per credential-bearing environment
   variable named in that project's `.specfuse/monitoring.yml` (`api_key`,
   `connection_string`, etc.), plus a token with permission to file issues
   (`GITHUB_TOKEN` is sufficient for issues in the same repository) — under
   the consumer repository's Settings → Secrets and variables → Actions.
   Every value the template consumes is a `${{ secrets.* }}` reference; it
   never embeds a literal credential.
3. Dial the components that should run here to `runner: gh-actions` in that
   project's `.specfuse/monitoring.yml`.

The template declares both `on.schedule` (a cron expression) and
`on.workflow_dispatch`, so it can be triggered by hand while debugging, not
only on its schedule. It requests exactly `permissions: {issues: write,
contents: read}` — least privilege for filing issues, nothing more — rather
than inheriting the default write-all token.

## The dial routes, and skips are reported, not silent

`specfuse monitor run` takes a `--runner` flag naming which surface this
invocation *is* (defaulting to `local`). It enumerates only the components
whose `runner` matches that flag; every other component is named in the run
summary along with the surface it belongs to, so a skipped component is
visible, not silently unmonitored. A component whose `runner` value isn't
one of `local` / `gh-actions` / `in-cluster` is a clear error naming the bad
value and the supported set — a typo'd dial must fail loudly, not run
nothing.

## `in-cluster` is out of scope here

`in-cluster` is a valid schema value today, but no runner surface
implements it in this feature. A component dialed to `runner: in-cluster`
is reported by `specfuse monitor run` as unhandled by design — naming
**FEAT-2026-0043**, which owns that surface — and is neither dropped
silently nor treated as an error. Do not dial a component to `in-cluster`
expecting it to be monitored until that feature ships.

## The harvest window

Each run reads only what is new since the previous one. The window for an
environment starts at its watermark (the time the previous non-dry run
started, kept in `.specfuse/monitor-watermarks/<env>.json`) and ends at this
run's start. With no readable watermark (a first run, a fresh CI runner, a new
operator) it starts 24 hours back instead, and the run summary says so.

The window applies to the checks that read event history: `error-logs` and
`http-5xx` filter on `ingestion_time()`, so a row stamped just before the
previous run but ingested after it is read by the next run rather than lost
between the two. Three check types are deliberately not bounded by it:

- `heartbeat` needs the most recent heartbeat however old it is;
- `http-status-regression` compares the windows around each deployment and
  carries its own fixed lookback;
- `invariant` runs the operator's query as written. A query that reads event
  history should bound itself (for example `| where TimeGenerated > ago(1h)`);
  otherwise every matching row in retention is a finding, deduplicated only by
  `fingerprint_by`.

A run in which any check errored leaves the watermark where it was, so the
next run retries the same window.

The watermark directory is local runtime state, not something to commit.
`specfuse init` adds `.specfuse/monitor-watermarks/` to a new project's
`.gitignore`, and `specfuse upgrade` adds it to a project initialised earlier
(it appends any snippet line the file lacks, leaving your own lines alone). On a CI
runner the directory starts empty every run — the shipped workflow template
does not cache it — so each run there reads the 24-hour fallback window.

## What `--dry-run` does and does not gate

`--dry-run` performs the read-only `fetch_failures()` calls against real
telemetry/broker transports — it is not an offline mode. It gates only the
writes: the watermark file and every `gh` invocation. If you point a dry
run at a production telemetry backend, it will consume that backend's read
quota exactly as a real run would.

## What a finding is, and how its issue is kept

Every finding is one GitHub issue per fingerprint. The fingerprint is the
`specfuse:finding` marker in the issue body, and it is the only thing that
identifies a finding: nothing a finding *carries* (its title, its context, the
time it was seen, a dead-lettered message's id) enters it.

### A recurrence reopens; it never refiles, and nothing is ever closed

On each run, a fingerprint is matched against issues in three states:

- **Open** — the issue is updated, as before.
- **Closed within the last 90 days** — the issue is **reopened** with exactly one
  comment carrying the new occurrence count and the first and last time it was
  seen, in UTC. No second issue is filed, so the earlier diagnosis and any
  "reopen if…" note stay attached to the finding.
- **Absent, or closed longer ago than 90 days** — a new issue is filed. After 90
  quiet days that is the honest reading, and the bound keeps the listing under
  GitHub's 100-row limit.

The monitor **reopens, never closes.** Closing on silence would erase the evidence
of an intermittent fault, so closing stays a human decision, and no code in
`specfuse/monitor` issues a close. A finding-meta marker the monitor cannot fully
understand (a hand-edited or truncated one) reads as absent rather than failing
the run.

### A finding that goes quiet is annotated, once

An open finding whose fingerprint has not been seen for **7 days** gets one
comment naming it a candidate for close, and a marker in its body so the comment
is not repeated. The monitor only does this for a component every one of whose
checks ran without error in that cycle — a broken check never makes a finding
look quiet — and it still closes nothing. If the fingerprint fires again, the
issue's body is rewritten without the marker, so a later quiet period is
annotated again. The pass reuses the cycle's own issue listing; `--dry-run`
prints the issues it would annotate.

### `dlq`: closing an issue means "acknowledged"

A dead-lettered message stays in the queue until someone resubmits or purges it,
so it is seen on every run. The `dlq` finding records the message ids it has seen.
A closed `dlq` issue whose recorded ids cover every message currently in the queue
**stays closed**, with no write at all — closing it means "acknowledged, replay
pending". A message id the issue has not recorded **reopens** it, with a comment
naming that message. Messages are only ever peeked; the monitor never receives,
completes or abandons one.

### `heartbeat`: a schedule that has not emitted yet is not silent

A target whose latest expected firing precedes the component's earliest observed
heartbeat is *pending its first firing*, and produces no `silent-schedule`
finding. A target that has emitted before and then missed a firing still does, and
a component with no heartbeat at all files nothing.

### What a finding contains

The title reads `<component>: <failure class> in <where>`, with no fingerprint.
Each issue carries the labels `component:<name>` and `check:<type>` (created on
first use). Every body states the occurrence count, when it was first seen (the earliest
occurrence the run's rows show; for `dlq`, the message's enqueued time) and when
the issue was last updated (UTC), what was seen in this run (count, first, last, and the instances), and the
**Observed** line. Per check, the sections after **Observed** are:

| check | sections |
| --- | --- |
| `error-logs` | Where (top in-app stack frame), Request (route and result code), Logger (category and message template), Likely client abort, Samples, Reproduce |
| `http-5xx` | Exception (type, message), Where, Dependency (target, type, result code, duration), Duration, Samples, Reproduce |
| `dlq` | Message (id, sequence number, subject, enqueued time, delivery count), Dead-letter reason, or the Exception message and top stack frames when the reason is blank, Body shape (the top-level keys, never the values), Peek it |
| `heartbeat` | Schedule (cron, dialect, timezone, expected firing), Last run (the function's last execution and result), Host last seen, a Host silent line when the component sent no request telemetry across the expected firing, and Earliest heartbeat (the component's first heartbeat, which the grace rule measures from) |
| `queue-stalled` | Queue (oldest active message age, depth, `stall_after`), Where |

A section with nothing to say is left out rather than printed empty. A
`queue-stalled` finding cannot show when the subscription last completed a
message: Service Bus runtime properties carry no completion time (their
`accessed_at_utc` changes on sends as well as receives, so it would mislead),
and reading one from the messages themselves would mean receiving them, which
the check never does.

Each check still issues exactly one query. Every correlation (an exception to its
request, a request to its dependency, a schedule to its host's liveness) is a join
inside that query. The **Reproduce** and **Peek it** sections are text for a
human to run, built from configuration and sample ids, and the monitor never runs
them. Every section is redacted before it leaves the machine.
