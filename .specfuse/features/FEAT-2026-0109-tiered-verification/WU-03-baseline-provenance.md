---
id: FEAT-2026-0109/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_provenance.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.16.0
started_at: 2026-09-08T12:28:57.455221+00:00
duration_seconds: 667.532
cost_usd: 0.78003
input_tokens: 58
output_tokens: 12252
---

# Record how the baseline was determined, not just what it said

**Objective.** Give the gate's `baseline:` block a provenance field, so a
reader can tell whether the record came from a gate-entry probe, from
attribution after a named unit failed, or from nothing having run.

**Context.** FEAT-2026-0109/T03; read `PLAN.md` and T01. Today
`write_gate_baseline` (`loop.py:4543`) records `sha`, `probed_at`, `entry_sha`
and `failing` — what the answer was, never how it was reached. Before T01 there
was only one way, so the omission cost nothing. After T01 there are three, and
they carry different weight: a gate-entry probe measured the tree before any
agent touched it; an attribution measured it after a specific unit failed and
was reset. An escalation reading `failing: [...]` cannot currently tell which.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file. This
unit adds one field to the record `write_gate_baseline` writes and one
correspondingly widened read in `read_gate_baseline`; neither T01's trigger nor
T02's key changes.

**Shape.** A `source` string distinguishing at least: probed at gate entry;
attributed after `<wu_id>` failed; and skipped. Carry the triggering `wu_id`
where there is one — "attributed after T02 failed" is the fact a reader wants,
and it is free at the call site. Keep it a plain scalar, not a nested block:
`read_gate_baseline` returns a dict other code destructures, and the
`_miniyaml` writer this record uses handles scalars without reflowing the rest
of the frontmatter.

**Why this is worth its own unit.** It is the field that makes lazy attribution
auditable, and it is the precondition for the CI fast path `PLAN.md` scopes out
— without provenance, a future CI-sourced baseline would be indistinguishable
from a locally measured one, and a later escalation could not tell "we measured
this tree" from "we trusted a Linux run".

**Compatibility.** A record written without `source` must keep parsing; treat
absence as unknown rather than failing the read. `read_gate_baseline` currently
returns `None` for malformed records and callers depend on that meaning
"never probed" — do not widen `None` to cover a merely-old record.

**Acceptance criteria.**

- `tests/test_baseline_provenance.py::test_entry_probe_records_its_source` fails on HEAD and passes after: a record written by the gate-entry path carries a `source` naming it.
- `::test_attribution_records_the_triggering_unit`: a record written by T01's attribution path carries a `source` naming attribution and the `wu_id` that triggered it.
- `::test_legacy_record_without_source_still_reads`: a record with no `source` parses, and `read_gate_baseline` does not return `None` for it.
- `::test_source_does_not_disturb_other_frontmatter`: writing the record leaves every other line of the gate file byte-identical, including `feature_oracle` and `cost_budget_usd` — the no-reflow property `write_frontmatter_block` exists to preserve.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** T01's trigger logic; T02's tree key; `verify()` and the
`feature_oracle` path; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if adding the field cannot be
done without changing `read_gate_baseline`'s return contract in a way its
existing callers would notice — `resolve_gate_start_sha` and the judge's diff
base both read that dict, and widening it is an operator decision.
</content>
