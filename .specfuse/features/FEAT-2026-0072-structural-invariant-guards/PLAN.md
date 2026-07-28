---
feature_id: FEAT-2026-0072
title: Structural-invariant guards — declared surfaces that nothing asserts on
slug: structural-invariant-guards
branch: feat/FEAT-2026-0072-structural-invariant-guards
roadmap_goal: Make every structural invariant this repo declares about itself enforceable by a check, so a skill without a discovery link or a done feature with an unclosed gate fails on the first run rather than drifting silently for weeks.
autonomy_default: review
status: active
planned_cost_usd: 14.00
---

# Plan: Structural-invariant guards

Three defects found in one day share one shape: **a surface the repo declares,
that nothing checks, drifting silently until something unrelated stumbles over
it.**

- **#257** — two bats suites existed and were wired into no gate. One had been red
  for weeks while CI stayed green, because CI never ran it.
- **#284** — `CLAUDE.md` states that `.claude/skills/` holds forward symlinks so
  discovery finds skills. Nothing creates them; the last were made by hand in
  June. Four skills sat invisible for seven weeks, one of them shipped the same
  day it was found.
- **#287** — three `done` features carry a terminal gate that is not `passed`, and
  `lint_plan` has no check that a done feature's gates are closed.

None was caught by a gate, because in each case the gate set did not know the
invariant existed. **#257 is already fixed**, and its guard
(`tests/test_bats_suites_gated.py`) is the working precedent this feature
generalises: assert the invariant in both directions, and make the assertion
itself falsifiable.

## Scope boundary

**IN.** The skill-discovery guard and something that creates a missing link; the
done-feature gate-consistency check in `lint_plan`; and reconciliation of the
state already on disk.

**OUT — re-solving #257.** Its guard shipped. This feature copies its shape and
leaves the file alone.

**OUT — a general invariant framework.** Two checks do not justify an abstraction
over checks. If a third and fourth arrive, that is when a shared harness earns
itself.

**OUT — the `specfuse:feature` label naming inconsistency and the seven
`.agents/skills/` links.** Both surfaced during investigation; neither is drift.
The links are operator tooling and are explicitly filtered rather than
"corrected".

## The two traps

Both are recorded because the obvious implementation is wrong in each case, and
both are the unsatisfiable-predicate shape `planning-discipline.md` §2 exists to
catch — a rule that fires on a correct tree.

**The skill-symlink check cannot be symmetric.** Seven entries in
`.claude/skills/` point at `../../.agents/skills/` — local operator tooling,
untracked. So `set(.specfuse/skills/*) == set(.claude/skills/*)` reports non-zero
on a correct tree. The guard asserts the **forward** direction completely (every
skill directory has a link resolving to it) and **filters the reverse** to links
resolving inside `.specfuse/skills/`.

**The done-feature check must exclude two features.**
`FEAT-2026-0001-health-endpoint` is `status: done` with both gates `open`, and
that is correct: it is the bundled worked-example fixture the roadmap reserves as
"the self-demonstrating reference installation a target project copies", a
template never executed and never to be. `FEAT-2026-0036-adopt-ruff-016` is `done`
with its gate `open` and its close WU still `pending`, because the roadmap records
it was "executed directly" as a config-only fix after a loop run on a flawed plan
blocked — the close ceremony deliberately never ran. Flipping its gate to `passed`
would assert a ceremony that did not happen. Both are excluded **by ID with an
inline reason**, or the likely "fix" is someone mutating a shipped fixture to
satisfy a linter.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  `grep -n 'status.*done' specfuse/loop/lint_plan.py | grep -i gate` and
  `grep -rn '\.claude/skills' scripts/*.sh specfuse/loop/scaffold.py`
- **Verdict:** `no existing mechanism, building new` — with one shape reused.

The first returns nothing: `lint_plan` validates feature dirs, PLAN frontmatter,
and the gate/WU graph, but carries no check relating a feature's `done` status to
its gates' statuses. The second returns two hits, both in `scripts/sync-scaffold.sh`
— lines 24 and 96 — and both are **comments describing the symlink contract**. The
script creates no link. So the contract is documented in two places and enforced in
none.

**Reusing the shape, not the code.** `tests/test_bats_suites_gated.py` (#257) is
the proven pattern: diff a declared set against an actual set, assert both
directions with the reverse filtered, and carry an explicit opt-out dict whose
entries require a written reason. T01 and T03 follow that shape. They do not
import from it — two checks over unrelated surfaces sharing a helper would couple
them for no gain.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero, for both new checks — **but only after this feature's reconciliation
  lands.**

This is the sharp part. On the tree as it stands today, the done-feature check
reports **three** findings (FEAT-2026-0007, FEAT-2026-0008, FEAT-2026-0036) and
the symlink check reports zero (PR #285 already restored the four links). A check
that fires on the current tree is unsatisfiable until the tree is corrected, so
T03 must land its reconciliation **in the same work unit** as the check —
0007 and 0008 flipped to `passed` because they genuinely completed, 0036 excluded
by ID because its close never ran. After that, both checks report zero on a
correct tree, and non-zero only on real drift.

## Task graph

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0072/T01
        file: WU-01-skill-symlink-guard.md
        depends_on: []
      - id: FEAT-2026-0072/T02
        file: WU-02-sync-creates-symlinks.md
        depends_on: [FEAT-2026-0072/T01]
      - id: FEAT-2026-0072/T03
        file: WU-03-done-feature-gate-check.md
        depends_on: []
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0072/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0072/T01
          - FEAT-2026-0072/T02
          - FEAT-2026-0072/T03
```

T03 is independent of T01 and T02: the two invariants are over unrelated surfaces
and share no code. T02 depends on T01 so the guard exists before the thing that
must satisfy it.

## Notes

- T02 modifies `scripts/sync-scaffold.sh`, a committed operator script, so
  `/authoring-work-units` §11 applies: `shellcheck` clean, `bash -n` parses, and a
  bats happy-path test. Both tools are present locally and `shellcheck` is not in
  `verification.yml`'s gate set, so the WU names it as a unit-specific check.
- Any new bats suite this feature adds must also be registered in
  `verification.yml` — `tests/test_bats_suites_gated.py` (#257) will fail
  otherwise. That is the precedent guard doing its job on this feature's own work,
  which is the point.
