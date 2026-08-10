---
id: FEAT-2026-0048/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles: [oracles]
---

# Close FEAT-2026-0048 — terminal gate

**Objective.** Close the feature: re-run every oracle fresh, prove the
guardrails actually hold, reconcile cost, write the retrospective and lessons,
enumerate consumer-visible contract changes, and record an honest verdict.

**Context.** Correlation ID `FEAT-2026-0048/G1-CLOSE`. Terminal close of a
single-gate feature. Depends on T01–T04.

`auto_close_disabled: true` is set deliberately: this close re-runs oracles per
`close-discipline.md` §1, which makes it load-bearing (#189).

**This close carries one obligation the others do not: proving that the thing
that can merge code does not merge code it shouldn't.** The feature's whole risk
argument rests on three claims, and a close that only writes prose verifies
none of them. Re-test all three in this session, from the shipped code:

1. The dial ships `off`, and this repo's `.specfuse/agent-policy.yml` still has
   `rules.bugs.automerge: off`.
2. The predicate fails closed on malformed input.
3. `JUDGE_PATHS` is imported, not copied, so a fix touching the driver, the
   rules, CI workflows, or the verification config cannot auto-merge.

**Also record honestly**, because the next reader will not infer them:

- This feature was **drafted solo, with no operator interview** (operator
  instruction, 2026-08-09). `PLAN.md` § *Assumed decisions* lists seven
  decisions taken without a human — state which the implementation validated,
  which it strained, and which are unexercised.
- This feature was **drafted before FEAT-2026-0044 shipped the schema it builds
  on**. Record what T01 found: whether the shipped schema matched the assumed
  table, and if not, what diverged and what it cost.

The closing sections are scaffolded at dispatch (`close-discipline.md` §4 and
the registry in `specfuse/loop/closing_requirements.py`) — fill them with
substance rather than re-deriving the headings.

Binding rules apply by reference: `result-contract.md`, `close-discipline.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. **Oracles re-run fresh in this session** (`close-discipline.md` §1), exit
   codes read directly: the full `code` gate set from
   `.specfuse/verification.yml` — `tests`, `lint`, `security`, `coverage`,
   `leak-scan`, `event-type-gate`, `roadmap-link-gate`, `arm-sweep-gate`,
   `monitoring-example-lint`, `agent-policy-example-lint`. Each command and its
   exit code recorded in `RETROSPECTIVE.md`.
2. **Guardrail claim 1 re-tested:** `resolve_bug_automerge()` against this
   repo's live `.specfuse/agent-policy.yml` returns `False`. Recorded.
3. **Guardrail claim 2 re-tested:** `evaluate_merge_guardrails` is called in
   this session with malformed input for each of its inputs and returns
   `eligible=False` without raising in every case. Recorded.
4. **Guardrail claim 3 re-tested:** `specfuse.loop.bug_lane.JUDGE_PATHS is
   specfuse.loop.arm_eval.JUDGE_PATHS` evaluates `True` in a fresh interpreter.
   Recorded.
5. **The composite oracle** no individual WU could run: with the dial forced
   `on` in a temporary in-memory policy, a PR fixture failing exactly one
   guardrail does not merge — repeated for all six. This is the feature-level
   assertion that all four WUs compose correctly, and it is the one that would
   catch every WU passing individually while the lane still merges something it
   should not.
6. `RETROSPECTIVE.md` exists with a `## Cost analysis` section reconciling each
   WU's `planned_cost_usd` against actual from `events.jsonl` (including re-arm
   cycles via `cumulative_*`), per-WU delta, gate total against the $26.00
   budget, and feature total against `PLAN.md`'s $21.00. Any WU over 50%
   variance carries a one-paragraph cause.
7. `RETROSPECTIVE.md` records the two feature-specific items in this WU's
   Context: the solo-drafting decision audit (all seven), and what T01 found
   about the schema it was drafted against.
8. `.specfuse/LEARNINGS.md` gains at least one entry, or an explicit note that
   nothing generalized. If drafting two dependent features in one unattended
   session produced a durable lesson, it belongs here.
9. **Consumer-visible contract changes** enumerated (`close-discipline.md` §3):
   the two new `rules.bugs` dials, the new `specfuse/loop/bug_lane*.py` modules,
   the `/fix-bug` lane gaining a triaged-issue intake, and the new
   `<!-- specfuse:bug-automerge -->` marker on merged PRs — or exactly
   `n/a — no consumer-visible contract change` if genuinely empty, which it is
   not.
10. Documentation reflects what shipped: the roadmap's FEAT-2026-0048 detail
    section describes the delivered shape, and the row and detail status agree.
11. A verdict is recorded. `met` only if every acceptance criterion across
    T01–T04 was verified in-loop. Otherwise `met_locally` / `partially_met` with
    a `## Hedged-verdict follow-up record` carrying, per unmet criterion, the
    criterion verbatim, why it is unverifiable here, the exact re-run condition
    that would upgrade it, and a `kind:` written as `- **kind:** \`<value>\``.
12. `## What the loop did NOT verify` lists every deferred criterion with where
    it actually gets checked, or exactly
    `(nothing — every acceptance criterion was verified in-loop)`. **A live
    auto-merge against a real PR is expected to appear here** — this feature
    never turns the dial on, so the end-to-end merge path is an
    operator-deferred oracle, not an in-loop one. Naming it honestly is required.
13. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this close verifies, it
does not implement; if an oracle fails, record it and emit `status: blocked`.
`.specfuse/agent-policy.yml` — the dial stays `off`; a close session must not
flip it to make an oracle greener. Other features' folders. `.specfuse/rules/`.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

Do **not** write `PLAN.md`'s `status` field — the driver owns the terminal flip
(`fire_terminal_flips`, gated on the verdict).

**Verification.** The `plannext` gate set plus the fresh full-`code` re-run in
criterion 1, the three guardrail re-tests in criteria 2–4, the composite oracle
in criterion 5, and `specfuse lint --closing`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any oracle in criterion 1 fails; **any of the three guardrail claims in criteria
2–4 does not hold** — that is a feature that must not ship as-is, and the
verdict is `not_met`, not a hedge; the composite oracle in criterion 5 shows a
merge reachable with a guardrail failing; `events.jsonl` lacks the cost data
criterion 6 needs; or T01 recorded a schema divergence whose consequences reach
further than this feature.
