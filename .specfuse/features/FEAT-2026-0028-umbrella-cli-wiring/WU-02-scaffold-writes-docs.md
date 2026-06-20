---
id: FEAT-2026-0028/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_docs.py
duration_seconds: 287.238
cost_usd: 0.88724
input_tokens: 29
output_tokens: 8765
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `scaffold.py` writes `.specfuse/docs/` on init + upgrade

**Objective.** Make `init_specfuse` lay down `.specfuse/docs/` from the seed, and
`upgrade_specfuse` overlay `docs/` in its versioned footprint, so both fresh and
existing repos receive the methodology docs.

**Context.** This is `FEAT-2026-0028/T02`, depends on T01 (docs now in
`specfuse/loop/data/docs/`). FEAT-2026-0026 wrote `init_specfuse` (writes the seed tree)
and `upgrade_specfuse` (overlays a versioned footprint of `templates/`, `rules/`,
`VERSION` — NOT docs, which didn't exist in the seed then). This WU extends both to
include `docs/`. Resolve all source bytes through the T02-FEAT-0026 resource API
(`iter_scaffold_files`/`read_scaffold`), never `Path(__file__)`. Ground in
`.specfuse/rules/result-contract.md` and `.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_scaffold_docs.py::test_init_writes_docs_tree` fails on
HEAD (init does not yet write `.specfuse/docs/`) and passes after; paired with
`test_upgrade_overlays_docs`.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_docs.py::test_init_writes_docs_tree` exists
   and fails on HEAD before this WU's edits.
2. After `init_specfuse(target)` on a fresh repo, `<target>/.specfuse/docs/` contains the
   full doc set (`methodology.md`, `skills.md`, `getting-started.md`,
   `concepts/ralph-lineage.md`, `concepts/architecture-addendum-...md`), each
   byte-matching `read_scaffold("docs/<relpath>")`.
3. `upgrade_specfuse`'s versioned overlay footprint includes `docs/`: on a repo with an
   older/absent `.specfuse/docs/`, upgrade writes the current docs (new files added,
   changed files overwritten); user-authored surfaces (features, verification.yml,
   roadmap, LEARNINGS) remain untouched; never-downgrade still honored.
4. **No `__file__` paths** — docs are resolved via the resource API; a test/grep confirms
   no new `Path(__file__)`-relative reads in `scaffold.py`.
5. The red test (AC1) and `test_upgrade_overlays_docs` pass after the edits; `code` gates
   green (coverage ≥ 90 on `specfuse/`).

**Do not touch.** `specfuse/loop/data/docs/` content (T01 owns it); the seed for
non-docs surfaces; `.specfuse/` state in this repo (tests write to `tmp_path` only);
secrets; `.git/`.

**Verification.** `code` gates incl. the new test file; the red→green proof (AC1, AC5);
the init-writes-docs + upgrade-overlays-docs assertions (AC2, AC3); the no-`__file__`
check (AC4). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If adding `docs/` to `upgrade_specfuse`'s footprint would also
re-overlay a doc a consumer is expected to customize (docs are versioned, not
user-authored — they should be overwritten; but if any doc is meant to be editable),
emit `status: blocked` and surface which, rather than silently clobbering operator edits.
