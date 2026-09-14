# FEAT-2026-0111 — follow-ups

One entry per criterion this close measured as failing. Each carries the
criterion verbatim, the evidence, and the re-run condition that would satisfy
it.

### The distilled set's content was accepted by a human

**Tracked as #3315.**

**Criterion (`GATE-01.md` definition of done).** "`.specfuse/rules-local/learnings-distilled.md`
is loaded by the binding block; its content was accepted by a human rather than
generated unattended; and the whole block — distilled file included — is under
2,500 words and stays there because a lint says so."

**Evidence.**

- The file is loaded: `binding_block_word_count()` lists
  `.specfuse/rules-local/learnings-distilled.md` at 57 words (exit 0).
- Its content is T01's tracer-bullet stub. The file's heading reads
  `# Distilled LEARNINGS (stub)` and its body opens "Placeholder for the
  human-accepted, weight-ranked distillate … that FEAT-2026-0111/T02-T03
  produce." An agent session wrote it and no human accepted it.
- Nothing in the tree runs the accept step against the real corpus. A `grep`
  for `apply_distilled_decisions` / `propose_distilled_learnings` over
  `specfuse/`, `scripts/`, `.specfuse/scripts/` and `plugins/` finds only
  their definitions in `loop.py` and one mention in
  `specfuse/loop/data/rules-local/README.md`. Their only callers are in
  `tests/test_distilled_accept_step.py`. No skill or CLI surface calls them.
- The gate's `feature_oracle` (`python3 -m unittest tests.test_binding_block_budget -v -b`)
  is green (5 tests, exit 0), but it asserts that the file is wired and
  counted, not what the file says.

**Re-run condition.** A human runs the accept step on the real
`.specfuse/LEARNINGS.md`. That run is recorded as a `type: human` work unit
with `evidence:`, placed before the close. After it,
`.specfuse/rules-local/learnings-distilled.md` holds the accepted entries in
place of the placeholder, and `python3 -m unittest tests.test_binding_block_allocation tests.test_binding_block_budget -v -b`
exits 0 on that tree.

### The sub-budget fails before the total does

**Tracked as #3316.**

**Criterion (T04).** "The distilled file has its own stated sub-budget, and
exceeding it fails before the total does, so the failure names the right
cause."

**Evidence.** The probe ran `check_binding_block_budget` on a temp copy of the
real binding block: the three trimmed rules (2,404 words) plus a synthetic
distillate of N words.

| Distillate words | Result |
|---|---|
| 96 | PASS, total 2,500 |
| 97 | `binding block is 2501 words, over its 2500-word cap` |
| 200 | `binding block is 2604 words, over its 2500-word cap` |
| 500 | `binding block is 2904 words, over its 2500-word cap` |
| 501 | `.specfuse/rules-local/learnings-distilled.md is 501 words, over its 500-word sub-budget` |

Every distillate from 97 to 500 words fails the **total** cap, not the
sub-budget. The effective room for the distillate is 96 words, not the 500 that
`LEARNINGS_DISTILLED_WORD_CAP`, `docs/methodology.md` and
`.specfuse/rules-local/README.md` all state.
`test_sub_budget_failure_is_named_before_the_total_failure` passes only because
its fixture block has the distillate and nothing else. Measured against the
corpus, `propose_distilled_learnings(word_cap=96)` proposes **0 of 244**
entries and `word_cap=500` proposes 3.

**Re-run condition.** On the real tree, a distillate one word over the
sub-budget produces the sub-budget message, and a distillate at the sub-budget
passes the total cap. So the sub-budget must be ≤ `BINDING_BLOCK_WORD_CAP`
minus the other `@` files' words. That can come from a smaller sub-budget, a
further trim, or an operator decision on the 2,500 cap. The last is not a unit's
call (`GATE-01.md`, "The blocking question").
