---
gate: 3
status: passed
cost_budget_usd: 28.00
baseline:
  sha: cad7e710de1ea71a2ea5010ed26770b830221f3e
  probed_at: 2026-07-29T11:13:09.800562+00:00
  failing: []
---

# Gate 3 — a finding becomes an issue, once, and something runs the cycle

## Definition of done

- The **sixth check type has an adapter**: `queue-stalled` reads a subscription's
  queue depth and age-of-oldest through `T01`'s `BrokerAdapter`, carries the
  target's `subscription` and `function`, and decides staleness from a declared
  threshold it **refuses to guess at** rather than a default it invents.
- **One fingerprint yields one issue.** The lifecycle finds-or-creates against a
  marker it verifies client-side, updates an occurrence count under a throttle, and
  annotates a quiet fingerprint — and **never closes one**. Two artifacts differing
  only in their target coordinates yield two issues; a second sighting of one
  fingerprint yields no second issue.
- **`specfuse-monitor run` drives a whole polling cycle**: config load, target
  enumeration on the 0069 axis, registry-driven provider dispatch, telemetry through
  the `resolve_telemetry` seam, fingerprinting, redaction, watermark fallback, and a
  run summary that names what was skipped and why. `--dry-run` issues **zero** `gh`
  calls, proven by an empty recorded call set.
- **Two runner surfaces exist**: the local runner, and a GitHub Actions workflow that
  ships as a template with least-privilege permissions and no literal secret. The
  `runner` dial routes components between them, and a component belonging to neither
  is reported rather than silently unmonitored.
- **The core stays provider-agnostic through the CLI.** No provider identifier is
  reachable from `specfuse/monitor/` outside `providers/`, the CLI included; the
  registry maps opaque config strings to lazily-imported modules.
- `RETROSPECTIVE.md` carries a `## Gate 3` section; the terminal close records a
  verdict, the consumer-visible contract enumeration with human acknowledgment, and a
  deferred list that names **`gate 1`** literally for the auto-close-debt
  reconciliation.

Every clause is decidable **by this gate**, per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`.
Note what is deliberately *not* claimed: **nothing here asserts that a real GitHub
repository received an issue, or that the shipped workflow ever ran.** Those are
structurally unverifiable in a work-unit session — `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`
records `gh` returning auth errors inside `claude -p` — so they are named deferred
items with operator-journal proxies (D-9, D-10, D-11), not clauses in the definition
of done. Nor does anything here assert an adapter works against a live Azure
environment; gate 2's D-1 … D-8 carry forward unchanged.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **§1 existing-mechanism search — run, two verdicts, both recorded.**
  *Issue lifecycle:* `grep -n "^def \|marker" specfuse/loop/escalation.py` →
  **found, reusing** the injected-runner seam, `_extract_issue_number`, the marker
  convention, and find-then-create — but **not** `_find_existing_issue`'s
  `--search` strategy, which FEAT-2026-0046's own retrospective records as unsafe
  for a deduplicating consumer. `T09` implements the fix that retrospective names.
  *Runner surface:* `ls .github/workflows` (three repo-own workflows, none a
  template) and `grep -rn "workflows" --include='*.sh' --include='*.py' scripts/
  specfuse/loop/*.py` (no match) → **no existing mechanism, building new**. Full
  text in `GATE-03-REVIEW.md` §3.
- **§2 escalation-predicate satisfiability — not applicable, with the reason.**
  Gate 3 introduces **no severity flip and no blocking check over existing repository
  state**. Every assertion is over new modules the gate itself writes, plus a new
  entry point and a new template, so a correct tree reports zero by construction.
  The one place a flip was tempting — making `stall_after` required and bounded in
  `lint_monitoring.py` — was **deliberately kept out of `T08`**, precisely because it
  would make §4's probe mandatory on a gate that otherwise needs none. It is a named
  follow-up in `GATE-03-REVIEW.md` §7, not a silent omission.
- **§3 flag-scope table — applicable, and `T10` carries it.** `--dry-run` is a
  behaviour flag whose headline claim is "a dry run touches nothing," and that claim
  is exactly the kind that stays true until someone adds a convenience. `WU-10`'s
  table crosses the claim against all eight code paths, marking `fetch_failures()`
  **not gated** on purpose so `--dry-run` is never mistaken for `--offline`; `T10`
  criterion 8 is its oracle. `--component` and `--env` are selectors, not behaviour
  flags, and `T11`'s `runner` dial is a routing decision, not a code-path gate —
  both recorded as assessed rather than omitted.
- **§4 runtime probe — not applicable, with the reason, and one substitute worth
  running.** §4 binds a gate whose WUs flip a **default value** or a **severity**.
  Gate 3 flips neither: it adds modules, an entry point, and a template, and changes
  no existing rule's outcome on any existing input. Recorded as assessed, not
  skipped — and `[FEAT-2026-0049/F4]`'s cost is why the reason is written out rather
  than left as "mechanical, nothing design-open."
  **The substitute the operator should run instead** is one command, and it grounds
  the whole gate's out-of-loop designation in an observation rather than an inherited
  claim: confirm `gh auth status` actually fails inside a `claude -p` session in this
  environment. Every "produces no in-loop evidence" designation in `T09`, `T10`, and
  `T11` rests on `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`; if `gh` in fact works
  here now, three WUs are scoped more pessimistically than they need to be and the
  gate should be re-armed with real criteria instead of deferred ones. See
  `GATE-03-REVIEW.md` §4.
- **Arming this gate means accepting a hedged terminal verdict as the likely
  outcome.** `T09`, `T10`, and `T11` produce real in-loop evidence about their own
  code and none about the GitHub surface underneath it; `T08` is the only unit whose
  evidence is complete in-loop. `GATE-02-REVIEW.md` §6.1 answer 4 records that an
  operator run against the downstream .NET backend **is planned**, which is what keeps
  `met` reachable — but it is reachable only *after* that run and the D-9 … D-11
  journal entries exist, not on the strength of a green stub suite.

## Reflection notes

<Written by the human at review time.>
