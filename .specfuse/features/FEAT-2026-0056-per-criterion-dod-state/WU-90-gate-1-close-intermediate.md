---
id: FEAT-2026-0056/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
auto_close_disabled: true
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.9.3
started_at: 2026-08-06T00:39:56.714800+00:00
duration_seconds: 1101.102
cost_usd: 8.293007
input_tokens: 138
output_tokens: 66412
---

# Close gate 1 — retrospective, lessons, docs, and the contract-change list

**Objective.** Fold gate 1's retrospective, its promoted lessons, and its
documentation reconciliation into one session, and enumerate the consumer-visible
contract changes this gate makes.

**Context.** This is `FEAT-2026-0056/G1-CLOSE-INTERMEDIATE`, the closing unit of gate
1 of FEAT-2026-0056. Gate 1 made per-criterion close state *recorded* and *linted*:
T01 added `specfuse/loop/criteria_state.py`, T02 wired the artifact into
`precreate_dispatch_skeleton` and proved it survives the re-arm fold, T03 declared
the requirement in `closing_requirements.py` and implemented it in `lint_closing.py`,
and T04 documented the contract and re-baselined the roadmap's benefit claim. Read
`PLAN.md` and `GATE-01.md` in this folder before starting.

`auto_close_disabled: true` is set deliberately. This close carries a
`close-discipline.md` §3 contract-change enumeration, which §3 makes load-bearing,
and gate 1 ships a new blocking lint finding that scaffold consumers will meet. An
auto-closed gate would leave every criterion below unfulfilled at `attempts: 0` with
nothing failing — `[FEAT-2026-0031/G1-CLOSE]` is that lesson.

**Gate 1 deliberately made no close cheaper.** Nothing reads the recorded state to
skip work until gate 2. When the retrospective reports cost, do not read gate 1's
close spend as evidence about the feature's savings claim — the mechanism that saves
money has not shipped yet. Saying that plainly is part of this unit's job.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required
artifacts and headings are pre-created in this session's skeleton; fill them in
rather than reconstructing their shape from memory.

**Acceptance criteria.**

1. **Oracles re-run fresh (§1).** Every oracle named in T01–T04's acceptance criteria
   is re-run in this session, full command, exit code read directly — the `code` gate
   set, both symbol-existence imports, T02's scoped debt-enumeration regression, T03's
   corpus sweep, and T04's sync-and-diff. Paste real command output. A producing
   unit's `done` is a claim; the re-run is the verification.
2. **The feature-level question (§1).** Answer one question no producing unit's
   criteria asked: **does a close dispatched today actually receive a
   `GATE-NN-CRITERIA.md` seeded from its own gate's criteria?** Every unit tested a
   part; nothing tested the composite. Report the answer with evidence, not an
   inference from four green units.
3. **The re-arm property, observed rather than asserted.** T02 tests that the
   artifact survives `fold_cumulative_on_rearm`. Confirm the test exercises the real
   fold path and not a stand-in, and say which. `[FEAT-2026-0053/G2-CLOSE]` is the
   precedent: the operator re-arm path zeroes without folding, so a guard keyed on
   "already folded" reads a never-folded unit as a folded one.
4. **Cost reconciliation.** Reconcile each WU's actual spend against its
   `planned_cost_usd` (T01 $3.00, T02 $4.00, T03 $3.00, T04 $2.50, this unit $4.50,
   G1-PLAN $6.00) and against the gate's $29.00 budget. Compute the same total
   independently from `events.jsonl` and compare — that log is the only surface that
   never loses a re-armed cycle. Report both numbers and explain any divergence.
5. **Deferred-verification list.** For every acceptance criterion across T01–T04 not
   verified in-loop, record the criterion, why it was not verified here, and where it
   actually gets checked. If there are none, write exactly `(nothing — every
   acceptance criterion was verified in-loop)`.
6. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename this gate makes that a scaffold consumer depends on — at minimum the new
   `GATE-NN-CRITERIA.md` artifact appearing in close sessions, the new blocking lint
   finding, the new `applies_when` value, and the `close-discipline.md` §5 section —
   and block on explicit human acknowledgment of the list. Append each item to
   `CHANGELOG.md`'s `Unreleased` section, classified and carrying `FEAT-2026-0056`.
   This is the same material as the enumeration, written once into both places.
7. **Lessons.** Promote what generalizes to `.specfuse/LEARNINGS.md`, or state in the
   retrospective that nothing does. A lesson that only restates this feature's design
   is not a lesson.
8. `RETROSPECTIVE.md` carries a `## Gate 1` section holding this gate's record, and a
   `## Cost analysis` section holding criterion 4's reconciliation. Both are in the
   pre-created skeleton — fill them in rather than writing the content under headings
   of your own choosing.
9. **Honest savings statement.** The retrospective says plainly that gate 1 shipped no
   cost saving, and that the roadmap's benefit paragraph was re-baselined by T04
   because the original claim assumed a mechanism `PLAN.md` rejects.
10. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any file under `specfuse/` (gate 1's code is complete; a fix here
would be work no unit reviewed). `.specfuse/verification.yml`. Any other feature's
folder under `.specfuse/features/`. `GATE-02.md`'s work-unit list — G1-PLAN owns
drafting gate 2. Generated directories, secrets, `.git/`. The driver owns all git
operations and owns the terminal status flips. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition, criterion 1 requires re-running the `code` gate set
in full — `python3 -m unittest discover -s tests -v -b`, `ruff check`, `bandit`,
`coverage --fail-under=90`, `leak-scan`, `event-type-gate` — with output pasted.
Run `specfuse-lint --closing` before emitting the RESULT block, per criterion 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: any
oracle re-run in criterion 1 fails — a red oracle on a gate whose units all report
`done` is exactly the composite failure this close exists to catch, and it is not
this unit's job to fix it; criterion 2's composite check shows a close does not
receive a seeded artifact; the human acknowledgment required by criterion 6 is not
available in this session; or `events.jsonl` and the WU frontmatter disagree on
total cost by more than 10% and the cause cannot be attributed.
