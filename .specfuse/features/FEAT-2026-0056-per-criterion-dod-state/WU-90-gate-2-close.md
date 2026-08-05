---
id: FEAT-2026-0056/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 2 — terminal close for FEAT-2026-0056

**Objective.** Run the feature's terminal close: re-run every oracle fresh, reconcile
cost, enumerate consumer-visible contract changes, promote lessons, and record the
terminal verdict.

**Context.** This is `FEAT-2026-0056/G2-CLOSE`, the terminal work unit of
FEAT-2026-0056. It is scaffolded as a `status: draft` placeholder so the linter reads
gate 2 as the feature's terminal gate and gate 1 as non-terminal — gate 1's
`plan-next` (`G1-PLAN`) inserts gate 2's substantive work units before this entry and
sets this WU's `depends_on` when it drafts them.

**This body is a placeholder.** `G1-PLAN` rewrites it against the work gate 2
actually contains. What is fixed now is the shape and the obligations, not the
detail. Read `PLAN.md`, `GATE-02.md`, and gate 2's `RETROSPECTIVE.md` before running.

`auto_close_disabled: true` is set deliberately and should stay set: this close
carries a `close-discipline.md` §3 contract-change enumeration and a terminal
verdict, and §3 makes such a close load-bearing.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required artifacts
and headings are pre-created in this session's skeleton; fill them in rather than
reconstructing their shape from memory.

**Acceptance criteria.**

<`G1-PLAN` replaces these with criteria scoped to gate 2's actual work units. The
obligations below are fixed by `close-discipline.md` and are not `G1-PLAN`'s to
remove.>

1. **Oracles re-run fresh (§1).** Every oracle named across the feature's acceptance
   criteria — both gates — is re-run in this session, full command, exit codes read
   directly. Never inherit a producing WU's self-report.
2. **The feature-level question (§1).** Answer one question no producing unit's
   criteria asked. For this feature the natural one: **on a real re-dispatched close,
   is the re-verification worklist actually smaller than the full criterion set, and
   is every carried-forward criterion `narrow`?** Report it with evidence from an
   observed run, not from the unit tests.
3. **Cost reconciliation.** Reconcile actual against planned across both gates
   ($28.00 as drafted), computing the total independently from `events.jsonl` and
   comparing. Report the feature's real close-cost delta — the headline this feature
   exists to move — and say honestly whether it moved.
4. **Deferred-verification list.** Criterion, reason, and where it actually gets
   checked, for everything not verified in-loop; or exactly `(nothing — every
   acceptance criterion was verified in-loop)`.
5. **Hedged follow-up record (§2).** On `met_locally` or `partially_met`, one titled
   entry per unmet criterion with the criterion verbatim, why it is unverifiable
   here, the exact re-run condition that would upgrade it to `met`, and a `kind:`.
   Write the `kind:` yourself — you ran the thing and know why it did not meet.
6. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across both gates, block on explicit human acknowledgment, and append each
   item to `CHANGELOG.md`'s `Unreleased` section carrying `FEAT-2026-0056`. If there
   genuinely are none, write exactly `n/a — no consumer-visible contract change`.
7. **Lessons.** Promote what generalizes to `.specfuse/LEARNINGS.md`, or state that
   nothing does.
8. `RETROSPECTIVE.md` carries a `## Gate 2` section holding this gate's record, and a
   `## Cost analysis` section holding criterion 3's reconciliation. Both are in the
   pre-created skeleton — fill them in rather than writing the content under headings
   of your own choosing.
9. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

Do **not** add a criterion flipping `PLAN.md`'s `status` to `done`. The driver owns
the terminal flips.

**Do not touch.** Any file under `specfuse/` unless gate 2's own work units placed it
there and the close's re-run found it broken — in which case escalate rather than
repair. `.specfuse/verification.yml`. Any other feature's folder under
`.specfuse/features/`. `GATE-01.md`. Generated directories, secrets, `.git/`. The
driver owns all git operations and owns the terminal status flips on `PLAN.md`, the
terminal gate, and the roadmap row. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition, criterion 1 requires re-running the `code` gate set
in full with output pasted. Run `specfuse-lint --closing` before emitting the RESULT
block, per criterion 8.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: any
oracle re-run in criterion 1 fails; criterion 2's observed run shows a carried-forward
criterion whose oracle is `broad`, which would mean the soundness contract leaked;
the human acknowledgment required by criterion 6 is not available in this session; or
the terminal verdict would be `not_met` — record what is unmet and stop rather than
flipping anything.
