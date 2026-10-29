---
id: FEAT-LOOP-2026-0248/T03
type: implementation
status: pending
attempts: 0
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-10-29T15:16:31+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 0.376264
    prior_duration_seconds: 88.399
    reason: "Authoring error, not the unit's work: produces declared tests/test_ids_migrate_all.py, which T03 only has to keep passing (AC2), so produces_not_in_diff refused twice. Path removed from produces."
oracle_env: macos_local
planned_cost_usd: 2.00
produces:
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T15:14:29.643382+00:00
duration_seconds: 88.399
cost_usd: 0.376264
input_tokens: 24
output_tokens: 6469
escalation_reason: deterministic_refusal_repeat
---

# T03 — `--include-prose` takes paths; `--exclude-id` protects shared numbers

**Objective.** An operator can include this repository's own docs, tests and code in the
rename while leaving alone every mention of an ID that another repository also uses.

**Context.** `FEAT-LOOP-2026-0248/T03`. This unit **edits** `ids.py` and the oracle module; `tests/test_ids_migrate_all.py` must keep passing but need not change.

- `--include-prose` with no value keeps today's meaning (all prose). With one or more
  values (paths or shell globs relative to the repository root, matched against
  `git ls-files` paths) it rewrites prose only in matching files; the dry run's `prose`
  lines then cover only the files left out.
- `--exclude-id ID` (repeatable) removes that old ID from every rewrite: no folder move, no
  structural or prose edit, no alias entry; the dry run lists it as skipped with
  "excluded by operator". Validate each value with `ids.FEATURE_ID_RE`.
- The dry run ends with a one-line count of remaining prose mentions per top-level
  directory, so the review is sized before it starts.

Un-skip the oracle's clause-4 class.

**Acceptance criteria.**

1. The clause-4 class: `--include-prose docs` rewrites a mention in `docs/` and not one in
   `tests/`; bare `--include-prose` rewrites both; `--exclude-id` leaves the ID's folder,
   rows and prose untouched and out of the alias map; an invalid `--exclude-id` value exits
   non-zero. Fails before, passes after.
2. `tests/test_ids_migrate_all.py` and `tests/test_ids_migrate.py` pass.

**Do not touch.** Structural classification (T02), validation (T01), rehearsal (T04).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If argparse cannot express "flag with optional list" without
breaking the existing bare-flag form, keep the bare form working and stop to name the
alternative rather than changing it.
