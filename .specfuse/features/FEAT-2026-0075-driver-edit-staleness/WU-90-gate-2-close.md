---
id: FEAT-2026-0075/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 2 — terminal close for FEAT-2026-0075

**Objective.** Run the feature's terminal close: re-run every oracle fresh, answer
whether the hazard is actually prevented, reconcile cost across both gates, enumerate
consumer-visible contract changes, promote lessons, and record the terminal verdict.

**Context.** This is `FEAT-2026-0075/G2-CLOSE`, the terminal work unit. Gate 1 made
the driver-staleness hazard visible; gate 2 made it preventable and gave the
two-invocation hold a sanctioned name. Read `PLAN.md`, `GATE-02.md`,
`GATE-02-REVIEW.md`, and `RETROSPECTIVE.md` before running.

**This body is a placeholder.** `G1-PLAN` rewrites it against the work gate 2 actually
contains. What is fixed now is the shape and the obligations, not the detail.

`auto_close_disabled: true` is set deliberately and stays set: this close carries a
`close-discipline.md` §3 contract-change enumeration and a terminal verdict.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required artifacts
and headings are pre-created in this session's skeleton; fill them in rather than
reconstructing their shape from memory.

**Acceptance criteria.**

<`G1-PLAN` replaces these with criteria scoped to gate 2's actual work units. The
obligations below are fixed by `close-discipline.md` and are not `G1-PLAN`'s to
remove.>

1. **Driver-restart precondition, if any gate-2 unit edited `specfuse/loop/`.** Check
   the dispatching process's start time against the last driver-editing unit's
   `started_at`. Report both, and emit `status: blocked` if the process predates it.
   This feature of all features must not close on a stale observation of its own
   subject.
2. **Oracles re-run fresh (§1).** Every oracle named across both gates' acceptance
   criteria is re-run in this session, full command, exit codes read directly. Never
   inherit a producing WU's self-report.
3. **The feature-level question (§1) — is the hazard actually prevented?** Answer one
   question no producing unit's criteria asked: **would the arm-time refusal have
   fired on the three historical occurrences** (FEAT-2026-0057's gate 1, and
   FEAT-2026-0056's gates 1 and 2), and does it report zero on the correctly-ordered
   gates now in the tree? The first half is what the feature claims; the second is
   what makes it safe to ship.
4. **Cost reconciliation.** Reconcile actual against planned across both gates
   ($24.50 as drafted, though `G1-PLAN` may have re-derived it), computing the total
   independently from `events.jsonl` and comparing.
5. **Deferred-verification list.** Criterion, reason, and where it actually gets
   checked, for everything not verified in-loop; or exactly `(nothing — every
   acceptance criterion was verified in-loop)`.
6. **Hedged follow-up record (§2).** On `met_locally` or `partially_met`, one titled
   entry per unmet criterion with the criterion verbatim, why it is unverifiable here,
   the exact re-run condition that would upgrade it, and a `kind:`. Write the `kind:`
   yourself — you ran the oracle and know why it did not meet.
7. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across both gates, block on explicit human acknowledgment, and append each
   item to `CHANGELOG.md`'s `Unreleased` carrying `FEAT-2026-0075`. Gate 1's list is
   already enumerated in `RETROSPECTIVE.md`; restate any item gate 2 changed rather
   than copying it forward. **The arm-time refusal is a breaking change for any
   downstream project with a driver-editing gate already planned** — say so plainly.
8. **Lessons.** Promote what generalizes, or state that nothing does. The candidate
   worth the most is the feature's own thesis: a written, promoted rule failed to
   prevent three recurrences, and what finally worked (or did not).
9. `RETROSPECTIVE.md` carries a `## Gate 2` section and a `## Cost analysis` section
   holding criterion 4's reconciliation. Both are in the pre-created skeleton.
10. `python3 .specfuse/scripts/lint_plan.py <this feature dir> --closing` exits 0
    before this WU reports `complete`.

Do **not** add a criterion flipping `PLAN.md`'s `status` to `done`. The driver owns
the terminal flips.

**Do not touch.** Any file under `specfuse/` unless gate 2's own work units placed it
there and this close's re-run found it broken — in which case escalate rather than
repair. `.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`.
Any other feature's folder under `.specfuse/features/`. `GATE-01.md` and gate 1's work
units. Generated directories, secrets, `.git/`. The driver owns all git operations and
owns the terminal status flips. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition, criterion 2 requires re-running the `code` gate set
in full with output pasted, and criterion 10 requires the closing lint to exit 0
before the RESULT block is written.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
restart check in criterion 1 shows a stale process; any oracle re-run in criterion 2
fails; criterion 3 shows the refusal would not have fired on the historical
occurrences, which means the feature does not do what it claims; the human
acknowledgment required by criterion 7 is not available; or the terminal verdict would
be `not_met` — record what is unmet and stop rather than flipping anything.
