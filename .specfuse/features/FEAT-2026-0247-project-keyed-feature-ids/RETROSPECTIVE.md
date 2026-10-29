# Retrospective — FEAT-2026-0247 gate 1 close

First and only close of gate 1 (single-gate feature, PLAN decision 7). Ten units: nine
loop-dispatched implementation units (T01–T06, T08–T10) and one human unit (T07). T08 and
T09 (the full rename) and T10 (broad-run fixes) were added after the baseline. This
session re-measured the oracles fresh and wrote the close deliverables.

## Measurements

Every command below was run in this session from the repository root with the project
venv, exit codes read directly. HEAD was `d3ff271dff0c08260df61cf09fb43f7997b44d2e` plus
this close's own uncommitted edits (`CHANGELOG.md`, this file, `LEARNINGS-pending.md`,
`GATE-01-CRITERIA.md`, `PLAN.md`'s post-merge checklist, the `verdict` field of
`WU-90-gate-1-close.md`). The close session may not run git commits.

The lifecycle-integration tests (`tests.test_lifecycle_integration`, reached by T02#4
and T09#2) fail inside the Bash sandbox with `loop.py: cannot create a directory under
'/Users/christian/.claude/session-env' (Operation not permitted)`, which is the sandbox
and not the feature. Those commands, and the full per-criterion run below, were
re-run with the sandbox off and pass.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_keyed_feature_ids_end_to_end -v -b` (exit 0):
`Ran 20 tests in 1.364s` / `OK`, every class running, none skipped:

```
Clause1AllocationContinuesLegacyNumbering          3
Clause2KeyedFeatureLints                           3
Clause3EverySiteAcceptsKeyedForm                   1
Clause4SkillsAllocateThroughIdsNext                2
Clause5UnkeyedPlannedRowWarns                      2
Clause6MigratePlannedOnly                          1
Clause7KeyedCorrelationIdValidatesAgainstEnvelope  4
Clause8UnkeyedRepoIsUnchanged                      2
Clause9MigrateAll                                  2
```

### No surviving skip (close criterion 1)

`grep -nE 'unittest\.skip|@skip|skipTest' tests/test_keyed_feature_ids_end_to_end.py`
prints nothing (exit 1). `grep -n skip` on the module reports one line, line 9, inside
the module docstring ("A skip surviving to the close is a hollow oracle"). It is prose.
T01 created the module with the other clauses skipped by owner name, and each owner
(T02–T05, T07, T08) removed its own; the verbose run above lists no `skipped` marker
for any of the twenty tests.

### One definition of a feature ID (close criterion 2)

Command: `grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/`

Output: nothing, exit 1. The criterion expected `specfuse/loop/ids.py` to be the one
hit; it is not a hit either, because `ids.py` builds the pattern from parts
(`FEATURE_ID_PATTERN = r"FEAT-(?:" + KEY_PATTERN + r"-)?\d{4}-\d{4}"`, `ids.py:34`), so
the legacy literal exists nowhere under `specfuse/`. That is stricter than the
criterion, not weaker. A wider sweep for any other hand-written ID pattern in Python:

`grep -rnE 'FEAT-(\\d|\[0-9\]|\\\\d)' specfuse/ --include='*.py' | grep -v 'specfuse/loop/ids.py'`
prints nothing (exit 1), and `grep -rnE 'FEAT-.{0,40}\{4\}' specfuse/ --include='*.py' | grep -v 'loop/ids.py'`
prints nothing (exit 1). The only other `FEAT-…{4}` text under `specfuse/` is the
core-owned, vendored grammar: `data/rules/correlation-ids.md:79` and five JSON schemas
under `data/schemas/`, each carrying the widened `FEAT-(?:[A-Z][A-Z0-9]{1,5}-)?` form.
Those are the T07 deliverable and are not a second Python definition (a JSON schema
cannot import `ids.py`); `test_vendored_grammar_embeds_the_shared_pattern` ties the
rule text to `ids.KEY_PATTERN`.

### Closing lint (close criterion 6)

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0247-project-keyed-feature-ids --closing`
(exit 0): `CLOSING-READY`, with the two post-pass notes for `close-h` and `close-i`.
The bare `specfuse lint --closing` warns that it measures the pipx-installed build, not
this checkout, so the checkout's script was run instead. The `plannext` gate's
`lint_plan.py <feature_dir>` is `OK — structurally valid`, with two WARNs: T07 has no
`oracle_env`, and gate 1 has 26 acceptance criteria across its substantive units, above 20.

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate. `events.jsonl` records two
`broad_run_result` events: 14:04:39 `ok: false` (see Failure-class breakdown), then
14:16:16 `ok: true`, `failing: []`, on the tree recorded in `GATE-01.md`'s `broad_run:`
block.

### Per-criterion oracles (30 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 30

All thirty were `unverified` on entry. Each was run in this session as its own command
by one script; each now records its oracle command, `kind: narrow`, `state: pass` and
`proved_at_sha` `d3ff271dff0c08260df61cf09fb43f7997b44d2e`, all exit 0.

| criterion | oracle | ran |
| --- | --- | --- |
| T01#1 | `tests.test_ids` + oracle clause 1, 2, 8 classes | 22 tests, OK |
| T01#2 | `tests.test_ids.RealCorpus` (every folder under `.specfuse/features/`, every roadmap row) | 2 tests, OK |
| T01#3 | `tests.test_ids tests.test_layout_validation` | 27 tests, OK |
| T01#4 | the five unchanged lint and layout modules | 77 tests, OK |
| T01#5 | `grep -nF 'FEAT-\d{4}-\d{4}'` on `lint_plan.py`, `lint_roadmap.py`, negated | no output |
| T02#1, T02#2 | `tests.test_ids_call_sites`; `…PartialLookup` | 4 and 3 tests, OK |
| T02#3 | the repo-wide grep above, negated | no output |
| T02#4 | `tests.test_lifecycle_integration tests.test_agent_policy_schema` | 34 tests, OK (sandbox off) |
| T03#1 | `tests.test_roadmap_add_skill` + oracle clause 4 | 51 tests, OK |
| T03#2 | `tests.test_skills_vendored_in_sync` | 4 tests, OK |
| T03#3 | `grep` for `#771`, `#1872` and `source (d)` in `.specfuse/skills/roadmap-add/SKILL.md` | present |
| T04#1 | `tests.test_lint_roadmap_unkeyed_rows` | 4 tests, OK |
| T04#2 | `lint_roadmap.lint_roadmap(Path('.'))` over this repo | one WARN (below), no error |
| T05#1–T05#3 | `tests.test_ids_migrate`; `…test_apply_is_idempotent`; `…test_archive_rewritten_and_features_untouched` | 6, 1, 1 tests, OK |
| T06#1, T06#2 | `tests.test_keyed_feature_ids_docs`; the two sync suites | 3 and 8 tests, OK |
| T06#3 | grep for a "prompt asks for the key" claim in the docs and skills, negated | no output |
| T07#1 | `WU-07-…md` `evidence:` names core PR `specfuse/specfuse#232` | present |
| T07#2 | `tests.test_scaffold_data_in_sync` | 4 tests, OK |
| T07#3 | oracle clause 7 class | 4 tests, OK |
| T07#4 | `tests.test_validate_event tests.test_scaffold_data_in_sync` | 63 tests, OK |
| T08#1, T08#2 | `tests.test_ids_migrate_all`; `tests.test_ids_migrate` | 7 and 6 tests, OK |
| T09#1 | `tests.test_ids_aliases` | 12 tests, OK |
| T09#2 | `tests.test_lifecycle_integration tests.test_keyed_feature_ids_docs tests.test_scaffold_data_in_sync` | 12 tests, OK (sandbox off) |
| T10#1 | `tests.test_judge_path_registry tests.test_caller_check_ratchet tests.test_layout_no_layout_goldens` | 26 tests, OK |
| T10#2 | `tests.test_ids tests.test_ids_migrate tests.test_ids_migrate_all` + oracle | 47 tests, OK |

T04#2's one WARN is `roadmap.md:29`, "FEAT-2026-0011's Detail cell is '—' but a detail
section already exists", which `PROGRESS.md` records as pre-existing at T04 and is not
produced by this feature (this repo sets no key, so the unkeyed-row WARN is silent here).
T07#1 quotes the operator's evidence; the PR itself was not re-fetched (no network in
this session).

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. keyed repo with legacy rows up to 0007 prints `FEAT-ACME-2026-0008`; unkeyed prints `FEAT-2026-0008` | `Clause1AllocationContinuesLegacyNumbering.test_keyed_next`, `test_unkeyed_next_is_todays`, `test_key_round_trips_through_layout_get`; `tests.test_ids` `NextId` (keyed counts both forms, other year ignored, empty) | proven |
| 2. keyed folder, row, heading and anchor pass `lint_plan` and `lint_roadmap`; `--dry-run --feature` loads it | `Clause2KeyedFeatureLints.test_keyed_feature_lints_and_loads`, with `test_legacy_positive_control` and `test_keyed_feature_in_legacy_roadmap_lints` | proven |
| 3. every ID-parsing site accepts the keyed form; `0008` resolves the keyed folder | `tests.test_ids_call_sites` (`CallSiteCases.test_keyed_and_legacy_through_each_site`, `PartialLookup` ×3 including the real-corpus-by-ordinal case); the repo-wide grep above | proven by the unit module. The oracle's own `Clause3` class only asserts that suite's `SITES` table is non-empty, so the oracle does not itself re-run these sites |
| 4. `/roadmap-add` and `/draft-feature` allocate through `ids next` | `Clause4SkillsAllocateThroughIdsNext` (both tests); `tests.test_roadmap_add_skill` (51 tests); `tests.test_skills_vendored_in_sync` | proven for the skill text. Nothing here runs a live skill session (see "did NOT verify") |
| 5. with a key, an unkeyed `planned` row WARNs; legacy non-planned rows and unkeyed repos draw nothing | `Clause5UnkeyedPlannedRowWarns` (both); `tests.test_lint_roadmap_unkeyed_rows` (fires, silent without key, silent on each exempt status, silent on a keyed `planned` row, `warn` never `error`) | proven |
| 6. `ids migrate --planned-only` reports, `--apply` re-keys row, heading, anchor, refs; `lint_roadmap` clean | `Clause6MigratePlannedOnly.test_apply_rekeys_planned_row_and_lints_clean`; `tests.test_ids_migrate` (dry run writes nothing, cross-section ref, code-span ref reported, idempotent, archive rewritten and `features/` untouched, no key exits non-zero) | proven |
| 7. a keyed correlation ID validates against the vendored envelope and the correlation-ID grammar | `Clause7…test_keyed_ids_validate`, `test_legacy_and_orchestrated_ids_still_validate`, `test_malformed_keys_are_rejected`, `test_vendored_grammar_embeds_the_shared_pattern`; `tests.test_validate_event` and `tests.test_scaffold_data_in_sync` (63 tests); core PR `specfuse/specfuse#232` per T07's `evidence:` | proven |
| 8. a repo without `ids.key` behaves byte-identically to HEAD on every surface above | `Clause8UnkeyedRepoIsUnchanged` (no layout; layout without an `ids` block); the legacy half of every paired case in clauses 1, 2, 3 and 5; `tests.test_layout_no_layout_goldens` (re-recorded in T10 for the one intentional template change); `lint_roadmap` over this repo (T04#2) | proven for the surfaces the tests drive. "Byte-identical to HEAD" is shown by assertions on outputs, not by a diff against a HEAD checkout |
| 9. `ids migrate --all` renames every owned feature after a reviewed dry run, leaves released CHANGELOG and foreign prose alone unless asked, and old IDs resolve at `--feature`, `gate_eval` and `gh_features` | `Clause9MigrateAll` (dry run lists, apply renames, alias map written, `ids.resolve` follows it, second apply "nothing to do", refuses without a key); `tests.test_ids_migrate_all` (dry run writes nothing, apply leaves prose and released CHANGELOG, `--include-prose`, refuses without a key, on a dirty tree and while a driver holds the lock); `tests.test_ids_aliases` (12 tests: each of the three lookups with an alias, without one, and with a dangling alias) | proven. The three-lookup half lives in `tests.test_ids_aliases`, not in the oracle |

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's
`planned_cost_usd`. The unit plans sum to **27.00**; `PLAN.md` states 26.50 and the
baseline snapshot (`arm_predicate_evaluated`) 21.00, because T08–T10 were added after the
baseline and `PLAN.md`'s total was not updated to match every unit. `GATE-01.md` sets
`cost_budget_usd: 30.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 4.00 | 0.7056 | 1 (passed) | 146.1 |
| T02 | 3.00 | 0.4167 | 1 (passed) | 93.2 |
| T03 | 2.00 | 0.3080 | 1 (passed) | 68.5 |
| T04 | 1.50 | 0.2209 | 1 (passed) | 42.6 |
| T05 | 3.00 | 0.3451 | 1 (passed) | 88.5 |
| T06 | 2.00 | 0.2202 | 1 (passed) | 57.1 |
| T07 (human) | 0.50 | not a driver cost | 0 (operator, see below) | — |
| T08 | 3.00 | 0.6224 | 1 (passed) | 160.8 |
| T09 | 2.00 | 0.3309 | 1 (passed) | 87.9 |
| T10 | 1.00 | 0.1331 | 1 (passed) | 35.7 |
| T01–T10 | 22.00 | 3.3030 | 9 recorded | 780.5 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 27.00 | **3.3030** | 9 recorded | 780.5 |

The nine recorded attempts spent $3.30 (15.0% of the $22.00 planned for them, 11.0% of
`cost_budget_usd`); every one passed on its first attempt. This close's own attempt is
written when the driver ends it, so it is not reconciled and the total excludes it. The
largest spenders were the two units that wrote the most code: T01 (the new
`ids.py` module and its tests) and T08 (`ids migrate --all`), together 40% of recorded
spend. The broad run is the driver's with no model session, so neither broad run is
charged to a unit.

**T07's operator wait.** T07 is a human unit (the core-owned grammar and event schemas
change through the methodology core, then are vendored). The driver halted with
`human_escalation` `human_step_required` at 13:22:46 UTC; the next unit, T08, started at
13:54:21. That is **31 min 35 s** of wall-clock, none of it driver spend. The work was
done in the operator's own Claude session (core PR `specfuse/specfuse#232` plus the
vendoring), so its model cost is outside `events.jsonl` and is not estimated here; T07's
$0.50 plan is for that work and is neither confirmed nor refuted. In the same window the
operator asked for the full rename, so the wait also includes drafting T08 and T09.

**What the self-halt cost.** The terminal judge-editing stop fired at 14:16:16 and the
acknowledgement was read at 14:22:47: **6 min 31 s**, $0.00 driver spend, nine
acknowledged paths (`ids.py` and `loop.py` among them).

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `tests` (`failures=4`) + `other` (`no_gate_marker`, `coverage`) | broad run 14:04:39 | 1 | not charged to a unit | four suite-wide checks the per-unit narrow tiers could not see: two `GOLDEN_TEMPLATE_SHA256` checks in `test_layout_no_layout_goldens` (T06 intentionally changed `roadmap.template.md`'s Notes), `test_judge_path_registry.test_no_module_is_unclassified` (`ids.py` in neither `JUDGE_MODULES` nor `NON_JUDGE_MODULES`), and `test_caller_check_ratchet` (`anchor` and `sort_key` in `ids.py` had no caller outside `tests/`). The `coverage` gate failed only because it `needs: [tests]`. Fixed by T10 ($0.13); the next broad run was green |
| `judge_editing_terminal` halt | G1-CLOSE 14:16:16 | 1 | $0.00 | expected (PLAN decision 8); acknowledged by the operator with a reason |

## Consumer-visible contract changes

Enumerated across T01–T10 for acknowledgment; each is in `CHANGELOG.md` `Unreleased`
(`Added` ×3, FEAT-2026-0247).

- **Added — the optional `ids.key` in `.specfuse/layout.yml`** and the keyed form
  `FEAT-<KEY>-YYYY-NNNN` (`KEY` matching `[A-Z][A-Z0-9]{1,5}`), accepted by every loop
  surface that parses a feature ID, with the lower-cased anchor and folder name.
- **Added — `python3 -m specfuse.loop.ids next`**, which `/roadmap-add` and
  `/draft-feature` now call to allocate the next ID instead of computing it in prose.
- **Added — a `lint_roadmap` WARN** for an unkeyed `planned` row when a key is set.
- **Added — the widened core-owned grammar and event schemas**, so a keyed correlation ID
  validates (vendored from core PR `specfuse/specfuse#232`).
- **Added — `ids migrate --planned-only`** (dry run by default, `--apply` writes).
- **Added — `ids migrate --all`** (opt-in full rename, `--apply`, `--include-prose`),
  `.specfuse/id-aliases.yml`, and one-hop alias resolution at `--feature`, `gate_eval`
  and `gh_features`.
- **Unchanged — a repository without `ids.key`:** no new finding, prompt or rename; every
  existing ID stays valid.

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## What the loop did NOT verify

1. **Key uniqueness across repositories.** Nothing detects two repositories picking the
   same key; there is no registry and no cross-repo check, by decision (PLAN scope
   boundary and Known limits). Where checked: by convention only, when an operator picks
   a key for each repository of a multi-repo project (PLAN's post-merge checklist, second
   item). A collision would surface as two repositories again sharing a bare ID.
2. **A real second repository adopting a key.** Every keyed case ran in a temporary
   repository built inside a test, or in this repository's own corpus with no key set.
   No other repository has set `ids.key`. Where checked: `PLAN.md`'s post-merge
   checklist: decide this repository's key and set it, set a distinct key in each other
   repository, then run the first keyed feature through the loop and confirm the branch
   name, commit subjects, `events.jsonl` correlation IDs and roadmap flips all carry the
   keyed ID. That last item also covers what no test here did: a real driver dispatch of
   a keyed feature (the oracle's clause 2 only `--dry-run`s one) and a live
   `/roadmap-add` session calling `ids next`.
3. **The lexical name-sort sites.** `loop.py`, `arm_sweep` and `upgrade_merge_gate` still
   order feature folders by name (PLAN Known limits). `FEAT-ACME-…` sorts after every
   `FEAT-2026-…`, so in a repository mixing both forms the newest feature is still last;
   no test drives a mixed legacy-and-keyed ordering through those sites, and the
   same lexical order applies after `ids migrate --all`. PLAN's Known limits
   say a `sort_key` helper is "available where order matters"; T10 deleted it because no
   code called it and the caller ratchet rejected it, so that sentence no longer
   describes the code. Where checked: the first repository that has both forms and runs
   a feature to the point where "newest" or the sort order matters; a future feature
   would need to add a real ordering key if a case with two different keys ever appears.
4. **A real full rename with `--all`.** `ids migrate --all` ran only against temporary
   git repositories built by the tests (two features, archive and live rows, events, a
   released CHANGELOG entry, a foreign prose mention). It has never renamed this
   repository or any other real one, whose corpus has more surfaces than the fixtures
   (prose mentions, issue and PR titles that stay on the old IDs).
   Where checked: `PLAN.md`'s post-merge checklist, last item: read the real dry run
   (moves, skips, ambiguous mentions) before `--apply`, then confirm the alias map. Git
   history, GitHub issue and PR titles and other repositories keep the old IDs by design.
5. **The oracle does not itself re-run the per-site and per-lookup proofs.** Clause 3
   asserts only that `test_ids_call_sites.CallSiteCases.SITES` is non-empty, and clause 9
   checks `ids.resolve` but not the three lookups. Those proofs are real, but they live
   in `tests.test_ids_call_sites` and `tests.test_ids_aliases`, which the feature oracle
   does not call. Where checked: the driver's broad run (`unittest discover`) and this
   close's per-criterion table above, both of which ran them green.
6. **The "fails on HEAD" halves of the red-first criteria** (T01#1, T02#1, T08#1, T09#1,
   T10#1) were recorded by each unit's own attempt, not re-observed here; this close
   re-observed only the passing side.
7. **The core PR was not re-fetched.** T07#1 is the operator's `evidence:` field
   (`specfuse/specfuse#232` merged as `073bcda`); this session had no network access.
   The vendored copies were checked against the repository's own sync tests, which pass.
8. **Behaviour on a consumer that runs `specfuse upgrade` across this change** was not
   exercised: the vendored `data/` copies are in sync (`test_scaffold_data_in_sync`), but
   no upgrade from a prior release was run. Where checked: the first consumer upgrade
   after the loop release containing this feature.

## Documentation pass

`docs/methodology.md` (the correlation ID line, "Project key" and "Renaming existing
features"), `docs/getting-started.md`, `docs/glossary.md` and the `/roadmap-add` and
`/draft-feature` skills (`.specfuse/` and `plugins/` copies) were read against the
shipped code: each names `ids.key` and the keyed form, states that existing IDs are not
renamed by default, and describes `--all` as opt-in with the alias map. The one claim to
check was that no prompt asks for the key; `docs/methodology.md:60` says "No prompt asks
for the key; it is read from `layout.yml`", and the T06#3 grep finds no contrary claim.
`tests.test_keyed_feature_ids_docs`, `test_skills_vendored_in_sync` and
`test_scaffold_data_in_sync` pass, so the `data/` and `plugins/` copies match.

## Retrospective

**What went well.** Ten units, every attempt passing first time, $3.30 against a $27.00
plan. The walking-skeleton shape worked: T01 created the module and the oracle with the
other clauses skipped by owner name, each owner removed its own skip, and none survived
to the close. Every "keyed accepted" assertion has its legacy positive control, and the
parser is tested against the real corpus (every folder under `.specfuse/features/` and
every roadmap row), per LEARNINGS `[FEAT-2026-0101/G1-CLOSE]`. Putting the core-owned
grammar in a last human unit (T07) kept the loop-side units unblocked until the end.

**What didn't.** Two things. First, the broad run caught four failures that no unit's
narrow tier could see: a new module under `specfuse/loop/` has to be classified in the
judge-path registry, every public symbol needs a non-test caller, and a deliberate
template change has to re-record its golden. None of the three was in any unit's
acceptance criteria, so it cost an operator diagnosis and T10. Second, the scope grew mid-gate: the operator asked for the full
rename after T07, adding T08 and T09, so `PLAN.md`'s total, the baseline and the unit
plans now disagree (26.50, 21.00, 27.00) and `lint_plan` will say so.

**Lessons.** Staged in `LEARNINGS-pending.md` (`autonomy_default: auto`, so this close
may not append to `.specfuse/LEARNINGS.md`): the registries a new driver module must
join, and not promising a helper in Known limits that no caller will use.

**Open follow-ups (not blockers).** The post-merge checklist items (decide this
repository's own key, other repositories' keys, one real keyed feature through the loop,
one real `--all` dry run), filed at close as `specfuse:post-merge`; a real ordering key
at the name-sort sites if two different keys ever share a repository; folding clause 3
and the three-lookup half of clause 9 into the oracle itself.
