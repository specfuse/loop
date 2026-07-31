---
id: FEAT-2026-0053/T13
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
human_only: true
oracle_env: macos_local
provenance: "RETROSPECTIVE.md gate-2 Findings 5 and 'What the loop did NOT verify' 4: FEATURE-REVIEW.md is written and never read — `grep -rn \"FEATURE-REVIEW\" .specfuse/skills specfuse/loop/data` returns zero matches, nothing surfaces it into a PR body, and /wrap-feature does not know it exists. That retrospective says G2-PLAN must either scope the last hop into gate 3 or record a deliberate deferral with a home. This WU is that scoping decision, and it widens PLAN.md's declared gate-3 scope boundary from docs-only, which is why it carries human_only."
produces:
  - plugins/specfuse/skills/wrap-feature/SKILL.md
  - .specfuse/skills/wrap-feature/SKILL.md
---

# `FEATURE-REVIEW.md` reaches the one human read

**Objective.** Make `/wrap-feature` surface an `auto` feature's accumulated
doubt into the PR body, so the single human checkpoint that `auto` trades four
gate reads for actually receives what those gate reads would have shown.

**Context.** Correlation ID `FEAT-2026-0053/T13`. Gate 2's `T08` built
append-only `FEATURE-REVIEW.md` accumulation — one section per auto-armed gate
carrying the verbatim `open_questions` list, the verbatim `## Doubt` prose, and
the per-class verdict line, all inside the single arm commit. It is verified end
to end by seven tests. It has no reader. Gate 2's retrospective states the
consequence plainly: *"Under `auto` this is the mechanism that replaces four
human gate reads with one PR read — so an unread accumulation file is not a
cosmetic gap, it is the checkpoint value silently not being delivered."*

`LEARNINGS-pending.md` is the same shape. `T09` stages lessons there under
`auto` and its template documents a four-step human promotion procedure at PR
review; as of gate 2's close, zero such files exist and no human has ever
performed the step. Both files are read at the same moment by the same person,
so both belong in the same surfacing change.

**This WU is a declared scope-boundary revision, and that is why it is
`human_only: true`.** `PLAN.md`'s scope boundary names gate 3 as "docs and
methodology rewrite". This is not documentation — it changes what
`/wrap-feature` does. `G2-PLAN` scoped it in rather than deferring it because
gate 3 is the terminal gate: there is no later gate in this feature to hold it,
and deferring means shipping a feature whose headline value proposition is
undelivered. **Rejecting this WU at the arming checkpoint is a legitimate call**
— it strands nothing, since the three docs WUs do not depend on it — but the
rejection should come with a home for the gap, not silence.

**Where the change goes.** `/wrap-feature`'s step 3 opens the PR with
`gh pr create --fill --base <resolved_base>`, which takes its body from the
commits. `--fill` cannot carry a file that is not a commit message. The change
is to that step: when the feature folder holds `FEATURE-REVIEW.md` (and/or
`LEARNINGS-pending.md`), assemble a body and open the PR with an explicit body
rather than `--fill`. The skill is prose executed by a model, so this is an
edit to the skill's step-3 instructions, not to any Python.

**Two copies, kept byte-identical.** `plugins/specfuse/skills/` is canonical and
`.specfuse/skills/` is a vendored copy; `tests/test_skills_vendored_in_sync.py`
is the drift guard. Editing one copy fails the suite.

**Hold the T08 decoupling.** The doubt prose is written *into*
`FEATURE-REVIEW.md` and is never read *by* the arm predicate. Surfacing it into
a PR body must not create any path where that prose becomes a mechanical input
to anything. It is text for a human, and it stays text for a human.

**Acceptance criteria.**

1. `grep -rn "FEATURE-REVIEW" plugins/specfuse/skills/wrap-feature/SKILL.md`
   returns at least one match — the finding that motivated this WU
   (`grep -rn "FEATURE-REVIEW" .specfuse/skills specfuse/loop/data` returning
   zero) no longer reproduces.
2. The skill's PR-opening step instructs: check for `FEATURE-REVIEW.md` in the
   feature folder; when present, include its content (or a faithful digest of
   every gate section's `## Doubt` and `open_questions`) in the PR body, and
   open the PR with that body instead of relying on `--fill`.
3. The skill instructs the same for `LEARNINGS-pending.md` when present,
   including a pointer to the promotion step its template documents — so the
   human at PR review is told there is a promotion to perform.
4. When neither file is present the skill's existing behavior is unchanged:
   `--fill` with the resolved base, single-confirm posture intact. The skill
   text says so explicitly, so a `review` feature's wrap is provably untouched.
5. The skill's "What this skill does NOT do" section still says it does not
   write to `RETROSPECTIVE.md`, `LEARNINGS.md`, or roadmap content, and gains
   nothing that contradicts read-only treatment of `FEATURE-REVIEW.md` and
   `LEARNINGS-pending.md`. Reading them into a PR body is read-only; promotion
   stays the human's act.
6. `python3 -m unittest tests.test_skills_vendored_in_sync -v` exits `0` — both
   copies byte-match.
7. `python3 -m unittest discover -s tests -v` exits `0`.
8. The skill's version block gains an entry naming this WU and what changed,
   following the existing `v0.3` / `v0.2` format.

**Do not touch.** `specfuse/loop/arm_txn.py` and every other `.py` file under
`specfuse/` — `T08`'s accumulation is delivered and correct; this WU adds a
reader, not a second writer, and nothing about how or when `FEATURE-REVIEW.md`
is written may change. The arm predicate and its class set: the doubt prose must
not become a predicate input, and adding one would invert this feature's
organizing principle. The auto-merge boundary — `/wrap-feature` still does not
merge, and this WU does not soften that by one word. Any skill other than
`wrap-feature`. `docs/` (T10, T11, T12 own it). `.specfuse/rules/`.
`RETROSPECTIVE.md` and the other feature-folder artifacts. Generated
directories, secrets, `.git/`. The driver owns all git — you edit files only.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_skills_vendored_in_sync -v`, plus
criterion 1's grep run exactly as written. Note that this WU's deliverable is
prose a model executes: the tests prove the copies match and nothing regressed,
they do not prove the instructions produce a good PR body. The human reading the
first `auto` feature's PR is the real oracle, and that is stated here rather
than hidden behind a green suite.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
the PR body cannot carry the accumulated content without exceeding a limit
`gh pr create` enforces — a truncated doubt summary is worse than a link, and
the choice between them belongs to a human. Emit `status: blocked` if satisfying
criterion 2 appears to require changing when or how `FEATURE-REVIEW.md` is
written: that is `T08`'s surface, this WU is forbidden it, and a reader that
needs the writer changed is a different work unit.
