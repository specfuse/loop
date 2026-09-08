---
id: FEAT-2026-0109/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces_driver_helper: attribute_failure_to_baseline
produces:
  - specfuse/loop/loop.py
  - tests/test_lazy_baseline_e2e.py
---

# Tracer bullet — skip the probe at gate entry, attribute on the first failure

**Objective.** Stop running the `code` set at gate entry, and instead run
`probe_baseline` against the post-reset tree when a unit's verification first
fails — so the attribution the probe exists to provide is computed when it is
needed and not before.

**Context.** FEAT-2026-0109/T01; read `PLAN.md`, including its
existing-mechanism search. **This is the tracer bullet** — the unit that makes
`GATE-01.md`'s `feature_oracle` runnable and green, and the only unit in this
gate permitted to leave stubs.

The surface is already factored for this. `probe_baseline(feature_dir, cfg)`
(`loop.py:4307`) takes no work unit and is already split out of `verify()`;
`gate_baseline_check` (`:4618`) owns the entry-time call and the record write;
`baseline_probe_enabled` (`:4643`) already resolves `--no-baseline-probe` and
the `baseline_probe` key. Add `attribute_failure_to_baseline(...)` beside them
and call it from the attempt-failure path, after the hard reset and **before**
the attempt is counted.

**Why this is safe, and where it is not.** The probe's job is attribution, not
prevention: a pre-existing failure already fails the unit either way. What
changes is who is blamed and whether the attempt is spent. The accepted cost is
one wasted dispatch when the tree really is pre-broken — see `PLAN.md` § Notes.
Do not try to recover that dispatch; bounding attribution to once per gate is
what keeps it to one.

**Ordering matters.** Attribution must read the tree the unit was dispatched
against, which is the post-reset tree, not the tree the failed attempt left
behind. Running it before the reset would measure the agent's own edits and
attribute its failure to itself.

**Acceptance criteria.**

- `tests/test_lazy_baseline_e2e.py::test_green_gate_entry_runs_no_gate_set` fails on HEAD and passes after: entering a gate and dispatching its first unit executes no `code`-set command, proven by an injected runner that records what it was asked to run.
- `::test_first_failure_triggers_attribution`: a unit whose verification fails causes `probe_baseline` to run once against the post-reset tree, and the resulting record names the unit that triggered it.
- `::test_preexisting_failure_does_not_consume_an_attempt`: when attribution finds the tree was already red, the escalation is `preexisting_gate_failure` and the unit's `attempts` is unchanged.
- `::test_genuine_failure_counts_normally`: when attribution finds the tree was green, the unit's attempt is counted and it retries as it does today.
- `::test_attribution_runs_at_most_once_per_gate`: a second failing unit in the same gate, at the same tree, does not re-probe.
- `::test_no_baseline_probe_flag_still_honoured`: `--no-baseline-probe` suppresses attribution too — the flag means "do not run gates on my behalf", and silently re-introducing a probe under it would break the one escape hatch operators already rely on.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** Tree-hash keying (T02) and the provenance field (T03) — this
unit may write the record in whatever shape exists today; `verify()`'s gate
resolution and the `feature_oracle` path (FEAT-2026-0101 owns them); `.git/`,
secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle` once it is green.

**Escalation triggers.** Emit `status: blocked` if the attempt-failure path
cannot call attribution before the attempt is counted without restructuring
`execute_unit_attempt`'s return contract — that is a design change for an
operator, not a judgement call here. Also block if the end-to-end test cannot
observe "no gate set ran" without mocking the runner out entirely; asserting on
a mock would not prove the skip, which is this unit's whole claim.
</content>
