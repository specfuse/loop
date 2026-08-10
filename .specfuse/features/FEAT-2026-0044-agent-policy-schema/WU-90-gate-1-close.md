---
id: FEAT-2026-0044/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
duration_seconds: 0.0
---

# Close FEAT-2026-0044 — terminal gate

**Objective.** Close the feature: re-run every oracle fresh, reconcile cost,
write the retrospective and lessons, enumerate consumer-visible contract
changes, and record an honest verdict.

**Context.** Correlation ID `FEAT-2026-0044/G1-CLOSE`. Terminal close of a
single-gate feature (four substantive WUs, ceremony proportionality —
`docs/methodology.md` §6). Depends on T01–T04.

`auto_close_disabled: true` is set deliberately: this close's criteria include
the `close-discipline.md` §1 fresh re-run, which makes it load-bearing, so the
auto-close predicate must not optimize it away (#189).

**Two things about this feature that the retrospective must record honestly**,
because they are unusual and the next reader will not infer them:

1. **This feature was drafted solo, with no operator interview**, on operator
   instruction (2026-08-09). `PLAN.md` § *Assumed decisions* lists seven
   decisions taken without a human. The retrospective must state which of them
   the implementation validated, which it strained, and which are still
   unexercised — the operator's veto checkpoint is this feature's PR, and that
   review is only as good as this record.
2. **FEAT-2026-0048 was drafted against this schema before it was built.** If
   any WU here changed the schema from what `PLAN.md` §*The schema* declared in
   T01, the retrospective must say so explicitly and name the field, because
   0048's `T01` verifies the shipped schema against what it assumed and will
   escalate on divergence.

The closing sections are scaffolded at dispatch (`close-discipline.md` §4 and
the registry in `specfuse/loop/closing_requirements.py`) — fill them with
substance rather than re-deriving the headings.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. **Oracles re-run fresh in this session** (`close-discipline.md` §1), exit
   codes read directly, never inherited from a WU's self-report: the full `code`
   gate set from `.specfuse/verification.yml` — `tests`, `lint`, `security`,
   `coverage`, `leak-scan`, `event-type-gate`, `roadmap-link-gate`,
   `arm-sweep-gate`, `monitoring-example-lint`, and the newly added
   `agent-policy-example-lint`. Each command and its exit code are recorded in
   `RETROSPECTIVE.md`.
2. `validate_agent_policy()` is run fresh against **both**
   `.specfuse/agent-policy.yml` and `.specfuse/agent-policy.yml.example`, and
   the retrospective records that neither returns an `ERROR: ` finding.
3. The satisfiability claim from `PLAN.md` is re-tested, not assumed: a queue
   entry naming a `done` feature produces a `WARN: ` and **does not fail** the
   gate; a queue entry naming a nonexistent FEAT-ID produces an `ERROR: ` and
   **does** fail it. Both verified by running the validator, and the result
   recorded.
4. `RETROSPECTIVE.md` exists with a `## Cost analysis` section reconciling each
   WU's `planned_cost_usd` against actual from `events.jsonl` (including all
   re-arm cycles via the `cumulative_*` fields), with a per-WU delta, a gate
   total against the $23.00 budget, and a feature total against `PLAN.md`'s
   $19.00. Any WU over 50% variance carries a one-paragraph cause.
5. `RETROSPECTIVE.md` records the two feature-specific items named in this WU's
   Context: the solo-drafting decision audit (all seven, each marked validated /
   strained / unexercised), and whether the shipped schema diverged from what
   T01 declared.
6. `.specfuse/LEARNINGS.md` gains at least one entry, or carries an explicit
   note that nothing generalized. If the solo-drafting experiment produced a
   durable lesson about drafting without an interview, it belongs here.
7. **Consumer-visible contract changes** enumerated (`close-discipline.md` §3):
   the new `.specfuse/agent-policy.yml` schema, the new
   `agent-policy-example-lint` gate, the new public
   `lint_roadmap.roadmap_statuses`, and the `/triage-issues` behavior change
   (the dial now comes from a file rather than from the operator each run) — or
   exactly `n/a — no consumer-visible contract change` if the enumeration is
   genuinely empty, which it is not.
8. Documentation reflects what shipped: the roadmap's FEAT-2026-0044 detail
   section describes the delivered shape, and the feature's row and detail
   status agree.
9. A verdict is recorded. `met` only if every acceptance criterion across
   T01–T04 was verified in-loop. If any was not, the verdict is `met_locally` or
   `partially_met` with a `## Hedged-verdict follow-up record` carrying, per
   unmet criterion, the criterion verbatim, why it is unverifiable here, the
   exact re-run condition that would upgrade it, and a `kind:` written as
   `- **kind:** \`<value>\``.
10. `## What the loop did NOT verify` lists every deferred criterion with where
    it actually gets checked, or exactly
    `(nothing — every acceptance criterion was verified in-loop)`.
11. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement. If an oracle fails, record the failure and emit
`status: blocked`; do not fix the code from the close session. Other features'
folders. `.specfuse/rules/`. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

Do **not** write `PLAN.md`'s `status` field: the driver owns the terminal flip
(`fire_terminal_flips`, gated on the verdict).

**Verification.** The `plannext` gate set plus the fresh full-`code` re-run
named in criterion 1, and `specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any oracle in criterion 1 fails (record which, and its output — do not fix it
here); the satisfiability re-test in criterion 3 does not behave as `PLAN.md`
claims, which would mean the CI gate is unsatisfiable and must not ship;
`events.jsonl` lacks the cost data criterion 4 needs; or the shipped schema
diverged from T01's declaration in a way that would break FEAT-2026-0048's
assumptions — that is an operator decision about a downstream feature, and it
must be surfaced, not absorbed.
