---
id: FEAT-2026-0039/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
---

# Gate 1 plan-next — draft gate 2 (the derive-monitoring skill)

**Objective.** Author gate 2's substantive WU files (the design-for-diagnosis rule,
the component-discovery reference implementation, the `derive-monitoring` skill,
and the fenced-block drift test), add them to `PLAN.md`'s gate-2 `work_units` graph
with `depends_on`, set `G2-CLOSE`'s `depends_on`, and write `GATE-02-REVIEW.md`.
Leave every drafted WU `status: draft` (unarmed).

**Context.** This is `FEAT-2026-0039/G1-PLAN`, following G1-CLOSE-INTERMEDIATE.
Gate 1 shipped the machine-checkable contract: `validate_monitoring`, the shipped
example, the schema doc, the shim, the seed, and the `monitoring-example-lint`
gate. Gate 2's job is the authoring surface — the skill that produces a
`monitoring.yml` which passes that validator.

Read `PLAN.md`'s `roadmap_goal`, its **Gate 2 sketch** section (four decisions
already made — treat them as constraints, not suggestions), its
escalation-predicate section, `GATE-02.md`'s definition of done, and gate 1's
`RETROSPECTIVE.md`. Then read the real files gate 2 will touch, so the drafted WUs
name actual surfaces rather than invented ones:

- `.specfuse/skills/derive-verification/SKILL.md` — the posture `derive-monitoring`
  mirrors (evidence first, ask only what code cannot answer, draft never
  auto-write). Read it before drafting the skill WU.
- `tests/test_roadmap_add_skill.py` and `tests/test_roadmap_archive_skill.py` —
  this repo's established shape for testing an interactive skill: a reference
  implementation of the deterministic algorithm, unit-tested. The discovery WU
  follows it.
- `.specfuse/rules/planning-discipline.md` and `close-discipline.md` — the two
  rules that live in `.specfuse/rules/` **without** being `@`-imported into
  `CLAUDE.md`. `design-for-diagnosis.md` takes the same posture.
- `plugins/specfuse/skills/` — canonical home for skill sources; `.specfuse/skills/`
  is the synced copy. A skill edited in the wrong one fails the sync suite.

Reference the binding rules under `.specfuse/rules/`; honor them. The driver owns
all git.

**Acceptance criteria.**

1. Gate 2's substantive WU files are authored in this feature folder in
   dispatchable form (five sections, `status: draft`, `planned_cost_usd`), each
   tracing to `GATE-02.md`'s definition of done. Expected shape, to be refined
   against what gate 1 actually shipped: the design-for-diagnosis rule; the
   discovery reference implementation plus its repo-tree fixture; the
   `derive-monitoring` skill plus its local-runner bootstrap artifacts; the
   fenced-`yaml`-block drift test. Whether the bootstrap artifacts ride with the
   skill WU or split into their own is this WU's call — state the reasoning in the
   review.
2. `PLAN.md`'s gate-2 `work_units` list is filled with the drafted WUs' ids, files,
   and `depends_on`; `G2-CLOSE`'s `depends_on` lists all gate-2 substantive WUs.
3. **`GATE-02-REVIEW.md`** written, weighted toward doubt: decisions and rationale,
   open risks, and a verification story per drafted WU. Three risks must be
   addressed explicitly, not left implicit:
   (a) the fixture is stylized — say what passing it does and does not prove about
   a real backend;
   (b) stack-specific detection leaking into what must stay provider-agnostic —
   name the boundary and how the drafted tests hold it;
   (c) the skill's interview quality has no in-loop oracle at all — say so.
4. Each gate-2 WU introducing new behavior carries a red-test-first acceptance
   bullet naming a specific test that fails on HEAD, or an explicit §12 exemption
   with a one-line rationale.
5. **The diagnosability audit's findings are drafted as WARN, not ERROR.**
   `PLAN.md` records why (a populated codebase predating the rule violates it
   everywhere by construction, making an ERROR predicate unsatisfiable on real
   input — `[FEAT-2026-0015/G2-CLOSE]`). The drafted WU must honor it; a drafted
   ERROR predicate fails this criterion.
6. **The skill WU names the `.claude/skills/` symlink as an operator-side
   pre-dispatch prerequisite**, not agent work. Claude Code's sandbox lists
   `.claude/skills` under `denyWithinAllow` — a deny rule inside an allow scope that
   survives `unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`). A WU drafted without
   this split will burn an attempt rediscovering the boundary.
7. **`G2-CLOSE` carries the `## Cost analysis` and `## What the loop did NOT
   verify` AC bullets**, and the latter is drafted to require naming the live run
   against a real multi-component backend as post-merge operator work, with the
   exact re-run condition that would upgrade it from deferred to verified.
8. **No arming** — gate 2's WUs stay `draft`. The human reviews
   `GATE-02-REVIEW.md` and arms them at the gate boundary.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (the driver owns gate
flips); the gate-2 surfaces themselves — `.specfuse/rules/design-for-diagnosis.md`,
the skill files, the fixture (gate 2's WUs create those; `plan-next` only DRAFTS
the WUs, it does not implement them); `.git/`, secrets. May create gate-2 WU files,
`GATE-02-REVIEW.md`, and edit `PLAN.md`'s gate-2 graph and `G2-CLOSE`'s
`depends_on`. See `.specfuse/rules/never-touch.md`.

**Escalation triggers.** Emit `status: blocked` if gate 1 shipped a schema
materially different from what `PLAN.md`'s gate-2 sketch assumes — drafting the
skill against a schema that no longer exists produces WUs that block on their first
attempt. Also block if the discovery algorithm cannot be factored into a
deterministic, testable reference implementation at all (if every part of discovery
turns out to require model judgment), because then gate 2's verification story
collapses to structural-only and that is a human decision about the feature's
worth, not a drafting choice to make silently. Blocked is respectable
(`result-contract.md` rule 4).

**Verification.** The `plannext` gate set the driver runs for `type: plan-next`,
plus `assert_next_gate_drafted_or_terminal` (gate 2's WUs exist and are drafted)
and the lint of the updated `PLAN.md` graph.
