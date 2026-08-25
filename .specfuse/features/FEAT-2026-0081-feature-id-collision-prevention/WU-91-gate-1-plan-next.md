---
id: FEAT-2026-0081/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
model: opus
effort: high
produces:
  - .specfuse/features/FEAT-2026-0081-feature-id-collision-prevention/PLAN.md
  - .specfuse/features/FEAT-2026-0081-feature-id-collision-prevention/GATE-02.md
  - .specfuse/features/FEAT-2026-0081-feature-id-collision-prevention/GATE-02-REVIEW.md
---

# Draft gate 2 — renumbering as a command

**Objective.** Draft gate 2's substantive work units against what gate 1 actually
shipped: the renumbering command, its dry-run, and the rule about which files
keep the old ID.

**Context.** Runs after `G1-CLOSE-INTERMEDIATE` and reads its record. Read
`PLAN.md`'s scope boundary and `GATE-02.md`'s *What `plan-next` must carry into
this gate* before drafting — both were written at draft time specifically so this
unit would not have to re-derive them, and both contain decisions that are easy to
reason away when optimising for internal consistency.

**Two inheritances, neither optional.**

1. **The ID-bearing surface list T02's check enumerates** is gate 2's work list.
   Gate 1's collision check had to know every place a feature ID is claimed in
   order to compare them; read that enumeration out of the shipped code rather
   than re-deriving it by inspection. Re-deriving it is exactly how the original
   manual renumbering missed files.
2. **`events.jsonl` and `PLAN.baseline.json` keep the OLD correlation ID.** The
   run really did execute under it; rewriting a log to match a later rename
   falsifies history to tidy a name. The renumbered feature's retrospective
   carries a note so a future reader correlating events knows what to expect.
   This is stated with its reasoning in `PLAN.md`; carry it into gate 2's WUs
   verbatim. **Do not let a gate-2 work unit "fix" it.**

**Scope facts already settled — do not re-open them.** `specfuse-renumber` ships
as a flat console script in this repo's `[project.scripts]`, working standalone.
`specfuse renumber` needs a one-line `DELEGATED_COMMANDS` entry in the umbrella
repo, which this repo cannot land; it is a cross-repo follow-up, not a work unit
here.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `close-discipline.md`,
`planning-discipline.md`) and the per-WU craft in
`.specfuse/skills/authoring-work-units/SKILL.md` apply. Do not restate them.

**Acceptance criteria.**

- `PLAN.md`'s task graph gains gate 2's substantive work units, inserted
  **above** the pre-declared `FEAT-2026-0081/G2-CLOSE` entry, with
  `G2-CLOSE`'s `depends_on` updated to name them. A `python3 -m
  specfuse.loop.lint_plan` run on this folder exits 0 afterwards.
- Each drafted WU file exists at the path its graph entry names, carries
  `status: draft` (armed by a human, not by this unit), and contains all five
  mandatory sections.
- Every drafted `implementation` WU that introduces new behavior names a scoped
  red test that fails on HEAD before it runs, per `/authoring-work-units` §12, or
  carries an explicit `Red-test exempt: <reason>` line.
- **The renumber command's WUs include a dry-run mode and a criterion that
  exercises it.** `GATE-02.md`'s arming discipline requires this: the failure
  this feature exists to make cheap is a silent partial rewrite, and a bulk
  mutator that produces one is worse than the hand sweep it replaces.
- **A criterion somewhere in gate 2 asserts the keep-the-old-ID rule
  mechanically** — a renumbered fixture's `events.jsonl` and
  `PLAN.baseline.json` still carry the old ID after the command runs. A rule
  stated only in prose is a rule the next agent reasons away.
- Every drafted WU carries a `planned_cost_usd`, and `GATE-02.md` carries a
  `cost_budget_usd` equal to the sum plus one re-attempt of the largest WU
  (`planning-discipline.md` §5). Closing-WU estimates use that section's floors.
- Gate 2 is the **terminal** gate: its closing shape stays a single `close` WU.
  Do not add a `close-intermediate`/`plan-next` pair.
- The drafted gate carries an **existing-mechanism search verdict** for the
  renumbering command (`planning-discipline.md` §1) — the grep command run and
  its verdict, recorded in `PLAN.md`. Gate 1's search found no renumbering
  mechanism; confirm that is still true rather than inheriting it.
- `GATE-02.md`'s definition of done is rewritten from the placeholder into the
  concrete milestone the drafted units produce.
- **`GATE-02-REVIEW.md` exists** — the review for the gate being **drafted**, not
  the one being closed. `assert_gate_review_exists` requires it and checks
  **after** dispatch, so omitting it costs a full re-attempt. Its frontmatter
  carries an explicit `open_questions:` list; under `autonomy_default: auto` a
  **missing** field is not an empty list and parks the feature, so write `[]`
  when nothing blocks execution rather than leaving it out.

**Do not touch.** Gate 1's WU files and their statuses; `RETROSPECTIVE.md`
(`G1-CLOSE-INTERMEDIATE` wrote it); source and test files — this unit drafts
plans, it does not implement; `.git/`, secrets. The driver owns git and the
terminal PLAN flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gates plus `python3 -m specfuse.loop.lint_plan`
on this feature folder exiting 0. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if gate 1's close record reports
that the ID-bearing surface enumeration is incomplete or was not produced — gate
2's work list depends on it, and drafting a bulk mutator against a guessed list
is how a silent partial rewrite ships. Also block if the close record shows T01's
extraction changed the scan's behavior, since gate 2's renumbering reads the same
ID surfaces and would inherit the change. If gate 2's WU files are absent from
the files you edited, emit `status: blocked` — do not claim complete. Blocked is
respectable (`result-contract.md` rule 4).
