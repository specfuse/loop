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

- `CHANGELOG.md` and `specfuse/loop/changelog.py`: a Keep-a-Changelog-shaped release-notes document and the parser that reads it back, classifying entries into added/changed/fixed/breaking and requiring each to carry a FEAT-ID or issue-number trace. (FEAT-2026-0064/T01)
- `specfuse/loop/changelog.py` gains `stamp_release`, `append_entry` and `split_version_field`: cutting a version stamps `Unreleased` with the version, the date and the umbrella version — packed into the heading's version field as `<version>+umbrella.<umbrella>` so the Keep-a-Changelog heading stays one schema-legal line — opens a fresh empty `Unreleased` above it, and refuses any append or re-stamp targeting a released section (FEAT-2026-0064/T03)
- `.specfuse/release.yml`: optional release configuration holding `tag_prefix` and the `version_sources` list, read by `scripts/bump_version.py` with this repository's values as the fallback, so a project installing the scaffold sets its own release conventions instead of inheriting ours (FEAT-2026-0064/T03)

### Breaking

- `scripts/bump_version.py` now requires `--umbrella-version`: cutting a release without naming the umbrella version that ships this driver is refused before any file is written, because `pipx upgrade specfuse` resolves through the umbrella package and a driver version nobody can install is half a release (FEAT-2026-0064/T03)
- New `close-k` closing requirement: a close whose "Consumer-visible contract changes" section names a real change now fails pre-squash unless `CHANGELOG.md`'s `Unreleased` gained an entry tracing to that feature's FEAT-ID — and because `specfuse init` does not create a root `CHANGELOG.md`, a downstream project inherits the check before it has the file, and must add one (FEAT-2026-0064/T02)

### Changed

- `close-discipline.md` §3 now requires the close ceremony to append its consumer-visible enumeration to `CHANGELOG.md`'s `Unreleased`, classified and carrying the FEAT-ID, and states that this is the same material §3 already demands rather than a second write; an `n/a` close appends nothing. The rule ships in the scaffold, so every project that upgrades inherits the obligation (FEAT-2026-0064/T02)
- `fix-bug` gains a mandatory pre-PR step: append one `Unreleased` entry carrying `#<issue-number>`, in the same commit as the fix — bugs have no close ceremony, so this is the bug side's only collection point and four of the nine PRs merged 2026-08-03/04 would otherwise have been dropped (FEAT-2026-0064/T02)
