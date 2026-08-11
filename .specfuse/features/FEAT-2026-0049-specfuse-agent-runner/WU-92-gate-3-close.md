---
id: FEAT-2026-0049/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
# AC5 writes CHANGELOG.md — a surface outside this feature's folder, which makes
# this close load-bearing. Without this flag `evaluate_auto_close` may skip the
# WU at attempts: 0 and every criterion below would go unfulfilled. Under
# `autonomy_default: auto` that is not hypothetical. See close-discipline.md, #293.
auto_close_disabled: true
---

# G3-CLOSE — terminal close (placeholder)

**Context.** Gate 3 is the feature's terminal gate, so its closing sequence is a
single `close` work unit collapsing retrospective, lessons, docs, and the
feature's terminal verdict into one session.

This file is scaffolded at draft time for one structural reason: the linter
treats the last non-empty gate as terminal, so without an entry here gate 1 would
be misread as terminal and its `close-intermediate` → `plan-next` sequence
rejected. It stays `status: draft` — unarmed — until gate 3 is really drafted.

`G2-PLAN` drafts gate 3's substantive work units above this entry, sets this
unit's real `depends_on`, and sharpens the criteria below against what gate 3
actually built rather than against this draft's guess.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Cost analysis` section reconciling every
   gate's actual spend against its `cost_budget_usd`, read from `events.jsonl`
   and WU frontmatter rather than estimated.
2. `RETROSPECTIVE.md` carries a `## What the loop did NOT verify` section naming
   every auto-close debt marker left by an earlier gate, plus each acceptance
   criterion not verified in-loop with the reason and where it actually gets
   checked — or the explicit
   `(nothing — every acceptance criterion was verified in-loop)` line.
3. The feature's terminal `verdict` is written to this unit's frontmatter and is
   one of `met` / `met_locally` / `partially_met` / `not_met`. On a hedged
   verdict, every follow-up entry carries a valid `kind:`.
4. Generalizable lessons are staged in `LEARNINGS-pending.md` in this feature
   folder. Under `autonomy_default: auto`,
   `assert_learnings_staged_under_auto` forbids touching
   `.specfuse/LEARNINGS.md`, and `close-b` accepts the staged file as satisfying
   evidence — so do not write "nothing generalizes" unless nothing actually does.
5. Consumer-visible contract changes are enumerated, and `CHANGELOG.md`'s
   `Unreleased` section carries a matching entry — `specfuse-agent` is a new
   console script, so the enumeration is not expected to be the `n/a` line.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source — a closing unit records, it does not
fix. `.specfuse/LEARNINGS.md` (staging file only, per AC4). `.specfuse/roadmap.md`
and `PLAN.md`'s `status` field — the driver owns the terminal flips via
`fire_terminal_flips`; do **not** add an acceptance criterion flipping
`PLAN.md status` to `done`.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0 and
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing.

**Escalation triggers.** If the terminal verdict would be `met` while any gate
left an unreconciled auto-close debt marker, stop — that combination is what
`assert_autoclose_debt_reconciled` refuses after dispatch, and reaching it means
the debt was never addressed. If cost reconciliation cannot complete because
`events.jsonl` rows are missing for some WU, name the WU rather than estimating:
#1024 records that those rows can be lost between a squash and the next
bookkeeping commit.
