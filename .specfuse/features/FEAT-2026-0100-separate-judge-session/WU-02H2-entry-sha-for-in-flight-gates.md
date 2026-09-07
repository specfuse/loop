---
id: FEAT-2026-0100/T02H2
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
model: sonnet
effort: medium
oracle_env: macos_local
provenance: "G1-CLOSE attempt 2 (2026-09-06), the judge's first finding: entry_sha was stamped at the first probe that ran T02H's code, commit 7e02525, so the judge's range held 4 of the gate's 34 commits"
produces:
  - specfuse/loop/loop.py
  - tests/test_judge_close_path.py
---

# Hygiene: a gate whose baseline predates `entry_sha` seeds it from the merge-base

**Objective.** `write_gate_baseline` (T02H) sets `entry_sha` to the probe's
`sha` the first time it is absent. On a gate that already had a baseline
before the field existed, that "first time" is a mid-gate re-probe, and the
judge diffs from there. When the gate file already carries a baseline but no
`entry_sha`, seed it from the merge-base of HEAD with the feature's
integration branch instead; only a gate with no prior baseline seeds it from
the probe.

**Context.** FEAT-2026-0100/T02H2, hygiene precursor to the close's third
attempt. `resolve_base(feat_fm)` already yields the integration branch and
`resolve_gate_start_sha` already runs `git merge-base` as its fallback; reuse
that call, do not add a second. A merge-base that cannot be computed leaves
`entry_sha` unset so the resolver's own fallback chain applies. Red test
first on a fixture whose `GATE-01.md` carries `sha` and `probed_at` but no
`entry_sha`, then is re-probed.

**Acceptance criteria.**

- `tests/test_judge_close_path.py::test_legacy_gate_reprobe_seeds_entry_sha_from_merge_base` fails on HEAD and passes after: after the re-probe, `entry_sha` equals `git merge-base <base> HEAD`, not the probe's `sha`.
- `::test_fresh_gate_first_probe_seeds_entry_sha_from_probe`: a gate with no prior baseline still gets `entry_sha == sha`.
- `tests/test_baseline_persistence.py` and the existing T02H tests pass unchanged.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `resolve_gate_start_sha`'s preference order; the probe's
skip decision; `_wu_sections.py` (T01H2); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if `write_gate_baseline` has
no access to the feature's PLAN frontmatter without a signature change that
breaks an existing caller; name the caller.
