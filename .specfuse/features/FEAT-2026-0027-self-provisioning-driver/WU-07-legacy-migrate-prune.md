---
id: FEAT-2026-0027/T07
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.50
effort: high
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - tests/test_migrate_legacy.py
produces_driver_helper:
  - migrate_legacy
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Legacy `scripts/`/`skills/` migration-prune (keep-list-guarded)

**Objective.** Add `scaffold.migrate_legacy(...)`: prune a consumer repo's now-redundant
legacy `.specfuse/scripts/` and `.specfuse/skills/` copies (delivered today by the
pip-installed `specfuse-loop` and the `/specfuse:*` plugin), driven by an **explicit
keep-list** so a live shim the loop still references is never deleted. Returns the pruned
paths; `dry_run` reports without deleting.

**Context.** This is `FEAT-2026-0027/T07`, gate 3 (terminal). The forward path
(`init.sh` deprecation banner, `init.sh:24-33`) moves the driver to `pip install
specfuse-loop` and skills to the `specfuse@specfuse` plugin marketplace — so a repo that
adopted the **legacy** install model carries copies under `.specfuse/scripts/` and
`.specfuse/skills/` that are now dead weight. `specfuse init --migrate` (cross-repo
umbrella CLI) prunes them; this WU ships the loop-dispatchable scaffold **API** it calls,
mirroring `init` / `upgrade_specfuse`. **The flag `--migrate` and its CLI surface are
cross-repo contract values — verify against `specfuse/specfuse`, do not invent them
here.**

**The hazard (read before scoping the prune).** Not every file under `.specfuse/scripts/`
is legacy dead weight. Verified at draft time, `.specfuse/verification.yml` invokes
`python3 .specfuse/scripts/lint_plan.py {feature_dir}` (plannext gate) and
`python3 .specfuse/scripts/leak_scan.py --all` (code gate) — these are **live shims**
re-exporting the pip package, and a blanket prune of `.specfuse/scripts/` would break the
loop's own gates. The skill tree (`.specfuse/skills/*`) is replaced by the plugin, but in
*this* source repo the skills are symlinks (see `.claude/CLAUDE.md`) — a consumer's may be
copies. **The keep-list is the whole correctness surface of this WU.** See
`GATE-03-REVIEW.md` "If you check only three things" #2 and Open question 2 — the keep-list
must be operator-confirmed before this WU is armed. Ground in
`.specfuse/rules/result-contract.md`, `never-touch.md` (§1 generated, §3 `.git/`).

**Red-test (§12):**
`tests/test_migrate_legacy.py::TestMigrateLegacy::test_keeps_live_shims`
fails on HEAD (no `migrate_legacy` symbol) and passes after.

**Acceptance criteria.**

1. **Red test first.**
   `tests/test_migrate_legacy.py::TestMigrateLegacy::test_keeps_live_shims`
   exists and fails on HEAD before this WU's edits
   (`python3 -m unittest tests.test_migrate_legacy.TestMigrateLegacy.test_keeps_live_shims`
   exits non-zero, or the file does not yet exist — both count as red).
2. **`migrate_legacy(target, *, dry_run=False) -> list[str]`** added to `scaffold.py`. It
   prunes legacy `.specfuse/scripts/` and `.specfuse/skills/` entries that are **not** in
   an explicit module-level keep-list constant (e.g. `_MIGRATE_KEEP`), returning the
   sorted list of pruned relative paths. The keep-list MUST include every path the loop
   still references — minimally `.specfuse/scripts/lint_plan.py` and
   `.specfuse/scripts/leak_scan.py` (and any other path `.specfuse/verification.yml`
   names). It never touches anything outside `.specfuse/scripts/` and `.specfuse/skills/`.
3. **Keep-list is a hard guard, not advisory.** If a path in the keep-list would be
   selected for pruning, `migrate_legacy` raises / refuses rather than deleting it (a test
   asserts a kept shim survives a real prune and a configured keep-member is never in the
   returned prune list).
4. **`dry_run` deletes nothing.** With `dry_run=True`, `migrate_legacy` returns the same
   prune list it would delete but performs **zero** filesystem deletions (test asserts the
   target tree is byte-identical after a dry-run).
5. **Idempotent + safe on absence.** Running `migrate_legacy` twice prunes on the first
   pass and returns `[]` on the second; running it when `.specfuse/scripts/` /
   `.specfuse/skills/` are absent returns `[]` without raising.
6. The red test (AC1) passes; new unit tests cover keeps-live-shims, prunes-legacy-entry,
   dry-run-deletes-nothing, idempotent-second-run, and absent-dirs-no-op; `code` gates
   green (coverage ≥ 90), including the loop's own `plannext` + `leak-scan` gates still
   running (proving the kept shims survived).

**Do not touch.** Gate 1 + gate 2 WUs (T01–T04) and their tests; the doctor (T05) and
first-run-prompt (T06) scope; `auto_sync`'s decision tree; **any path outside
`.specfuse/scripts/` and `.specfuse/skills/`** (especially `.specfuse/features/`,
`.specfuse/rules/`, `.specfuse/templates/`, `.specfuse/verification.yml`,
`.specfuse/LEARNINGS.md`, `roadmap*.md`); the cross-repo `specfuse` CLI; secrets;
`.git/`. The driver owns all git — edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gates (`python3 -m unittest discover -s tests -v` incl.
`tests/test_migrate_legacy.py`; `ruff check`; coverage ≥ 90; the `plannext` + `leak-scan`
gates must still pass, proving `lint_plan.py` / `leak_scan.py` survived). Symbol check:
`python3 -c "from specfuse.loop.scaffold import migrate_legacy"`. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** **If the keep-list cannot be determined exhaustively** — i.e. you
cannot enumerate every `.specfuse/scripts/` / `.specfuse/skills/` path the loop or
`.specfuse/verification.yml` still references — emit `status: blocked` and name the gap
rather than shipping a prune that might delete a live dependency (the brief's explicit
escalation: do not draft a blanket prune). If pruning a skill would break a path the
plugin does **not** yet provide under `/specfuse:*` (the migration leaves a capability
gap), block and name the missing skill. If a kept path is a symlink whose target lies
outside `.specfuse/` (this source repo's skills are symlinks), do not follow + delete the
target — prune the link entry only, and if the distinction is ambiguous, block. If
`migrate_legacy` is absent from the files you edited, emit `status: blocked` — do not
claim complete.
