# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead. A
closing WU's own post-pass check refuses to pass if its diff touches
`.specfuse/LEARNINGS.md` while this feature is in `auto` mode.

**How a human promotes an entry from here.** At PR review for this feature:
read each entry, judge whether it generalizes into a rule that should change
how a future work unit is written or executed, and copy accepted entries into
`.specfuse/LEARNINGS.md` below its append marker. Leave rejected or narrowed
entries here with a short note on why.

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0115/G1-CLOSE] **A RESULT block's `status: blocked` written as a
  YAML block-scalar can be misread as `complete`, turning a legitimate,
  in-scope block into a false `spinning_signature_repeat` escalation after
  only two identical, correct blocks.** T02 reported `status: blocked` twice
  in a row, both times for the same real reason — its original scope forbade
  the edits its own design needed — and both attempts errored identically on
  test collection (`ERROR: test_fix_unit_insertion_refused`). The driver's
  escalation classifier read two identical failures as a spin and stopped
  after attempt 2 rather than the unit's full budget. T02's own
  `re_arm_history` names the actual cause: the driver's RESULT parser read the
  block-scalar value as `complete` (open defect `#3436`), not as `blocked` —
  the "spin" was a parsing defect in the escalation path, not a genuine
  two-strikes-same-shape failure in the unit. The override that re-armed T02
  correctly named the parse defect rather than accepting the spin
  classification at face value, but nothing caught this before real spend was
  lost (`$1.259` across the two misclassified attempts) and #3436 is still
  open. Authoring/ops rule: when a `spinning_signature_repeat` or
  `spinning_detected` escalation's failure signature is a test **collection**
  error (`unittest.loader._FailedTest`, an `ERROR` rather than a `FAIL`) on a
  unit whose own RESULT reported `status: blocked`, check the raw RESULT text
  for a block-scalar `blocked_reason:` or `status:` value before trusting the
  spin classification — the failure signature the classifier compares may be
  downstream of a RESULT-parsing defect, not the unit's actual work. Fixing
  `#3436` itself is out of scope for this close.

- [FEAT-2026-0115/G1-CLOSE] **Recurrence, not a new lesson: `[FEAT-2026-0110/G1]`'s
  canonical-vs-synced-copy trap fired again, at real cost, inside the same
  repository that already promoted the rule.** T04's `produces:` named
  `.specfuse/skills/authoring-work-units/SKILL.md` — the copy
  `scripts/sync-scaffold.sh` overwrites from the canonical
  `plugins/specfuse/skills/authoring-work-units/SKILL.md` — while T04's own
  criterion 3 required running that same sync script. Two attempts
  (`files_changed_mismatch`, then `produces_not_in_diff`) and `$2.777` were
  spent before the drafting error was named and the canonical path added to
  `produces:`, after which the very next attempt passed. `[FEAT-2026-0110/G1]`
  already states the general rule in this repo's own `LEARNINGS.md`, including
  the exact "editing the derived copy would have been silently reverted by the
  next sync" phrasing and naming `plugins/` as canonical for skills. This
  entry is not a restatement — it is evidence that the promoted lesson has not
  yet changed how a WU's `produces:` list gets drafted when the WU's own
  criteria include a sync step. Candidate for `/learnings-curate`'s attention:
  either the authoring skill needs a drafting-time check ("does this WU's own
  criteria run a sync/mirror script that touches a path in `produces:`?"), or
  the existing lesson's phrasing isn't surfacing at the point a WU is drafted.
