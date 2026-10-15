---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_http_status_regression_end_to_end -v -b"
cost_budget_usd: 30.00
baseline:
  sha: 9fc3628b4cc386192ba55f7b69a509c4d84aefe2
  probed_at: 2026-10-15T02:59:12.218130+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:40b9f5f698e4b13c64573ca3176b0f2b78878624:4acc6dfc5e8cece358c167d876515eba4a39a500:5ac0b44bbd69937ed3c8a06990258a47c356e49d:5ff66b6e4d8a264f23709ea60706111a4c59ed11:6d43e5c8b8e5590d710db3708ae6bfa41921deef:767d4a5a9b7945d21ea4943948071347d5339753:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:84bb8013b5c92bb31c205b015fc53ccf38bcb1a9:97bcab1bc7244262cec901f46035f51dfdd07278:b4305b01d3eb16aff49cab646a99f7c26d7ca9f3:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: 8453d774e34f8241362417ae0d23b166f841f912
  source: attributed:FEAT-2026-0203/T03
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "(failures=2,"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
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
