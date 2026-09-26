---
id: FEAT-2026-0115/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - .specfuse/rules/result-contract.md
  - specfuse/loop/data/rules/result-contract.md
  - plugins/specfuse/skills/authoring-work-units/SKILL.md
  - .specfuse/skills/authoring-work-units/SKILL.md
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
escalation_reason: spinning_detected
re_arm_override: true
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-09-26T17:11:02+00:00
    prior_status: blocked_human
    prior_attempts: 3
    prior_cost_usd: 2.776901
    prior_duration_seconds: 1163.681
    reason: "produces: named the synced copy .specfuse/skills/.../SKILL.md, which criterion 3's sync-scaffold.sh overwrites from plugins/ on every attempt (drafting error). Canonical plugins path added; retained tree from attempt 2 passed verification."
---

# Document `blocked_next:` where the sessions and the authors read

**Objective.** Record the `blocked_next:` RESULT field, the `fix_unit_inserted`
event, the two `defaults` keys and the authoring guidance, canonical and mirror.

**Context.** FEAT-2026-0115/T04. (1) `.specfuse/rules/result-contract.md`: add
`blocked_next:` to the schema fence under `blocked_reason:` with its three keys,
and one paragraph in the Rules section: a block that names a drafted fix unit is
inserted by the driver when the feature runs `auto` and the draft passes the arm
checks; the draft must carry `provenance: agent`, `status: draft` and the five
sections. (2) `docs/methodology.md` §2: the `fix_unit_inserted` event, the
`defaults.fix_unit_insertion` and `defaults.max_fix_units_per_unit` keys, one
line each, plus the example in `.specfuse/verification.yml.example`. (3)
`/authoring-work-units` §5: an escalation trigger of the form "block; the fix is
a new unit" should say the session drafts that unit and names it in
`blocked_next:`, so the block costs no wait. **Edit the canonical file
`plugins/specfuse/skills/authoring-work-units/SKILL.md`**; `.specfuse/skills/`
is a synced copy that `scripts/sync-scaffold.sh` overwrites from `plugins/`
(this is why three attempts lost the edit). Run the sync after editing so
both carry it. Docs mirror: copy `docs/methodology.md` to
`specfuse/loop/data/docs/methodology.md` (the sync script does not cover
`docs/`); `tests/test_scaffold_data_in_sync.py` is the check for both.
Red-test exempt: documentation; the sync test is the oracle.

**Acceptance criteria.**

1. `grep -c "blocked_next" .specfuse/rules/result-contract.md docs/methodology.md plugins/specfuse/skills/authoring-work-units/SKILL.md .specfuse/skills/authoring-work-units/SKILL.md`
   reports at least 1 for each file.
2. `grep -n "fix_unit_insertion\|max_fix_units_per_unit" .specfuse/verification.yml.example docs/methodology.md`
   exits 0.
3. After running `scripts/sync-scaffold.sh`,
   `python3 -m unittest tests.test_scaffold_data_in_sync -v -b` exits 0.
4. `python3 .specfuse/scripts/leak_scan.py --all` exits 0.

**Do not touch.** `specfuse/loop/*.py` (T01–T03); `.specfuse/verification.yml`
(the live file — only the example changes); `.specfuse/rules/never-touch.md` and
`security-boundaries.md`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criteria 3 and 4 above. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if this repo's binding block
(`binding_block_word_count`) would exceed its cap after the result-contract edit —
say by how many words; trim, do not drop the schema line.
