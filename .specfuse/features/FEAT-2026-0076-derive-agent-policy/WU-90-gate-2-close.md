---
id: FEAT-2026-0076/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
---

# Close FEAT-2026-0076 — terminal gate

**Objective.** Terminal close: re-run every oracle fresh, reconcile feature cost,
write the retrospective and lessons, enumerate consumer-visible contract changes,
and record an honest verdict.

**Context.** Correlation ID `FEAT-2026-0076/G2-CLOSE`. Placeholder drafted at
feature-drafting time so the linter reads gate 1 as non-terminal; `G1-PLAN`
updates its `depends_on` to the substantive work units it inserts above this
entry, and fills in the criteria gate 2's shape actually needs.

**The deferral this close inherits and must not drop.** `PLAN.md` §
*The oracle problem* fixes it in advance:

> *an agent following `derive-agent-policy`'s prose, run against a repository
> whose policy file it has not seen, proposes the values
> `propose_policy_defaults` computes.*

Gate 1 could not prove it. If gate 2 does not either, this close carries it
forward with its re-run condition — one operator invocation against this
repository's own `.specfuse/agent-policy.yml` — and the verdict is hedged
accordingly. A `met` verdict here requires that claim to have actually been
tested, not assumed.

**Also record.** Whether the provenance mechanism `G1-PLAN` chose held up under
implementation, and whether the disjoint-key boundary survived gate 2 — a review
skill is exactly the shape that would be tempted to write `queue:`.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.** Filled in by `G1-PLAN` against gate 2's drafted work
units. At minimum, and non-negotiably: oracles re-run fresh
(`close-discipline.md` §1); a `## Cost analysis` reconciling per-WU planned
against actual and a feature total against `PLAN.md`'s $37.00; the inherited
deferral recorded with its re-run condition; consumer-visible contract changes
enumerated; a verdict recorded, `met` only if every acceptance criterion across
both gates was verified in-loop; and `specfuse lint --closing` exiting 0.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement. `PLAN.md`'s `status` field: the driver owns the terminal flip
(`fire_terminal_flips`, gated on the verdict). Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set plus a fresh full-`code` re-run and
`specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
any oracle fails, if the inherited deferral cannot be honestly recorded, or if
`events.jsonl` lacks the cost data the analysis needs.
