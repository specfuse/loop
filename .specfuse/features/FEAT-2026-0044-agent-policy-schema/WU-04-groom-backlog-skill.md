---
id: FEAT-2026-0044/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/groom-backlog/SKILL.md
  - tests/test_groom_backlog_skill.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T03:52:23.366925+00:00
duration_seconds: 385.41
cost_usd: 0.784942
input_tokens: 1212
output_tokens: 9300
---

# Ship the `/groom-backlog` skill

**Objective.** Create `plugins/specfuse/skills/groom-backlog/SKILL.md` — the
periodic ritual that reads real repo state, surfaces queue-hygiene findings and
per-candidate trade-offs, proposes a new ordered queue, and writes
`.specfuse/agent-policy.yml` only on explicit operator accept.

**Context.** Correlation ID `FEAT-2026-0044/T04`. Depends on
`FEAT-2026-0044/T02` for `load_policy` and the queue-drift findings. Independent
of T03.

The policy file without a grooming ritual goes stale the week it is written:
features complete, issues arrive triaged, blockers clear. The roadmap row calls
this "a ten-minute periodic grooming session [that] keeps the agent autonomous
between check-ins."

**Copy the output shape of `/pick-feature`, not its algorithm.** Read
`plugins/specfuse/skills/pick-feature/SKILL.md` first. Its decision shape is the
one the roadmap row names — per-candidate trade-offs in prose with a
recommendation, the human picks. The difference: `/pick-feature` selects **one**
feature and flips it `active`; `/groom-backlog` proposes an **ordered queue**
and writes the policy file. Do not import or restate `/pick-feature`'s hats
wholesale; reference the skill.

**Skills are canonical in `plugins/specfuse/skills/`.** Author there, then run
`scripts/sync-scaffold.sh` to vendor into `.specfuse/skills/`.
`tests/test_skills_vendored_in_sync.py` and
`tests/test_skill_discovery_links.py` both fail if a skill exists in only one
place or has no `.claude/skills/` discovery link — the sync script creates the
link, so run it rather than making the link by hand.

**Load-bearing strings from T01/T02, quoted verbatim:** config path
`.specfuse/agent-policy.yml`; module `specfuse/loop/agent_policy.py`; reader
`load_policy`; validator `validate_agent_policy`; finding prefixes `ERROR: ` and
`WARN: `; queue key is top-level `queue:`.

**The skill's required contract**, which the tests in criterion 1 assert on:

- **Reads, in this order:** the current `queue:` via `load_policy`; queue-drift
  findings via `validate_agent_policy`; the roadmap's `planned` / `active` /
  `blocked` rows; open issues carrying a triage marker; and `LEARNINGS.md`.
- **Surfaces queue hygiene first** — entries whose feature is `done` or
  `abandoned` (the `WARN: ` findings from T02) proposed for removal; entries
  that do not exist (`ERROR: `) flagged as unresolvable by the skill; and
  `blocked` entries whose blocker is itself queued, noted as a reorder
  candidate.
- **Then per-candidate trade-offs in prose**, with a recommended order and the
  one reason each position is where it is.
- **Writes only on explicit accept**, and writes exactly one file:
  `.specfuse/agent-policy.yml`. It does not flip roadmap statuses, does not
  create features, and does not touch `PLAN.md` frontmatter — `/pick-feature`
  and `/draft-feature` own those.
- **No `--auto` mode.** An unattended process rewriting the operator's own
  priority declaration inverts the point of the file. State this as a hard rule
  in the skill's "What this skill does NOT do" section.
- **Empty queue is a valid outcome**, not a failure: it means the agent works
  bugs only and asks for priorities.
- Carries the standard **escalation-framing** section binding it to
  `.specfuse/rules/operator-escalation.md`, matching every other skill in the
  directory.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
skill file does not exist. The test asserts on the skill's *structure* — a
markdown contract test, the same shape other skill guards in this repo use.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_groom_backlog_skill.py::TestGroomBacklogSkill::test_skill_file_exists`
   exists and **fails on HEAD before this WU runs**.
2. `plugins/specfuse/skills/groom-backlog/SKILL.md` exists with YAML
   frontmatter carrying `name: groom-backlog` and a `description:` that names
   the trigger phrases (`/groom-backlog`, "groom the backlog", "update the
   queue").
3. A test asserts the skill body names `.specfuse/agent-policy.yml`,
   `load_policy`, and `validate_agent_policy` as exact-match literals — the
   skill must reference the real API, not describe it approximately.
4. A test asserts the skill body contains a "What this skill does NOT do"
   section that states it has no `--auto` mode and writes only on explicit
   accept.
5. A test asserts the skill body states that the only file it writes is
   `.specfuse/agent-policy.yml`.
6. A test asserts the skill body contains the escalation-framing section
   referencing `.specfuse/rules/operator-escalation.md`, matching the other
   skills in the directory.
7. A test asserts the skill body documents the queue-hygiene pass and
   distinguishes the `WARN: ` (proposed for removal) case from the `ERROR: `
   (unresolvable, human must fix) case.
8. A test asserts the skill body states that an empty queue is a valid accepted
   outcome.
9. The skill carries the Apache-2.0 comment header used by every other skill in
   `plugins/specfuse/skills/`.
10. `scripts/sync-scaffold.sh` has been run;
    `.specfuse/skills/groom-backlog/SKILL.md` is byte-identical to the canonical
    copy and `.claude/skills/groom-backlog` is a symlink resolving to it.
11. `python3 -m unittest tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
    exits zero after this WU's edits.

**Do not touch.** `plugins/specfuse/skills/pick-feature/SKILL.md` — read it for
shape, do not edit it. `specfuse/loop/agent_policy.py` — T01 and T02 own it;
this WU consumes the API, it does not extend it. `.specfuse/agent-policy.yml` —
T02 authored the dogfood file; the skill *describes* writing it, this WU does
not rewrite it. `.specfuse/skills/groom-backlog/` directly — author the
canonical `plugins/` copy and let the sync script vendor it. `.specfuse/roadmap.md`.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, plus
`agent-policy-example-lint`. Plus the scoped run in criterion 11.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`scripts/sync-scaffold.sh` fails or reports drift in surfaces this WU did not
touch; or the skill cannot be written without deciding a policy question this
feature deliberately left out of scope (the scoring formula is FEAT-2026-0011's
and is `blocked` on ADR-0002 — the queue here is an operator-authored order, not
a computed ranking; if grooming seems to require a score, stop and report).
If `plugins/specfuse/skills/groom-backlog/SKILL.md` is absent from the files you
edited, emit `status: blocked` — do not claim complete.
