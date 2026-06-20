---
id: FEAT-2026-0027/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_manifest.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Scaffold manifest + local-edit detection

**Objective.** Record a `.specfuse/.scaffold-manifest` (sha256 per versioned file) at
init/upgrade, and add `scaffold.detect_modified(target)` so auto-sync (T02) can tell a
pristine versioned file from a user-edited one.

**Context.** This is `FEAT-2026-0027/T01`, gate 1. Auto-sync must decide overlay-vs-prompt
per versioned file; that needs a record of what was written. FEAT-2026-0026's
`init_specfuse`/`upgrade_specfuse` write the versioned tree; this WU has them also write a
manifest of `{relpath: sha256}` for the versioned files they wrote, and adds a comparator.
"Versioned" = the same set `upgrade_specfuse` overlays (templates/, rules/, docs/, VERSION
— NOT user-authored: features/, verification.yml, roadmap.md, LEARNINGS.md). Pure stdlib
(`hashlib`). Ground in `.specfuse/rules/result-contract.md` and `never-touch.md`.

**Red-test (§12):** `tests/test_scaffold_manifest.py::test_manifest_written_on_init` and
`::test_detect_modified_flags_edit` fail on HEAD (manifest + comparator absent) and pass
after.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_manifest.py::test_manifest_written_on_init`
   exists and fails on HEAD before this WU's edits.
2. `init_specfuse` and `upgrade_specfuse` write `.specfuse/.scaffold-manifest` — a stable,
   parseable map of `versioned-relpath -> sha256` covering exactly the versioned files
   they wrote (deterministic ordering; e.g. sorted JSON). The manifest is NOT in the
   versioned-overlay set itself (it records, it isn't recorded).
3. `scaffold.detect_modified(target) -> list[str]` returns the sorted relpaths of
   versioned files present in the manifest whose on-disk sha256 now differs (user edits);
   files matching the manifest are not reported; a missing manifest is handled (returns
   `[]` or a documented sentinel — no crash).
4. After `init` then no edits, `detect_modified` returns `[]`; after editing one versioned
   file, it returns exactly that relpath.
5. The red tests (AC1) pass after the edits; `code` gates green (coverage ≥ 90 on
   `specfuse/`).

**Do not touch.** `loop.py` (T02 wires auto-sync); user-authored scaffold surfaces;
`.specfuse/` state in this repo (tests use `tmp_path`); secrets; `.git/`.

**Verification.** `code` gates incl. the new test; the red→green proof (AC1, AC5); the
detect-modified round-trip (AC4). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the "versioned set" the manifest should cover can't be derived
from the existing overlay constants (i.e. `upgrade_specfuse` and the manifest would
disagree on what's versioned), emit `status: blocked` and name the divergence rather than
hardcoding a second, drifting list.
