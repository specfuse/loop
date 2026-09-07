---
id: FEAT-2026-0100/T02H
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
model: sonnet
effort: medium
oracle_env: macos_local
provenance: "G1-CLOSE attempt 1 (2026-09-06), FOLLOW-UPS.md entry 2: the judged event's diff_base was the re-probed baseline sha 7f50a47, whose range covered 2 lines of GATE-01.md against the gate's real 3,677 (merge-base 64dde90)"
produces:
  - specfuse/loop/loop.py
  - tests/test_judge_close_path.py
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-06T16:32:13.482391+00:00
duration_seconds: 1147.336
cost_usd: 0.811421
input_tokens: 64
output_tokens: 18268
---

# Hygiene: the judge diffs from gate entry, not from the latest baseline probe

**Objective.** `resolve_gate_start_sha` (`loop.py:6377`) prefers
`GATE-NN.md`'s `baseline.sha`, and the baseline probe re-runs after every
driver-restart halt and overwrites it. On a gate that halts, the judge's
diff shrinks to the last probe's range. Record the gate's entry sha once and
prefer it.

**Context.** FEAT-2026-0100/T02H, hygiene precursor to the close's re-run.
`write_gate_baseline` (`loop.py:4366`) writes `sha` and `probed_at` on every
probe. Add `entry_sha`: set on the first probe of a gate and never
overwritten by later probes (a re-probe rewrites `sha` and `probed_at` only;
`read_gate_baseline` returns `entry_sha` when present). `resolve_gate_start_sha`
prefers `entry_sha`, then the merge-base with the integration branch, then
the latest `sha` as a last resort, and the `judged` event's
`diff_base_source` names which one was used. Do not change what the
re-probe skip logic compares (`sha == HEAD`). Red test first, on a fixture
whose gate is probed, halted, and probed again before its close.

**Acceptance criteria.**

- `tests/test_judge_close_path.py::test_judge_diff_base_survives_a_reprobe` fails on HEAD and passes after: after two `write_gate_baseline` calls with different shas, `resolve_gate_start_sha` returns the first, and the `judged` event's `diff_base_source` reads `GATE-NN.md baseline.entry_sha`.
- `::test_entry_sha_is_written_once`: the second probe leaves `entry_sha` unchanged and updates `sha`.
- `::test_legacy_baseline_without_entry_sha_falls_back_to_merge_base`.
- `tests/test_baseline_persistence.py` passes unchanged.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `judge.py` (T01H); the probe's skip decision; the judge's
lower-only rule; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if `read_gate_baseline`'s
"malformed block is absent" tolerance cannot accommodate a fourth key without
changing an existing fixture's reading; name the fixture.
