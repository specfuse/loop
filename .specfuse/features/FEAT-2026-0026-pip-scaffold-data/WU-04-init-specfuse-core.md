---
id: FEAT-2026-0026/T04
type: implementation
effort: high
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_init.py
duration_seconds: 286.185
cost_usd: 0.681981
input_tokens: 21
output_tokens: 10612
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse init` core — write `.specfuse/` from package resources

**Objective.** Add `specfuse.loop.scaffold.init_specfuse(target)` — the in-process core
that lays down a fresh `.specfuse/` tree in a target repo from the packaged seed (T02's
resource API), refusing if `.specfuse/` already exists. This is the substrate the
umbrella `specfuse init` CLI calls (the CLI itself is cross-repo; see the review).

**Context.** This is `FEAT-2026-0026/T04`, gate 2, depends on T02 (`iter_scaffold_files`,
`read_scaffold`, `scaffold_version`). Gate 1 packaged the seed and exposed the read API;
this WU writes it out. Parity target is `init.sh` INIT mode (`init.sh:388-475`): it copies
versioned items (`templates/`, `rules/`, `verification.yml.example`, `VERSION`) and seeds
user-authored files (`roadmap.md`, `LEARNINGS.md`, an empty `features/`, and
`verification.yml` from the `.example` — `init.sh` also detects a `ci-check.sh`; see
escalation). The `.claude`/`.gitignore` wiring is T05; the end-to-end installed-wheel test
is T06 — keep this WU to the `.specfuse/` filesystem write + refusal contract. Pure
stdlib, no `Path(__file__)` (resolve via T02's API only). Ground in
`.specfuse/rules/result-contract.md` and `.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_scaffold_init.py::test_init_refuses_when_specfuse_exists`
fails on HEAD (function absent) and passes after this WU; paired with
`test_init_writes_full_tree`.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_init.py::test_init_refuses_when_specfuse_exists`
   exists and fails on HEAD before this WU's edits (import error / missing symbol).
2. `specfuse/loop/scaffold.py` gains `init_specfuse(target: str | Path, *, ci_check: str | None = None) -> list[str]`
   that, against a target dir with **no** `.specfuse/`:
   - writes `.specfuse/templates/` and `.specfuse/rules/` from the packaged seed,
   - writes `.specfuse/VERSION` (== `scaffold_version()`),
   - seeds `.specfuse/roadmap.md` and `.specfuse/LEARNINGS.md` from the packaged
     `roadmap.template.md` / `LEARNINGS.template.md`,
   - creates an empty `.specfuse/features/` directory (e.g. a `.gitkeep`),
   - seeds `.specfuse/verification.yml` from the packaged `verification.yml.example`,
   - returns the list of relpaths written.
3. **Refusal contract.** If `<target>/.specfuse/` already exists, `init_specfuse` raises a
   distinct, catchable error (e.g. `ScaffoldExistsError`) whose message points at
   `specfuse upgrade`; nothing is written (no partial tree).
4. **Byte-faithful seed.** Every file written from a *versioned* seed (`templates/`,
   `rules/`, `VERSION`, `verification.yml` seeded from the `.example`) byte-matches the
   corresponding `read_scaffold(relpath)` content — proven in a test that diffs against the
   resource API, not against `.specfuse/` on disk.
5. **No `__file__` paths.** `init_specfuse` resolves all source bytes through T02's API
   (`iter_scaffold_files`/`read_scaffold`); a test or grep confirms no new
   `Path(__file__)`-relative reads in `scaffold.py`.
6. The red test (AC1) and `test_init_writes_full_tree` pass after the edits; `code` gates
   stay green (coverage ≥ 90 on `specfuse/`).

**Do not touch.** This repo's own `.specfuse/` (tests write to a `tmp_path`, never the
repo root); `specfuse/loop/data/` content (T01 owns it); the driver modules; T05's
`.claude`/`.gitignore` surface; secrets; `.git/`. Do **not** add a `specfuse` console
script here — the umbrella CLI is cross-repo (see GATE-02-REVIEW.md).

**Verification.** `code` gates (tests incl. the new file, coverage ≥ 90, ruff, bandit);
the red→green proof (AC1, AC6); the refusal + no-partial-write test (AC3); the
byte-faithful diff against `read_scaffold` (AC4). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the `ci-check.sh` auto-detection (`init.sh:211-251` writes a
delegating `verification.yml` when a `ci-check.sh` exists in the target) cannot be made
self-contained inside `init_specfuse` without reaching outside the seed, scope it to the
`ci_check` parameter (caller-supplied) and emit a note rather than re-implementing
filesystem probing here — flag for T06/the review. If `roadmap.template.md` /
`LEARNINGS.template.md` are absent from the packaged seed (T01 shipped only `.example`),
emit `status: blocked` naming the missing seed file rather than inventing seed content.
