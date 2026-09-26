---
id: FEAT-2026-0114/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - .specfuse/rules/result-contract.md
  - specfuse/loop/data/rules/result-contract.md
  - .specfuse/skills/authoring-work-units/SKILL.md
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
duration_seconds: 1168.046
cost_usd: 1.630024
input_tokens: 60
output_tokens: 7881
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T15:31:20.693600+00:00
---

# Document `produces_amended:` where the sessions and the authors read

**Objective.** Record the new RESULT key, the `produces_dropped:` unit field and
the `produces_amendable` switch in the surfaces that bind sessions and authors,
canonical and mirror alike.

**Context.** FEAT-2026-0114/T04. Three surfaces, each with a mirror under
`specfuse/loop/data/` that `scripts/sync-scaffold.sh` regenerates and
`tests/test_scaffold_data_in_sync.py` checks at the broad run (the FEAT-2026-0103
lesson: name both, run the sync). (1) `.specfuse/rules/result-contract.md`: add
`produces_amended:` to the schema fence beside `produces_unchanged:` and a
sentence to closing obligation 1 saying when each applies (unchanged = the
deliverable already holds; amended = the plan named a path the solution did
not need) and that an amendment may drop but never add. (2)
`docs/methodology.md` §2: the `produces_dropped:` driver-owned field and the
`defaults.produces_amendable` key, one line each, plus the example in
`.specfuse/verification.yml.example`. (3) `/authoring-work-units` §13: one
paragraph — an author who is unsure a path will change should not declare it;
the runtime amendment exists for the plan being wrong, not for hedged
declarations. Red-test exempt: documentation; the sync test is the oracle.

**Acceptance criteria.**

1. `grep -c "produces_amended" .specfuse/rules/result-contract.md docs/methodology.md .specfuse/skills/authoring-work-units/SKILL.md`
   reports at least 1 for each file.
2. `grep -n "produces_amendable" .specfuse/verification.yml.example docs/methodology.md`
   exits 0.
3. After running `scripts/sync-scaffold.sh`,
   `python3 -m unittest tests.test_scaffold_data_in_sync -v -b` exits 0.
4. `python3 .specfuse/scripts/leak_scan.py --all` exits 0.

**Do not touch.** `specfuse/loop/*.py` (T01–T03); `.specfuse/verification.yml`
(the live file — only the example changes); `.specfuse/rules/never-touch.md`
and `security-boundaries.md`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criteria 3 and 4 above. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if the binding block for
this repo (`binding_block_word_count`) would exceed its cap after the
result-contract edit — say by how many words; the fix is to trim, not to skip
the schema line.
