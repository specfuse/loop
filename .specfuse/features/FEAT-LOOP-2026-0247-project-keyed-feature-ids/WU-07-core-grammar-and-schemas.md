---
id: FEAT-LOOP-2026-0247/T07
type: human
status: done
attempts: 0
evidence: "Core PR specfuse/specfuse#232 (https://github.com/specfuse/specfuse/pull/232) merged as 073bcda: optional KEY- after FEAT- in methodology/rules/correlation-ids.md (shapes, combined regex, next-ID rule) and in schemas/event.schema.json, events/spec_validated, events/spec_issue_resolved, events/spec_issue_routed; INIT- unchanged. Core CI green after adding KNOWN_DIVERGENCES / KNOWN_SCAFFOLD_DIVERGENCES waivers (loop and orchestrator copies; each names what clears it) and keyed cases in TestCorrelationIdWideningIsAdditive. Vendored with scripts/sync-scaffold.sh (commit c1e3c3a; re-sync against merged core main reports no change). Oracle clause-7 class un-skipped and passing; it reads the vendored schema files directly because tests.test_validate_event sets SPECFUSE_SCHEMA_ROOT to a fixture process-wide. tests.test_validate_event, test_scaffold_data_in_sync, the oracle, test_ids and test_ids_call_sites: 100 tests OK in one process. Executed by the operator's Claude session at the operator's instruction."
planned_cost_usd: 0.50
---

# T07 — widen the core-owned grammar and event schemas, then vendor them

**Objective.** You land the keyed form in the methodology core, which owns the
correlation-ID grammar and the event schemas, and vendor it into this repo, so a keyed
feature's events validate.

**Context.** `FEAT-LOOP-2026-0247/T07`. `scripts/sync-scaffold.sh` lists these as
`CORE_FILES`, vendored from `../specfuse/methodology` into `.specfuse/`; the script
stops when the loop edits one. The loop cannot make this change itself, so it is a
human unit, placed after every loop-side unit (`close-discipline.md` §2): the driver
halts here and dispatches nothing.

Files, in the methodology core:

- `rules/correlation-ids.md`: the component-local shapes (lines ~23-27) and the combined
  regex (~69) accept an optional `KEY-` after `FEAT-`, `KEY` = `[A-Z][A-Z0-9]{1,5}`;
  one paragraph on the optional key and grandfathering.
- `schemas/event.schema.json:27` (`correlation_id`),
  `schemas/events/spec_validated.schema.json:20`,
  `schemas/events/spec_issue_resolved.schema.json:18`,
  `schemas/events/spec_issue_routed.schema.json:18`: the same widening of the `FEAT`
  branch. `INIT-` unchanged.

The pattern text must equal `specfuse.loop.ids.FEATURE_ID_PATTERN` (T01).

**Acceptance criteria.**

1. A methodology-core PR with the changes above is merged (record its URL in
   `evidence`).
2. `bash scripts/sync-scaffold.sh` vendors them into `.specfuse/` and
   `specfuse/loop/data/` in this repo, and the result is committed on this feature's
   branch.
3. The oracle's clause-7 class is un-skipped and passes: a keyed correlation ID
   validates through `specfuse.loop.validate_event`, and a malformed key is rejected.
4. `python3 -m unittest tests.test_validate_event tests.test_scaffold_data_in_sync -b`
   passes (its line-62 pattern imports from `ids` or matches the widened text).

**Do not touch.** `INIT-` grammar. Anything in this repo outside the vendored files, the
oracle's clause-7 class and `tests/test_validate_event.py`.

**Verification.** AC3 and AC4 commands. Then `/unblock-wu` is not needed: record
`evidence`, set `status: done`, and re-run the driver.

**Escalation triggers.** If core review rejects the widening, record the reason here and
re-scope: the close then records clause 7 as `not_met` with the core PR as its
follow-up.
