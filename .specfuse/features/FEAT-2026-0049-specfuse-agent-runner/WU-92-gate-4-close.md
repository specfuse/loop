---
id: FEAT-2026-0049/G4-CLOSE
type: close
status: pending
attempts: 1
planned_cost_usd: 5.00
# AC6 writes CHANGELOG.md — a surface outside this feature's folder, which makes
# this close load-bearing. Without this flag `evaluate_auto_close` may skip the
# WU at attempts: 0 and every criterion below would go unfulfilled. Under
# `autonomy_default: auto` that is not hypothetical: gates 1 and 2 both
# auto-closed at attempts: 0 and left 57 criteria unreconciled between them.
# See close-discipline.md, #293.
auto_close_disabled: true
---

# G4-CLOSE — the terminal close

**Context.** `FEAT-2026-0049/G4-CLOSE`. Gate 4 is the feature's terminal gate, so
its closing sequence is a single `close` work unit collapsing retrospective,
lessons, docs, and the feature's terminal verdict into one session.

**Drafted by `G1-PLAN`, renumbered from `G3-CLOSE` by `G2-PLAN`, and sharpened by
`G3-PLAN` (2026-08-11)** against what the feature actually built rather than
against `G1-PLAN`'s guess at it. `GATE-04-REVIEW.md` § "The terminal close,
sharpened" records what changed and why.

This close inherits an unusually specific set of obligations because three gates
before it wrote down exactly what they could not discharge. Read
`RETROSPECTIVE.md` § "What the loop did NOT verify (gate 3)" first — it names,
per criterion, what gate 3 met only against fixtures and what no close session
can ever reconcile. Nothing below asks you to re-derive that list; it asks you to
carry it correctly.

**Acceptance criteria.**

1. **The oracles re-run fresh, in this session** (`close-discipline.md` §1), exit
   codes read directly and never inherited from a producing WU's self-report:
   the full `code` gate set, plus the gate-4 test modules scoped
   (`tests.test_agent_queue_read`, `tests.test_agent_driver_invoke`,
   `tests.test_agent_provider_feature`). `RETROSPECTIVE.md` records each command
   and its observed result.
2. `RETROSPECTIVE.md` carries a `## Cost analysis` section reconciling every
   gate's actual spend against its `cost_budget_usd`, read from `events.jsonl`
   and WU frontmatter rather than estimated. Four gates, four budgets: $36.00,
   $45.50, $38.50, $29.50.
3. `RETROSPECTIVE.md` carries a `## What the loop did NOT verify` section that
   **names gate 1, gate 2 and gate 3 explicitly**, plus gate 4's own deferrals.
   The guard reads only the **last** such section in the file, so this one
   supersedes gate 3's the moment it is written — every earlier gate's deferrals
   must be carried into it, not left behind in a section that is no longer the
   record.

   **Reconcile every outstanding `specfuse:autoclose-debt` marker in
   `RETROSPECTIVE.md`**, by gate number, whatever the count is when this WU runs.
   Two are open as drafted — **gate 1: 27 criteria; gate 2: 30 criteria** — and
   gate 3's close already reconciled both, so the work here is to carry that
   reconciliation forward with its evidence, not to redo it. Gate 3 left no
   marker (its close ran rather than auto-closing) but must still be named, for
   the superseding reason above. `assert_autoclose_debt_reconciled` searches this
   section for each marked gate number and refuses the pass **after** dispatch,
   so a missing gate number costs a full re-attempt: write the numbers literally,
   never as "every earlier gate".

   For each criterion, state whether it has since been verified and by what, or
   that it remains unverified. **A criterion still unverified is a legitimate
   outcome; recording it as verified without a run is not.**
4. The feature's terminal `verdict` is written to this unit's frontmatter and is
   one of `met` / `met_locally` / `partially_met` / `not_met`. On a hedged
   verdict, every follow-up entry carries a valid `kind:`. Three groups already
   have their `kind` decided by the close that met them, and this WU carries them
   rather than re-deciding:

   - gate 3's ten fixture-only criteria (`RETROSPECTIVE.md` § "Gate 3 — the
     criteria met only against fixtures") — `externally-verifiable-later`, with
     the live condition each already names;
   - the eleven red-before-green halves (T01#1 … T11#1, and T12#1–T14#1 if gate 4
     inherits the same shape) and the four no-file-under-`specfuse/loop/`-was-
     edited diff claims (T06#2, T07#2, T10#2, T11#2) — `inherent`, because both
     need `git` and a close session runs no `git` command by contract, so no
     future close can discharge them either;
   - **gate 4's own criteria, met entirely against fixture feature folders and an
     injected runner** — `externally-verifiable-later`, condition: one
     `specfuse-agent run` against a repository whose `queue:` top is a feature
     other than this one.
5. Generalizable lessons are staged in `LEARNINGS-pending.md` in this feature
   folder. Under `autonomy_default: auto`, `assert_learnings_staged_under_auto`
   forbids touching `.specfuse/LEARNINGS.md`, and `close-b` accepts the staged
   file as satisfying evidence — so do not write "nothing generalizes" unless
   nothing actually does. `LEARNINGS-pending.md` already holds gate 3's four;
   append rather than overwrite.
6. Consumer-visible contract changes are enumerated, and `CHANGELOG.md`'s
   `Unreleased` section carries a matching entry. The enumeration is **not** the
   `n/a` line — `GATE-04-REVIEW.md` § "The terminal close, sharpened"
   pre-populates it so this session does not rediscover it from the diff:
   the `specfuse-agent` console script; its
   `--repo` / `--policy` / `--features-root` / `--monitoring-config` /
   `--max-minutes` / `--max-tokens` / `--max-items` flags; and the behaviour
   change to `default_providers()` that makes an unattended `specfuse-agent run`
   dispatch the gate driver. That last one is a change to an existing command
   rather than an addition, and is the entry most likely to be missed.
7. **Say plainly whether the feature was ever shown to do what it was funded to
   do.** No `specfuse-agent run` has executed against live repository state at
   any point in gates 1–4; every behaviour is proven by test against injected
   runners. `RETROSPECTIVE.md` states that as a headline, not a footnote, and
   separates "not proven" from "disproven" — see `operator-escalation.md`
   § "The feature briefing". Two standing findings belong in the same place:
   `reconcile` was called by six providers across four gates and did nothing
   every time, and `--max-tokens` is wired end to end while every provider still
   reports `spend=0`.
8. Every entry in `GATE-04-CRITERIA.md` carries a `kind:` and a `state:` per
   `close-discipline.md` §5 — `narrow` for a scoped nodeid, a symbol-existence
   import, or a structural assert; `broad` for the full suite, which re-runs on
   every close attempt rather than carrying a green forward.
9. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source — a closing unit records, it does not
fix; a defect found here is a finding for the retrospective and, if it must be
fixed, a bug with its own branch, not an edit from this session.
`.specfuse/LEARNINGS.md` (staging file only, per AC5). Gate 1's, gate 2's and
gate 3's WU files and their gate files — this unit reports on what closed, it
does not revise it. The `specfuse:autoclose-debt` markers themselves: they record
that a gate auto-closed, which stays true, and deleting one erases history rather
than discharging it. `.specfuse/roadmap.md` and `PLAN.md`'s `status` field — the
driver owns the terminal flips via `fire_terminal_flips`; do **not** add an
acceptance criterion flipping `PLAN.md status` to `done`. The driver owns all
git; this session edits files only and runs no `git` command.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0 and
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing.

**Escalation triggers.** If the terminal verdict would be `met` while any gate
left an unreconciled auto-close debt marker, stop — that combination is what
`assert_autoclose_debt_reconciled` refuses after dispatch, and reaching it means
the debt was never addressed. If the terminal verdict would be `met` while no
`specfuse-agent run` has ever executed against live state, stop and reconsider:
`met` is a claim that the feature was shown to work, and criterion 7 exists
because it has not been. If cost reconciliation cannot complete because
`events.jsonl` rows are missing for some WU, name the WU rather than estimating —
#1024 records that those rows can be lost between a squash and the next
bookkeeping commit. If a gate-4 work unit turns out to have shipped a defect this
close can see, record it as a finding and let the verdict carry it; do not fix
it here.
