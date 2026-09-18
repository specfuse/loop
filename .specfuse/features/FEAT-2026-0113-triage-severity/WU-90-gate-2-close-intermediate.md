---
id: FEAT-2026-0113/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: draft
attempts: 0
planned_cost_usd: 4.50
auto_close_disabled: true
oracle_env: macos_local
oracles:
  - recent-commits
  - diff-stat
---

# G2-CLOSE-INTERMEDIATE — close gate 2

**Context.** Gate 2 made triage record a severity: rubric read from the
repository's own `severity:*` label descriptions, marker written first, label
projected second, and a repository defining no such labels left byte-identical.
This unit folds the retrospective, the durable lessons and the documentation pass
into one session. `close-discipline.md` is binding on the oracle re-runs and on
what a verdict may and may not assert.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Gate 2` section recording what gate 2 proved
   per criterion, and — the load-bearing one — **whether the opt-out equality in
   T06 criterion 2 actually held**: the measured `gh` argv sequence for a
   repository defining no `severity:*` label, against the sequence today's code
   issues. A repository that opted out and saw a write change is what stops gate 3.
2. That section includes a `## Cost analysis` heading, reconciled against each
   unit's `planned_cost_usd` and the per-attempt records in `events.jsonl`, not
   estimated.
3. The deferred-verification list names every acceptance criterion not verified
   in-loop, each with its reason and where it actually gets checked — or the
   explicit line `(nothing — every acceptance criterion was verified in-loop)`.
   Gate 1 carried a residual here worth re-stating or retiring: no oracle in this
   feature has yet read a real issue body outside this repository.
4. The consumer-visible contract changes are enumerated, and `CHANGELOG.md` gains
   the entry gate 1 deliberately deferred to the gate that ships the write path —
   the three-field marker, the `severity:<value>` projection, and the fact that
   defining `severity:*` labels is the opt-in.
5. Any durable rule this gate surfaced is promoted to `.specfuse/LEARNINGS.md`.
   Candidate visible at draft time: an opt-out proved by argv equality rather than
   by prose is a different and much stronger claim than "behaves equivalently".
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this unit closes a gate, it
does not implement. Gate 1's work units and `GATE-01-CRITERIA.md`, which are
sealed history. Other features' folders.

**Verification.** `specfuse lint --closing`, plus the `plannext` gate set in
`.specfuse/verification.yml`. Gate 2's `feature_oracle` is re-run fresh in this
session per `close-discipline.md` §1 and its verdict recorded in
`## Measurements`.

**Escalation triggers.** If criterion 1's answer is that a repository defining no
`severity:*` label saw any write change, stop and escalate rather than recording
it and closing green — that finding invalidates the gate's definition of done and
gate 3 has no premise to build on. Likewise if the marker's two-field form is no
longer byte-identical.
