---
id: FEAT-2026-0117/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - .specfuse/rules/close-discipline.md
  - specfuse/loop/data/rules/close-discipline.md
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
---

# Document the carry-forward rule where closes and authors read it

**Objective.** Record the invalidation rule, the two new entry fields, the
Measurements line and the switch in `close-discipline.md` §5 and the
methodology, canonical and mirror.

**Context.** FEAT-2026-0117/T04. (1) `.specfuse/rules/close-discipline.md` §5:
add that a carried `narrow` green is invalidated when the gate diff since its
`proved_at_sha` touches a path in its `covers:` (driver-seeded; a criterion with
no derivable `covers:` is never carried), that carried entries carry
`carried_from_attempt`, and that a re-close's `## Measurements` states
`carried forward: N criteria, re-measured: M`. Keep §1's sentence that broad
oracles and the `feature_oracle` re-run on every attempt. (2)
`docs/methodology.md` §2: the `covers:`, `carried_from_attempt` and
`invalidated_by` entry fields and `defaults.carry_forward_narrow_greens`, one
line each, plus the example in `.specfuse/verification.yml.example`. Mirrors
regenerate through `scripts/sync-scaffold.sh`; `tests/test_scaffold_data_in_sync.py`
is the check. Red-test exempt: documentation; the sync test is the oracle.

**Acceptance criteria.**

1. `grep -c "carried_from_attempt" .specfuse/rules/close-discipline.md docs/methodology.md`
   reports at least 1 for each file.
2. `grep -n "carry_forward_narrow_greens" .specfuse/verification.yml.example docs/methodology.md`
   exits 0.
3. After running `scripts/sync-scaffold.sh`,
   `python3 -m unittest tests.test_scaffold_data_in_sync -v -b` exits 0.
4. `python3 .specfuse/scripts/leak_scan.py --all` exits 0.

**Do not touch.** `specfuse/loop/*.py` (T01–T03); `.specfuse/verification.yml`
(the live file — only the example changes); `.specfuse/rules/never-touch.md`,
`result-contract.md` and `security-boundaries.md`; plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criteria 3 and 4 above. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if §5's existing wording
contradicts the invalidation rule in a way a one-paragraph addition cannot
reconcile — quote the sentence.
