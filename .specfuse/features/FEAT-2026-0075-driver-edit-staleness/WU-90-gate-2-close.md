---
id: FEAT-2026-0075/G2-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 2 — terminal close for FEAT-2026-0075

**Objective.** Run the feature's terminal close: re-run every oracle fresh, answer
whether the hazard is actually prevented, reconcile cost across both gates, enumerate
consumer-visible contract changes, promote lessons, and record the terminal verdict.

**Context.** This is `FEAT-2026-0075/G2-CLOSE`, the terminal work unit. Gate 1 made the
driver-staleness hazard visible — and then failed to observe its own code run, because
the process dispatching its close predated the entire gate. Gate 2 narrowed the
predicate to the importable surface (`T04`), gave the two-invocation split a sanctioned
halt the process performs on itself (`T05`), and wired that halt to the squash-diff
detection so the driver stops rather than dispatching into a process that cannot execute
the change (`T06`). Read `PLAN.md`, `GATE-02.md`, `GATE-02-REVIEW.md` and
`RETROSPECTIVE.md` before running.

**What makes this close different from gate 1's.** Gate 1's close was blocked because it
could not make its central observation. This one can — `GATE-02.md`'s arming discipline
requires gate 2 to start under a driver launched after gate 1's last commit, which makes
`T04`'s squash the first live execution of gate 1's warning in this repository's
history. If that observation is again unavailable, say so and block; do not reconstruct
it from `ps` output and call it a result.

`auto_close_disabled: true` is set deliberately and stays set: this close carries a
`close-discipline.md` §3 contract-change enumeration and a terminal verdict.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required artifacts and
headings are pre-created in the feature's skeleton; fill them in rather than
reconstructing their shape from memory.

**Acceptance criteria.**

1. **Driver-restart precondition.** `T04`, `T05` and `T06` all edit `specfuse/loop/`.
   Check the dispatching process's start time against `T06`'s `started_at` (and against
   `GATE-01.md`'s `baseline.probed_at`, which is how gate 1's close identified the
   stale process). Report every timestamp, and emit `status: blocked` if the process
   predates `T06`. **This feature of all features must not close on a stale observation
   of its own subject** — and it has already done so once.
2. **Oracles re-run fresh (§1).** Every oracle named across both gates' acceptance
   criteria is re-run in this session, full command, exit codes read directly. Never
   inherit a producing WU's self-report.
3. **The feature-level question (§1) — is the hazard actually prevented?** Two halves,
   both required, neither answerable by a producing unit's criteria:
   - **Would the halt have fired on the four historical occurrences?** FEAT-2026-0057's
     gate 1, FEAT-2026-0056's gates 1 and 2, and **this feature's own gate 1**. Answer
     from each feature's recorded `files_touched` and dispatch order, and name any
     occurrence where it would not have.
   - **Does it report zero on the correctly-ordered gates now in the tree?** Re-run the
     90-gate sweep `GATE-02.md` § *Escalation-predicate satisfiability* records and
     paste the output. A halt reported on any of the 49 gates with no driver-module edit
     means the shipped control is mis-scoped.
4. **Gate 1's deferred-verification list is closed out.** `RETROSPECTIVE.md` §5 lists
   four rows deferred to "the first gate completion under a driver started after
   `cbc3b23`" — `T02#4`, `T03#5`, `T03#7`, and gate 1's own composite criterion 2. State
   for each whether gate 2's dispatch observed it, quoting the observed output
   (`STALE DRIVER PROCESS:` lines, the gate summary block, and any
   `driver_staleness_detected` entry in this feature's `events.jsonl`). An observation
   that did not happen is recorded as still-deferred with a named site, not silently
   dropped.
5. **Cost reconciliation.** Reconcile actual against planned across both gates —
   `PLAN.md` carries $32.00 total, gate 1 $19.50 and gate 2 $12.50 against a $17.50
   budget — computing the total independently from `events.jsonl` and comparing.
   `RETROSPECTIVE.md` § *Cost analysis* records that gate 1's `events.jsonl` **lost**
   `G1-CLOSE-INTERMEDIATE`'s cycle entirely while its frontmatter read `attempts: 2`;
   state whether that divergence recurred in gate 2 and what the true totals are.
6. **Deferred-verification list.** Criterion, reason, and where it actually gets
   checked, for everything not verified in-loop; or exactly `(nothing — every
   acceptance criterion was verified in-loop)`.
7. **Hedged follow-up record (§2).** On `met_locally` or `partially_met`, one titled
   entry per unmet criterion with the criterion verbatim, why it is unverifiable here,
   the exact re-run condition that would upgrade it, and a `kind:`. Write the `kind:`
   yourself — you ran the oracle and know why it did not meet. `GATE-02-REVIEW.md` §
   *Deferred with a home* names the follow-ups gate 2 deliberately did not build; carry
   them forward rather than re-deriving them.
8. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across both gates, block on explicit human acknowledgment, and append each
   item to `CHANGELOG.md`'s `Unreleased` carrying `FEAT-2026-0075`. Gate 1's five items
   are already enumerated in `RETROSPECTIVE.md` §6 and awaiting that acknowledgment;
   restate any item gate 2 changed rather than copying it forward. Two gate-2 items are
   known now and must not be softened:
   - **`T04` narrows an already-shipped predicate.** A path under
     `specfuse/loop/data/` that warned in gate 1 is silent after gate 2.
     `classified: changed`.
   - **`T06` can stop a driver run mid-gate with a non-zero exit code.** Any downstream
     project whose gate edits `specfuse/loop/` now needs a second invocation, and any
     script or CI job reading the driver's exit status sees a new value.
     **This is a breaking change — say so plainly**, and state what an operator who hits
     it should do.
9. **Lessons.** Promote what generalizes, or state that nothing does. The candidate
   worth the most is whether the control shipped in gate 2 actually closed the loop that
   `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
   opened — including the honest negative case, since gate 2's own arming still required
   a manual restart that no shipped code could enforce.
10. `RETROSPECTIVE.md` carries a `## Gate 2` section and a `## Cost analysis` section
    holding criterion 5's reconciliation. Both are in the pre-created skeleton.
11. `python3 .specfuse/scripts/lint_plan.py <this feature dir> --closing` exits 0 before
    this WU reports `complete`.

Do **not** add a criterion flipping `PLAN.md`'s `status` to `done`. The driver owns the
terminal flips.

**Do not touch.** Any file under `specfuse/` unless gate 2's own work units placed it
there and this close's re-run found it broken — in which case escalate rather than
repair. `.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`. Any
other feature's folder under `.specfuse/features/`. `GATE-01.md` and gate 1's work
units. Generated directories, secrets, `.git/`. The driver owns all git operations and
owns the terminal status flips. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this unit's
exit oracle. In addition, criterion 2 requires re-running the `code` gate set in full
with output pasted, criterion 3 requires the 90-gate sweep pasted, and criterion 11
requires the closing lint to exit 0 before the RESULT block is written.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
restart check in criterion 1 shows a stale process; any oracle re-run in criterion 2
fails; criterion 3's first half shows the halt would not have fired on the historical
occurrences, which means the feature does not do what it claims; criterion 3's second
half reports a halt on a gate with no driver-module edit, which means a mis-scoped
control is about to ship; the human acknowledgment required by criterion 8 is not
available; or the terminal verdict would be `not_met` — record what is unmet and stop
rather than flipping anything.
