---
id: FEAT-2026-0028/T04
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


# `specfuse upgrade <repo>` overlays the seed, then pip-upgrades

**Objective.** Rewire `cmd_upgrade` so `specfuse upgrade <repo>` first overlays the
versioned scaffold onto the target's `.specfuse/` via
`specfuse.loop.scaffold.upgrade_specfuse(target)` (never-downgrade honored), then runs
the existing pip-upgrade of `specfuse-loop`+`specfuse` and prints the `/plugin update`
hint. Add the required `target` positional to the `upgrade` subcommand.

**Context — INTERACTIVE / CROSS-REPO. This WU is verified in `specfuse/specfuse`, NOT
in this loop run.** This is `FEAT-2026-0028/T04`, gate 2 (terminal, interactive); the
loop driver cannot dispatch or verify sibling-repo edits (see T03's context). Deliverables
are umbrella-repo paths: `specfuse/cli.py`, `tests/test_cli.py`.

Today `cmd_upgrade` takes **no** target — it only pip-upgrades the two packages and
prints the plugin hint. The rewire adds a `target` positional (`specfuse upgrade <repo>`)
and an overlay step. The scaffold API:
`scaffold.upgrade_specfuse(target, *, ci_check=None) -> list[str]` overlays the versioned
seed (templates/, rules/, verification.yml.example, VERSION, docs/), prunes versioned
files the seed dropped, seeds missing user-authored files, re-wires `.claude/`, and
returns the sorted relpaths written; it raises `scaffold.ScaffoldDowngradeError` when the
target's `.specfuse/VERSION` is newer than the installed seed.

**Ordering decision (overlay BEFORE pip-upgrade) — with rationale.** `cmd_upgrade`
overlays with the *currently installed* seed, then pip-upgrades the packages. A
pip-upgrade in the running process replaces the on-disk package but NOT the already
imported `specfuse.loop.scaffold` module, so overlaying *after* pip-upgrade in the same
process would still apply the OLD seed unless the process re-execs. Overlay-first is the
honest single-process order: this run overlays the current seed; the pip-upgrade means the
NEXT `specfuse upgrade` overlays the newer one. The re-exec-after-pip alternative (apply
the just-fetched seed in one invocation) is deferred — see `GATE-02-REVIEW.md` open
questions. Ground in `.specfuse/rules/result-contract.md` and
`.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_cli.py::test_upgrade_overlays_then_pip` — on a tmp repo
holding a stale `.specfuse/` (older/partial seed), assert (a) `upgrade_specfuse` ran (the
target's `.specfuse/` is refreshed — e.g. `VERSION` now matches the installed seed) and
(b) the pip-upgrade runner was invoked, in that order. Fails on HEAD (no overlay; no
target arg), passes after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_cli.py::test_upgrade_overlays_then_pip` exists and
   fails on HEAD before this WU's edits (HEAD `cmd_upgrade` neither overlays nor accepts a
   target).
2. The `upgrade` subparser gains a required `target` positional; `specfuse upgrade <repo>`
   calls `scaffold.upgrade_specfuse(target)` **before** the pip-upgrade, then runs the
   existing `_pip_install(["specfuse-loop", "specfuse"], upgrade=True)` and prints
   `PLUGIN_UPDATE_HINT`. A test asserts the overlay precedes the pip call.
3. **Downgrade refusal surfaces cleanly.** When `upgrade_specfuse` raises
   `scaffold.ScaffoldDowngradeError`, it is caught and turned into a non-zero exit with a
   stderr message conveying the refusal; the pip-upgrade does NOT run. A test asserts the
   non-zero exit and that the pip runner was not called.
4. A pip-upgrade failure (`_pip_install` returns non-zero) still propagates as a non-zero
   exit with the existing diagnostic — behavior preserved (overlay already succeeded).
5. AC1/AC3 tests pass after the edits; `pytest tests/test_cli.py` is green; stub-era
   upgrade assertions (pip-only, no target) are removed, not left dangling.

**Do not touch.** `cmd_init` and its tests (T03 owns the init rewire); the `--dry-run`
flag (T05 owns it); `pyproject.toml`'s `specfuse-loop` pin (stays `>=0.2.0`); the
`specfuse/loop` repo; secrets; `.git/`. The loop driver owns all git — run no `git`.
Deliverables: `specfuse/cli.py`, `tests/test_cli.py` (umbrella repo).

**Verification.** Run **in `specfuse/specfuse`, not this loop**: `pytest tests/test_cli.py`
(AC1/AC3/AC5 ordering + refusal); `python -c "import specfuse.cli"`. The loop's only gate
on this file is the structural lint of this feature folder. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `upgrade_specfuse`'s signature or downgrade-exception name on
the editable `specfuse-loop` differs from
`upgrade_specfuse(target, *, ci_check=None) -> list[str]` / `ScaffoldDowngradeError`,
STOP and reconcile against the installed `specfuse.loop.scaffold` source, emitting
`status: blocked` with the mismatch (authoring §8). If the overlay-before-pip ordering
proves wrong in practice (e.g. the team wants re-exec-after-pip), raise it rather than
silently re-ordering — the rationale above is load-bearing.
