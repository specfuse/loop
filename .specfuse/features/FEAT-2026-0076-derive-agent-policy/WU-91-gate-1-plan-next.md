---
id: FEAT-2026-0076/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
---

# Draft gate 2 — the review half

**Objective.** Draft gate 2's substantive work units against what gate 1 actually
learned, and write `GATE-02-REVIEW.md` for the operator's arming decision.

**Context.** Correlation ID `FEAT-2026-0076/G1-PLAN`. Depends on
`FEAT-2026-0076/G1-CLOSE-INTERMEDIATE`.

**Gate 2's shape, from the operator's decision 1.** Gate 1 bootstraps a policy
file from nothing; **gate 2 reviews and corrects one that already exists** —
reading current values, distinguishing agent-chosen defaults from deliberate
operator choices, and proposing per-block corrections without clobbering intent.

**The open question you are here to answer.** `PLAN.md` deliberately left this
undecided, and gate 1's close was told to produce the input for it:

> How does review tell an agent-chosen default from a deliberate operator choice?

Two shapes were identified at drafting, and the choice was withheld on purpose:

- **Compare against the shipped `DEFAULT_*` constants.** Cheap, no schema
  change. Lossy in one case: an operator who deliberately chooses a value equal
  to the default is indistinguishable from one who never chose.
- **Record provenance when written.** Accurate, and a schema change —
  `PLAN.md`'s scope boundary puts schema changes out of *this feature*, so
  taking this shape means either widening the boundary with the operator's
  agreement or filing it as its own feature.

**Decide it against the number gate 1 reported**, not against which is more
elegant. If most values turned out non-derivable, the lossy comparison covers
little and the schema change may be the only thing that helps; if most were
derivable, comparison is probably enough. Recommend, with the count as the
reason — the operator arms this gate and makes the call.

**Draft, do not arm.** Every work unit you write ships `status: draft`. This
feature runs `autonomy_default: review` **specifically** so the operator reads
`GATE-02-REVIEW.md` before arming — that checkpoint is why the gates were staged
(PLAN.md decision 4). Do not flip anything to `pending`.

**Per-WU craft** is `/authoring-work-units`' job — read it and apply it rather
than inventing a shape here. The red-test-first trigger (§12) applies to every
behaviour-introducing implementation WU you draft.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `GATE-02-REVIEW.md` exists and is non-empty, carrying an `open_questions`
   list in its frontmatter — a **required explicit list**; `[]` means nothing
   blocks execution, and a missing field parks the feature under any future
   `auto` dial.
2. The review artifact answers the provenance question with a **recommendation
   and the derivability count as its stated reason**, and names which of the two
   shapes it recommends — or a third, if gate 1 surfaced one.
3. If the recommendation is the schema-change shape, the review says plainly that
   it exceeds `PLAN.md`'s scope boundary and needs either the operator widening
   that boundary or a separate feature. Silently widening scope is the failure
   this criterion exists to prevent.
4. Gate 2's substantive work units are drafted in `PLAN.md`'s graph **above** the
   existing `G2-CLOSE` entry, each with a `file:` and `depends_on:`, and each WU
   file is written with `status: draft`.
5. Every drafted implementation WU names a scoped red test that fails on HEAD,
   per `/authoring-work-units` §12, or carries an explicit `Red-test exempt:
   <reason>` line.
6. Every drafted WU carries a `planned_cost_usd`, and `GATE-02.md` gains a
   `cost_budget_usd` equal to the sum plus one re-attempt of the largest WU
   (`planning-discipline.md` §5 corollary).
7. No work unit is flipped to `pending` and no gate status is changed — a test of
   this criterion is simply that `GATE-02.md` still reads `status: open` and
   every drafted WU reads `status: draft`.
8. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0076-derive-agent-policy`
   exits zero after the drafting.

**Do not touch.** Any source file under `specfuse/`, `plugins/`, or `tests/` —
this unit drafts a plan, it implements nothing. Gate 1's work units or its
retrospective. `PLAN.md`'s `status` field. The `G2-CLOSE` placeholder's position
in the graph — insert before it, never after. Generated directories, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml`:
`plan-lint`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
gate 1's retrospective does not report the derivability count criterion 2 needs
(it is `G1-CLOSE-INTERMEDIATE`'s criterion 3 — report its absence rather than
inventing a number); or gate 2's scope cannot be drafted without a schema change
the operator has not agreed to, in which case say so in the review artifact and
stop rather than drafting past the boundary.
