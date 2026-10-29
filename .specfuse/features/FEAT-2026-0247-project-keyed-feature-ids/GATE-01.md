---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_keyed_feature_ids_end_to_end -v -b"
cost_budget_usd: 30.00
broad_run:
  tree: 054923b0bea95ba720a9a42a693f4da9e9ea960f:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:452dd9cf3ec63b136f069bb87773a0ca70fcdb44:4acc6dfc5e8cece358c167d876515eba4a39a500:54069afa85d0e2f632d4b6c38a9dd16af893c659:5ff66b6e4d8a264f23709ea60706111a4c59ed11:6dd6c8d6e05565b4d72ac742014b0b59baf2a9d9:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9b3386cac79ef7bbd03df4b421ab7dc4a900d9d6:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d033ecaa5f19f2adc264c6fb5faf9753a1c3f9ad:e22fb8aa46642577521545b94c1c195c991fea00:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-10-29T14:04:39.974183+00:00
  ok: false
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "(failures=4,"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
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
