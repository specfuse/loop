---
id: FEAT-LOOP-2026-0247/T06
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 2.00
produces:
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - docs/glossary.md
  - specfuse/loop/data/docs/glossary.md
  - docs/getting-started.md
  - .specfuse/roadmap.template.md
  - specfuse/loop/data/roadmap.template.md
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_keyed_feature_ids_docs.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T13:21:48.922993+00:00
duration_seconds: 57.07
cost_usd: 0.220176
input_tokens: 16
output_tokens: 4609
---

# T06 — the docs explain the key, how to choose it, and grandfathering

**Objective.** An operator running several repos learns from the shipped docs that a
key exists, where to set it, how to choose it, and that existing IDs never change.

**Context.** `FEAT-LOOP-2026-0247/T06`. Update the loop-owned docs that define or show the ID
shape: `docs/methodology.md` (§ correlation IDs, around lines 30-54), `docs/glossary.md`
(16, 27), `docs/getting-started.md:140`, and the roadmap template's Notes ("allocated
sequentially per year"). State: the optional `ids.key` in `.specfuse/layout.yml`; the
`FEAT-<KEY>-YYYY-NNNN` form and its lower-cased anchor; numbering stays per repo and
continues from the highest ordinal of either form; legacy IDs are permanent;
`ids migrate --planned-only` for folderless planned rows; pick a short key distinct
across the repos of one project (uniqueness is by convention).

The roadmap template's canonical copy is `.specfuse/` and the methodology/glossary
canonical copies are `docs/`; run `bash scripts/sync-scaffold.sh` and confirm the
`specfuse/loop/data/` copies match. `driver-event.schema.json` is loop-owned: update its
`$comment` to say the correlation-ID shape now comes from `specfuse.loop.ids`.

Do **not** edit `.specfuse/rules/correlation-ids.md` or any `CORE_FILES` schema: those
are owned by the methodology core and change in T07.

**Acceptance criteria.**

1. `tests/test_keyed_feature_ids_docs.py` asserts each surface above names `ids.key`,
   the keyed form, and that legacy IDs are never renamed. Fails before, passes after.
2. `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
   passes after the sync.
3. No doc claims a prompt asks for the key (none does).

**Do not touch.** Core-owned files (T07). Skills (T03). Code.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If the sync script reports a core-owned file as edited, revert
that edit; it belongs to T07.
