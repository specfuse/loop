---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_keyed_feature_ids_end_to_end -v -b"
cost_budget_usd: 30.00
---

# Gate 1 — a keyed feature works end to end; an unkeyed repo is unchanged

## Definition of done

**Stated as an outcome.** Driven through the real modules in a temporary repository
(the `tests/test_lifecycle_integration.py` style):

1. With `ids.key: ACME` in `.specfuse/layout.yml` and legacy roadmap rows up to
   `FEAT-2026-0007`, `python3 -m specfuse.loop.ids next` prints `FEAT-ACME-2026-0008`.
   Without a key it prints `FEAT-2026-0008`, as today's allocation would.
2. A keyed feature folder (`FEAT-ACME-2026-0008-<slug>`), its roadmap row, heading and
   anchor (`feat-acme-2026-0008`) pass `lint_plan` and `lint_roadmap`, and
   `specfuse-loop --dry-run --feature FEAT-ACME-2026-0008` loads it.
3. Every code site that parses a feature ID accepts the keyed form, and the partial
   lookup `0008` resolves the keyed folder.
4. `/roadmap-add` and `/draft-feature` allocate through `ids next`.
5. With a key set, a `planned` row without it draws a WARN; legacy non-planned rows and
   unkeyed repos draw nothing.
6. `ids migrate --planned-only` reports, and with `--apply` re-keys, folderless planned
   rows (row, heading, anchor, refs), leaving `lint_roadmap` clean.
7. A keyed correlation ID validates against the vendored event envelope and the
   correlation-ID grammar (core change, T07).
8. A repository without `ids.key` behaves byte-identically to HEAD on every surface
   above.
9. `ids migrate --all` (added 2026-10-29) renames every feature the repository owns
   after a reviewed dry run, leaves released CHANGELOG entries and foreign prose
   mentions alone unless asked, and old IDs still resolve through
   `.specfuse/id-aliases.yml` at the `--feature`, `gate_eval` and `gh_features`
   lookups.

The `feature_oracle` proves 1–9 end to end (clause 9 added with T08/T09). It is red on the current tree (the module
does not exist); `FEAT-2026-0247/T01` is the walking skeleton that creates it and turns
clauses 1, 2 and 8 green, with every other class `unittest.skip` naming its owner
(T02–T05, T07). A skip surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One definition of a feature ID.** Every unit imports the pattern and parser from
  `specfuse.loop.ids`; a new `FEAT-\d{4}-\d{4}` literal anywhere is a finding.
- **Legacy is a positive control.** Every "keyed form accepted" assertion is paired with
  the same assertion on a legacy ID and on an unkeyed repo.
- **Real corpus.** Parser tests run over every folder under `.specfuse/features/` and
  every roadmap row, not only fixtures.
- **Core-owned files are not edited here.** `.specfuse/rules/correlation-ids.md` and the
  `CORE_FILES` schemas change only through T07's core PR and `scripts/sync-scaffold.sh`.
- **Expected self-halt.** T01–T02 edit judge surfaces; the terminal judge-editing stop
  fires before the close. Acknowledge with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
