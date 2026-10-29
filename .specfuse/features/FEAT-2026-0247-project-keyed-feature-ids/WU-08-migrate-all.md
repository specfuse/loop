---
id: FEAT-2026-0247/T08
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 3.00
provenance: "Operator request on 2026-10-29, after T07: 'Can we provide a helper script that would allow to rename all the existing features in all the documents in a given repository knowing that the git history would still be wrong?' The operator accepted the proposed design (an --all mode of T05's migrate, reviewed dry run, alias map, own-IDs-only, released CHANGELOG sections and a running driver refused) with 'add T08'."
produces:
  - specfuse/loop/ids.py
  - tests/test_ids_migrate_all.py
  - tests/test_keyed_feature_ids_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T13:54:21.439249+00:00
duration_seconds: 160.758
cost_usd: 0.622449
input_tokens: 32
output_tokens: 19482
---

# T08 — `ids migrate --all` re-keys every feature of the repository

**Objective.** An existing project that adopts a key can rename all of its own features
in one reviewed step, accepting that git history, GitHub titles and other repositories
keep the old IDs.

**Context.** `FEAT-2026-0247/T08`. This unit **edits** `ids.py` (T01, T05) and the
oracle module T01 created. Add `--all` as the alternative to `--planned-only` (exactly
one is required) on `python3 -m specfuse.loop.ids migrate`, reusing T05's rewrite
machinery rather than a second rewriter:

- **Which IDs.** This repository's own unkeyed IDs only: every ID with a
  `.specfuse/features/<ID>-*` folder or a row in `roadmap.md` / `roadmap-archive.md`.
  Each keeps its year and ordinal and gains `ids.key`.
- **Where.** Every git-tracked text file (`git ls-files`, skipping binaries): whole-ID
  matches (T05's boundary rule, so `FEAT-2026-0042` never matches inside
  `FEAT-2026-00421` or an already keyed ID), their lower-cased anchors, `branch:` in
  `PLAN.md`, and `correlation_id` values in `events.jsonl`. Folders move with `git mv`.
- **Not rewritten.** `CHANGELOG.md` sections below `## Unreleased` (CI's
  `changelog-append-only` rejects edits to released entries); listed as skipped.
- **Ambiguous mentions.** A whole-ID match outside the structural surfaces (roadmap
  rows/headings/anchors, `PLAN.md`/WU frontmatter, `events.jsonl`, folder names) is
  prose that may cite another repository's feature with the same number. The dry run
  lists each one `file:line`; `--apply` rewrites them only with `--include-prose`.
- **Alias map.** `--apply` writes `.specfuse/id-aliases.yml` (`old: new`, appended,
  never rewritten) for T09's lookups.
- **Refusals.** No `ids.key`; `.specfuse/.loop.lock` held by a live driver; a dirty
  working tree. Each exits non-zero with a one-line reason.

The dry run (default) prints, per ID, the folder move, the count of replacements per
file, the skipped CHANGELOG sections and the ambiguous prose mentions, and writes
nothing. Add the oracle class `Clause9MigrateAll` (GATE-01.md clause 9).

**Acceptance criteria.**

1. `tests/test_ids_migrate_all.py`, in a temporary git repository with two features,
   archive and live rows, events, a released CHANGELOG entry and a prose mention of a
   foreign `FEAT-2026-0071`: the dry run writes nothing and lists moves, skips and the
   ambiguous mention; `--apply` moves folders, rewrites structural surfaces and events,
   leaves the released CHANGELOG entry and the prose mention unchanged (rewritten with
   `--include-prose`), writes the alias map, and `lint_plan` plus `lint_roadmap` report
   no error afterwards. A second `--apply` finds nothing to do. Each refusal exits
   non-zero. Fails before, passes after.
2. `--planned-only` behaves exactly as after T05 (`tests.test_ids_migrate` unchanged
   and passing).

**Do not touch.** `next_id`, the grammar, `lint_roadmap.py`. Git history, branches,
remotes and GitHub (the command never runs `git commit`, `git branch` or `gh`).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If a structural surface cannot be told from prose without
parsing that another module owns (for example WU frontmatter), reuse that module's
parser; a second frontmatter parser is a finding.
