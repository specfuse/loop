---
id: FEAT-2026-0010/T05
type: implementation
effort: medium
status: done
attempts: 2
duration_seconds: 841.032
cost_usd: 2.052703
input_tokens: 56
output_tokens: 38302
---

# Driver auto-archive hook on feature completion

**Objective.** Wire the driver so that when a feature's gates are all
`passed` and `loop.py` flips its `PLAN.md` `status` to `complete`, it
also archives the feature's roadmap detail section in the same run —
moving the inline `## FEAT-…` section out of `.specfuse/roadmap.md`
into `.specfuse/roadmap-archive.md` and replacing the Detail cell `—`
with the back-link. Idempotent. This is the deferred Scope OUT item
from PLAN.md ("Auto-archive hook in loop.py at PLAN status flip —
manual-first cut; auto follow-up after this feature lands").

**Context.** Correlation ID `FEAT-2026-0010/T05`. Read
`.specfuse/scripts/loop.py` to see the existing feature-complete
branch (the `gate is None` arm at the top of `run()` where
`write_frontmatter_field(feature_dir / "PLAN.md", "status", "complete")`
is called). The hook fires AFTER that flip, BEFORE `return 0`. Read
`.specfuse/skills/roadmap-archive/SKILL.md` for the canonical
algorithm — Steps 1–6 of `Algorithm — single feature` are what the
new helper must reproduce. Read `FEAT-2026-0010/T04`
(`WU-04-migrate-done-features.md`) for the precedent of direct
re-implementation vs subprocess invocation; per `[FEAT-2026-0010/G1]`
LEARNINGS entry on "subprocess vs re-implement", a Python helper that
re-implements the algorithm directly is the right shape here — the
driver is Python and cannot reliably shell out to a markdown skill.
The load-bearing strings (anchor literal `<a id="feat-yyyy-nnnn"></a>`
and back-link literal `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`)
are owned by `.specfuse/roadmap-archive.md`'s Conventions section and
the skill SKILL.md; quote them verbatim. Binding rules in
`.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`correlation-ids.md`) apply.

**Acceptance criteria.**

1. `.specfuse/scripts/loop.py` defines a new top-level function
   `auto_archive_feature(feature_id: str, repo_root: pathlib.Path) -> str`
   that implements Steps 1–6 of the `roadmap-archive` skill's
   single-feature algorithm against `repo_root / ".specfuse/roadmap.md"`
   and `repo_root / ".specfuse/roadmap-archive.md"`. Returns one of
   `"archived"`, `"already archived"`, or `"refused: <reason>"` (the
   skill's exact wire format minus the leading feature-id prefix).
   Verifiable: `python3 -c "from importlib import import_module; m =
   import_module('loop', package=None); assert
   hasattr(m, 'auto_archive_feature')"` (run with PYTHONPATH set to
   `.specfuse/scripts`).
2. The `run()` function's `gate is None` branch (the existing
   all-gates-passed completion branch) is amended: after the
   `write_frontmatter_field(... "status", "complete")` call and before
   `return 0`, it invokes `auto_archive_feature(feature_id, REPO_ROOT)`
   and prints the resulting status line (e.g.
   `f"{feature_id}: archived"` or
   `f"{feature_id}: already archived"`). On any return value beginning
   with `refused:`, the driver prints a warning and continues — refusal
   is not a driver failure (the feature is `complete` and the operator
   can run `/roadmap-archive` manually).
3. `tests/test_loop_auto_archive.py` exists and exercises the helper
   end-to-end against a temp-repo fixture. The fixture writes a minimal
   `.specfuse/roadmap.md` (one `done` data row plus a matching inline
   detail section) and a minimal `.specfuse/roadmap-archive.md`
   (scaffold with the `<!-- Archived sections appended below -->`
   marker). Required test cases: (a) happy path — `done` row with `—`
   Detail cell and inline section → returns `"archived"`, mutates both
   files, the Detail cell is the exact back-link literal, the archive
   has the exact anchor literal above the moved section; (b)
   idempotency — calling the helper a second time on the same fixture
   returns `"already archived"` and makes zero further file edits
   (verified by file-mtime or byte-equal compare against a snapshot);
   (c) refusal — a `planned` row returns `"refused: status=planned"`
   and makes zero file edits.
4. The fixture in (3) follows the `[FEAT-2026-0013/G1-CLOSE]`
   tempdir-race rule: `git init` is not required (no git operations in
   the helper), but if the test does spawn any git subprocess for any
   reason it must use `-c gc.auto=0` and the sync-barrier pattern;
   `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` is
   acceptable.
5. The new helper does NOT shell out to the skill, does NOT run `git`,
   and does NOT touch any path outside `.specfuse/roadmap.md` /
   `.specfuse/roadmap-archive.md`. The driver's existing
   `commit_bookkeeping` path is the surface that commits these edits —
   the helper itself returns without committing.

**Do not touch.** The `roadmap-archive` skill at
`.specfuse/skills/roadmap-archive/SKILL.md` and its symlink under
`.claude/skills/` (T02 owns the skill; this WU re-implements the
algorithm in-driver, leaves the skill intact for human use). The
`roadmap-add` skill (T03 owns). Any other feature's WU file or detail
section. Any path under `.specfuse/features/FEAT-2026-0010-…/` other
than this WU's own file. Templates. Rules. `.git/`. Generated
directories (none here, but the rule stands). Secrets (`.env`,
`*.pem`, `*.key`, `credentials.json`). **The driver owns all git
operations — do not run `git`.** See `.specfuse/rules/never-touch.md`.

Expected total file count touched: exactly 2 — `.specfuse/scripts/loop.py`
and `tests/test_loop_auto_archive.py` (new). The squash commit must touch
no other paths.

**Verification.**

- `python3 -m unittest discover -s tests -v` — full suite stays green;
  the new test file is included.
- Scoped: `python3 -m unittest tests.test_loop_auto_archive -v` exits 0
  with all three test cases passing.
- Symbol existence (per
  `.specfuse/skills/authoring-work-units/SKILL.md` §9):
  `PYTHONPATH=.specfuse/scripts python3 -c "from loop import
  auto_archive_feature"` exits 0.
- Lint: `ruff check .specfuse/scripts tests scripts` passes.
- Security: `bandit -r .specfuse/scripts -ll` passes.
- Coverage: `coverage run --source=.specfuse/scripts -m unittest
  discover -s tests && coverage report --fail-under=90` passes
  (consistent with the project floor).

**Escalation triggers.**

- If `.specfuse/scripts/loop.py`'s `gate is None` completion branch
  cannot be located or its shape has changed substantially (the
  `write_frontmatter_field(... "status", "complete")` line is no longer
  there, or it has been refactored into a separate function), emit
  `status: blocked` — naming the structural drift — rather than
  guessing where the hook belongs. The driver's completion path is
  load-bearing.
- If `.specfuse/roadmap-archive.md`'s `<!-- Archived sections appended
  below -->` marker is absent at execution time, emit `status: blocked` —
  the skill's algorithm and this helper both depend on it; absence
  implies T01 was undone or the file was hand-rewritten.
- If the new helper or test cannot reproduce the load-bearing string
  literals verbatim because of Python escaping, encoding, or Markdown
  parser surprises, emit `status: blocked` rather than substituting a
  visually-similar variant. T01, T02, T04 all rely on byte-exact
  matches.
- If `auto_archive_feature` is absent from your edits to `loop.py` at
  the end of the session, emit `status: blocked` — per
  `[FEAT-2026-0007/G1-LESSONS]` and `.specfuse/skills/
  authoring-work-units/SKILL.md` §9, completeness escalation fires
  before RESULT, not after.
