---
id: FEAT-2026-0114/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces_driver_helper:
  - collect_produces_dropped
produces:
  - specfuse/loop/judge.py
  - tests/test_judge_sees_dropped_produces.py
---

# A dropped deliverable is evidence the judge reads

**Objective.** Put every `produces_dropped:` entry of the gate's units into the
judge's evidence bundle, so a criterion that depended on a dropped path is
judged against the drop and its reason rather than against a silent edit.

**Context.** FEAT-2026-0114/T03. `build_judge_bundle` in `specfuse/loop/judge.py`
assembles the gate's definition of done, the parsed `GATE-NN-CRITERIA.md`
entries, the gate diff and `## Measurements`, each capped at 8,000 characters.
Add `collect_produces_dropped(feature_dir, gate_n)` that reads each unit file
in the gate's graph and returns `[(unit_id, path, reason)]` from
`produces_dropped:` frontmatter; render it as one more bundle section,
`## Deliverables dropped by amendment`, with the literal line `(none)` when
empty, under the same cap. The judge prompt already instructs the judge to lower
on evidence it can see; no prompt-text change beyond naming the section.

**Acceptance criteria.**

1. `tests/test_judge_sees_dropped_produces.py` fails on HEAD before this unit's
   edits (the module is absent); after,
   `python3 -m unittest tests.test_judge_sees_dropped_produces -v -b` exits 0.
2. That module asserts on a temp feature dir with one unit carrying
   `produces_dropped:` that the bundle text contains the section heading, the
   unit id, the path and the reason; and that a feature with no drops renders
   the section with `(none)`.
3. `python3 -m unittest tests.test_judge_module tests.test_judge_close_path tests.test_judge_path_registry -v -b`
   exits 0 with no edit to those modules.

**Do not touch.** `loop.py` (T01/T02 own the driver side); the lower-only rule
and `judge_close`; `.specfuse/rules/` and `docs/` (T04); plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the bundle's per-section
cap would truncate the new section on a realistic gate (say at how many drops);
or if `JUDGE_PATHS` (test_judge_path_registry) would need a new entry this unit
is not allowed to add.
