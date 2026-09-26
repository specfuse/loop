---
id: FEAT-2026-0116/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces_driver_helper:
  - replay_with_failing_sets
produces:
  - specfuse/loop/replay_spin.py
  - tests/test_replay_spin_failing_sets.py
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T18:05:01.444360+00:00
duration_seconds: 183.257
cost_usd: 0.853835
input_tokens: 56
output_tokens: 15440
---

# Replay the new rule over the corpus, and document the field

**Objective.** Let the close measure the change on recorded history — how many
past `spinning_signature_repeat` escalations would not fire under the failing-set
rule — and record the `failing_tests` field where the contract is documented.

**Context.** FEAT-2026-0116/T03. `specfuse/loop/replay_spin.py` already replays
`parse_gate_failure_signature` and `detect_spinning_signature_repeat` over
historical `events.jsonl` files. Add `replay_with_failing_sets(events_paths)`
that re-derives each `attempt_outcome`'s failing set from its `failure_excerpt`
(the full log is gone for old events; say so in the output) and reports, per
feature, the escalations that fired historically and whether the new rule would
fire — a CLI flag `--failing-sets` prints the table. In `docs/methodology.md`
§2's attempt-outcome contract, add `failing_tests` (one line) and the
signature rule for `tests` (one line); regenerate the mirror with
`scripts/sync-scaffold.sh`. Red test first for the replay.

**Acceptance criteria.**

1. `tests/test_replay_spin_failing_sets.py` fails on HEAD before this unit's
   edits (the module is absent); after,
   `python3 -m unittest tests.test_replay_spin_failing_sets -v -b` exits 0.
2. That module asserts, on a synthetic events file with one historical
   `spinning_signature_repeat` whose two excerpts name different tests, that
   the replay reports it as `would_not_fire`, and `would_fire` when they name
   the same test.
3. `grep -c "failing_tests" docs/methodology.md` reports at least 1, and after
   `scripts/sync-scaffold.sh`, `python3 -m unittest tests.test_scaffold_data_in_sync -v -b`
   exits 0.
4. `python3 -m unittest tests.test_replay_spin -v -b` exits 0 with no edit to
   that module.

**Do not touch.** `loop.py` (T01/T02); `.specfuse/rules/`; `.specfuse/verification.yml`;
plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criterion 3. The broad tier is the driver's, once per gate — never run
in-session.

**Escalation triggers.** Stop with `status: blocked` if the excerpt cap (500
bytes) loses the test ids for the corpus's real Maven events so the replay can
say nothing — report the share of events it could classify.
