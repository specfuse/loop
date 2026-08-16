---
id: FEAT-2026-0050/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
human_only: true
produces:
  - plugins/specfuse/skills/draft-feature/SKILL.md
  - .specfuse/skills/draft-feature/SKILL.md
  - tests/test_draft_feature_answers_mode.py
model: sonnet
effort: medium
---

# Add `/draft-feature`'s answers-supplied mode

**Objective.** Document, in `/draft-feature`'s own SKILL.md, a mode in which the
interview's answers arrive as supplied text instead of a conversation — and
restate the skill's write rule as **never writes without answers** (D2).

**Context.** FEAT-2026-0050/T05, gate 2, no dependencies. `human_only: true`:
this unit restates a rule humans rely on, and `GATE-02-REVIEW.md` § Open
question 1 is where that restatement is challenged. **Do not dispatch this unit
until that question is answered at arming.**

D2, from `PLAN.md`: extend `/draft-feature` rather than build a second drafting
path, because this repository has twice paid for one algorithm living in two
places. The hard rule is restated, not weakened.

Read `GATE-02-REVIEW.md` § Open question 1 before writing: it records what the
skill's text actually says today, which is not what `PLAN.md`'s D2 quotes. The
skill carries a `**Run interactively.**` paragraph whose stated reason is
mechanical (redirected stdin consumes the interview's channel) and a RESULT
section that already contemplates non-interactive dispatch. There is no
sentence forbidding a headless write.

The precedent to follow is FEAT-2026-0042/T03, which added a `## Headless mode`
section to `/fix-bug` — also a skill titled "interactive", also one that halts
for humans — with named outcomes, an explicit never-prompts rule, an
additive-only assertion against HEAD, and both skill surfaces byte-identical.
`tests/test_fix_bug_headless.py` is that unit's test and is the shape this
unit's test should take.

A skill has three surfaces in this repo: canonical
(`plugins/specfuse/skills/`), vendored (`.specfuse/skills/`), and a
`.claude/skills/` discovery symlink into the vendored copy. The symlink already
exists for `draft-feature`; the two SKILL.md files are byte-identical on HEAD
and must stay so.

**Acceptance criteria.**

1. `tests/test_draft_feature_answers_mode.py` names
   `AnswersSuppliedModeTests::test_mode_section_states_the_answers_rule` and it
   **fails on HEAD before this unit runs** — the file does not yet exist, and
   `python3 -m unittest tests.test_draft_feature_answers_mode` exits non-zero on
   an absent module.
2. `SKILL.md` carries a new `## Answers-supplied mode` section stating: the
   skill writes when it has answers, whatever channel they arrived through; it
   never prompts and never waits in this mode; an unanswered elicitation
   question means it does not write at all (D1's fallback), and a defaulted
   decision is written into the drafted `PLAN.md` as an explicit assumption.
3. The drafted folder lands `status: planned` and unarmed in this mode, stated
   explicitly in the new section — the recommendation `GATE-02-REVIEW.md`
   § Open question 1 makes, and the constraint the arming reviewer is being
   asked to approve on. The skill's existing "Does not flip status to `active`"
   line already says this for the interactive path; the new section says it for
   this one.
4. The change is **additive**: every heading and hard rule present in HEAD's
   `SKILL.md` is still present, byte-compared against `git show HEAD:<path>` in
   the test, the same assertion `tests/test_fix_bug_headless.py` makes. The
   interactive Method is not rewritten.
5. Both surfaces — `plugins/specfuse/skills/draft-feature/SKILL.md` and
   `.specfuse/skills/draft-feature/SKILL.md` — are byte-identical after the
   change, asserted by the test.

**Do not touch.** Any other skill under `plugins/specfuse/skills/` or
`.specfuse/skills/` — this unit changes `draft-feature` only. No file under
`specfuse/` (T04, T06, and T07 own the code; this unit is skill prose and its
test). `.specfuse/rules/*.md` — binding rules are referenced, never restated or
edited from a WU. `.claude/skills/draft-feature` is an existing symlink and is
not re-created. Do not touch `.git/` or any secrets file. **The driver owns all
git — this session edits files only and never runs `git`** (reading history via
`git show` inside the test file is the test's business at run time, not a git
operation this session performs).

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed; a sandboxed run
hits unrelated network restrictions during pip build-dependency resolution.
Scoped red/green run:
`python3 -m unittest tests.test_draft_feature_answers_mode -v`. Sync check:
`python3 -m unittest tests.test_skills_vendored_in_sync -v`.

**Escalation triggers.** If `GATE-02-REVIEW.md` § Open question 1 carries no
recorded human answer when this unit is dispatched, report `status: blocked` —
`human_only: true` means the arming decision is the precondition, and writing
the restatement first would remove the signature the review exists to collect.
If the restatement cannot be written without contradicting a hard rule already
in `SKILL.md`, report `status: blocked` quoting both sentences rather than
resolving the contradiction unilaterally.
