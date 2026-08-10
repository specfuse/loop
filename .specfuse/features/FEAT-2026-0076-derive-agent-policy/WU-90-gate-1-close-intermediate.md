---
id: FEAT-2026-0076/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
model: opus
effort: high
gate_set: plannext
driver_version: 0.10.0
started_at: 2026-08-10T15:35:02.957711+00:00
duration_seconds: 872.917
cost_usd: 7.302612
input_tokens: 144
output_tokens: 45809
---

# Close gate 1 — bootstrap half

**Objective.** Close gate 1: re-run its oracles fresh, reconcile cost, append the
gate's retrospective section and its lessons, and record honestly what this gate
did **not** prove.

**Context.** Correlation ID `FEAT-2026-0076/G1-CLOSE-INTERMEDIATE`. Non-terminal
gate, so this is the folded retro+lessons+docs close; `G1-PLAN` follows and
drafts gate 2.

`auto_close_disabled: true` is set deliberately: the criteria below include the
`close-discipline.md` §1 fresh re-run, which makes this close load-bearing, so
the auto-close predicate must not optimize it away (#189).

**The one thing this close must not soften.** `PLAN.md` § *The oracle problem*
fixes a deferral in advance, and it exists because `[FEAT-2026-0069/G2-CLOSE]`
records a green-gated skill that emitted 30 components on its first real repo:

> *an agent following `derive-agent-policy`'s prose, run against a repository
> whose policy file it has not seen, proposes the values
> `propose_policy_defaults` computes.*

Gate 1 does not prove that and cannot. Every test here exercises the algorithm or
asserts on prose; none composes them by having an agent execute the skill. Record
the deferral in those words, with its re-run condition — one operator invocation
against this repository's own `.specfuse/agent-policy.yml`.

**Feed the open question forward.** `PLAN.md` leaves gate 2's provenance
mechanism deliberately undecided — how review distinguishes an agent-chosen
default from a deliberate operator choice. The input that should decide it is
**how many values gate 1 actually found derivable**. Report that number and what
it implies, so `G1-PLAN` drafts against evidence rather than a guess.

Closing sections are scaffolded at dispatch (`close-discipline.md` §4 and the
registry in `specfuse/loop/closing_requirements.py`) — fill them with substance
rather than re-deriving headings.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. **Oracles re-run fresh in this session** (`close-discipline.md` §1), exit
   codes read directly, never inherited from a WU's self-report: the full `code`
   gate set from `.specfuse/verification.yml`. Each command and its exit code
   recorded in `RETROSPECTIVE.md`.
2. `propose_policy_defaults` is run fresh against each shipped fixture, and the
   retrospective records, per fixture, which values were proposed and which were
   correctly withheld for lack of evidence.
3. **The derivability count is reported**: how many of the four in-scope values
   yielded a proposal on a realistic repository, and how many fell back to the
   shipped default. This is `G1-PLAN`'s input for the provenance question.
4. `RETROSPECTIVE.md` carries a `## Gate 1` heading for this gate's section —
   the exact heading `assert_retrospective_gate_section` requires. That guard
   runs AFTER dispatch, so omitting the heading costs a full re-attempt
   rather than a warning (`close-discipline.md` §4).
5. That gate-1 section carries a `## Cost analysis`
   reconciling each WU's `planned_cost_usd` against actual from `events.jsonl`
   (including re-arm cycles via `cumulative_*`), per-WU delta, and a gate total
   against the $27.00 budget. Any WU over 50% variance carries a one-paragraph
   cause.
6. `.specfuse/LEARNINGS.md` gains at least one entry, or carries an explicit
   note that nothing generalized.
7. **The named deferral is recorded verbatim** from `PLAN.md` § *The oracle
   problem*, with its re-run condition, under the scaffolded deferred-verification
   heading. A close that reports gate 1 green without it is the failure
   `[FEAT-2026-0069/G2-CLOSE]` describes.
8. **Consumer-visible contract changes** enumerated (`close-discipline.md` §3):
   the new `specfuse.loop.policy_proposals` module, the new
   `derive-agent-policy` skill, and the boundary statement added to
   `/groom-backlog` — or exactly `n/a — no consumer-visible contract change` if
   genuinely empty, which it is not.
9. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement; if an oracle fails, record it and emit `status: blocked`.
`PLAN.md`'s `status` field — the driver owns terminal flips, and this is not the
terminal gate regardless. Gate 2's work units — `G1-PLAN` drafts them.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set plus the fresh full-`code` re-run named
in criterion 1, and `specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any oracle in criterion 1 fails (record which, and its output — do not fix it
here); `propose_policy_defaults` emits a value `validate_agent_policy` rejects,
which would mean T01's central property does not hold; or `events.jsonl` lacks
the cost data criterion 5 needs.
