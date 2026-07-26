---
gate: 1
status: open
baseline:
  sha: 07796867343bb04ad0cbe63370ddf6d396ca895e
  probed_at: 2026-07-26T16:44:18.149696+00:00
  failing: []
---

# Gate 1 — the schema expresses per-target enumeration, and the validator enforces which check types may carry it

## Definition of done

- `monitoring.yml` can express per-subscription DLQ attribution and per-schedule
  heartbeat: a check carries an optional `targets` list, and each target carries the
  coordinates its check type needs.
- The validator enforces the axis distinction — `dlq` and `queue-stalled` **must** carry
  targets, `heartbeat` **may**, `error-logs` and `http-5xx` **must not**.
- Every shipped surface carrying a YAML example has been migrated, so the repo's own
  `monitoring-example-lint` gate and `tests/test_monitoring_fenced_blocks.py` are green
  against the new contract rather than the old one.
- `queue-stalled` exists as a check type, so a wedged consumer is no longer invisible to
  every check the schema can express (issue #247).
- FEAT-2026-0040's adapter interface has a machine-checkable answer to "do I enumerate
  per component or per target."
- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`), generalizable lessons are
  promoted to `.specfuse/LEARNINGS.md`, and docs plus roadmap status reflect what was
  actually built.
- Gate 2's work units are drafted, and `GATE-01-REVIEW.md` is written.

**What this gate deliberately does NOT prove.** `/derive-monitoring` still emits N
components for a deployable carrying N triggers. The schema will be able to express the
right answer before discovery is able to produce it. That is gate 2, and gate 1's close
must state it plainly rather than let the schema's correctness read as the feature's
completion.

The closing sequence (`close-intermediate` → `plan-next`) is part of every non-terminal
gate and is enforced by the linter. The driver runs the gate unattended, then stops here
for human review-and-arm: read the review artifact, accept or edit the drafted
next-gate work units, flip the accepted ones to `pending`, set this gate's status to
`passed`, and re-run.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** Gate 2 re-keys
  `discover_components`, which changes what the discovery reference implementation
  returns for existing fixtures. That is a behavioral default change, so it may **not**
  be armed on "mechanical, nothing design-open." Apply the re-key locally, run
  `python3 -m unittest discover -s tests -v` — the full oracle, not a subset — and paste
  the failure list into `GATE-01-REVIEW.md`. That list becomes the WU's enumerated test
  surface.
- **Escalation-predicate satisfiability (§2).** If any gate 2 WU asserts a "zero
  findings" predicate over a fixture it also authors, confirm the predicate is
  satisfiable on a correct input before arming — and confirm the fixture is not being
  used as evidence for the extractability claim it cannot support.
- **Flag-scope table (§3).** No behavior flag is expected in gate 2. If one appears,
  it needs the table.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
</content>
