---
id: FEAT-2026-0046/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - plugins/specfuse/skills/attention/SKILL.md
  - .specfuse/skills/attention/SKILL.md
  - tests/test_attention_skill_structure.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.5.0
started_at: 2026-07-27T21:34:06.231203+00:00
duration_seconds: 219.853
cost_usd: 0.869812
input_tokens: 42
output_tokens: 9347
---

# Author the /attention skill: one priority-ordered view of everything needing a human

**Objective.** Ship the `/attention` skill — a read-only inbox that sweeps
`.specfuse/` state and the `needs-human` issue queue into one priority-ordered list —
plus the structural test that keeps its required sections present.

**Context.** Correlation ID `FEAT-2026-0046/T03`. Depends on `T01` for the label
vocabulary the skill queries (`NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`). Independent of
`T02`: the skill reads the queue, it does not emit into it.

**A prose artifact needs a structural oracle.** `[FEAT-2026-0003/G2-LESSONS]` is
explicit: automated code gates pass trivially for markdown, so a work unit whose only
output is a `SKILL.md` receives a structurally vacuous pass — no test runs, nothing
falsifiable executes. The rule's remedy is a structural linter checking required
sections. That is what `tests/test_attention_skill_structure.py` is for, and it is why
this WU's red test is a structure assertion rather than a behaviour assertion.

**Skills are canonical in `plugins/`.** `scripts/sync-scaffold.sh` vendors
`plugins/specfuse/skills/` into `.specfuse/skills/` byte-for-byte, and
`tests/test_skills_vendored_in_sync.py` fails when the two drift. Write the canonical
copy first, then sync. Editing only one copy fails the suite.

**Reuse `gate-status`, do not reimplement it.** `PLAN.md`'s existing-mechanism search
recorded the reuse: `gate-status` already produces the per-feature diagnosis — what is
blocked, likely root cause, options, recommended action — for the active feature.
`/attention` generalises across features and delegates the per-feature read. Building
a second diagnosis engine is precisely the duplication that search exists to prevent.

**What the sweep covers**, from this feature's roadmap detail section: blocked work
units, gates sitting at `awaiting_review`, features whose status is `blocked`, and
stale pull requests. The first three are local file reads under `.specfuse/`. The
fourth needs a live `gh pr list` and is the one input not derivable from repository
state — the skill must degrade gracefully when `gh` is unavailable rather than
failing the whole sweep, in the same spirit as `wrap-feature`'s handling of an absent
`gh`.

**The skill is a view, never a second source of truth.** The issue queue is
authoritative. `/attention` presents; it does not write. T04 proves this with a test;
this WU must state the prohibition in the skill text so that test has something to
match.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`. The skill's own output, when it halts
for a decision, is bound by `.specfuse/rules/operator-escalation.md`.

**Acceptance criteria.**

1. `tests/test_attention_skill_structure.py::TestAttentionSkillStructure::test_required_sections_present`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `plugins/specfuse/skills/attention/SKILL.md` exists with YAML frontmatter carrying
   a `name` field equal to `attention` and a non-empty `description` field.
3. The skill body contains a `## Hard rules` heading.
4. The skill body contains a `## Method` heading.
5. The skill body contains a hard rule stating the skill is read-only and does not
   write state, including the literal word `read-only`.
6. The skill body names all four swept state classes: the literal strings
   `blocked_human`, `awaiting_review`, `blocked`, and `stale`.
7. The skill body names `gate-status` as the per-feature diagnosis it delegates to.
8. The skill body names `needs-human` as the issue label it queries.
9. The skill body documents a priority ordering — a `## Priority order` heading whose
   section lists the swept classes in the order they are presented.
10. The skill body documents graceful degradation when `gh` is unavailable, and states
    that the local sweep still runs in that case.
11. `.specfuse/skills/attention/SKILL.md` is byte-identical to the canonical copy at
    `plugins/specfuse/skills/attention/SKILL.md`.
12. `python3 -m pytest tests/test_attention_skill_structure.py -q` exits zero after
    this WU's edits (the same file named in criterion 1).
13. `python3 -m pytest tests/test_skills_vendored_in_sync.py -q` exits zero — the
    vendoring guard still holds with the new skill present.

**Do not touch.** `.specfuse/skills/gate-status/SKILL.md` and its canonical copy —
this WU delegates to that skill, it does not modify it. `verification.yml`. Files
owned by T01, T02, or T04. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 12, and the
vendoring guard in criterion 13. Note that the code gates alone cannot judge this
WU's real output — criteria 2 through 11 are what actually verify it, which is the
`[FEAT-2026-0003/G2-LESSONS]` remedy in practice.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`scripts/sync-scaffold.sh` does not vendor a newly added skill directory without
manual registration and the registration surface is unclear; the four swept state
classes cannot all be read from `.specfuse/` files without inventing a new state
field; or `gate-status`'s interface cannot be delegated to without duplicating its
logic. If either SKILL.md copy is absent from the files you edited, emit
`status: blocked` — do not claim complete.
