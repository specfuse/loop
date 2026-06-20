---
id: FEAT-2026-0028/T05
type: implementation
status: done
attempts: 0
planned_cost_usd: 1.75
oracle_env: macos_local
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `--dry-run` previews the scaffold write set without touching the target

**Objective.** Add a `--dry-run` flag to both `specfuse init` and `specfuse upgrade` that
reports the relpaths the scaffold would write under `<target>/.specfuse/` and writes
**nothing** to the real target. Finish the stub-era test sweep so `tests/test_cli.py`
exercises only the real (no-longer-stub) scaffold API.

**Context — INTERACTIVE / CROSS-REPO. This WU is verified in `specfuse/specfuse`, NOT
in this loop run.** This is `FEAT-2026-0028/T05`, gate 2 (terminal, interactive); depends
on T03 (`cmd_init` rewire) and T04 (`cmd_upgrade` rewire). The loop driver cannot dispatch
or verify sibling-repo edits. Deliverables are umbrella-repo paths: `specfuse/cli.py`,
`tests/test_cli.py`.

**Preview semantics decision (the scaffold API has NO dry-run path).** Both
`scaffold.init` and `scaffold.upgrade_specfuse` write to disk and return the written
relpaths; neither accepts a `dry_run=`. Rather than add a dry-run param to the
`specfuse-loop` API (a separate loop-repo change, OUT of this feature — see
`GATE-02-REVIEW.md`), `--dry-run` previews by running the real scaffold against a
**throwaway copy** and reporting its returned relpath list, leaving the real target
untouched:

- `init --dry-run`: if `<target>/.specfuse/` already exists, surface the same refusal as a
  real init (T03); otherwise run `scaffold.init` into a `tempfile.TemporaryDirectory()`
  and print its returned relpaths as "DRY RUN — would write N files under
  `<target>/.specfuse/`". This preview is exact: `init` writes a fresh tree independent of
  target state.
- `upgrade --dry-run`: copy the target's existing `.specfuse/` into a temp dir, run
  `scaffold.upgrade_specfuse` against the copy, and report the relpaths it would write;
  the real target is untouched and no pip-upgrade runs. The overlay's write/prune set is
  reproduced exactly because it operates on a faithful copy of the target tree. (Preview
  fidelity caveat — and the cleaner native-`dry_run` follow-up — noted in the review.)

Ground in `.specfuse/rules/result-contract.md` and `.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_cli.py::test_init_dry_run_writes_nothing` — invoke
`cli.main(["init", str(tmp_repo), "--dry-run"])` and assert `<tmp_repo>/.specfuse/` does
NOT exist afterward and the planned relpaths were printed. Fails on HEAD (no `--dry-run`
flag → argparse error / nonzero), passes after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_cli.py::test_init_dry_run_writes_nothing` exists and
   fails on HEAD before this WU's edits.
2. Both subparsers accept `--dry-run` (store_true). `specfuse init <repo> --dry-run`
   leaves `<repo>/.specfuse/` non-existent (or unchanged) and prints the planned relpaths;
   `specfuse upgrade <repo> --dry-run` leaves the target `.specfuse/` byte-unchanged,
   runs no pip-upgrade, and prints the planned write set.
3. **Writes-nothing is asserted, not assumed.** Tests capture the target tree before/after
   each `--dry-run` invocation and assert equality (init: still absent; upgrade: identical
   listing + contents). The dry-run exit code is 0 on the success path.
4. `init --dry-run` on a target that already has `.specfuse/` exits non-zero with the T03
   refusal message (dry-run does not bypass the exists-refusal).
5. **Stub sweep complete.** `tests/test_cli.py` contains no remaining assertions tied to
   the removed curl-bash / pip-only-upgrade stubs; every test exercises the real scaffold
   API (editable `specfuse-loop`). `pytest tests/test_cli.py` is green.

**Do not touch.** The scaffold API itself in `specfuse/loop/scaffold.py` (no `dry_run=`
param added here — that is a deferred loop-repo change); `pyproject.toml`'s `specfuse-loop`
pin; the `specfuse/loop` repo; the core init/upgrade success paths beyond threading the
`--dry-run` branch (T03/T04 own them); secrets; `.git/`. The loop driver owns all git —
run no `git`. Deliverables: `specfuse/cli.py`, `tests/test_cli.py` (umbrella repo).

**Verification.** Run **in `specfuse/specfuse`, not this loop**: `pytest tests/test_cli.py`
(AC1/AC3/AC4/AC5 — red→green, writes-nothing, refusal, stub sweep). The loop's only gate
on this file is the structural lint of this feature folder. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If reproducing the `upgrade` overlay against a temp copy proves
unfaithful (the prune/seed-missing logic reads paths the copy does not capture), STOP and
prefer either scoping `--dry-run` to `init` for this gate or escalating for a native
`dry_run=` param in the scaffold API — emit `status: blocked` rather than shipping a
dry-run preview that disagrees with the real overlay (a preview that lies is worse than no
preview).
