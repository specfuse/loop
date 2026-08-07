---
id: FEAT-2026-0075/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 1 — retrospective, lessons, docs, and the contract-change list

**Objective.** Fold gate 1's retrospective, its promoted lessons, and its
documentation reconciliation into one session, enumerate the consumer-visible contract
changes, and — uniquely for this feature — report whether the warning gate 1 built
fired in this close's own dispatch.

**Context.** This is `FEAT-2026-0075/G1-CLOSE-INTERMEDIATE`, gate 1's closing unit.
Gate 1 made the driver-staleness hazard visible: `T01` added the detection predicate
(`specfuse/loop/driver_edit.py`), `T02` wired an immediate warning at the squash site,
and `T03` added the gate-completion summary plus a `driver_staleness_detected` event.
Read `PLAN.md`, `GATE-01.md`, and `.specfuse/LEARNINGS.md`'s two restart entries
before starting.

`auto_close_disabled: true` is set deliberately. This close carries a
`close-discipline.md` §3 contract-change enumeration, and gate 1 changes what every
driver run prints and what every feature's event log may contain. An auto-closed gate
would leave every criterion below unfulfilled at `attempts: 0` with nothing failing —
`[FEAT-2026-0031/G1-CLOSE]` is that lesson.

**Your own dispatch is the experiment, and criterion 1 comes before everything else.**
`T02` and `T03` both edited `specfuse/loop/loop.py`. If the driver was restarted as
`GATE-01.md` requires, this session is the first close in this repository's history to
have seen this feature's own warning fire in its own run. If it was not, you are
running the pre-`T02` code and cannot observe anything — which is the fourth
occurrence of the hazard this feature exists to fix, and must be reported as a finding
rather than worked around.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required artifacts
and headings are pre-created in this session's skeleton; fill them in rather than
reconstructing their shape from memory.

**Acceptance criteria.**

1. **Driver-restart precondition, checked before anything else is written.**
   `GATE-01.md` § *Arming discipline* requires the driver be restarted after `T03`
   completes. Compare the dispatching process's start time
   (`ps -eo pid,lstart,etime,command`) against `T03`'s `started_at`. Report both. If
   the process predates `T03`, **say so and emit `status: blocked`** — every in-situ
   observation below would be about pre-`T02` code, and reporting one would be the
   fourth occurrence of this feature's own subject.
2. **The feature-level question (§1) — did the warning fire in this dispatch?** Answer
   one question no producing unit's criteria asked: **did this close's own dispatch
   carry the immediate staleness warning `T02` built, and does the gate-end summary
   `T03` built name `T02` and `T03` as driver-editing units with this close dispatched
   after them?** Answer from what you actually observed in this run's output and this
   feature's `events.jsonl`, quoting both. Every producing unit tested a part in a
   fresh interpreter; nothing tested the composite in a real dispatch, which is the
   precise gap that makes this hazard invisible.
3. **Oracles re-run fresh (§1).** Every oracle named in `T01`–`T03`'s criteria is
   re-run in this session, full command, exit codes read directly — the `code` gate
   set, all symbol-existence imports, the purity and grep checks, and `T03`'s
   `event-type-gate` sweep over every feature's `events.jsonl`. Paste real output.
4. **The warning's negative case, observed rather than asserted.** `T02` criterion 6
   and `T03` criterion 6 both require silence on a non-driver-editing unit. Confirm
   from this gate's own record that `T01` — which produced only
   `specfuse/loop/driver_edit.py`, a driver path — is classified consistently with
   what `T02` and `T03` were classified as, and say plainly whether the predicate
   treats a *new* driver module the same as an edit to an existing one. If gate 1's
   design got that wrong, it is a finding for gate 2, not something to reconcile here.
5. **Cost reconciliation.** Reconcile each WU's actual spend against its
   `planned_cost_usd` (`T01` $2.50, `T02` $3.50, `T03` $3.00, this unit $4.50,
   `G1-PLAN` $6.00) and against the gate's $25.50 budget. Compute the same total
   independently from `events.jsonl` and compare — that log is the only surface that
   never loses a re-armed cycle. Report both numbers and explain any divergence.
6. **Deferred-verification list.** For every acceptance criterion across `T01`–`T03`
   not verified in-loop, record the criterion, why it was not verified here, and where
   it actually gets checked. If there are none, write exactly `(nothing — every
   acceptance criterion was verified in-loop)`.
7. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename this gate makes that a scaffold consumer depends on — at minimum the new
   `specfuse/loop/driver_edit.py` module surface, the new warning text every driver run
   may now print, the gate-completion summary, and the `driver_staleness_detected`
   event type every downstream project's `events.jsonl` may now carry — and block on
   explicit human acknowledgment. Append each item to `CHANGELOG.md`'s `Unreleased`
   section classified and carrying `FEAT-2026-0075`.
8. **Lessons.** Promote what generalizes to `.specfuse/LEARNINGS.md`, or state in the
   retrospective that nothing does. Do **not** re-promote
   `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` or
   `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` — both are already
   there, and this gate was planned against them. What would be new is anything gate 1
   learned about *why a written rule did not prevent three recurrences*, which is the
   feature's actual thesis.
9. `RETROSPECTIVE.md` carries a `## Gate 1` section holding this gate's record and a
   `## Cost analysis` section holding criterion 5's reconciliation. Both are in the
   pre-created skeleton — fill them in rather than writing the content under headings
   of your own choosing.
10. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any file under `specfuse/` — gate 1's code is complete, and a fix
here would be work no unit reviewed; a defect found by criterion 3's re-run is a
finding to report, not to repair. `.specfuse/verification.yml`. `.specfuse/rules/` and
`.specfuse/templates/`. Any other feature's folder under `.specfuse/features/`.
`GATE-02.md`'s work-unit list — `G1-PLAN` owns drafting gate 2. Generated directories,
secrets, `.git/`. The driver owns all git operations and owns the terminal status
flips. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition, criterion 3 requires re-running the `code` gate set
in full with output pasted. Run `specfuse-lint --closing` before emitting the RESULT
block, per criterion 10.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 1 shows the dispatching process predates `T03`; any oracle re-run in
criterion 3 fails — a red oracle on a gate whose units all report `done` is exactly
the composite failure a close exists to catch; criterion 2's observation shows the
warning did not fire despite a correctly restarted driver, which means gate 1's
central claim is unmet and gate 2 must not be drafted against it; or the human
acknowledgment required by criterion 7 is not available in this session.
