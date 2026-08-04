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

### Fixed

- A `produces:` entry that is a directory is now an ERROR in `specfuse-lint` and refused before dispatch, instead of after a full session. The driver already refused it correctly, but only post-session and three times over — $6.42 and 20.6 minutes observed on a real feature for a `Path.is_dir()` call on static frontmatter (#593)
- An unterminated frontmatter block is now a lint finding naming the missing `---`, instead of a traceback blaming an arbitrary body line. A file the parser cannot read no longer makes its whole feature folder unevaluable by every check (#306)
- The scaffold-upgrade merge gate no longer returns a false halt against a package-era target. It invokes the packaged linter when the target ships no `.specfuse/scripts/lint_plan.py` shim, skips non-feature directories, and reports an unrunnable linter as its own blocker instead of blaming every feature by name (#309)

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
