---
id: FEAT-2026-0080/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 8.00
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/answer-escalation/SKILL.md
  - .specfuse/skills/answer-escalation/SKILL.md
  - tests/test_answer_escalation_skill.py
---

# Add the `/answer-escalation` skill

**Objective.** Ship a human-invoked skill that reads one parked `needs-human`
issue, explains what stopped the agent, and records the operator's disposition —
leaving guidance for the next agent run and unparking the issue.

**Context.** Correlation ID `FEAT-2026-0080/T01`. This is the human half of the
escalation loop; PLAN.md's D1 states the agent half is excluded, not deferred.

The problem this closes: `AnsweredEscalationProvider`
(`specfuse/agent/providers/answers.py:12-16`) records an operator's numbered reply
and explicitly "does not carry out the chosen option", leaving `NEEDS_HUMAN_LABEL`
in place. `BugsProvider.advertise` (`specfuse/agent/providers/bugs.py:341`) skips
any issue carrying `needs-human` or `blocked-wu` via `_HUMAN_OWNED_LABELS`. Net
effect: an answered escalation is acknowledged and parked forever.

Read before writing:

- `.specfuse/rules/operator-escalation.md` — the six-part framing this skill's
  own output must follow. Binding by reference; do not restate it in `SKILL.md`.
- `.specfuse/rules/human-output.md` — this is an interactive skill, so it reports
  to the operator and emits no RESULT block.
- `specfuse/loop/escalation.py` — `NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`,
  `_CORRELATION_MARKER_TEMPLATE`, and `render_escalation_body`, which is what
  writes the numbered options the skill reads back.
- `.specfuse/skills/attention/SKILL.md` — the closest sibling: read-only, sweeps
  the same queue, degrades gracefully when `gh` is absent. Match its posture.
- `.specfuse/skills/pick-feature/SKILL.md` — the decision-presentation shape
  (prose options with pros and cons, then a recommendation, never a table).

PLAN.md's D2 table maps each `CATEGORY_LABELS` value to its owning skill; D3 fixes
the write order; D4 makes `skip` inert. Those are decided — implement them, do not
re-open them.

**Acceptance criteria.**

1. `tests/test_answer_escalation_skill.py::TestAnswerEscalationSkill::test_skill_file_exists_in_both_trees`
   fails on HEAD before this WU runs (the skill does not exist), and the failure is
   recorded in the attempt note.
2. `plugins/specfuse/skills/answer-escalation/SKILL.md` exists with YAML
   frontmatter carrying `name: answer-escalation` and a `description:` naming its
   trigger phrases.
3. `.specfuse/skills/answer-escalation/SKILL.md` is byte-identical to the
   canonical copy — asserted by a test, matching the existing convention in
   `tests/test_fix_bug_headless.py`.
4. `SKILL.md` states the skill is human-invoked only and must not run headless,
   giving the reason: the disposition choice is the entire point and a redirected
   stdin has no channel to supply it.
5. `SKILL.md` names all four dispositions — hand off, answer, close, skip — each
   as its own documented step.
6. `SKILL.md` carries the category-to-owning-skill routing table with an entry for
   every value in `escalation.CATEGORY_LABELS`. A test asserts the table's category
   set equals `CATEGORY_LABELS` exactly, so a category added later fails this test
   rather than silently routing nowhere.
7. `SKILL.md` documents the guidance-comment marker
   `<!-- specfuse:operator-guidance id=<correlation_id> -->`, following the
   existing `<!-- specfuse:… -->` idiom, so a later reader can locate the operator's
   guidance mechanically.
8. `SKILL.md` states the write order explicitly — guidance comment first, label
   release second — and gives the reason from PLAN.md D3.
9. `SKILL.md` states that `skip` writes nothing at all: no comment, no label edit,
   no issue state change.
10. `SKILL.md` states that the skill triggers no fix and no retry: it never invokes
    `/fix-bug`, never opens a PR, and never merges.
11. `SKILL.md` documents graceful degradation when `gh` is unavailable or
    unauthenticated — report plainly and stop, rather than half-applying a
    disposition.
12. All tests in `tests/test_answer_escalation_skill.py` pass after this WU's
    edits.

**Do not touch.** `specfuse/agent/providers/answers.py` and any other Python under
`specfuse/` — this WU ships markdown and a test only. `.specfuse/skills/fix-bug/`
and its canonical copy belong to T02. Generated directories, secrets, `.git/`. The
driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage`, `leak-scan`. Plus, specific to this unit:

- `python3 -m unittest tests.test_answer_escalation_skill -v` passes.
- `diff plugins/specfuse/skills/answer-escalation/SKILL.md .specfuse/skills/answer-escalation/SKILL.md`
  exits 0.
- `python3 -c "from specfuse.loop.escalation import CATEGORY_LABELS; print(sorted(CATEGORY_LABELS))"`
  and confirm every printed category appears in the skill's routing table.

Note for the `leak-scan` gate: write examples with placeholder issue numbers and
`example.com` hosts. Real repository paths and org names in skill prose are what
the structural scan flags.

**Escalation triggers.** Stop and emit `status: blocked` rather than pushing
through if: `escalation.CATEGORY_LABELS` contains a category with no plausible
owning skill and PLAN.md's D2 table does not cover it (a routing decision belongs
to the operator, not this session); or the byte-identical convention between the
canonical and vendored skill trees conflicts with an existing sync mechanism you
discover while working. If `plugins/specfuse/skills/answer-escalation/SKILL.md` is
absent from the files you edited, emit `status: blocked` — do not claim complete.
