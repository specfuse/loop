# Monitoring secrets checklist

Merge and execution semantics land in FEAT-2026-0040 (`specfuse-monitor run`).
This file is a shape declaration only: the list of environment-variable
**names** an operator must export before running monitoring checks locally.
It names variables, never values — it is safe to commit and safe to read.

Pair this checklist with `.specfuse/monitoring.overrides.yml` (copied from
`monitoring.overrides.yml.example`): every `credentials.*` value in that file
is one of the names below.

## Required environment variables

- `ACME_TELEMETRY_STAGING_API_KEY` — Acme Telemetry console, staging
  workspace, API keys page.
- `ACME_BROKER_STAGING_CONNECTION_STRING` — Acme Broker console, staging
  namespace, connection strings page (read-only credential).
- `ACME_TELEMETRY_PROD_API_KEY` — Acme Telemetry console, production
  workspace, API keys page.
- `ACME_BROKER_PROD_CONNECTION_STRING` — Acme Broker console, production
  namespace, connection strings page (read-only credential).

## How to use this checklist

1. Export each name above on the machine that will run
   `specfuse-monitor run --dry-run` (FEAT-2026-0040), using whatever secret
   store your shell profile or process manager already uses.
2. Never write a value for any of these names into a tracked file, a commit
   message, or this checklist itself — only the name belongs here.
3. If a name above is missing on your machine, obtain the value from the
   console page listed next to it; do not invent or reuse a value from
   another environment.
