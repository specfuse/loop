---
id: FEAT-2026-0029/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.75
produces: .specfuse/skills/scaffold-upgrade/SKILL.md
---

# Author the scaffold-upgrade skill (SKILL.md)

**Objective.** Write `.specfuse/skills/scaffold-upgrade/SKILL.md` — the Claude
Code skill that dry-run-reports or end-to-end upgrades a target project's Specfuse
scaffold, calling T01's helper for the merge-safety decision.

**Context.** This is `FEAT-2026-0029/T02`. It wraps the existing
`specfuse upgrade [--dry-run] <target>` CLI in the git choreography humans repeat
by hand. Model the file on `.specfuse/skills/wrap-feature/SKILL.md` (the closest
analog — push / open PR / watch CI / merge, pure markdown, single-confirm on
outward-facing steps, graceful degradation when `gh` is absent) and on the shape
of the other skills under `.specfuse/skills/`. This WU produces prose
instructions, not code.

`Red-test exempt:` pure-markdown skill — no code behavior to red→green. (The
red→green proof lives in T01's helper and T03's deploy bats.)

**Acceptance criteria.**

1. `.specfuse/skills/scaffold-upgrade/SKILL.md` exists with YAML frontmatter whose
   `name:` is `scaffold-upgrade` and a `description:` that states it upgrades a
   target project's scaffold and supports `--dry-run`. Grep-checkable:
   `grep -q 'name: scaffold-upgrade' .specfuse/skills/scaffold-upgrade/SKILL.md`.
2. A **Dry-run** section documents: run `specfuse upgrade --dry-run <target>`,
   print the would-change summary, and **state plainly that an upgrade would be
   performed** — with NO branch/commit/push/PR (report only). Grep-checkable that
   the words "dry-run" and "would be performed" appear.
3. A **Live flow** section documents these steps in this order, each named
   explicitly: (a) refuse if the target working tree is dirty, or `gh` is absent,
   or the `specfuse` CLI is absent; (b) `git fetch origin` then open a `chore/…`
   branch off `origin/main` (fresh remote base, not stale local main);
   (c) run `specfuse upgrade <target>`; (d) commit; (e) push `--no-verify`;
   (f) open a PR via `gh pr create`; (g) watch CI to green; (h) call
   `.specfuse/scripts/upgrade_merge_gate.py`'s `decide(...)` with CI status + the
   post-upgrade health report; (i) on `merge` → squash-merge; on `halt` → STOP and
   point the operator at `/feature-conversion`, naming the FAIL features.
4. A **Target** subsection documents the path-arg (defaults to cwd), mirroring
   `specfuse upgrade <target>`.
5. A **Hard rules** section forbids: force-merging past branch protection, merging
   on any health FAIL, and editing feature folders (conversion is a hand-off, not
   this skill's job). It states the skill does NOT change `specfuse upgrade`'s own
   behavior.
6. The file follows the structural conventions of the sibling skills (a
   `## When to invoke`, a hard-rules block, and a `## What this skill does NOT do`
   section are present).

**Do not touch.** T01's helper and its tests, T03's wiring/docs, the driver and
linter internals, `.git/`, secrets. Edit only the new SKILL.md. The driver owns
all git. See `.specfuse/rules/never-touch.md`.

**Verification.** No `code` gate exercises a markdown skill; verify with the
grep-assertions in AC1–AC3 and a read-through against `wrap-feature/SKILL.md` for
structural parity. Confirm the file is valid: it has frontmatter delimited by
`---` and a level-1 `#` title.

**Escalation triggers.** If the health-report shape that step (h) must pass to
`decide(...)` is not yet pinned by T01 (T01 blocked or its parser undecided), emit
`status: blocked` — the skill must call the helper with the real report format,
not an invented one. If the file cannot be created at
`.specfuse/skills/scaffold-upgrade/SKILL.md`, emit `status: blocked` — do not claim
complete. Blocked is respectable (`result-contract.md` rule 4).
