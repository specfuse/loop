---
id: FEAT-2026-0058/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
produces:
  - .specfuse/templates/DECISIONS.template.md
  - specfuse/loop/data/templates/DECISIONS.template.md
  - .specfuse/features/FEAT-2026-0058-decision-registry/DECISIONS.md
  - tests/test_decisions_format.py
duration_seconds: 1720.732
cost_usd: 4.954247
input_tokens: 7676
output_tokens: 38875
---

# Define the DECISIONS.md format and fill it for this feature

**Objective.** A documented `DECISIONS.md` format — one entry per decision, with
a bounded status and override provenance — plus this feature's own decisions
written into it.

**Context.** FEAT-2026-0058/T01, gate 1. The incumbent surface is a
`## Decisions taken at draft time` prose section, present in 6 of this
repository's 66 PLAN files. This unit replaces it with a registry that other
artifacts cite.

Each entry carries: a decision **ID** unique within the feature (`D1`, `D2`, …),
the **statement**, an **owner**, a **status** from a closed set, and a
**provenance link** to where the decision was taken. `status` is bounded rather
than prose because `[FEAT-2026-0059/G1-CLOSE/classify-beats-prose]` measured the
difference: a bounded token from the party with the context turns every
downstream reader's question from "read carefully and infer" into a one-line
function over the set.

Overrides carry provenance, per `PLAN.md` D3 and
`[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]`: a decision that reaches `ratified`
from `overridden-pending-signoff` records `overridden_from`, `signed_off_by`,
and `signed_off_at`, so it never becomes byte-identical to one that was never
overridden.

**This feature's own `DECISIONS.md` is written here**, carrying `PLAN.md`'s
D1–D4. The format's first real consumer is the feature that defines it — the
cheapest available dogfood, and it stops this PLAN being the seventh copy of the
pattern being retired.

**Acceptance criteria.**

1. `tests/test_decisions_format.py::TestDecisionsFormat::test_status_is_a_closed_set`
   fails on HEAD before this unit runs (no format module or template exists) and
   passes after: a `status` outside the documented set is rejected, asserted
   against the set read from the format's own definition rather than a retyped
   literal.
2. A parser reads a `DECISIONS.md` into entries carrying id, statement, owner,
   status, and provenance link; a malformed entry is a reported error, not a
   silently dropped row.
3. A decision whose status is `overridden-pending-signoff` **or** which was ever
   overridden carries `overridden_from`, `signed_off_by`, `signed_off_at`. A
   test asserts an entry that reached `ratified` from an override is
   distinguishable, by a query over parsed fields, from one ratified from the
   start — the exact distinguishability `[FEAT-2026-0070]` records as lost when
   provenance is not carried.
4. `.specfuse/templates/DECISIONS.template.md` exists and is byte-identical to
   its packaged copy under `specfuse/loop/data/templates/`, asserted by the
   existing scaffold-sync guard rather than a new one.
5. This feature's `DECISIONS.md` contains D1–D4 from `PLAN.md`, each with an
   owner and a provenance link, and parses clean under the parser from criterion
   2.
6. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
   exits 0.

**Registering the new scaffold template.** `.specfuse/templates/DECISIONS.template.md`
is a *seeded* scaffold file, and this repository tracks its seed set in nine
hard-coded registries. A new template that is not added to all of them reddens
the tree, and the failures arrive one registry at a time — three prior attempts
each rediscovered one and were discarded before reaching the next. The list,
derived from `templates/GATE.template.md`, a fully-registered template:

| File | Site |
|---|---|
| `tests/test_init_integration.py` | two sets — `:34` and `:120` |
| `tests/test_upgrade_integration.py` | `:41` |
| `tests/test_scaffold_upgrade.py` | `:21` — a dict, key *and* value |
| `tests/test_scaffold_resources.py` | `:22` — `_EXPECTED_RELPATHS` |
| `tests/test_scaffold_init.py` | two sites — `:16` set, `:58` dict |
| `tests/test_scaffold_data_in_sync.py` | `:27` — the `specfuse/loop/data/` sync manifest |
| `scripts/sync-scaffold.sh` | `:241` — the sync script's own file list |

Line numbers are where `GATE.template.md` sits today and will drift; grep
`templates/GATE.template.md` across the repo for the current set and match it
entry for entry. **Do not** copy `LEARNINGS-pending.template.md` as the model —
it appears in only four of the nine and is not a seeded template.

If a tenth registry surfaces, that is worth reporting in the close notes: nine
hand-maintained copies of one list is the defect shape this feature exists to
remove, applied to scaffold files rather than decisions.

**Registering the new module.** Criterion 2's parser lands as a new file under
`specfuse/loop/`, and every module there must be classified in exactly one of
`arm_eval.JUDGE_MODULES` or `arm_eval.NON_JUDGE_MODULES` — `test_judge_path_registry`
fails an unclassified one. A `DECISIONS.md` parser is not on the arm/close/merge
judge path, so it belongs in `NON_JUDGE_MODULES` with a one-line note saying why,
matching the entries already there.

**Do not touch.** `specfuse/loop/lint_plan.py` — T02 and T03 own the lint.
`specfuse/loop/closing_requirements.py` — the close ceremony's contract-change
enumeration is out of scope by D4. Any other feature's folder.

**Verification.** `./scripts/smoke-test.sh` — the full gate set, run
unsandboxed; a sandboxed run hits unrelated network restrictions during pip
build-dependency resolution, not this change.

**Escalation triggers.** If the format cannot express a decision this repository
has actually taken — try D1–D4 here and FEAT-2026-0050's D1–D3 — stop and report
`status: blocked` naming the decision that does not fit. A format that cannot
hold real decisions would force restatement, which is the failure this feature
exists to remove.
