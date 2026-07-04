---
id: FEAT-2026-0029/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.25
produces: .claude/skills/scaffold-upgrade/SKILL.md
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.6
started_at: 2026-07-04T03:51:19.194501+00:00
duration_seconds: 163.722
cost_usd: 0.346482
input_tokens: 13430
output_tokens: 1710
---

# Wire and register the scaffold-upgrade skill

**Objective.** Register the `scaffold-upgrade` skill in the source-repo layout the
Specfuse **plugin** ships from: add the `.claude/skills/` forward discovery symlink
and list the skill in both `skills.md` copies.

`Red-test exempt:` wiring + docs only — no new runtime behavior. The behavioral
red→green proofs live in T01 (the helper) and T02 (the skill body).

**Context.** This is `FEAT-2026-0029/T03` (depends on T02's SKILL.md existing).
Specfuse skills are delivered to target projects by the **Claude Code plugin**
(`/plugin install specfuse@specfuse`), NOT by the pip scaffold — see
`docs/getting-started.md` ("The skills come from the plugin, not from" the
scaffold). The source-of-truth layout the plugin publishes is **real dir in
`.specfuse/skills/<name>/` + a forward discovery symlink
`.claude/skills/<name>` → `../../.specfuse/skills/<name>`** (created by
`wire_claude_code`; the inverse broke discovery in issue #56 — see the header of
`tests/init_skills_idempotent.bats`). This WU puts the new skill into that layout
and documents it. There is no `init.sh` / `specfuse init` change to make — the CLI
deliberately does not copy skills.

**Known pre-existing defect — OUT OF SCOPE, do not fix here.** Tests 1 and 2 of
`tests/init_skills_idempotent.bats` assert `specfuse init` deploys `.specfuse/skills/`
into a target; those tests are **already red on HEAD** (verified) because they
encode the pre-FEAT-2026-0026 "init.sh copies skills" model that the plugin
delivery replaced. That test is not a CI gate and its staleness is a separate
concern (tracked outside this feature). Do NOT make it pass, weaken it, or fix
`scaffold.py` skill-deploy to satisfy it — that is scaffold-internals territory and
a different unit of work. Only test 3 (`source repo holds skill content in
.specfuse (real), not .claude`) is the live invariant this WU must keep green.

Reference the binding rules under `.specfuse/rules/`; honor them.

**Acceptance criteria.**

1. `.claude/skills/scaffold-upgrade` exists as a symlink pointing at
   `../../.specfuse/skills/scaffold-upgrade` (forward direction), and
   `test -s .claude/skills/scaffold-upgrade/SKILL.md` succeeds (resolves to a
   non-empty file — the #56 dangling-symlink failure mode is absent).
2. A `scaffold-upgrade` entry is added to **both** `docs/skills.md` and
   `specfuse/loop/data/docs/skills.md`, in the same one-line style as the
   neighboring `wrap-feature` / `feature-conversion` entries. Grep-checkable:
   `grep -q 'scaffold-upgrade' docs/skills.md` and the data copy.
3. `bats tests/init_skills_idempotent.bats -f 'source repo holds'` (test 3 only)
   still passes — the source-layout invariant is intact. (Tests 1 & 2 remain
   pre-existing-red and are out of scope per the note above; do not run the whole
   file as a pass/fail gate.)

**Do not touch.** The SKILL.md body itself (T02 owns it), T01's helper/tests, the
driver, linter, and `scaffold.py` internals, the stale `init_skills_idempotent.bats`
tests 1 & 2, `.git/`, secrets. Do not invert the symlink direction (that is the #56
bug). The driver owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.**
`test -L .claude/skills/scaffold-upgrade && test -s .claude/skills/scaffold-upgrade/SKILL.md`
(AC1); the two greps in AC2; `bats tests/init_skills_idempotent.bats -f 'source repo holds'`
(AC3). Plus the repo `code` gates (`tests`, `lint`) to confirm nothing regressed.

**Escalation triggers.** If T02's SKILL.md is absent (the dependency did not
produce its file), emit `status: blocked` — there is nothing to wire. If wiring the
skill into the plugin source layout turns out to require a change outside this WU's
scope (e.g. a `scaffold.py` or plugin-manifest edit), emit `status: blocked` naming
it rather than reaching into driver internals. Blocked is respectable
(`result-contract.md` rule 4).
