---
id: FEAT-2026-0247/T09
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 2.00
provenance: "Part of the operator-accepted design for the full rename (see T08's provenance): old IDs live on in commit messages, GitHub issue and PR titles and other repositories, so after `ids migrate --all` the loop's ID lookups resolve them through `.specfuse/id-aliases.yml`."
produces:
  - specfuse/loop/ids.py
  - specfuse/loop/loop.py
  - specfuse/loop/gate_eval.py
  - specfuse/loop/gh_features.py
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - tests/test_ids_aliases.py
  - tests/test_keyed_feature_ids_end_to_end.py
produces_driver_helper:
  - _FEATURE_ID_RE
---

# T09 — old IDs still resolve after a full rename

**Objective.** After `ids migrate --all`, an operator who types an old ID, or an issue
titled with one, still reaches the renamed feature.

**Context.** `FEAT-2026-0247/T09`. This unit **edits** `ids.py`, three lookup sites and
the oracle module T01 created. Add `ids.resolve(repo_root, feature_id)`: the ID itself
when it has a folder, else its `.specfuse/id-aliases.yml` target (one hop; the file is
absent in most repositories and then nothing changes). Route through it:

- the driver's `--feature` argument (`loop.py`, the `_FEATURE_ID_RE` check and folder
  glob);
- `gate_eval`'s feature-folder lookup (full-ID and partial-ordinal paths);
- `gh_features`' issue-title-to-feature match (`[FEAT-…]` titles).

Add (editing T06's text) a short "Renaming existing features" paragraph to `docs/methodology.md` (sync the
packaged copy): what `--all` rewrites, what it cannot (git history, GitHub, other
repositories), the alias map, and the prose-mention review. Extend `Clause9MigrateAll`
with the alias round trip.

**Acceptance criteria.**

1. `tests/test_ids_aliases.py`: with an alias map, each of the three sites resolves the
   old ID to the renamed folder; without one, each behaves exactly as before; an alias
   whose target has no folder is reported, not followed into an error. Fails before,
   passes after.
2. `python3 -m unittest tests.test_lifecycle_integration tests.test_keyed_feature_ids_docs tests.test_scaffold_data_in_sync -b`
   passes.

**Do not touch.** `migrate` (T08). The grammar. Sort sites.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** A lookup site beyond the three named that an operator would
reasonably type an old ID into: list it and stop rather than widening silently.
