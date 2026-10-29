---
id: FEAT-2026-0247/T05
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/ids.py
  - tests/test_ids_migrate.py
  - tests/test_keyed_feature_ids_end_to_end.py
---

# T05 — `ids migrate --planned-only` re-keys folderless planned rows

**Objective.** An existing project that adopts a key can bring its not-yet-started
roadmap rows into the keyed form in one reviewed step, and nothing with history moves.

**Context.** `FEAT-2026-0247/T05`. This unit **edits** `ids.py` and the oracle module
T01 created. Add `python3 -m specfuse.loop.ids migrate --planned-only [--apply]`:

- Candidates: rows with status `planned`, no key, and no `.specfuse/features/<ID>-*`
  folder. Everything else is listed as skipped with the reason (has a folder, not
  planned, already keyed).
- Each candidate keeps its year and ordinal and gains the configured key
  (`FEAT-2026-0042` becomes `FEAT-ACME-2026-0042`), so no ordinal is reused or
  renumbered.
- `--apply` rewrites, in `.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md`: the
  table row ID, the `## ` heading, the `<a id>` anchor, and every `#feat-…` ref to it.
  Without `--apply` it prints the plan and writes nothing.
- No key configured: exit non-zero with a one-line message naming `ids.key` in
  `.specfuse/layout.yml`.

Un-skip the oracle's clause-6 class.

**Acceptance criteria.**

1. `tests/test_ids_migrate.py`: dry run writes nothing and lists candidates and skips;
   `--apply` re-keys a candidate with an inbound ref from another section and leaves
   `lint_roadmap` with no error; a row with a folder, an `active` row and an already
   keyed row are untouched; no key exits non-zero. Fails before, passes after.
2. Running `--apply` twice is idempotent (second run finds no candidates).
3. The command never touches `.specfuse/features/`, `events.jsonl`, `CHANGELOG.md` or
   git.

**Do not touch.** `ids.py`'s grammar and `next_id` (T01). `lint_roadmap.py` (T04).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** A ref shape to a planned row that the rewrite cannot place
safely (for example inside a code block): skip it, report it, and stop if it is not
rare.
