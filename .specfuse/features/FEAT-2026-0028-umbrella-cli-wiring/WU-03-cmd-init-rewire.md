---
id: FEAT-2026-0028/T03
type: implementation
status: done
attempts: 0
planned_cost_usd: 1.50
oracle_env: macos_local
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse init <repo>` calls the scaffold API (drop the curl-bash bridge)

**Objective.** Rewire the umbrella CLI's `cmd_init` so `specfuse init <repo>` scaffolds
`.specfuse/` by calling `specfuse.loop.scaffold.init(target, ci_check=...)` instead of
pip-installing the driver and printing a curl-bash bootstrap. Surface the
`.specfuse/`-already-exists refusal cleanly (point at `specfuse upgrade`).

**Context — INTERACTIVE / CROSS-REPO. This WU is verified in `specfuse/specfuse`, NOT
in this loop run.** This is `FEAT-2026-0028/T03`, gate 2 (terminal, interactive). The
loop driver runs in the `specfuse/loop` repo and cannot dispatch or verify edits to the
sibling `specfuse/specfuse` umbrella repo — a human runs this WU there, against an
**editable** `specfuse-loop` (the scaffold API lives on `specfuse-loop` `main`, not a
release). The deliverables are umbrella-repo paths: `specfuse/cli.py` and
`tests/test_cli.py`.

Today (pre-rewire) `specfuse/cli.py::cmd_init` does `_pip_install(["specfuse-loop"])`
then prints a `curl … init.sh | bash` bootstrap and the plugin hint — it does NOT
scaffold. The umbrella already declares `specfuse-loop>=0.2.0` as a hard dependency, so
`from specfuse.loop import scaffold` is importable at runtime; no init-time pip install
is needed. The scaffold API:
`scaffold.init(target, *, ci_check=None) -> list[str]` writes a fresh `.specfuse/` tree
and wires `.claude/`, returning the sorted relpaths written; it raises
`scaffold.ScaffoldExistsError` (subclass of `Exception`) when `<target>/.specfuse/`
already exists and writes nothing. Ground in `.specfuse/rules/result-contract.md` and
`.specfuse/rules/never-touch.md`. The `specfuse-loop` dep string stays `>=0.2.0` — the
bump to `>=0.3.0` is the coordinated release, OUT of this feature.

**Red-test (§12):** `tests/test_cli.py::test_init_scaffolds_specfuse_tree` — invoke
`cli.main(["init", str(tmp_repo)])` on a tmp repo with no `.specfuse/` and assert
`<tmp_repo>/.specfuse/` now exists with the seed tree. Fails on HEAD (curl-bash stub
writes nothing), passes after the rewire.

**Acceptance criteria.**

1. **Red test first.** `tests/test_cli.py::test_init_scaffolds_specfuse_tree` exists and
   fails on HEAD (the stub `cmd_init` writes no `.specfuse/`) before this WU's edits.
2. `cmd_init` calls `specfuse.loop.scaffold.init(target, ci_check=<resolved>)` and, on
   success, prints a one-line summary of what was scaffolded (e.g. file count under
   `<target>/.specfuse/`) plus `PLUGIN_UPDATE_HINT`; it no longer prints any
   `curl … init.sh | bash` text and no longer pip-installs `specfuse-loop` at init time.
   (`grep -L 'curl' specfuse/cli.py` — the curl bootstrap string is gone.)
3. **Refusal surfaces cleanly.** When `<target>/.specfuse/` already exists,
   `scaffold.ScaffoldExistsError` is caught and turned into a non-zero exit with a
   stderr message that names the path and points the operator at `specfuse upgrade`;
   nothing is scaffolded. A test asserts the exit code is non-zero and the message
   mentions `upgrade`.
4. A non-directory / missing `target` still exits non-zero with the existing
   "not a directory" diagnostic (behavior preserved).
5. `test_init_scaffolds_specfuse_tree` (AC1) and the refusal test (AC3) pass after the
   edits; the umbrella's `pytest tests/test_cli.py` is green; the stub-era init
   assertions (curl/pip-install-at-init) are removed, not left dangling.

**Do not touch.** `cmd_upgrade` and its tests (T04 owns the upgrade rewire); the
`--dry-run` flag (T05 owns it); `pyproject.toml`'s `specfuse-loop` version pin (stays
`>=0.2.0` — the bump is the coordinated release, out of scope); the `specfuse/loop` repo
(this WU edits only the umbrella `specfuse/specfuse`); secrets; `.git/`. The loop driver
owns all git — run no `git`. Deliverables: `specfuse/cli.py`, `tests/test_cli.py` (in
the umbrella repo).

**Verification.** Run **in `specfuse/specfuse`, not this loop**: `pytest tests/test_cli.py`
(red→green proof AC1/AC5; refusal AC3); `python -c "import specfuse.cli"` import check;
`grep` confirming the curl string is gone (AC2). The loop's only gate on this file is the
structural lint of this feature folder — the umbrella tests are the real oracle and run
in that repo. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `scaffold.init`'s signature on the editable `specfuse-loop`
differs from `init(target, *, ci_check=None) -> list[str]` (e.g. `ci_check` removed, or a
different exists-refusal exception name), STOP and reconcile against the installed
`specfuse.loop.scaffold` source rather than coding to this spec's remembered signature —
emit `status: blocked` naming the mismatch (authoring §8: verify cross-surface contract
values against the source).
