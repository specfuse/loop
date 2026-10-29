<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-2026-0247

`autonomy_default: auto`, so `FEAT-2026-0247/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). These two
are staged for the operator to **promote, narrow, or reject** at PR review.

---

- **[FEAT-2026-0247/G1-CLOSE] A unit that adds a module under `specfuse/loop/` must also
  join the suite-wide registries, and the walking skeleton is where to list them.** The
  new `ids.py` passed every unit's narrow tier, then the broad run failed four checks:
  the module was in neither `JUDGE_MODULES` nor `NON_JUDGE_MODULES`
  (`test_judge_path_registry`), two of its public helpers had no caller outside `tests/`
  (`test_caller_check_ratchet`), and a deliberate template edit left
  `GOLDEN_TEMPLATE_SHA256` stale (`test_layout_no_layout_goldens`). All four lived in
  modules outside every unit's `produces:`. Put "classify the module, give each public
  symbol a real caller, re-record any golden the unit changes on purpose" in the
  tracer-bullet unit's criteria, and name the three test modules there.

- **[FEAT-2026-0247/G1-CLOSE] Do not promise a helper in PLAN "Known limits" that no
  caller will use.** PLAN said "T01's sort key is available where order matters"; no
  site ever called `ids.sort_key`, the caller ratchet rejected it, and T10 deleted it,
  leaving the limit's sentence false. If a limit is "lexical order is good enough",
  say that and stop; add the helper in the unit that first needs it.
