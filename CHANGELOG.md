<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Changelog

All notable changes to this project are documented here, in the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) shape: an
`Unreleased` section collects entries as work lands, and each release heading
stamps a version and a date once one is cut.

Every entry is classified `added` / `changed` / `fixed` / or `breaking`, and
carries a `FEAT-YYYY-NNNN` or `#<issue-number>` trace back to the
retrospective or issue that explains it. `specfuse/loop/changelog.py` parses
this document against that schema; it is not free-form prose.

<!--
No backfill: fifty-one features and every prior bug PR predate this file and
are deliberately not represented here. Reconstructing them from commit
subjects would produce exactly the low-quality summaries this feature exists
to prevent, and it would read as authoritative. See
.specfuse/features/FEAT-2026-0064-release-notes/PLAN.md for the reasoning.
Entries below cover only work landing from FEAT-2026-0064 onward.
-->

## [Unreleased]

### Added

- `specfuse/loop/prerun.py`, a new importable module shipped in the wheel. `run_pre_dispatch(wu, feature_dir, cfg)` resolves a work unit's `prep` and `oracles` set names against `verification.yml` and runs them — `prep` fail-fast in declared order with a distinct `PREP_HALT_CLASS`, `oracles` capture-all — by calling `_run_gate_set` rather than reimplementing gate execution. An unknown set name returns a named CONFIGURATION ERROR mirroring `verify()`'s `extra_gates` phrasing, never a silent pass. Additive as an import path: nothing previously occupied it. The driver calls it on every dispatch — see the behaviour change under Changed (FEAT-2026-0057)
- `specfuse/loop/prerun_capture.py`, a new importable module shipped in the wheel. `format_oracle_capture(results)` turns captured oracle output into a prompt section bounded by `ORACLE_CAPTURE_BUDGET_BYTES` (8000, reused from `truncate_failure_note`'s existing budget for the same class of injected content), splitting the budget evenly across oracles, selecting retained lines through `select_gate_report_lines` rather than a positional tail, and marking any truncation with the exact byte count dropped. Known rough edge, still open: an `oracles` entry is informational and `select_gate_report_lines` is a pass/fail verdict selector, so a captured block that fits within its budget share still carries a `NO VERDICT FOUND ... Run the command directly.` banner — see the partial fix under Fixed (FEAT-2026-0057)
- The `verification` skill documents the `prep` / `oracles` work-unit frontmatter contract, in both the plugin-shipped and vendored copies — both keys resolve against `verification.yml` set names and both run before dispatch — with a table and a choosing rule against `extra_gates`, which runs at exit (FEAT-2026-0057)

### Changed

- **The driver now honours `prep:` and `oracles:` in work-unit frontmatter.** `WorkUnit` gains `prep: list[str]` and `oracles: list[str]`, `load_wu` parses both with the same contract `extra_gates` has (a string is coerced to a one-element list, a list is preserved, any other type raises ``ValueError: `prep` must be a string or list of strings``), and `execute_unit_attempt` calls `run_pre_dispatch` before the session is spawned, appending the formatted `## Captured oracle output (pre-dispatch)` section to the work-unit body the session receives. Two consumer-visible consequences on upgrade: a work unit carrying a `prep:` or `oracles:` key of the wrong shape now fails to load where the key was previously ignored, and `load_verification()` is now read on every dispatched attempt rather than only at verification time (FEAT-2026-0057)
- A failing `prep` entry halts before dispatch with a distinct outcome. No session is spawned and no cost is incurred; the work unit flips to `blocked_human` and two new event payload values appear in `events.jsonl` — an `attempt_outcome` with `outcome: "prep_halted"` carrying `halt_class` and `summary` extras, and a `human_escalation` with `reason: "prep_halted"`. Anything enumerating outcome or escalation-reason values should expect them (FEAT-2026-0057)
- `WU.template.md` documents the `prep`, `oracles`, and `extra_gates` frontmatter keys in its `AUTHOR-SET FIELDS` block — each naming that it resolves against a `verification.yml` set name and each saying *when* it runs: `prep` and `oracles` before dispatch, `extra_gates` at exit. `extra_gates` has shipped since #62 and was undocumented in the template until now. The file is in `scaffold.py`'s `_VERSIONED_OVERLAY_PREFIXES`, so `specfuse upgrade` overwrites the vendored copy in every downstream project; the change is documentation only and no behaviour rides on it (FEAT-2026-0057)
- `verification.yml.example` seeds a **commented** `oracles:` set with a worked example and a note that its entries are informational captures rather than pass/fail gates. The file is in `scaffold.py`'s `_VERSIONED_OVERLAY_EXACT` and is copied to `verification.yml` on `init`, so upgrades overwrite it — but because the set is commented, a fresh `specfuse init` still produces a config with no live `oracles` set and no behaviour change (FEAT-2026-0057)

### Fixed

- `format_oracle_capture` no longer appends `select_gate_report_lines`' `NO VERDICT FOUND ... Run the command directly.` banner to a captured oracle block that had to be **truncated** to fit its budget share. **Partial fix — captures within their budget share are unaffected and still carry the banner**, because `_run_gate_set` composes it into each result's `report` string before `format_oracle_capture` is reached, and the filter sits after `_fit_to_budget`'s within-budget early return. A project adopting `oracles:` should expect its injected captures to still instruct the reading agent to re-run the captured command; tracked as FU-5R in the feature's `RETROSPECTIVE.md` (FEAT-2026-0057)

## [0.9.3+umbrella.0.9.3] - 2026-08-05

### Added

- Work-unit frontmatter gains `folded_through_re_arm`, an integer marker stamped by the driver's re-arm fold in the same write set as the accumulators. `detect_rearm_dispatch` now compares it against `re_arm_count` instead of reading `cost_usd`'s value, so a re-arm whose prior cycle genuinely cost nothing still folds. An absent marker reads as `0`, so the field is additive and an un-migrated project keeps working (FEAT-2026-0067)
- `specfuse/loop/rearm_migration.py` stamps the new marker onto work units that were already re-armed before this contract, and folds forward the shape whose prior spend survived only in `re_arm_history[].prior_cost_usd`. Importable as `census`, `migrate_file`, and `migrate_repo`; run it once against `.specfuse/features/` after upgrading (FEAT-2026-0067)

### Changed

- `cumulative_cost_usd`, `cumulative_duration_seconds`, `cumulative_input_tokens`, and `cumulative_output_tokens` now accumulate on every re-arm unconditionally, including one whose prior cycle cost $0.00. Previously the fold ran only when `cost_usd > 0` at dispatch, so a zero-cost cycle left its duration and token counts unaccumulated too — anything reading these four fields now reads a more complete quantity than before (FEAT-2026-0067)
- `task_completed` events carry the corrected accumulator: the emitter reads `cumulative_cost_usd` from frontmatter, so a re-arm the old guard skipped now reports a larger lifetime figure. Anything aggregating `events.jsonl` for cost will see the step (FEAT-2026-0067)
- `WU.template.md`, in both the packaged and vendored copies, documents `folded_through_re_arm` and states that `cumulative_*` is unconditionally the lifetime accumulator. `cost.py`'s module docstring no longer presents the fold-never-ran shape as a supported ongoing design and names it as a pre-migration legacy its fallback still tolerates (FEAT-2026-0067)

### Fixed

- `rearm_migration.py` no longer double-counts a work unit that was re-armed and never re-dispatched. When `cost_usd` already agrees with the `re_arm_history` prior-cost sum within tolerance the money is already in the file, so `cost_usd` and `duration_seconds` are reset to `0.0` in the same write set instead of a second copy being added to `cumulative_*`. A project whose feature folders hold `completed_out_of_loop` units — or any unit re-armed without a subsequent dispatch — would otherwise have had those records inflated by exactly one prior cycle on the first migration run. The re-armed-and-re-dispatched case is unchanged (FEAT-2026-0067)

## [0.9.2+umbrella.0.9.2] - 2026-08-04

### Fixed

- A `produces:` entry that is a directory is now an ERROR in `specfuse-lint` and refused before dispatch, instead of after a full session. The driver already refused it correctly, but only post-session and three times over — $6.42 and 20.6 minutes observed on a real feature for a `Path.is_dir()` call on static frontmatter (#593)
- An unterminated frontmatter block is now a lint finding naming the missing `---`, instead of a traceback blaming an arbitrary body line. A file the parser cannot read no longer makes its whole feature folder unevaluable by every check (#306)
- The scaffold-upgrade merge gate no longer returns a false halt against a package-era target. It invokes the packaged linter when the target ships no `.specfuse/scripts/lint_plan.py` shim, skips non-feature directories, and reports an unrunnable linter as its own blocker instead of blaming every feature by name (#309)
- CI now runs every gate `.specfuse/verification.yml` declares. `scripts/smoke-test.sh` derives its list from that file instead of carrying a hand-maintained copy, which had drifted six gates behind — including two that shipped with features and had never been executed (#592)

## [0.9.1+umbrella.0.9.1] - 2026-08-04

### Fixed

- `specfuse init` now seeds a root `CHANGELOG.md`, and `specfuse upgrade` creates one when absent without touching an existing file. Without it, the first feature in a fresh project carrying any consumer-visible change failed `close-k` at its terminal close, on a file the scaffold never created (#575)
- `sync-scaffold.sh` halts instead of silently reverting a local edit to a core-vendored file. It records each vendored file hash, so core moving forward is a fast-forward while a loop-local edit stops the run with the file named and the edit intact (#581)

## [0.9.0+umbrella.0.9.0] - 2026-08-04

<!--
ONE-TIME EXCEPTION to this file's no-backfill rule, recorded so it is not read as
precedent. The backfilled entries below cover work merged between
the v0.8.0 tag and this file's creation in FEAT-2026-0064 — twelve features and
eleven bug PRs that shipped before any collection point existed.

It is included because two of those changes BREAK a downstream project on upgrade
and a consumer had no way to discover them: `close-k` fails a close on a project
that has no root CHANGELOG.md, and the `event-type-gate` widened to the whole
envelope. Shipping a release whose notes omit its own breaking changes would
defeat the document on its first outing.

Every entry below is lifted from the originating feature's
`RETROSPECTIVE.md` § "Consumer-visible contract changes" — the enumeration
close-discipline.md §3 already required — NOT reconstructed from commit subjects.
That distinction is the whole argument of FEAT-2026-0064: a generator walking PR
titles turns "no installed console script can reach the firing path" into
"autofix wiring".

The no-backfill rule stands for the 51 features that predate v0.8.0. They have no
§3 enumeration to lift, and inventing one is the failure this file exists to
prevent.
-->

### Breaking

- `scripts/bump_version.py` now requires `--umbrella-version`: cutting a release without naming the umbrella version that ships this driver is refused before any file is written, because `pipx upgrade specfuse` resolves through the umbrella package and a driver version nobody can install is half a release (FEAT-2026-0064/T03)
- New `close-k` closing requirement: a close whose "Consumer-visible contract changes" section names a real change now fails pre-squash unless `CHANGELOG.md`'s `Unreleased` gained an entry tracing to that feature's FEAT-ID — and because `specfuse init` does not create a root `CHANGELOG.md`, **a downstream project inherits the check before it has the file, and must add one** (FEAT-2026-0064/T02)
- New `close-j` closing requirement: `close-discipline.md` §2 gains a required per-entry `kind:` on the hedged-verdict follow-up record, from the closed set `acceptance-discharged` / `externally-verifiable-later` / `routed-finding` / `inherent`. **A hedged close that passed before now fails the lint.** Unhedged closes (`verdict: met`) are unaffected. The record's entry format is now machine-read — `**kind:** \`value\``, entries split on `### ` — so a record written as a YAML block or with `kind:` unbackticked lints as *missing* rather than *differently formatted* (FEAT-2026-0059/T01)
- The `event-type-gate` verification gate widens from one field to the whole envelope. It keeps its name and its `verification.yml` entry, but a downstream project whose `events.jsonl` carries any envelope violation — not just an unknown `event_type` — starts failing a gate that previously ignored it (FEAT-2026-0073/T02)
- A new `roadmap-link-gate` in `.specfuse/verification.yml`'s `code` set. **A downstream project whose roadmap already carries ERROR-severity link rot starts failing a gate it did not previously have.** Intended: the rot is real, bidirectional, and was invisible (FEAT-2026-0034/T02)
- A new `arm-sweep-gate` in the same set, reporting which arm-predicate branches have been observed on real input. Fails only when the sweep cannot evaluate a baselined feature, never on an unexercised branch (FEAT-2026-0063/T02)
- `scripts/bump_version.py` now requires `--umbrella-version`: cutting a release without naming the umbrella version that ships this driver is refused before any file is written, because `pipx upgrade specfuse` resolves through the umbrella package and a driver version nobody can install is half a release (FEAT-2026-0064/T03)
- New `close-k` closing requirement: a close whose "Consumer-visible contract changes" section names a real change now fails pre-squash unless `CHANGELOG.md`'s `Unreleased` gained an entry tracing to that feature's FEAT-ID — and because `specfuse init` does not create a root `CHANGELOG.md`, a downstream project inherits the check before it has the file, and must add one (FEAT-2026-0064/T02)

### Added

- `/diagnose-issue` skill: reads a harvester finding and the component source it implicates, and posts a structured root-cause diagnosis carrying machine-readable `confidence` and `fix_scope` fields. Shipped on all three skill surfaces (FEAT-2026-0041)
- `specfuse.monitor.diagnosis` — new public module. `Diagnosis`, `render`, `parse`, `DiagnosisParseError`, `FIX_SCOPES`. Its `<!-- specfuse:diagnosis … -->` marker is a **wire contract**: FEAT-2026-0042 parses it, so its shape cannot change silently (FEAT-2026-0041/T01)
- `specfuse.monitor.diagnose_cli` — headless diagnosis entry point, invoked as `python3 -m specfuse.monitor.diagnose_cli`. No console script added; the module path is the interface (FEAT-2026-0041/T03)
- `specfuse.monitor.autofix` and `specfuse.monitor.autofix_state` — the autofix decision layer and its GitHub-held rate-limit state (one attempt per fingerprint, daily cap). Fires headless `fix-bug` only when a diagnosis is confident and `fix_scope: small`, behind a per-component `autofix` dial that defaults to `"off"`. **Nothing fires on a schedule** — the entry point is deliberately not a console script and not a `specfuse-monitor` subcommand (FEAT-2026-0042)
- `fix-bug` gains a documented headless mode: every interactive halt maps to a named outcome, so an automated caller gets a verdict rather than a hang. Its refusal paths become a second guardrail behind the autofix predicate (FEAT-2026-0042/T03)
- `specfuse/loop/lint_roadmap.py` — reads `roadmap.md` and `roadmap-archive.md` as one link graph and checks blocked-by resolution, ref resolution in both directions, anchor adjacency, cross-file ID uniqueness, and row-versus-section status agreement, the last added by issue #465 (FEAT-2026-0034)
- `specfuse/loop/arm_sweep.py` — reports which arm-predicate verdict branches have been observed on real input, excluding features that structurally cannot be evaluated (FEAT-2026-0063/T01)
- `schemas/driver-event.schema.json` — a driver-local event registry packaged into the scaffold, sanctioning driver event types the vendored orchestrator envelope has no concept of, resolved by fall-through on a deep copy so the vendored schema on disk is never touched (FEAT-2026-0060)
- The same registry gains a `correlation_id` surface — `closing_names` and `hygiene_suffix_pattern` — so the envelope accepts the closing-sequence `G<n>-<NAME>` and hygiene `TNNH` ID shapes `correlation-ids.md` documents. **285 validation errors across 38 feature folders went to zero** (FEAT-2026-0073/T01)
- `auto-fix-attempted-failed` joins `LABEL_REGISTRY`, provisioned by `specfuse init` / `upgrade` like every other declared label (FEAT-2026-0042/T02)
- `/accept-hedged-close` now prints a **verdict-ceiling headline before any entry detail** — "no in-repo rework can raise this verdict" versus "rework exists: `<named condition>`" — computed from the entries' `kind:` values, and prompts each `routed-finding` for a tracking surface (FEAT-2026-0059)
- `CHANGELOG.md` and `specfuse/loop/changelog.py`: a Keep-a-Changelog-shaped release-notes document and the parser that reads it back, classifying entries into added/changed/fixed/breaking and requiring each to carry a FEAT-ID or issue-number trace. (FEAT-2026-0064/T01)
- `specfuse/loop/changelog.py` gains `stamp_release`, `append_entry` and `split_version_field`: cutting a version stamps `Unreleased` with the version, the date and the umbrella version — packed into the heading's version field as `<version>+umbrella.<umbrella>` so the Keep-a-Changelog heading stays one schema-legal line — opens a fresh empty `Unreleased` above it, and refuses any append or re-stamp targeting a released section (FEAT-2026-0064/T03)
- `.specfuse/release.yml`: optional release configuration holding `tag_prefix` and the `version_sources` list, read by `scripts/bump_version.py` with this repository's values as the fallback, so a project installing the scaffold sets its own release conventions instead of inheriting ours (FEAT-2026-0064/T03)

### Changed

- `specfuse.monitor.redaction._redact_text` → **`redact_text`**: promoted from module-private to public API so diagnosis prose routes through the same redaction boundary as failure artifacts rather than duplicating the secret patterns. `redact_artifact` is unchanged (FEAT-2026-0041/T01)
- `budget_projection` and the per-gate budget brake now read a work unit's **lifetime** spend rather than its current dispatch cycle, so a re-armed unit is no longer invisible to either. Measured under-read on a real feature: $6.23 and $5.01 (FEAT-2026-0062)
- `decision_class_paths` recognises non-Python dependency manifests — `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `Gemfile`, `*.csproj`, `composer.json` — and reports `not_evaluable` rather than `clean` on a manifest it cannot parse. A stop class that reports clean on unreadable input is worse than an absent one (FEAT-2026-0061)
- `validate_event.load_validator()` widens the vendored envelope on a deep copy; the packaged schema file is never modified, so a vendor sync cannot silently revert the fix; the mechanism arrived with FEAT-2026-0060 and was extended here (FEAT-2026-0073)
- `close-discipline.md` §3 now requires the close ceremony to append its consumer-visible enumeration to `CHANGELOG.md`'s `Unreleased`, classified and carrying the FEAT-ID, and states that this is the same material §3 already demands rather than a second write; an `n/a` close appends nothing. The rule ships in the scaffold, so every project that upgrades inherits the obligation (FEAT-2026-0064/T02)
- `fix-bug` gains a mandatory pre-PR step: append one `Unreleased` entry carrying `#<issue-number>`, in the same commit as the fix — bugs have no close ceremony, so this is the bug side's only collection point and four of the nine PRs merged 2026-08-03/04 would otherwise have been dropped (FEAT-2026-0064/T02)

### Fixed

- A gate's FAIL report now contains the failure. `select_gate_report_lines` pins any verdict line found before the positional tail, with an explicit elision marker, and states `NO VERDICT FOUND` rather than presenting unrelated trailing output as the failure. Measured cost of the defect: two attempts, 1350 seconds, $5.31, escalated as spinning with no diagnosis; shipped as a direct bug fix in PR #322 (FEAT-2026-0068)
- `auto_archive_feature` no longer swallows the following feature's `<a id>` anchor when moving a section to the archive (#314)
- The pre-flight baseline probe no longer blames the integration branch for a **resumed** gate's failure, and no longer prints its own changeset as "proof the feature's tree matches its integration branch" — a diff that refuted the sentence above it. Remediation now points at the branch, with `git log -S<signature>` named; fixed in PR #473 (#360)
- A detail section whose `**Status:**` disagrees with its roadmap row is now an ERROR. Twenty-one of forty-two archived sections carried the disagreement when the check was written; repaired in PR #464 and guarded in #468 (#465)
- Tests no longer shell out to `python3 -m pytest`, which is a dependency of nothing in this repository and absent from CI — five instances across three features passed locally and failed only on the runner. `tests/test_no_pytest_subprocess.py` guards against a sixth (#519)
- The all-gates-passed poll no longer writes `PLAN.md status: complete`, a value absent from the valid-status vocabulary (#280)
- `lint_plan`'s bare-root-path warning and the driver's in-diff cross-check no longer disagree on how a repo-root deliverable must be spelled, fixed in PR #279 (#259)
- Stamping a release no longer produces a CHANGELOG that fails its own parser. `stamp_release` opens a fresh empty `Unreleased` and `parse_changelog` flagged every empty section, so cutting any release emitted a document failing its own parse test (#562)
