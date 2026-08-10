---
id: FEAT-2026-0076/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - tests/test_agent_policy_key_ownership.py
model: sonnet
effort: medium
---

# Fence review mode against clobbering what it does not own

**Objective.** State, in `/derive-agent-policy`'s prose, that review mode
preserves every key it does not own and never drops a key the existing file
already carries — and extend the disjoint-ownership suite so a future edit that
widens review mode fails instead of passing silently.

**Context.** Correlation ID `FEAT-2026-0076/T06`. Depends on
`FEAT-2026-0076/T05`, which writes the review-mode prose this WU fences.

**Why this WU exists, and why the fence is worth its own unit.** Gate 1's T03
wrote the disjoint-key boundary — `derive-agent-policy` owns `rules`, `budgets`,
`escalation`; `/groom-backlog` owns `queue`; neither writes the other's keys —
and shipped `tests/test_agent_policy_key_ownership.py` to keep it true. That
boundary was written against a **bootstrap** skill, which starts from nothing
and only ever emits the three blocks it owns.

Review mode changes the risk. A skill that **reads the whole existing file** in
order to review it has every unowned key in hand, and re-emitting a "corrected"
document is the natural-feeling next step. `WU-90-gate-2-close.md` names this in
advance: *a review skill is exactly the shape that would be tempted to write
`queue:`.* T04's reference implementation makes the mistake structurally
impossible on the code side (it returns a per-key readout, never a document);
this WU makes the same guarantee legible and testable on the **prose** side,
which is the side an agent actually executes.

**The two properties, stated exactly:**

| Property | What review mode must do |
|---|---|
| **Non-ownership** | Never write `queue` (`/groom-backlog`'s), and never write `version` or `rules.triage` — neither is in this skill's asked-or-proposed set, and gate 1's prose already marks `rules.triage` "not in this skill's scope to ask" |
| **Non-clobbering** | A corrected block it proposes must not drop a key the existing file carries. Reviewing `budgets` and returning two of its three keys is a deletion wearing a correction's clothes |

The second is the one no existing test covers. T03's suite asserts which key
*blocks* each skill may write; it says nothing about whether a block a skill
legitimately owns comes back **whole**.

**Scope note.** `version` and `rules.triage` were unowned by name in T03's
exhaustiveness check because that check operates on top-level key blocks and
`version` is excluded there by construction. This WU does not re-open that
check's definition — it adds a review-mode-specific statement and its test. If
extending the ownership sets turns out to require changing T03's exhaustiveness
assertion, that is an escalation trigger below, not a quiet edit.

**Skills are canonical in `plugins/specfuse/skills/`.** Edit the canonical copy,
then run `scripts/sync-scaffold.sh`.

**The incremental edit this WU makes to a path T03 already delivered.**
`lint_plan.py` emits a WARN because `produces: tests/test_agent_policy_key_ownership.py`
was already delivered by `FEAT-2026-0076/T03`. That is expected and the path is
kept deliberately: the review-mode ownership assertions belong in the
disjoint-ownership suite, not in a suite of their own. This WU's edit is
**additive** — it appends one new test class (`TestReviewModePreservation`) and
leaves every T03-era method untouched, which criterion 6 asserts directly.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
review-mode non-clobbering statement does not yet exist in the skill's prose.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_agent_policy_key_ownership.py::TestReviewModePreservation::test_review_mode_states_non_clobbering`
   exists and **fails on HEAD before this WU runs** (the statement is absent from
   the skill's prose).
2. `plugins/specfuse/skills/derive-agent-policy/SKILL.md`'s review-mode section
   states that review mode **must never write** `queue`, `version`, or
   `rules.triage`, naming `/groom-backlog` as `queue`'s owner — the same
   disclaim-the-other-side shape T03 established, applied to the mode that has
   the whole file in hand.
3. The same section states the non-clobbering property: a proposed correction to
   an owned block preserves every key the existing file already carries in that
   block, and dropping one is a deletion, not a correction.
4. A test asserts the non-clobbering statement names at least one concrete
   consequence — that a `budgets` correction returning fewer keys than the file
   carries is a deletion — so the rule cannot be satisfied by a vague sentence
   about "preserving intent."
5. A test asserts review mode's stated must-never-write set covers **every**
   top-level key block the skill does not own, derived from the file's own
   stated ownership rather than from a literal list hardcoded in the test — so a
   new top-level key added later with no review-mode statement fails this test,
   which is the intended alarm.
6. `tests/test_agent_policy_key_ownership.py`'s existing T03-era test methods are
   present and pass **unmodified**; this WU adds a class, it does not rewrite the
   suite.
7. `scripts/sync-scaffold.sh` has been run and the vendored copy is
   byte-identical to the canonical original.
8. `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
   exits zero after this WU's edits.

**Do not touch.** `plugins/specfuse/skills/groom-backlog/SKILL.md` — T03 already
states that side of the boundary and this WU adds nothing there; if
`/groom-backlog`'s text needs to change, that is an escalation.
`specfuse/loop/policy_review.py` and `specfuse/loop/policy_proposals.py` — this
WU writes prose and a test, no code change. `specfuse/loop/agent_policy.py` — no
schema change (`PLAN.md` § *Scope boundary*).
`tests/test_derive_agent_policy_skill.py` and
`tests/test_derive_agent_policy_review_mode.py` — gate 1's and T05's oracles
respectively. `.specfuse/skills/` directly — edit the canonical `plugins/` copy
and run the sync script. `.specfuse/agent-policy.yml`. Generated directories,
secrets, `.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`,
and the remaining entries in that set. Plus the scoped run in criterion 8.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 5's derived-coverage check cannot be satisfied because the schema
carries a top-level key that neither skill nor review mode should own — report
which key, because an unowned key is a real gap and not a test to loosen (this is
T03's escalation trigger, re-armed for the mode that reads the whole file); or
satisfying criterion 5 would require changing T03's existing exhaustiveness
assertion rather than adding to it. If the non-clobbering statement is absent
from `plugins/specfuse/skills/derive-agent-policy/SKILL.md` in the files you
edited, emit `status: blocked` — do not claim complete.
