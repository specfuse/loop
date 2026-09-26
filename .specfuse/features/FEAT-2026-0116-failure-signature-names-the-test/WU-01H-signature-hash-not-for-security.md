---
id: FEAT-2026-0116/T01H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - specfuse/loop/loop.py
---

# The signature hash tail is not a security hash

**Objective.** Make the `security` gate green again: `signature_from_failing_tests`
hashes the joined ids with `hashlib.sha1` for a stable truncation tail, and bandit
reads that as a weak security hash (B324).

**Context.** FEAT-2026-0116/T01H, hygiene for T01 (gate 1 broad run, 2026-09-26):
`bandit -r specfuse .specfuse/scripts -ll` reports `B324:hashlib Use of weak SHA1
hash for security` at the `hashlib.sha1(` call in `signature_from_failing_tests`
in `specfuse/loop/loop.py`. The hash is a truncation fingerprint, not a
credential; pass `usedforsecurity=False`. Nothing else changes. Red-test exempt:
the `security` gate itself is the oracle (red on HEAD, green after).

**Acceptance criteria.**

1. `bandit -r specfuse .specfuse/scripts -ll` exits 0 (it reports one High B324
   finding on HEAD before this unit's edit).
2. `python3 -m unittest tests.test_failure_signature_names_the_test tests.test_spinning_repeat_same_failing_set -v -b`
   exits 0 with no edit to those modules (the produced signatures are unchanged).

**Do not touch.** Any other line of `signature_from_failing_tests`; `extract_failing_tests`;
`detect_spinning_signature_repeat`; `replay_spin.py`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus criterion 1.
The broad tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` (one-line `blocked_reason`) if
bandit reports a second finding this unit does not own.
