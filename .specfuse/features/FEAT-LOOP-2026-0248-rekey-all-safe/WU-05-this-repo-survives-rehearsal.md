---
id: FEAT-LOOP-2026-0248/T05
type: implementation
status: blocked_human
attempts: 0
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-10-29T17:04:06+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 4.00
    prior_duration_seconds: 5059.215
    reason: "Planning error, not the unit's work: the prescribed --include-prose scope included tests/, specfuse/, docs/ and plugins/, whose mentions are mostly fixtures and illustrative example IDs (78, then 32 failures in operator rehearsals), and the fixed produces list could not be known in advance. Scope narrowed to this repository's own history; produces removed; T06 added for the stale in-process validation."
oracle_env: macos_local
planned_cost_usd: 4.00
max_attempts: 3
duration_seconds: 22.023
cost_usd: 0.118917
input_tokens: 10
output_tokens: 1215
---

# T05 — this repository's full suite passes a rehearsal of the rename

**Objective.** The rehearsal from 2026-10-29 is re-run with the fixed tool and comes back
green: with key `LOOP`, this repository can be fully renamed without a failing test.

**Context.** `FEAT-LOOP-2026-0248/T05`. This unit **edits** existing test modules only;
which ones is discovered by the rehearsal, so it declares no `produces:`. Run, from the
repository root:

```
python3 -m specfuse.loop.ids migrate --all --include-prose '.specfuse/features/**' '.specfuse/roadmap.md' '.specfuse/roadmap-archive.md' '.specfuse/LEARNINGS*.md' --rehearse
```

`ids.key: LOOP` is set in `.specfuse/layout.yml` on this branch. The prose scope is this
repository's own history only. `tests/`, `specfuse/`, `docs/` and `plugins/` are left
out on purpose: their mentions are fixtures and illustrative example IDs that happen to
share numbers with real features (two operator rehearsals that included them failed 78
and 32 tests, and rewrote vendored core files). Real feature folder names in those
trees are still rewritten by T02's structural rule.

Operator rehearsals with the wider scope failed in, among others: `test_ids` (RealCorpus),
`test_ids_call_sites`, `test_keyed_feature_ids_end_to_end`, `test_agent_policy_queue`,
`test_feature_id_resolution`, `test_gate_eval_calibration`, `test_gh_features`,
`test_lint_correlation_id`, `test_validate_event`, `test_monitoring_bootstrap_artifacts`,
`test_layout_no_layout_goldens`. Re-run with the scope above first; fix only what still
fails.

For each failing test, fix the **assumption**, not the assertion: a test that reads a real
feature folder, roadmap row or event by a hard-coded legacy ID resolves it through
`ids.resolve` or by ordinal; a real-corpus test that asserts the legacy pattern extracts
every ID accepts either shape via `ids.parse`; a golden or sentinel the rename
legitimately rewrites is matched in whichever form the tree holds. Each fixed test must
still pass on the unrenamed tree. Never edit `specfuse/`; a failure that needs a code
change is an escalation (name the module and case).

**Acceptance criteria.**

1. The command above exits zero, and its output (validation result plus the test
   command's summary line) is quoted in this unit's RESULT `notes`.
2. `python3 -m unittest discover -s tests -b` passes on the real, unrenamed tree.
3. No assertion is deleted or loosened to pass; every edited test still fails if the
   behaviour it guards regresses (state, per edited module, the regression it still
   catches).

**Do not touch.** `specfuse/` code (T01–T04 own it; a needed code change is an
escalation). The real tree's feature folders, roadmap and policy: nothing is applied here.

**Verification.** The narrow tier for `implementation`, plus AC1's command.

**Escalation triggers.** A failure whose fix needs `ids.py` or another `specfuse/` module:
stop, name the module and the case. A failure that only a foreign-ID exclusion would fix:
stop and ask the operator which ID to pass to `--exclude-id`.
