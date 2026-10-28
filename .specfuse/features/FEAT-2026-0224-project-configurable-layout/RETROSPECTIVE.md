# Retrospective — FEAT-2026-0224 gate 1 close

First and only close of gate 1 (single-gate feature, PLAN decision 1). Seven
implementation units (T01–T07); this session re-measured the oracles fresh and wrote
the close deliverables.

## Measurements

All commands were run in this session from the repository root with the project venv,
exit codes read directly. HEAD was `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1` with this
close's own working-tree edits (`CHANGELOG.md`, this file, `LEARNINGS-pending.md`,
`GATE-01-CRITERIA.md`, the `verdict` field of `WU-90-gate-1-close.md`) uncommitted.
This session may not run git commits; the tree state is HEAD plus those edits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_layout_end_to_end -v -b` (exit 0):
`Ran 8 tests` / `OK`, every class running, none skipped:

```
NoLayoutGetIsToday          1
EntriesLayoutGet            1
EntriesLinkRenders          1
NoLayoutGoldens             1
LintChecksDecisionLinks     1
InvalidLayoutIsReported     2
TemplateFollowsStyle        1
```

### No surviving skip

`grep -n 'skip' tests/test_layout_end_to_end.py` reports one line, line 8, inside the
module docstring ("Classes owned by later units are skipped, each naming its owner").
There is no `unittest.skip` decorator or call: T01 created the module with the T02,
T03, T04, T05 and T07 classes skipped by owner name, and each owner removed its own.
The verbose run above lists no `skipped` marker for any of the eight tests.

### Goldens' integrity (close criterion 3)

`git log --format='%h %ad %s' --date=iso -- tests/test_layout_no_layout_goldens.py
specfuse/loop/lint_roadmap.py` and `git log --name-status b784c60^..HEAD`:

| commit | time (-0400) | touches |
| --- | --- | --- |
| `b784c60` T04 | 2026-10-27 21:29:26 | **adds** `tests/test_layout_no_layout_goldens.py` (the `lint_roadmap` goldens) |
| `93922b4` T05 | 2026-10-27 21:30:36 | first and only edit to `specfuse/loop/lint_roadmap.py`; does not touch the golden file |
| `5e5d04a` T07 | 2026-10-27 21:32:59 | **appends** `NoLayoutTemplateGoldens` (the template golden) to the golden file |

- The goldens were committed 70 seconds before T05's commit. The loop commits per work
  unit, so commit order is the finest grain `git log` offers for "before T05's first
  edit"; T05's only commit is the first one that touches `lint_roadmap.py`.
- `git diff b784c60 93922b4 --stat -- tests/test_layout_no_layout_goldens.py` prints
  nothing: the file is identical across T05.
- `git diff b784c60 HEAD -- tests/test_layout_no_layout_goldens.py | grep -c '^-[^-]'`
  prints `0`: T07's edit is purely additive. The `lint_roadmap` goldens
  (`GOLDEN_LINT`, `GOLDEN_GET`, the link golden, `tests/fixtures/layout_goldens/`) are
  byte-identical to T04's. `git diff b784c60 HEAD --stat -- tests/fixtures` prints
  nothing.
- T07's addition is a **new** golden for a surface (the roadmap template) that T07
  itself changes. It is a sha256 of HEAD's template taken before the layout region
  markers, written in the same unit that edits the template, so it proves "no layout
  renders the old bytes" only as far as the digest was taken from the pre-change text.
  `tests.test_layout_no_layout_goldens` passes (OK; `Ran 34 tests`
  together with `tests.test_lint_roadmap`). The escalation trigger ("a changed no-layout golden") does
  not apply: no existing golden changed.

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate. `events.jsonl` records two
`broad_run_result` events. The first, 01:41:05Z, was `ok: false`: `tests` failed
(`failures=1`, `test_init_integration.TestInitFullLayout.test_roadmap_seeded_from_template`
asserting the old seed bytes against the new layout region markers) and `coverage`
reported `no_gate_marker`. `f4b3450` fixed that test; the second, 01:50:24Z, is
`ok: true`, `failing: []`, on the tree recorded in `GATE-01.md`'s `broad_run:` block.
Its `tests` log (`work/gate-logs/tests-20261028T014932084897Z.log`) reads
`Ran 4806 tests` / `OK (skipped=4)`; none of the four skips is in the oracle module.

### Per-criterion oracles (18 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 18

All eighteen were `unverified` on entry and each was run in this session; each now
records its oracle command, `kind: narrow`, `state: pass`, and `proved_at_sha`
`03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`.

| criterion | oracle (exit 0 unless stated) |
| --- | --- |
| T01#1 | `unittest …NoLayoutGetIsToday …EntriesLayoutGet` OK |
| T01#2 | `unittest tests.test_layout` (`Ran 20 tests` with the registry module) OK |
| T01#3 | `unittest tests.test_judge_path_registry` OK |
| T02#1–#3 | `unittest tests.test_layout_validation tests.test_layout` (`Ran 22 tests` with `test_layout_link`) OK |
| T03#1–#2 | `unittest tests.test_layout_link` OK; `…RenderLink.test_no_layout_adr_matches_skill_example` `Ran 1 test` OK |
| T04#1–#2 | `unittest tests.test_layout_no_layout_goldens` OK (positive control `test_positive_control` included) |
| T05#1 | `unittest tests.test_lint_roadmap` (`Ran 34 tests` with the golden module) OK |
| T05#2 | golden module OK, and `git diff b784c60 HEAD -- …goldens.py | grep -c '^-[^-]'` prints `0` |
| T05#3 | `unittest tests.test_layout_end_to_end.LintChecksDecisionLinks` `Ran 1 test` OK |
| T06#1–#2 | `unittest tests.test_block_feature_layout` and `tests.test_skills_vendored_in_sync` OK (`Ran 13 tests` with `test_scaffold_data_in_sync`) |
| T07#1 | `unittest tests.test_layout_end_to_end.TemplateFollowsStyle` OK |
| T07#2 | `unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync` `Ran 8 tests` OK |
| T07#3 | `grep -rn "an ADR" plugins/specfuse/skills/{attention,gate-status,groom-backlog,pick-feature,roadmap-add}/SKILL.md docs/methodology.md docs/skills.md` exit 1, no output |

T06#1 and T01's "red on HEAD" halves are properties of the tree *before* each unit and
cannot be re-observed from here; the units' own attempts recorded them, and this close
re-ran only the green halves.

Also run: `tests.test_changelog_schema tests.test_changelog_append_only
tests.test_changelog_collection` (`Ran 38 tests`, OK) after the `CHANGELOG.md` edit;
`ruff check specfuse .specfuse/scripts tests scripts` (`All checks passed!`);
`python3 .specfuse/scripts/lint_plan.py <feature_dir>` (`OK — … structurally valid`).
The close's `gate_set` is `plannext` (the `plan-lint` gate above); the `code` gates
are the driver's broad run.

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. no `layout.yml`: `layout get` prints today's defaults; blocker link, `lint_roadmap` findings and template byte-identical | `NoLayoutGetIsToday.test_defaults`; `NoLayoutGoldens.test_blocked_dangling_lint_matches_golden` (with the positive control `test_positive_control`: `GOLDEN_LINT["blocked_dangling"]` carries an ERROR); `tests.test_layout_no_layout_goldens` `test_get_every_key`, `test_link_block_feature_example`, `test_lint_every_fixture`, `NoLayoutTemplateGoldens.test_render_equals_head_template`, `test_fresh_seed_equals_head_seed`; `tests.test_layout_link.RenderLink.test_no_layout_adr_matches_skill_example` | proven |
| 2. entries layout: `get` returns the declared values; `layout link` renders `[D-0007: …](../docs/decisions/decisions.md#D-0007)` from `.specfuse/` | `EntriesLayoutGet.test_entries`, `EntriesLinkRenders.test_link_cli`; `RenderLink.test_entries_fragment` | proven |
| 3. `lint_roadmap` accepts the link when the anchor exists, ERRORs naming the anchor when it does not, and ERRORs when the target is outside `decisions.location` | `LintChecksDecisionLinks.test_missing_anchor_and_outside_location_are_errors`; `tests.test_lint_roadmap` `test_fragment_with_explicit_anchor_is_clean`, `test_fragment_with_missing_anchor_is_error_naming_it`, `test_fragment_matching_heading_slug_is_clean`, `test_entries_layout_link_outside_location_is_error`, and the no-layout controls `test_no_layout_link_outside_docs_adr_is_clean`, `test_no_layout_fragment_with_anchor_is_clean` | proven |
| 4. absolute path, `..`, Windows drive or backslash, symlink escape is an ERROR; `paths:` is a WARN naming the follow-up | `InvalidLayoutIsReported.test_absolute_location_exits_1_naming_path`, `test_paths_block_exits_0_with_warn`; `tests.test_layout_validation` one test per form: `test_rejects_absolute_location`, `test_rejects_dotdot_segment`, `test_rejects_windows_drive_forward_slash`, `test_rejects_windows_drive_backslash`, `test_rejects_backslash`, `test_rejects_symlink_escaping_repo`, `test_paths_block_is_warn_naming_follow_up`, with `test_no_file_is_clean` and `test_valid_entries_file_is_clean` as controls | proven |
| 5. entries style: the template's Blocked-by example is an entries link and passes `lint_roadmap` | `TemplateFollowsStyle.test_entries_template_has_no_adr_and_lints_clean`; `tests.test_scaffold_data_in_sync`, `tests.test_skills_vendored_in_sync` for the copies | proven |

Clause 3's "outside the location" and clause 4's absolute-path / `paths:` cases are the
only ones the `feature_oracle` observes through its own fixtures; the remaining forms in
clause 4 (drive, backslash, symlink) are proven by `tests.test_layout_validation`, not
by the oracle module, which the gate's arming discipline allows (the oracle "proves 1–5
end to end", the unit tests prove each branch).

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's
`planned_cost_usd` (`PLAN.md` plans 24.00 = 19.00 for T01–T07 + 5.00 close); no figure
is estimated. `GATE-01.md` sets `cost_budget_usd: 26.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 3.00 | 0.2501 | 1 (passed) | 55.0 |
| T02 | 2.50 | 0.2465 | 1 (passed) | 62.8 |
| T03 | 3.00 | 0.1686 | 1 (passed) | 35.0 |
| T04 | 2.00 | 0.8797 | 3 (failed, failed, then passed after re-arm) | 179.9 |
| T05 | 3.50 | 0.3123 | 1 (passed) | 68.5 |
| T06 | 2.00 | 0.2498 | 1 (passed) | 80.5 |
| T07 | 3.00 | 0.6706 | 2 (`produces_not_in_diff`, then passed) | 142.7 |
| T01–T07 | 19.00 | 2.7776 | 10 | 624.4 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 24.00 | **2.7776** | 10 | 624.4 |

The ten recorded attempts spent $2.78 (14.6% of the $19.00 planned for them, 10.7% of
`cost_budget_usd`). This close's own attempt is not in `events.jsonl` while it runs (its
`attempt_outcome` is written when the driver ends the attempt), so it is not reconciled
here and the total excludes it. The arm predicate's budget class read "projected spend
$7.78 within 2.0x baseline planned total $24.00 (cap $48.00)".

**The expected `judge_editing` halt (PLAN decision 3) did not fire.** T01 did edit
`specfuse/loop/arm_eval.py` (+2 lines, the `layout.py` entry in the non-judge module
registry; `driver_staleness_detected` for T01 lists `arm_eval.py` and `layout.py`, with
`halted: false`). The only `arm_predicate_evaluated` event in the log, 01:41:05Z after
the first broad run failed, reports `would_arm: true` and `judge_editing: clean — "no
drafted WU touches judge-path surfaces"`; every other class was also clean. The class
reads `drafted` WUs, the successor gate's units a `plan-next` drafts, and a
single-gate feature has none, so an edit to a judge module by an implementation unit of
a terminal gate is invisible to it. The halt therefore cost **$0.00 and no
operator time**, and the operator's intended review of the registry entry did not
happen through it. The `arm_eval.py` diff is two lines, listed here for review:
`git diff main -- specfuse/loop/arm_eval.py`.

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `tests` (`spinning_signature_repeat`, `(errors=1)`) | T04 attempts 1, 2 | 2 | 0.5844 | the plan's `produces:` named a glob under `tests/` (`tests/fixtures/layout_goldens/**`), which the narrow tier turned into a bogus unittest module `tests.fixtures.layout_goldens.**` and errored on both attempts; the driver escalated on the repeated signature; the operator chose to rewrite T04 `.py`-only (`re_arm_dispatched`, 01:28:24Z) and the third attempt passed at $0.2953 |
| `produces_not_in_diff` | T07 attempt 1 | 1 | 0.5727 | the plan named `groom-backlog/SKILL.md` (both copies) as produces, but that file's only ADR mention is the specific `ADR-0002` blocking FEAT-2026-0011, not style wording; attempt 2 passed in 13.9 s with `produces_unchanged` justifications for both paths |
| `tests` (`failures=1`) + `other` (`no_gate_marker`) | first broad run | 1 | not charged to a unit | `test_init_integration` still asserted the pre-change seeded roadmap bytes; fixed in `f4b3450`, which the second broad run confirms |

T04's spin is the known failure recorded as issue #3539 (a non-`.py` `produces:` under
`tests/` becomes a bogus unittest module); the memory note is
"No non-.py produces under tests/". The PLAN pre-dated that knowledge for this unit.
T07's miss was a plan error, not a hollow pass: the unit had edited 21 files.

## Deferred verification

1. **The umbrella `specfuse layout get` delegated command is not built and not tested
   by this feature** (PLAN decision 2). It lives in the sibling `specfuse/specfuse`
   repository (`DELEGATED_COMMANDS` in `specfuse/cli.py`), which the driver cannot
   dispatch to, and its target `specfuse.loop.layout:main` exists for installed users
   only after a loop release. Every criterion in this gate invoked the module from
   source with `python3 -m specfuse.loop.layout`; none exercised `specfuse layout`, the
   installed console script, or a pipx build. Where checked: `PLAN.md`'s post-merge
   checklist, first item. After a release containing `specfuse.loop.layout`, open the
   umbrella PR adding the `"layout"` entry, raise its loop floor, publish, and confirm
   `specfuse layout get decisions.style` prints `adr` in a project with no `layout.yml`.
2. **No real entries-style consumer project was driven.** Every entries-style
   observation is a fixture repository built inside a test (`EntriesLayoutGet`,
   `EntriesLinkRenders`, `LintChecksDecisionLinks`, `TemplateFollowsStyle`,
   `test_block_feature_layout`'s entries case). Nothing here shows that a project's
   own `decisions.md` anchors, its heading conventions, or its existing roadmap pass
   the new anchor and location checks, or that `/block-feature` run by a model (the
   test checks the skill's text and the commands it names, not a session following it)
   produces a link `roadmap-link-gate` accepts. Where checked: `PLAN.md`'s post-merge
   checklist, second item: in a consumer repo that records decisions as entries, add a
   `layout.yml`, run `/block-feature` on one feature, and confirm the rendered link
   passes `roadmap-link-gate`.
3. **The `block-feature` skill is verified by its text, not by a session.**
   `tests.test_block_feature_layout` asserts the skill names `layout link`, reads
   `decisions.style`, builds no hand-made `docs/adr` path, and that the commands it
   names run in a no-layout and an entries repo. It does not show a model reading the
   skill and choosing the layout branch. Checked together with item 2.
4. **The fragment-link change on existing projects was observed only on fixtures.**
   Decision 5 turns a false "does not resolve" error into a real anchor check for every
   project. This repo's own roadmap stays green under `roadmap-link-gate` (the second
   broad run's `roadmap-link-gate` log: `0 error(s), 1 warning(s)`, the warning a
   FEAT-2026-0011 detail-cell WARN), but no other project's roadmap was linted.
   Where checked: the first consumer to upgrade, which sees it as the `Changed` entry
   in `CHANGELOG.md`.
5. **The authoring follow-up is not started.** `paths:` keys, a literal-path audit and
   the generator's `x-async.emit` assertions (clabonte/generator#2971) are out of scope
   in `PLAN.md`; a `paths:` block is a WARN only. Nothing is claimed about them.

## Consumer-visible contract changes

Enumerated across T01–T07 for acknowledgment; each is in `CHANGELOG.md` `Unreleased`
(`Added` ×1, `Changed` ×1, FEAT-2026-0224).

- **Added — an optional `.specfuse/layout.yml` with a `decisions:` block** (`style`
  `adr` | `entries`, `location`, `link` over `{location}`, `{path}`, `{id}`,
  `{domain}`), and `specfuse.loop.layout` with `get <key>`, `check` and `link
  --target --label [--from] [--domain]` (`python3 -m specfuse.loop.layout [--repo]`).
  With no file, every value is today's default.
- **Added — layout validation findings.** An absolute, `..`, Windows-drive,
  backslash or symlink-escaping `location` is an ERROR; an unknown `style` or `link`
  placeholder is an ERROR; a `paths:` block and an unknown top-level key are WARN.
- **Added — `lint_roadmap` checks, when `decisions:` is declared**, that a
  non-FEAT, non-URL Blocked-by link lands under `decisions.location` (ERROR
  otherwise), and the layout's own findings. A roadmap with no layout file gets none
  of these.
- **Changed — `block-feature`** builds the Blocked-by link with `layout link` rather
  than by hand; the roadmap template and its seed carry the style-dependent example
  between region markers that `specfuse init` renders through the layout (a project
  with no layout seeds the same bytes as before); `attention`, `gate-status`,
  `groom-backlog` (unchanged text), `pick-feature`, `roadmap-add`,
  `docs/methodology.md` and `docs/skills.md` say "a decision record" for "an ADR".
- **Changed — for every project, layout or not: a Blocked-by link's `#fragment` is
  stripped before the file check and then checked as an anchor.** A fragment link that
  was a false "does not resolve" ERROR is now clean when the anchor exists and an
  ERROR naming the anchor when it does not. Links without a fragment report as before.
  This is the one behaviour change for a project that does not adopt `layout.yml`
  (PLAN decision 5), and it is recorded in the changelog's `Changed` entry.

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## Documentation pass

`docs/methodology.md` and `docs/skills.md` (with their `specfuse/loop/data/docs/`
copies) were checked against the shipped code: the "decision record" wording replaces
"an ADR" at the sites the PLAN's replaced-wording grep named, `grep -rn "an ADR"`
over the five skills and two docs reports nothing, and `tests.test_scaffold_data_in_sync`
and `tests.test_skills_vendored_in_sync` pass, so the `plugins/` and `.specfuse/`
copies and the `data/` copies are byte-identical. No user-facing page describes `layout.yml`'s keys: the two docs
above only mention it ("ADR or decision entry, per `layout.yml`"), and the key reference is
`specfuse/loop/layout.py`'s docstring, `layout --help` and the `CHANGELOG.md` entry.
That is a gap, recorded under Open follow-ups.

## Retrospective

**What went well.** The ordering held: T04 recorded the goldens before any consumer
changed, T05 followed it in the graph, and the golden file is byte-identical across
T05 (`git diff` empty) and purely additive across T07, so "no layout = today" is
evidence rather than a claim. The walking skeleton did its job: the oracle module
existed after T01 with five classes skipped by owner name, and the final tree has none
skipped. Every "no findings" assertion has a firing control beside it
(`test_positive_control`, the `no_layout_*` lint tests, the entries-layout ERROR
tests). Seven units spent 14.6% of plan, and the broad run was green on its second
attempt.

**What didn't.** Three plan-level errors cost real attempts, none of them code: T04's
`produces:` glob under `tests/` (the already-known #3539, two failed attempts and a
human escalation), T07's `produces:` naming a file that needed no change (one wasted
$0.57 attempt), and the first broad run, which failed on a test outside every unit's
narrow set (`test_init_integration` asserting the old seed bytes). The decision-3
expectation that `judge_editing` would halt the arm was wrong for a single-gate
feature, so the registry edit in `arm_eval.py` had no review gate; it has two lines and
is in the PR diff. No real consumer was touched and no umbrella change exists, by
design, so the feature is verified from source and fixtures only.

**Lessons.** Staged in `LEARNINGS-pending.md` (`autonomy_default: auto`, so this close
may not append to `.specfuse/LEARNINGS.md`): the `judge_editing` class cannot fire on
a terminal-gate feature, and a feature that changes a seed or rendered artifact needs
every test that asserts the old bytes named in its narrow set.

**Open follow-ups (not blockers).** The two post-merge checklist items
(`specfuse:post-merge`, filed at close); a user-facing page describing `layout.yml`;
the authoring follow-up for `paths:`; the PLAN decision 3 premise (item 1 of the
lessons) for whoever plans the next feature that edits `arm_eval.py`.
