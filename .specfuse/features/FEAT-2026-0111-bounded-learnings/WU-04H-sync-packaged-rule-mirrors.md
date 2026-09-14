---
id: FEAT-2026-0111/T04H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - specfuse/loop/data/rules/result-contract.md
  - specfuse/loop/data/rules/never-touch.md
  - specfuse/loop/data/rules/security-boundaries.md
---

# Sync the packaged rule mirrors, and record that two are core-owned

**Objective.** Bring `specfuse/loop/data/rules/` back byte-identical to the
three canonical `.specfuse/rules/` files T04 trimmed, and record in the commit
why two of them are not this repository's to trim.

**Context.** FEAT-2026-0111/T04H — a hygiene unit
(`/authoring-work-units` §7), inserted after gate 1 halted at T05's entry with
`preexisting_gate_failure`. T04 trimmed all three binding rules to fit the
2,500-word cap and did not run the package-sync, so
`tests/test_result_block_audience.py::test_packaged_copy_is_byte_identical`
fails and the `coverage` gate reports `no_gate_marker` behind it. `data/` is a
byte-for-byte copy of the canonical `.specfuse/` sources
(`scripts/sync-scaffold.sh` stage 3) and this unit is that copy, nothing more.

**The part that is not routine, and must reach the commit message.** Two of
the three trimmed files are **core-owned**: `never-touch.md` and
`security-boundaries.md` are vendored FROM `specfuse/methodology/` by stage 1
of the same script, alongside `correlation-ids.md` and
`verification-discipline.md`. Only `result-contract.md` is loop-local. T04
took 33 words from the loop-local file and **137 from the two core-owned
ones**.

Core is not a sibling of this checkout, so stage 1 is skipped and nothing has
collided yet. When someone next syncs with core present, the #581 baseline
guard classifies those two as "the loop edited a core-owned file" and **halts
for a human** rather than clobbering — which is the safe outcome, and the
reason keeping these trims is defensible. It is not silent, and this unit's
job is to make sure the person who meets that halt finds the reason rather
than a mystery.

**Acceptance criteria.**

- All three files under `specfuse/loop/data/rules/` are byte-identical to
  their `.specfuse/rules/` counterparts, verified with `cmp` per file rather
  than by trusting the sync script's exit code.
- `python3 -m unittest tests.test_result_block_audience tests.test_scaffold_data_in_sync -v -b` passes.
- The full suite is green — `python3 -m unittest discover -s tests -b` — since
  the halt named two gates and the second is expected to clear once the first
  does; if `coverage` still fails afterwards it is a separate finding, not
  this one.
- **The commit message names the two core-owned files, the 137 words taken
  from them, and that a future core sync will halt on them by design.** A
  future reader meeting the #581 guard must be able to find this from
  `git log` alone.

**Do not touch.** The content of any `.specfuse/rules/*.md` file — T04's trim
stands and re-litigating it is not this unit's job. `.specfuse/rules-local/`
and the binding block's `@` lines. The word-count lint and its threshold.
Anything under `.specfuse/features/` other than this unit's own frontmatter.

**Verification.** Narrow tier for `implementation`, plus the full suite above
and a per-file `cmp` of the three pairs. This unit changes only vendored
copies, so a green suite is the whole oracle.

**Escalation triggers.** Stop with `status: blocked` if the mirrors cannot be
made identical by copying — that would mean `data/` carries an edit of its own
that the copy would destroy, which is a different defect and needs a human to
decide which side is right. Stop also if the full suite stays red after the
sync, since the halt's second failing gate would then be independent of this
fix rather than a knock-on.
