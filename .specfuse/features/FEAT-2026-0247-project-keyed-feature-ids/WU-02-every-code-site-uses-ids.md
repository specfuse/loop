---
id: FEAT-2026-0247/T02
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/agent_policy.py
  - specfuse/loop/changelog.py
  - specfuse/loop/gh_features.py
  - specfuse/loop/promotion.py
  - specfuse/loop/upgrade_merge_gate.py
  - specfuse/loop/gate_eval.py
  - specfuse/loop/loop.py
  - tests/test_ids_call_sites.py
  - tests/test_keyed_feature_ids_end_to_end.py
produces_driver_helper:
  - _FEATURE_ID_RE
  - _LEARNINGS_FEAT_ID_RE
  - _BARE_FEAT_REF_RE
---

# T02 — every code site that parses a feature ID uses `ids`

**Objective.** No code path rejects, drops or mis-parses a keyed feature ID.

**Context.** `FEAT-2026-0247/T02`. This unit **edits** the oracle module T01 created.
Replace each private literal with an import from `specfuse.loop.ids`:

- `agent_policy.py:65` `_FEAT_ID_RE` (queue and override entries; messages at 728, 736,
  887 name the keyed form too)
- `changelog.py:39` `_TRACE_RE`
- `gh_features.py:18` (the `[FEAT-…]` issue-title pattern, `INIT-` branch unchanged)
- `promotion.py:43` `FEATURE_ID_RE`
- `upgrade_merge_gate.py:27` `_FEATURE_DIR_RE`
- `loop.py:301` `_LEARNINGS_FEAT_ID_RE`, `loop.py:1160` `_FEATURE_ID_RE` (the
  `--feature` argument), `loop.py:8537` `_BARE_FEAT_REF_RE` (anchor refs)

and replace the positional parse in `gate_eval.py:461-466` (`name.split("-")`,
`parts[2]` as ordinal) with `ids.parse`, so the partial lookup `0008` and a slug lookup
resolve keyed and legacy folders alike.

Un-skip the oracle's clause-3 class: a keyed ID through each site above, paired with the
legacy ID through the same site.

**Acceptance criteria.**

1. `tests/test_ids_call_sites.py` drives each site with a keyed ID and fails on the T01
   tree for each one; it passes after. Each keyed case is paired with its legacy case.
2. The partial-lookup test resolves `0008` to `FEAT-ACME-2026-0008-x` and to
   `FEAT-2026-0008-x` in separate fixtures, and runs the resolver over the real
   `.specfuse/features/` corpus by ordinal with no change in result from HEAD.
3. `grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/` returns only `specfuse/loop/ids.py`.
4. `python3 -m unittest tests.test_lifecycle_integration tests.test_agent_policy_schema -b`
   passes.

**Do not touch.** `ids.py`'s grammar (T01 owns it; a needed change is an escalation).
Name-only sort sites (`loop.py:1207-1311`, `arm_sweep.py:75`, `state.py:280`): the
lexical order is correct for keyed-after-legacy (PLAN Known limits). Skills, docs,
core-owned files.

**Verification.** The narrow tier for `implementation`, plus the AC4 command.

**Escalation triggers.** A site whose behaviour for a legacy ID would change: stop and
name it.
