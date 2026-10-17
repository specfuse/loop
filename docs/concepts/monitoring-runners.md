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
`.gitignore`. A project initialised earlier keeps its existing gitignore block
(`specfuse upgrade` does not rewrite it), so add the line by hand. On a CI
runner the directory starts empty every run — the shipped workflow template
does not cache it — so each run there reads the 24-hour fallback window.

## What `--dry-run` does and does not gate

`--dry-run` performs the read-only `fetch_failures()` calls against real
telemetry/broker transports — it is not an offline mode. It gates only the
writes: the watermark file and every `gh` invocation. If you point a dry
run at a production telemetry backend, it will consume that backend's read
quota exactly as a real run would.
