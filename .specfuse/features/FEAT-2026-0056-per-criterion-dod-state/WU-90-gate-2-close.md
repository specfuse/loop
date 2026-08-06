---
id: FEAT-2026-0056/G2-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
duration_seconds: 1001.041
cost_usd: 3.658889
input_tokens: 76
output_tokens: 38635
---

# Close gate 2 — terminal close for FEAT-2026-0056

**Objective.** Run the feature's terminal close: re-run every oracle fresh, answer
whether a re-dispatched close is actually cheaper, reconcile cost across both gates,
enumerate consumer-visible contract changes, promote lessons, and record the terminal
verdict.

**Context.** This is `FEAT-2026-0056/G2-CLOSE`, the terminal work unit of
FEAT-2026-0056. Gate 1 made per-criterion close state recorded and linted. Gate 2
made it consumed: `T05` keeps the artifact alive across a failed attempt, `T06` stops
a freshly seeded artifact from failing its own lint, `T07` partitions recorded state
into a carry-forward set and a re-verification worklist, and `T08` puts that worklist
in the close session's prompt. Read `PLAN.md`, `GATE-02.md`, `GATE-02-REVIEW.md`, and
`RETROSPECTIVE.md` in this folder before running.

**Your own dispatch is the experiment.** This is the first close in the repo's
history to receive a re-verification worklist, and `GATE-02-CRITERIA.md` will be
seeded in this session by the driver. Criterion 2 is the feature-level question and
it is answerable only from what you actually observe in your own prompt and folder —
not from the unit tests, which pass in fresh interpreters regardless.

`auto_close_disabled: true` is set deliberately and stays set: this close carries a
`close-discipline.md` §3 contract-change enumeration and a terminal verdict.

Binding rules apply by reference — `.specfuse/rules/close-discipline.md`,
`result-contract.md`, `never-touch.md`, `correlation-ids.md`. The required artifacts
and headings are pre-created in this session's skeleton; fill them in rather than
reconstructing their shape from memory.

**Acceptance criteria.**

1. **Oracles re-run fresh (§1).** Every oracle named across the feature's acceptance
   criteria — both gates, `T01`–`T08` — is re-run in this session, full command,
   exit codes read directly. Never inherit a producing WU's self-report. Use the
   `.specfuse/scripts/` shims, not the installed `specfuse-lint` console script, and
   say in the record which you ran —
   `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]`.

2. **Driver-restart precondition, checked before anything else is written.**
   `GATE-02.md` § *Arming discipline* requires the driver be restarted after `T08`
   completes. Check the dispatching process's start time
   (`ps -eo pid,lstart,etime,command`) against `T08`'s `started_at`. Report both. If
   the process predates `T08`, **say so and emit `status: blocked`** — every in-situ
   observation this close would make is about the pre-T08 code, and reporting one
   would repeat gate 1's finding 1 in the gate that was armed to prevent it.

3. **The feature-level question (§1) — is the worklist real?** Answer one question no
   producing unit's criteria asked: **in this session's own dispatch, did the prompt
   carry a re-verification worklist, was the carried-forward set non-empty and
   strictly smaller than the full criterion set, and was every carried-forward entry
   `kind: narrow`?** Report it from the observed prompt and the observed
   `GATE-02-CRITERIA.md`, quoting both. A carried-forward `broad` entry means the
   soundness contract leaked — see the escalation triggers. An empty carried-forward
   set is a legitimate answer and must be reported as one, with the reason, rather
   than presented as a failure of the run.

4. **Per-criterion state (§5).** For every entry in `GATE-02-CRITERIA.md` this close
   verifies, write the `kind` and `state` yourself — you ran the oracle and know its
   scope. Never infer either from another reader's record. An entry you did not
   verify stays pristine; do not annotate it to make a lint green.

5. **Cost reconciliation.** Reconcile actual against planned across both gates,
   computing the total independently from `events.jsonl` and from WU frontmatter and
   comparing the two, with the divergence stated. `PLAN.md`'s frontmatter
   `planned_cost_usd: 28.00` predates gate 2's draft and is below the two gates' WU
   estimates ($23.00 + $18.00); report the real number against the two gate
   `cost_budget_usd` values rather than against the stale feature figure, and name
   the discrepancy.

6. **The close-cost delta, honestly.** This feature exists to move one number. Report
   whether it moved: what this close's own worklist let it skip, in criteria and in
   oracle invocations, and what it could not skip. `T04` already re-baselined the
   roadmap claim — the repo's `tests` gate is a `broad` oracle that re-runs every
   attempt, and the saving is per-criterion reasoning, regeneration, and the scenario
   matrix. Do not restate the retired "roughly halves close cost" wording. A single
   first-attempt close is a sample of one; say so.

7. **Deferred-verification list.** Criterion, reason, and where it actually gets
   checked, for everything not verified in-loop; or exactly `(nothing — every
   acceptance criterion was verified in-loop)`. Gate 1's list (`D1`–`D4`) carries
   forward: `D4` — the artifact's survival across a genuine multi-attempt close — is
   `T05`'s subject and should be resolved here or re-deferred with a reason.

8. **Hedged follow-up record (§2).** On `met_locally` or `partially_met`, one titled
   entry per unmet criterion with the criterion verbatim, why it is unverifiable
   here, the exact re-run condition that would upgrade it to `met`, and a `kind:`.
   Write the `kind:` yourself.

9. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across both gates, block on explicit human acknowledgment, and append each
   item to `CHANGELOG.md`'s `Unreleased` section carrying `FEAT-2026-0056`. Gate 1's
   five items are already enumerated in `RETROSPECTIVE.md` § *Consumer-visible
   contract changes*; **item 1's behaviour is changed by `T06`** and must be restated
   accordingly, not copied. Gate 2 adds at least
   `criteria_state.build_reverification_worklist`, `criteria_state.criteria_filename`
   / `CRITERIA_FILENAME_RE`, `loop.format_reverification_worklist`, the new
   `_clean_attempt_untracked` carve-out, and the new prompt section every close
   session now receives. If there genuinely are none beyond gate 1's, write exactly
   `n/a — no consumer-visible contract change`. Note that
   `closing_requirements.consumer_visible_section_is_na` classifies this section by
   substring — a real enumeration that quotes the exemption line is read as exempt;
   gate 1 tripped this and it is FEAT-2026-0064's to fix, not yours.

10. **Lessons.** Promote what generalizes to `.specfuse/LEARNINGS.md`, or state that
    nothing does. Do not re-promote
    `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]` or
    `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` — both are already there
    and gate 2 was planned against them.

11. `RETROSPECTIVE.md` carries a `## Gate 2` section holding this gate's record and a
    `## Cost analysis` section holding criterion 5's reconciliation. Both are in the
    pre-created skeleton — fill them in rather than writing the content under
    headings of your own choosing.

12. `python3 .specfuse/scripts/lint_plan.py <this feature dir> --closing` exits 0
    before this WU reports `complete`.

Do **not** add a criterion flipping `PLAN.md`'s `status` to `done`. The driver owns
the terminal flips.

**Do not touch.** Any file under `specfuse/` unless gate 2's own work units placed it
there and this close's re-run found it broken — in which case escalate rather than
repair. `.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`.
Any other feature's folder under `.specfuse/features/`. `GATE-01.md` and gate 1's
work units. Generated directories, secrets, `.git/`. The driver owns all git
operations and owns the terminal status flips on `PLAN.md`, the terminal gate, and
the roadmap row. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition, criterion 1 requires re-running the `code` gate set
in full with output pasted, and criterion 12 requires
`python3 .specfuse/scripts/lint_plan.py <this feature dir> --closing` to exit 0
before the RESULT block is written.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
driver-restart check in criterion 2 shows the dispatching process predates `T08`; any
oracle re-run in criterion 1 fails; criterion 3's observed run shows a carried-forward
criterion whose `kind` is `broad`, which means the soundness contract leaked and is
not something to reconcile in a close; the human acknowledgment required by criterion
9 is not available in this session; or the terminal verdict would be `not_met` —
record what is unmet and stop rather than flipping anything.
