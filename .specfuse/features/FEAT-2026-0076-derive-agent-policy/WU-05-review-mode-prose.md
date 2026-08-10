---
id: FEAT-2026-0076/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - tests/test_derive_agent_policy_review_mode.py
model: sonnet
effort: medium
---

# Add the review half to the skill's prose

**Objective.** Extend `/derive-agent-policy`'s `SKILL.md` and `PROMPT.md` with a
**review mode** — reading an existing `.specfuse/agent-policy.yml`, presenting
each in-scope value against its proposal and its shipped baseline, and proposing
per-block corrections — and ship the structural test that fails if the prose
stops describing the algorithm T04 actually implements.

**Context.** Correlation ID `FEAT-2026-0076/T05`. Depends on
`FEAT-2026-0076/T04`, whose module this prose describes. The dependency is the
same one gate 1 used between T01 and T02, for the same reason: **the skill's
prose must describe an algorithm that exists.** Writing the review-mode prose
before `review_agent_policy` is built would leave an operator following it
inventing the classification by hand, which is precisely what
`propose_policy_defaults` was built to stop.

**The two modes, and why the file keeps both.** Gate 1's prose describes
bootstrap: a repository with no policy file, or one nobody has touched, gets a
proposal-and-ask interview. Review mode is the other half of the operator
decision recorded in `PLAN.md` decision 1 — an existing file, read and corrected
without clobbering intent. The skill is one skill with two entry conditions, not
two skills: the questions in Step 2 are the same questions, and only the
starting state differs. The prose must make the entry condition explicit
(*does `.specfuse/agent-policy.yml` already exist?*) rather than leaving a
reader to guess which half applies.

**Provenance is a hint, and the prose must say so in those terms.** The decision
and its reason are in `GATE-02-REVIEW.md` § *The provenance question*, and gate
1's retrospective is the evidence behind it. Two facts the prose must carry,
because an operator reading a review readout will otherwise over-trust it:

- A value equal to the shipped baseline **probably** was never chosen — but an
  operator who deliberately picked that exact value looks identical. Review says
  "this matches the shipped default, so it may never have been decided", never
  "this was never decided".
- A value differing from the shipped baseline **was** touched by someone. That
  direction is not lossy, and the prose should say that it is the reliable one.

**Skills are canonical in `plugins/specfuse/skills/`** and vendored into
`.specfuse/skills/` by `scripts/sync-scaffold.sh`, which also maintains the
`.claude/skills/` discovery link. `tests/test_skills_vendored_in_sync.py` and
`tests/test_skill_discovery_links.py` both fail if a skill exists in only one
place — run the script rather than hand-editing the vendored copy.

**Why a new test file rather than extending gate 1's.**
`tests/test_derive_agent_policy_skill.py` is gate 1's structural oracle for the
bootstrap half. Keeping it untouched lets gate 2's close assert the same
"existing tests pass unmodified" property gate 1 asserted for T01 — a property
gate 1's close could only partly evidence, and which is cheap to preserve here.
Criterion 8 is that assertion.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because
`tests/test_derive_agent_policy_review_mode.py` does not exist and the prose it
asserts on has not been written.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_derive_agent_policy_review_mode.py::TestReviewMode::test_prose_names_review_api_literals`
   exists and **fails on HEAD before this WU runs** (the test file is absent —
   which counts as red).
2. `plugins/specfuse/skills/derive-agent-policy/SKILL.md` gains a review-mode
   section naming `review_agent_policy` and
   `specfuse/loop/policy_review.py` as **exact literals**, so the prose fails
   this WU's test if T04's API is renamed and the prose is not.
3. The prose states the **entry condition** explicitly: an existing
   `.specfuse/agent-policy.yml` selects review mode, its absence selects the
   bootstrap interview gate 1 shipped. A test asserts both branches are named.
4. For each of the four in-scope keys the prose describes a readout carrying the
   current value, the proposal with its evidence string, the shipped baseline,
   and the provenance classification — matching the shape T04 returns. A test
   asserts all four key names appear in the review-mode section.
5. The prose states that a value matching the shipped baseline is a **hint, not
   a claim**, in words a test can find, and states the asymmetry: differing from
   the baseline reliably means someone chose it; matching it does not reliably
   mean nobody did.
6. The prose keeps review mode's corrections on the same **staged per-block
   accept** contract gate 1 established — `rules`, then `budgets`, then
   `escalation`, three separate accept/edit/reject decisions, never one blanket
   yes. A test asserts the review-mode section names all three blocks.
7. `PROMPT.md` gains the matching review-mode instructions, so an operator who
   pipes the prompt gets the review half and not only the bootstrap half. A test
   asserts `PROMPT.md` names `review_agent_policy`.
8. `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
   exits zero after this WU's edits — `test_derive_agent_policy_skill` must pass
   **unmodified**, which is the proof this WU added the review half without
   breaking the bootstrap half's contract.
9. `scripts/sync-scaffold.sh` has been run and both vendored copies
   (`SKILL.md`, `PROMPT.md`) are byte-identical to their canonical originals.

**Do not touch.** `specfuse/loop/policy_review.py` and
`specfuse/loop/policy_proposals.py` — this WU writes prose and a test, no code
change; if the prose cannot describe the module accurately, that is an
escalation, not a licence to edit the module. `specfuse/loop/agent_policy.py` —
no schema change (`PLAN.md` § *Scope boundary*).
`tests/test_derive_agent_policy_skill.py` — gate 1's oracle, and criterion 8
depends on it staying untouched. `plugins/specfuse/skills/groom-backlog/` —
`/groom-backlog`'s surface; the ownership statement there is T03's and any
further boundary text is T06's. `.specfuse/skills/` directly — edit the
canonical `plugins/` copies and run the sync script. `.specfuse/agent-policy.yml`
— the live file's values are not this WU's business. Generated directories,
secrets, `.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`,
and the remaining entries in that set. Plus the scoped run in criterion 8.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`review_agent_policy`'s shipped signature or return shape disagrees with what
criterion 4 describes — report the disagreement rather than writing prose that
describes an algorithm the module does not implement, which is the exact failure
`[FEAT-2026-0069/G2-CLOSE]` records; or describing review mode honestly would
require the skill to write a key it does not own (see T06). If
`review_agent_policy` is absent from
`plugins/specfuse/skills/derive-agent-policy/SKILL.md` in the files you edited,
emit `status: blocked` — do not claim complete.
