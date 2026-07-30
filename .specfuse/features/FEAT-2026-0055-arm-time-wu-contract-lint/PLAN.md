---
feature_id: FEAT-2026-0055
title: Arm-time WU contract lint — produces satisfiability + boundary consistency
slug: arm-time-wu-contract-lint
branch: feat/FEAT-2026-0055-arm-time-wu-contract-lint
roadmap_goal: Refuse or warn on WU-contract defects at arm time instead of after burned attempts — a produces path the WU's own Do-not-touch forbids is un-armable (ERROR), a produces path an earlier done WU already delivered is flagged (WARN), and the two deliverable gates' path semantics are unified so one declaration form satisfies both.
autonomy_default: review
status: done
planned_cost_usd: 27.00
---

# Plan: arm-time WU contract lint

**Evidence base (portfolio review, 2026-07-30).** Produces/deliverable contract mismatches cost
~$55 across the portfolio (`produces_not_in_diff` $27.7, `no_deliverable_files` $13.1,
`deliverable_missing` $14.4), all discovered post-attempt. The canonical case:
FEAT-2026-0066/T04 burned $11.43 over 3 attempts plus a human escalation on a `produces:` path
that (a) T03 had already fully delivered and (b) T04's own Do-not-touch barred it from touching —
unsatisfiable by construction, derivable from the WU files alone before any dispatch. The
literal-vs-glob split between the two deliverable gates is documented only in folklore comment
blocks that features copy into every WU (`FEAT-2026-0065/T01 paid two cycles / 6 attempts /
$10.43 learning this — do not re-derive it`).

**Companion to FEAT-2026-0054.** 0054 made the *closing*-format guards pre-satisfied and
lint-checkable in-session; this feature does the same for the *per-WU deliverable* contract, at
the arm boundary. Same durable rule ([FEAT-2026-0070]): the earlier enforcement point names the
later one — every new lint finding names the post-attempt guard that would otherwise fire.

## Existing-mechanism search (planning-discipline.md §1)

Run at draft time (2026-07-30), against merged main + 0054:

| Command | Verdict |
|---|---|
| `grep -n "def check_\|def lint" specfuse/loop/lint_plan.py` | `check_*` + `lint(feature_dir)` aggregator convention exists — **add checks there, no new tool**. |
| `grep -n "_slice_section" specfuse/loop/lint_plan.py` | Section extractor exists (`:142`) — **reuse for Do-not-touch parsing**. |
| `grep -n "def assert_declared_deliverables\|def assert_produces_in_diff" specfuse/loop/loop.py` | The dual-semantics pair at `loop.py:4519` (literal existence) and `:4548` (literal or fnmatch vs diff) — **unify, do not add a third gate**. |

Verdict: everything extends existing surfaces. New logic: two lint checks + one semantics
unification.

## Design decisions

- **WARN vs ERROR split (deliberate softening of the roadmap text).** "Already delivered by an
  earlier WU" is WARN — iterative shared-file edits are legitimate (0066's T05/T07 re-touched
  `reconcileListProperty.mustache` across WUs by design). "Inside own Do-not-touch" is ERROR —
  no legitimate WU declares a deliverable it is forbidden to write. T04's deadlock was the
  conjunction; the ERROR leg alone makes it un-armable.
- **Expected self-WARN.** Within this very feature, T02's `produces:` includes
  `specfuse/loop/lint_plan.py`, which T01 (by then `done`) also declares — the new WARN will
  fire on its own feature. That is the rule working, not a defect; T02's body states the
  incremental edit, which is exactly the authoring response the WARN message prescribes.

## Escalation-predicate satisfiability

The ERROR rule asserts on WU-authoring shape, not on any external input, and must report zero on
every existing conformant feature: the acceptance criteria require running the new lint over all
current feature folders in this repo and showing zero ERROR findings (WARNs are expected and
enumerated). If any existing feature ERRORs, the rule is wrong or the feature is — T02 stops and
escalates rather than shipping a lint that fails the tree it lands in.

## Scope boundary

**IN.** `check_produces_satisfiability` (WARN) and `check_produces_boundary` (ERROR) in
`lint_plan.py`; unified path semantics for `assert_declared_deliverables` /
`assert_produces_in_diff`; folklore-comment deletion from `WU.template.md`; arm-time references
in the `arm-gate` and `authoring-work-units` skills.

**OUT.**
- Closing-ceremony surfaces — FEAT-2026-0054 shipped them.
- Per-criterion DoD state — FEAT-2026-0056. Oracle contract — FEAT-2026-0057.
- Semantic AC validation (does the WU make sense) — lint checks contract shape only.
- Auto-fixing WU files. The lint names defects; authors fix them.

## Gate shape (1 gate — ceremony proportionality, docs/methodology.md §6)

Four substantive WUs: single gate, single terminal `close`.

## Gate graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0055/T01
        file: WU-01-produces-satisfiability-warn.md
        depends_on: []
      - id: FEAT-2026-0055/T02
        file: WU-02-boundary-consistency-error.md
        depends_on: [FEAT-2026-0055/T01]
      - id: FEAT-2026-0055/T03
        file: WU-03-unify-produces-semantics.md
        depends_on: [FEAT-2026-0055/T02]
      - id: FEAT-2026-0055/T04
        file: WU-04-surfacing-and-boilerplate-deletion.md
        depends_on: [FEAT-2026-0055/T03]
      - id: FEAT-2026-0055/T05
        file: WU-05-boundary-extraction-fix.md
        depends_on: [FEAT-2026-0055/T04]
      - id: FEAT-2026-0055/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0055/T05]
```

## Notes

- Correlation IDs: `FEAT-2026-0055/TNN`; commit trailer `Feature: FEAT-2026-0055/TNN`.
- Canonical prose surfaces per the 0054/T04 lesson: `.specfuse/` (rules/templates) and
  `plugins/specfuse/skills/` (skills) are canonical; `specfuse/loop/data/` is the sync mirror.
- Portfolio success measure (verified downstream, not here): `produces_not_in_diff` /
  `no_deliverable_files` / `deliverable_missing` attempts at zero on the next generator-class
  feature run under a driver carrying this feature.
