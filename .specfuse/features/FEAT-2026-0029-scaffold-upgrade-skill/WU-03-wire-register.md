---
id: FEAT-2026-0029/T03
type: implementation
status: blocked_human
attempts: 0
planned_cost_usd: 1.25
produces: .claude/skills/scaffold-upgrade/SKILL.md
oracle_env: macos_local
duration_seconds: 301.264
cost_usd: 1.757017
input_tokens: 14015
output_tokens: 16958
---

# Wire and register the scaffold-upgrade skill

**Objective.** Make the `scaffold-upgrade` skill discoverable and deployable:
add the `.claude/skills/` forward symlink, list it in both `skills.md` copies, and
prove it deploys readable via the init-skills bats regression.

**Context.** This is `FEAT-2026-0029/T03` (depends on T02's SKILL.md existing).
The canonical skill-packaging pattern is **real dir in `.specfuse/skills/<name>/`
+ a forward discovery symlink `.claude/skills/<name>` → `../../.specfuse/skills/<name>`**
(created by `wire_claude_code`; the inverse broke `init`/`--upgrade` in issue #56 —
see the header of `tests/init_skills_idempotent.bats`). `init.sh` copies the whole
`.specfuse/skills/` tree into targets, so no `init.sh` change is needed; the skill
just has to sit in the canonical layout and survive the bats idempotency check.

Reference the binding rules under `.specfuse/rules/`; honor them.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** extend `tests/init_skills_idempotent.bats` so a
   test asserts `scaffold-upgrade/SKILL.md` deploys as a readable file in the
   target after `init.sh` (e.g. add `scaffold-upgrade` to the checked `SKILLS`
   list or add a dedicated `@test`). The new assertion fails on HEAD because the
   skill is not yet wired/deployed.
2. `.claude/skills/scaffold-upgrade` exists as a symlink pointing at
   `../../.specfuse/skills/scaffold-upgrade` (forward direction), and
   `test -s .claude/skills/scaffold-upgrade/SKILL.md` succeeds (symlink resolves
   to a non-empty file — the #56 dangling-symlink failure mode is absent).
3. A `scaffold-upgrade` entry is added to **both** `docs/skills.md` and
   `specfuse/loop/data/docs/skills.md`, in the same one-line `- **`/name`** — …`
   style as the neighboring `wrap-feature` / `feature-conversion` entries.
   Grep-checkable: `grep -q 'scaffold-upgrade' docs/skills.md` and the data copy.
4. The extended `tests/init_skills_idempotent.bats` passes after this WU
   (`bats tests/init_skills_idempotent.bats` exits 0).

**Do not touch.** The SKILL.md body itself (T02 owns it), T01's helper/tests, the
driver and linter internals, `.git/`, secrets. Do not invert the symlink direction
(that is the #56 bug). The driver owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.** `bats tests/init_skills_idempotent.bats` (AC1/AC4);
`test -L .claude/skills/scaffold-upgrade && test -s .claude/skills/scaffold-upgrade/SKILL.md`
(AC2); the two greps in AC3. Plus the repo `code` gates (`tests`, `lint`) to
confirm nothing else regressed.

**Escalation triggers.** If T02's SKILL.md is absent (the dependency did not
produce its file), emit `status: blocked` — there is nothing to wire. If the bats
harness cannot run in the execution environment (`bats` not installed), emit
`status: blocked` naming the missing dependency rather than skipping the
regression. Blocked is respectable (`result-contract.md` rule 4).
