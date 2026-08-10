---
id: FEAT-2026-0076/G2-CLOSE
type: close
status: done
attempts: 1
verdict: met_locally
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
model: opus
effort: high
gate_set: plannext
driver_version: 0.10.0
started_at: 2026-08-10T16:52:49.451088+00:00
duration_seconds: 1081.033
cost_usd: 11.136132
input_tokens: 3772
output_tokens: 66925
---

# Close FEAT-2026-0076 — terminal gate

**Objective.** Terminal close: re-run every oracle fresh, reconcile feature cost,
write the retrospective and lessons, enumerate consumer-visible contract changes,
and record an honest verdict.

**Context.** Correlation ID `FEAT-2026-0076/G2-CLOSE`. Placeholder drafted at
feature-drafting time so the linter reads gate 1 as non-terminal; `G1-PLAN`
updated its `depends_on` to the three substantive work units it inserted above
this entry — `T04` (`review_agent_policy`), `T05` (the review-mode prose), `T06`
(the non-clobber fence) — and filled in the criteria below.

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

**The mechanism `G1-PLAN` chose**, so this close can judge it rather than
re-derive it: comparison against the **shipped baseline** —
`agent_policy.DEFAULT_*` where a constant exists, `.specfuse/agent-policy.yml.example`
where one does not — with the lossy direction disclosed in the output as a
caveat. Reasoned from gate 1's derivability count in `GATE-02-REVIEW.md` §
*The provenance question*. **No schema change was taken**, so `PLAN.md`'s scope
boundary stands unwidened; the provenance-recording alternative was filed as a
successor feature rather than folded in. If gate 2's implementation crossed that
boundary anyway, say so plainly — a silently widened scope is the failure the
review artifact's criterion 3 exists to prevent, and this close is where it
would surface.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. **Oracles re-run fresh** (`close-discipline.md` §1): the full `code` gate set
   from `.specfuse/verification.yml` executed in this session, each exit code
   read directly from the process, never inherited from a producing WU's
   self-report. Plus the scoped runs T04/T05/T06 name and the symbol-existence
   check `python3 -c "from specfuse.loop.policy_review import review_agent_policy"`.
2. **`review_agent_policy` re-run fresh against a fixture per provenance class**
   — baseline-match, baseline-differ, key-absent, baseline-unavailable — with
   its return value observed directly rather than inferred from a green test.
   This is gate 1's close pattern, and it is what made T01's silent withholding
   visible; the classification is the thing gate 2 shipped, so the close should
   watch it run.
3. **Whether the chosen provenance mechanism held up**, in prose: whether the
   shipped-baseline comparison covered all four in-scope keys in practice,
   whether the lossy direction stayed disclosed at the output, and whether
   anything in implementation argued for the provenance-recording shape after
   all. A recommendation either way, with what gate 2 observed as the reason.
4. **Whether the disjoint-key boundary survived** — `queue` written by neither
   `review_agent_policy` nor the skill's review-mode prose, evidenced by T04's
   criterion 8 and T06's suite re-run in this session.
5. **A `## Cost analysis`** reconciling per-WU planned against actual across
   both gates, and a feature total against `PLAN.md`'s `planned_cost_usd` of
   **$38.50** and `GATE-02.md`'s `cost_budget_usd` of **$19.50**. Gate 1's close
   already reported implementation spend running ~40% of estimate on this
   feature; note whether gate 2 repeated that pattern, since two gates is the
   first point at which it is a trend rather than an anecdote.
6. **The inherited deferral recorded with its re-run condition** — see the
   verbatim text above. A `met` verdict requires that claim to have actually
   been tested, not assumed.
7. **Consumer-visible contract changes enumerated** (`close-discipline.md` §3):
   at minimum `specfuse.loop.policy_review` as a new importable module and the
   review mode added to the published `/derive-agent-policy` skill, or exactly
   `n/a — no consumer-visible contract change` if neither shipped.
8. **Per-criterion state** (`close-discipline.md` §5) written into gate 2's
   criteria artifact if one exists, `kind` and `state` per entry, never inferred.
9. **A verdict recorded**, `met` only if every acceptance criterion across both
   gates was verified in-loop; hedged otherwise, with the §2 follow-up record
   and a `kind:` per entry.
10. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement. `PLAN.md`'s `status` field: the driver owns the terminal flip
(`fire_terminal_flips`, gated on the verdict). Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set plus a fresh full-`code` re-run and
`specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
any oracle fails, if the inherited deferral cannot be honestly recorded, or if
`events.jsonl` lacks the cost data the analysis needs.
