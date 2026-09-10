<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# LEARNINGS staged by FEAT-2026-0103

Staged here rather than appended to `.specfuse/LEARNINGS.md` directly: this
feature runs `autonomy_default: auto`, where `assert_learnings_staged_under_auto`
forbids a closing WU from writing the shared file. Promote from here.

- [FEAT-2026-0103/G1] In a repository with a canonical/mirror split, a WU's
  `produces:` must name the **canonical** side, never the generated mirror.
  T04 was told to document a new key and listed
  `specfuse/loop/data/verification.yml.example` — the package copy that
  `scripts/sync-scaffold.sh` regenerates from `.specfuse/` — so its edit was
  correct, verified, and on the side that the next sync would overwrite. Its
  own per-attempt gates were green; only the gate's broad run caught it, as
  `test_package_data_matches_canonical`, and repairing it cost a whole extra
  work unit ($1.61 against a $1.00 plan). Rule: when drafting a `produces:`
  list, check each path against the repo's sync direction (here: `.specfuse/`
  and `docs/` are canonical, `specfuse/loop/data/**` is the mirror) and name
  the source, not the copy. A `produces:` entry under a directory some script
  regenerates is an authoring defect even when the edit itself is right.

- [FEAT-2026-0103/G1] A hygiene WU armed from a broad-run failure must name
  **every** drift the broad run reported, not the one that names the WU's
  headline file. T04H's first body named the `verification.yml.example` drift
  and not the `docs/methodology.md` one; two consecutive attempts repaired
  exactly what they were told about, were refused by
  `test_package_docs_match_canonical` — a test the body never mentioned — and
  produced an identical summary with an identical touched set, which is
  precisely the shape `detect_deterministic_refusal_repeat` escalates on. The
  session was not spinning; it was solving the stated problem correctly and
  being graded on an unstated one. Rule: when arming a repair WU from a broad
  run, transcribe the full `failing:` list from the gate's `broad_run_result`
  into the WU body and make each entry an acceptance criterion. A refusal a
  session cannot see in its own brief is not a signal it can act on, and the
  spinning detector will read the repeat as the session's fault.
