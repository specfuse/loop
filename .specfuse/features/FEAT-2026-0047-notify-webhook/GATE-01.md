---
gate: 1
status: passed
cost_budget_usd: 24.50
baseline:
  sha: e0ec4972e3e9ccd87f578bf51c7341233e273a19
  probed_at: 2026-08-10T08:52:14.435059+00:00
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings
    - gate: coverage
      failure_class: coverage
      failure_signature: $ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
---

# Gate 1 — escalations reach the operator's channel, and agent silence alarms itself

## Definition of done

- A webhook notifier exists with per-provider payload adapters, reading its URL
  from an environment variable named in config — never from config itself.
- `escalation.webhook_env` has replaced `escalation.webhook`, the validator
  rejects a literal URL, and the shipped example is migrated in the same unit.
- New and re-pinged needs-human issues post a one-liner and a link.
- An unanswered escalation past the SLA window re-pings exactly once, then parks.
- Agent silence past a configured threshold is detectable from repo state alone
  and surfaces in `/attention`.
- Every implementation work unit in this gate is `done`.
- The terminal close has run: retrospective, lessons, docs, and verdict.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

Single-gate feature (four substantive WUs, `docs/methodology.md` §6). No
`plan-next`, no next gate to arm.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe (§4).** T01 raises `validate_agent_policy`'s strictness (a
  literal URL in `webhook_env` becomes an `ERROR: `). The probe is cheap and
  bounded: this repo's own policy file carries an **empty** value, so the full
  `agent-policy-example-lint` gate must report zero both before and after. T01's
  criteria require running it, and require the example's migration to land in
  the same unit so no intermediate tree is red.
- **Flag-scope table (§3).** No WU introduces or flips a behavior flag.
  `webhook_env` is a configuration *value*, not a dial: empty means no-op,
  non-empty means post. T01 records this distinction rather than a table.
- **Escalation-predicate satisfiability (§2).** Answered in PLAN.md: zero on a
  conforming file, including the empty-value case this repo actually ships.

## The two risks this gate carries

1. **An outbound channel is irreversible.** Anything posted is cached and
   indexed by a third party the moment it lands, and deleting the message does
   not unpublish it. Every payload is redacted through
   `monitor/redaction.redact_text` before leaving the process, and no test may
   perform a real HTTP request.
2. **A bearer credential must not enter git.** The whole point of the
   `webhook_env` rename is that the URL lives in the environment. A reviewer
   should check that no code path writes the resolved URL into config, a log
   line, an event payload, a rendered message, or an error string.

## Reflection notes

<Written by the human at review time. This gate was drafted and armed without an
operator interview, on operator instruction (2026-08-09). PLAN.md § *Assumed
decisions* lists eight decisions taken solo; § *The security correction* is the
one to read first, because it changes a field FEAT-2026-0044 shipped the same
night.>
