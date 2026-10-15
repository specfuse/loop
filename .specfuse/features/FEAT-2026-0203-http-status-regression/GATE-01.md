---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_http_status_regression_end_to_end -v -b"
cost_budget_usd: 30.00
---

# Gate 1 — a deployment that raises server-fault 4xx files one finding

## Definition of done

**Stated as an outcome.** A `monitoring.yml` declaring an `http-status-regression`
check on a component passes `specfuse-monitor-lint`; the harvester, run through
`run_cycle(dry_run=True)` over a stub transport whose rows describe one deployment
after which `401` rose from a small share of requests to well over three times that
share, prints exactly one `would file:` line for that component, check type and
status code; and a second cycle over the same rows produces the same fingerprint, so
the finding is filed once per deployment, not once per run.

The `feature_oracle` above proves that end to end. It is red on the current tree (the
module does not exist) and `FEAT-2026-0203/T01` is the walking skeleton that turns it
green — the only unit in this gate permitted to stub (`/authoring-work-units` §14).
T01 creates the oracle module first, because the oracle is appended to every
attempt's gate list and a module that lands last fails every earlier unit on
`ModuleNotFoundError` (`FEAT-2026-0113` gate 2 paid four attempts for that).

Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe (§4).** T02 flips a severity: a malformed `stall_after` becomes a
  lint error. Before arming T02, apply that change locally, run the full `tests`
  gate, and paste the failure list into `GATE-01-REVIEW.md`. The expected list is the
  one pinned opacity test (`test_queue_stalled_threshold_coordinate_is_opaque`) and
  nothing else; anything more is a shipped `stall_after` the plan missed.
- **One query (PLAN.md decision 5).** A drafted change that detects the deployment in
  one query and counts the windows in a second has folded a returned value into a
  query. That is a `security-boundaries.md` violation, not a variant.
- **Existing-mechanism search (§1).** `parse_stall_after_seconds` already parses the
  duration grammar. A unit that writes a second duration regex has not done the
  search.

## Reflection notes

<Written by the human at review time.>
