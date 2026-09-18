---
id: FEAT-2026-0113/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
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
   per criterion, and — the load-bearing one — **whether T06 criterion 2's
   non-interference assertion actually held**: the measured `gh` argv sequence for a
   repository that declares its own `severity:*` scheme, showing zero
   `gh label create` calls and no description rewritten. A repository whose own
   labels were disturbed is what stops gate 3. Record alongside it that the
   provisioning branch created its labels **before** the first `--add-label`
   (criterion 2b), since a label applied before it exists fails (#3244).
2. That section includes a `## Cost analysis` heading, reconciled against each
   unit's `planned_cost_usd` and the per-attempt records in `events.jsonl`, not
   estimated.
3. The deferred-verification list names every acceptance criterion not verified
   in-loop, each with its reason and where it actually gets checked — or the
   explicit line `(nothing — every acceptance criterion was verified in-loop)`.
   Gate 1 carried a residual here worth re-stating or retiring: no oracle in this
   feature has yet read a real issue body outside this repository.
4. The consumer-visible contract changes are enumerated, and `CHANGELOG.md` gains
   the entry gate 1 deliberately deferred to the gate that ships the write path:
   the three-field marker, the `severity:<value>` projection, and the two rubric
   sources — a repository's own label descriptions where it declares a scheme, and
   specfuse's published `DEFAULT_SEVERITY_RUBRIC` plus provisioned labels where it
   declares none. State plainly that a repository declaring its own scheme has
   nothing created or overwritten, since that is the property an existing consumer
   will check first.
5. Any durable rule this gate surfaced is promoted to `.specfuse/LEARNINGS.md`.
   Two candidates visible at draft time. First: a non-interference contract proved
   by argv over the whole call sequence is a different and much stronger claim than
   "behaves equivalently" in prose. Second, from this gate's own arm checkpoint: a
   safety constraint stated over a *bundle* ("the rubric must be the operator's")
   can be strictly wider than the constraint that is actually load-bearing ("the
   floor must be the operator's"), and the wider version shipped a feature that was
   inert by default — worth a rule about separating the decision that gates an
   action from the definition it is measured against.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this unit closes a gate, it
does not implement. Gate 1's work units and `GATE-01-CRITERIA.md`, which are
sealed history. Other features' folders.

**Verification.** `specfuse lint --closing`, plus the `plannext` gate set in
`.specfuse/verification.yml`. Gate 2's `feature_oracle` is re-run fresh in this
session per `close-discipline.md` §1 and its verdict recorded in
`## Measurements`.

**Escalation triggers.** If criterion 1's answer is that a repository declaring its
own `severity:*` scheme had a label created, or any description of its own
overwritten, stop and escalate rather than recording it and closing green — that
finding invalidates the gate's definition of done and gate 3 has no premise to
build on. Likewise if provisioning ran anywhere other than the declares-none
branch, or if the marker's two-field form is no longer byte-identical.
