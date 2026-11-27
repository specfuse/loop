---
class: added
trace: FEAT-LOOP-2026-0253
---
New opt-in per-gate key `inputs:` (git pathspec globs): the per-attempt verify reuses the earlier PASS of that gate, reported `PASS (cached)`, while its command and matching files are unchanged; the broad run, baseline probe, feature_oracle and any gate another gate needs always run fresh. An `inputs:` that is not a non-empty list of non-empty strings is a CONFIGURATION ERROR.
