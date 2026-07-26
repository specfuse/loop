<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: design for diagnosis

This rule governs the *target application's* code — not this loop's own
execution. It states what a deployed component must do so the check types a
`monitoring.yml` admits (`dlq`, `error-logs`, `http-5xx`, `heartbeat`,
`invariant`) produce a diagnosable finding instead of a bare alert. A check that
fires without one of these properties tells an operator only that something is
wrong, not what or where.

This rule is **reference-only**: it is seeded into every scaffolded project but
not `@`-imported into `CLAUDE.md`. Read it when writing or reviewing the
instrumentation of a component that a `monitoring.yml` entry points at. It is
provider-agnostic and language-agnostic on purpose — it states properties, not
implementations. How a project achieves a property (which library, which
platform's native tracing, which log shipper) belongs in that project's
`.specfuse/rules-local/`, never here.

## Correlation IDs propagate across component boundaries

A single request or message carries one correlation ID from the moment it enters
the system until every component that touched it has finished with it. The ID
must appear in every log line emitted while handling that request, and in the
envelope of every message produced as a result of it — not just at the entry
point.

This is the property an `error-logs` check depends on to be traceable: without
a propagated ID, a check can report that an error occurred, but an operator
cannot join that error line to the request that caused it, to the upstream
component that sent it, or to the downstream messages it produced. The finding
stops at "an error happened somewhere."

This rule is the target application's runtime sibling of
[correlation-ids.md](correlation-ids.md), which governs this loop's own IDs
(features, work units, commits). The two are not the same ID space and this
rule does not restate that file's format — it only asserts the analogous
property must hold in the code the loop's checks monitor.

## Structured logging with a stable field set

Log records are machine-parseable — key-value pairs or an equivalent structured
form, not free-text prose a human composed for other humans. The field set for
a given kind of event (a request handled, an error raised, a message consumed)
is stable across releases: the same event kind uses the same field names every
time it is emitted.

An `error-logs` check fingerprints a finding by grouping repeat occurrences of
the same underlying failure. Fingerprinting on structured fields (an error
code, a component role, a correlation ID) is stable; fingerprinting on prose is
not — a message with an interpolated timestamp, a reordered clause, or a
rephrased sentence looks like a new failure every time, and the check reports
noise instead of one grouped finding.

## Per-component role names match `monitoring.yml`

Every component's logs and metrics self-identify with a role name, and that
name is the same string a `monitoring.yml` entry's `name` field uses to
identify it. A component that does not stamp its own role onto everything it
emits cannot be told apart from its neighbors once findings are harvested.

This matters most in a multi-component `monitoring.yml`: a finding harvested
without a matching role name cannot be attributed to the one component that
produced it, so an operator investigating an alert has no starting point closer
than "somewhere in the system." A single-component project has a weaker version
of the same requirement — the name still anchors the finding to the
`monitoring.yml` entry that defined the check.

For example, an `acme-orders` service and an `acme-billing` service sharing one
log destination must each stamp their own role name on every record; a shared,
unstamped log stream makes the two indistinguishable once findings are
harvested.

## DLQ entries carry failure context, not just the payload

A message that lands in a dead-letter queue carries, alongside its original
payload, the context of why it failed: the exception or error that caused the
dead-letter, the correlation ID of the request that produced it, and the
number of delivery attempts made before it was dead-lettered.

A `dlq` check counts entries in a dead-letter queue and reports when the count
crosses a threshold. If an entry carries only the original payload, the check
can report that something failed and how many times, and nothing about why —
an operator has to reproduce the failure from scratch, from a payload alone,
with no error, no attempt count, and no correlation ID to trace back to the
request that produced it. Context captured at dead-letter time is the
difference between a diagnosis and a re-investigation.
