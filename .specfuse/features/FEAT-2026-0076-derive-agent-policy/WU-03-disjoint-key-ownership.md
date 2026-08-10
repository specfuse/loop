---
id: FEAT-2026-0076/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/groom-backlog/SKILL.md
  - tests/test_agent_policy_key_ownership.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T15:15:15.068244+00:00
duration_seconds: 1187.617
cost_usd: 2.544881
input_tokens: 100
output_tokens: 25203
---

# Write the disjoint-key boundary into both skills

**Objective.** State the key-ownership boundary as a hard rule in **both**
`derive-agent-policy` and `/groom-backlog`, and ship the test that fails if
either widens into the other's keys.

**Context.** Correlation ID `FEAT-2026-0076/T03`. Depends on
`FEAT-2026-0076/T02`, which creates one of the two files this WU edits.

**Why this exists, in the operator's own words.** This repository has repeatedly
justified design decisions with *"one writer per config file"* — it is why
`derive-verification` does not write `agent-policy.yml`, and why
`/groom-backlog` was scoped to a single file. **This feature breaks that
principle**: `/groom-backlog` already writes `agent-policy.yml`, so
`derive-agent-policy` is a second writer of the same file.

The operator's decision (PLAN.md decision 2) was **disjoint key ownership**: the
invariant becomes *one writer per key block*, not per file. That is a weaker
invariant than the one it replaces, and a weaker invariant that lives only in
someone's memory decays. Hence this WU: it is written down in both places, and a
test fails if it stops being true.

**The boundary, exactly:**

| Skill | Owns | Must never write |
|---|---|---|
| `derive-agent-policy` | `rules`, `budgets`, `escalation` | `queue` |
| `/groom-backlog` | `queue` | `rules`, `budgets`, `escalation` |

Both skills state their own ownership **and** disclaim the other's. Stating only
what you own is what lets a later edit widen a skill "helpfully" — the disclaimer
is the half that makes the boundary testable.

**Scope note, recorded at drafting.** Editing `/groom-backlog` is technically
another feature's surface (FEAT-2026-0044 shipped it). It is kept in this feature
because the decision that created the boundary is this feature's, and splitting
it would leave the boundary written on one side only — which is the same as not
writing it down. Surfaced to the operator at drafting and kept deliberately.

**Skills are canonical in `plugins/specfuse/skills/`.** Edit both canonical
copies, then run `scripts/sync-scaffold.sh`.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because
`/groom-backlog` does not yet disclaim the other blocks.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_agent_policy_key_ownership.py::TestKeyOwnership::test_groom_backlog_disclaims_the_other_blocks`
   exists and **fails on HEAD before this WU runs** (the disclaimer is absent).
2. `plugins/specfuse/skills/groom-backlog/SKILL.md` states that it owns `queue:`
   and **must never write** `rules`, `budgets`, or `escalation`, naming
   `derive-agent-policy` as their owner.
3. `plugins/specfuse/skills/derive-agent-policy/SKILL.md` states that it owns
   `rules`, `budgets`, and `escalation` and **must never write** `queue:`,
   naming `/groom-backlog` as its owner.
4. A test asserts, for each skill, that its body names **every** key block it
   owns.
5. A test asserts, for each skill, that its body names **every** key block it
   must not write, so a future edit widening one skill fails rather than passing
   silently.
6. The two ownership sets are **disjoint and exhaustive** over the file's
   non-`version` top-level keys — a test derives the union from the two skills'
   stated sets and asserts it covers `queue`, `rules`, `budgets`, `escalation`
   with no overlap. A new top-level key added later with no owner fails this
   test, which is the intended alarm.
7. Both skills state the invariant in the form the operator chose: **one writer
   per key block**, not per file — so a reader who remembers the older
   per-file phrasing sees why it changed.
8. `scripts/sync-scaffold.sh` has been run and both vendored copies are
   byte-identical to their canonical originals.
9. `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
   exits zero after this WU's edits — `test_groom_backlog_skill` must still pass
   untouched, which is the proof this WU added to that skill without breaking
   its existing contract.

**Do not touch.** `specfuse/loop/agent_policy.py` — this WU writes prose and a
test, no schema or validation changes. `specfuse/loop/policy_proposals.py`.
`.specfuse/agent-policy.yml` — the live file's *values* are not this WU's
business. `.specfuse/skills/` directly — edit the canonical `plugins/` copies.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped run in criterion 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
criterion 6's exhaustiveness check cannot be satisfied because the schema carries
a top-level key neither skill should own (report which — an unowned key is a real
gap, not a test to loosen); or editing `/groom-backlog` would require changing
its existing behaviour rather than adding a statement of boundary. If the
disclaimer is absent from `plugins/specfuse/skills/groom-backlog/SKILL.md` in the
files you edited, emit `status: blocked` — do not claim complete.
