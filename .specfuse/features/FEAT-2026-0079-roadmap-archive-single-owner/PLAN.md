---
feature_id: FEAT-2026-0079
title: One owner for the roadmap-archive algorithm
slug: roadmap-archive-single-owner
branch: feat/FEAT-2026-0079-roadmap-archive-single-owner
roadmap_goal: One operation behaves one way whether the driver or a human runs it — the roadmap-archive algorithm gets a single owner and the skill delegates to it.
autonomy_default: review
status: planned
planned_cost_usd: 14.00
---

# Plan: One owner for the roadmap-archive algorithm

`auto_archive_feature` (`specfuse/loop/loop.py`) and the `/roadmap-archive` skill are
two implementations of one algorithm — the driver's own docstring says so: *"Re-implement
roadmap-archive single-feature algorithm (Steps 1–6) in-driver."* #1169 taught the driver
to reconcile a moved section's cross-references and its `**Status:**` marker; the skill
was deliberately left untouched to keep that PR inside bug scope. The two now describe
different behaviour for the same operation, and the skill is the path a **human** takes,
so an operator following its prose reproduces the defect the driver no longer has — on
rows an unrelated feature owns, which is the part of #1169 that landed the failure on the
wrong person.

This feature removes the drift surface rather than re-syncing it. The driver keeps the
algorithm; the skill stops describing it and invokes it. Promoted from #1183 after the
bug lane refused it three times — correctly: the resolution is a design choice spanning
a new CLI surface and a vendored skill, not a bug-sized fix.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -rn "auto_archive_feature" specfuse/ .specfuse/scripts/` and
  `grep -n "Re-implement\|re-implement\|same algorithm as" specfuse/loop/*.py`
- **Verdict:** `found auto_archive_feature (specfuse/loop/loop.py:3928), reusing`. It is the
  complete algorithm including `_reconcile_moved_section` (loop.py:3884), and it is **not
  reachable from any CLI** — its only caller is `fire_terminal_flips` (loop.py:4290). This
  feature builds no new archiving logic; it exposes what exists and points the skill at it.
- The same grep found exactly one other driver-side re-implementation claim, and it is a
  counter-example: `policy_proposals.py:18` documents that it *does not* re-implement
  `agent_policy`'s constants/validator. So this is a one-instance problem, not a class needing
  a sweep.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to blocking, and asserts
no "zero issues" close predicate.

## Scope boundary

**In:** a CLI entry point for the existing archiver; a `.specfuse/scripts/` re-export shim;
rewriting the skill's Steps 2–5 to invoke it; a structural guard that the mechanics-prose
cannot return; the LEARNINGS rule recording the settlement.

**Out, deliberately:**

- **A `--auto` batch mode on the CLI.** The skill keeps `--auto`'s selection loop *and its
  confirmation prompt*, calling the CLI once per feature. Moving the loop into the driver
  also moves the confirmation, and an unattended batch archiver that never asks is a
  materially riskier thing than what exists today. Follow-up if the per-feature loop proves
  clumsy in practice.
- **A `pyproject.toml` console script.** `pyproject.toml` is both a judge path and a
  dependency manifest, so an entry point there fires `judge_editing` *and*
  `decision_class_paths` for no functional gain. Invocation is
  `python3 -m specfuse.loop.roadmap_archive` or the shim — exactly how `gate_eval` is reached,
  which is likewise not a console script.
- **Any change to the archiving algorithm itself.** Behaviour is held constant; only its
  reachability and its single owner change.
- **A binding rule in `.specfuse/rules/`.** Considered and rejected at drafting: this is a
  call about how *this* repo's driver and skills relate, not a methodology contract binding on
  every downstream consumer, and `.specfuse/rules/` is a judge path that would cost an arming
  stop to write.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0079/T01
        file: WU-01-archive-cli-entry.md
        depends_on: []
      - id: FEAT-2026-0079/T02
        file: WU-02-skill-delegates-to-cli.md
        depends_on: [FEAT-2026-0079/T01]
      - id: FEAT-2026-0079/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0079/T01, FEAT-2026-0079/T02]
```
