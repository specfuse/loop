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
