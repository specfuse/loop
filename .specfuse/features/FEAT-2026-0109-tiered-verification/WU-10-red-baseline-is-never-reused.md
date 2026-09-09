---
id: FEAT-2026-0109/T10
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_red_baseline_never_reused.py
---

# A red baseline record is never reused; only a green one is a cache

**Objective.** Stop a recorded failure outliving its fix. A `failing`-non-empty
baseline record must always re-probe rather than be reused, so no cached red
verdict can survive the change that fixes it.

**Context.** FEAT-2026-0109/T10; read the commit message of `8bc2c82` and
`GATE-03.md`. This unit exists because gate 3 **livelocked** on its own
mechanism, and the operator chose to fix it here rather than defer it.

**What happened, in events.** T09's attempt failed on its own lint error.
Attribution ran, matched a cached red record, and attributed T09's failure to
that pre-existing entry — leaving `attempts` at 0. T09 could never consume an
attempt, never surface its own defect, and never progress; every restart
repeated it. `53f4996` fixed the recorded failure and
`tests.test_lint_closing_criteria` went green, but the next attribution emitted
**no `baseline_attribution` event at all**: it reused the 11:54:54 record and
re-escalated a failure that no longer existed. Only hand-clearing the block
(`8bc2c82`) broke the loop.

**Root cause.** `_current_tree_hash` (T02) builds its key from `git ls-tree
HEAD` with the `.specfuse` entry dropped. That exclusion is *correct for its
stated purpose* — bookkeeping commits write to `.specfuse/` on every gate entry,
and keying on the raw root tree would invalidate the record on exactly the
commits T02 exists to survive. Do not undo it. But the `code` gate set **reads**
`.specfuse/`: the corpus lint walks real feature folders, as do the
roadmap-link, arm-sweep and event-type gates. So a failure inside `.specfuse/`
can be recorded and no `.specfuse/`-side fix can invalidate the record holding
it. T07's "at most once per tree state per gate" bound then makes it sticky.

**The fix, and why this one rather than widening the key.** Reuse only a
**green** record. A green record is a real cache: nothing to re-check, and
T02's whole benefit — surviving bookkeeping commits — is preserved intact. A
red record is the one case where re-checking is the point, because the operator
is presumably fixing it; reusing it can only ever be redundant or wrong. This
removes the entire livelock class regardless of which paths the gates read,
without trying to enumerate them — an enumeration that would be wrong again the
next time a gate learns to read something new.

**Incremental edit to `specfuse/loop/loop.py`.** T02 delivered the key and the
reuse comparison; T07 corrected its wording. This unit adds one condition to the
reuse decision — a record whose `failing` is non-empty is not reusable — and
changes nothing about how the key is computed, when attribution fires, or the
once-per-tree-state bound for green records.

**Acceptance criteria.**

- `tests/test_red_baseline_never_reused.py::test_a_red_record_is_re_probed_even_at_the_same_tree` fails on HEAD and passes after: with a persisted record carrying a non-empty `failing` and an unchanged tree key, the next attribution runs `probe_baseline` again rather than reusing the record.
- `::test_a_green_record_is_still_reused_at_the_same_tree`: T02's caching is intact — a `failing: []` record at an unchanged tree key does not re-probe. This is the boundary that keeps the fix from degrading into "always re-probe".
- `::test_a_green_record_still_survives_a_bookkeeping_commit`: a commit touching only `.specfuse/` leaves a green record reusable — T02's original purpose, asserted directly so this unit cannot quietly undo it.
- `::test_a_fixed_red_record_clears_without_hand_editing`: record red, fix the underlying failure with a `.specfuse/`-only change, attribute again, and assert the new record is green — the exact sequence that livelocked gate 3 and required `8bc2c82` by hand.
- `python3 -m unittest tests.test_lazy_baseline_e2e tests.test_baseline_tree_hash_key tests.test_baseline_provenance -q` reports `OK` — gate 1's mechanisms are undisturbed.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** `_current_tree_hash`'s `.specfuse/` exclusion (correct, and
undoing it reintroduces the invalidation T02 exists to prevent); when
attribution fires (T01); T07's bound for green records; T09's surfaces;
`.git/`, secrets.

**Verification.** The narrow tier for `implementation`, plus this gate's
`feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if reuse-only-when-green turns
out insufficient — if a red record can still outlive its fix by some path this
unit does not cover, that is a deeper design question about what the key must
contain, and widening it is an operator decision rather than a judgement to make
mid-unit. Also block if any gate-1 test must change its expectations to
accommodate this; those are the guarantees this unit must not disturb.
</content>
