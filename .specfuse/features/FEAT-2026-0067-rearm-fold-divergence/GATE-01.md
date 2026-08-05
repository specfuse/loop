---
number: 1
status: passed
cost_budget_usd: 20.00
baseline:
  sha: 4ebc96cb69635b54b299e5eaf1488d492336756c
  probed_at: 2026-08-05T10:03:34.959288+00:00
  failing: []
---

# Gate 1 — one fold path, contract and code agreeing

**Definition of done.** A re-arm folds the prior cycle's spend into
`cumulative_*` every time, driven by an explicit marker rather than by
inferring "already folded" from a zero. Every re-armed work unit in this
repository carries one shape, and the frontmatter contract says which.

**Why one gate.** Three substantive work units, under the ceremony
proportionality threshold of 4 (`docs/methodology.md` §6).

**If you check only three things at review:**

1. `detect_rearm_dispatch` no longer reads `cost_usd` to decide whether a fold
   is owed. A re-arm whose prior cycle genuinely cost $0.00 must still fold.
2. The fold is idempotent. Running it twice for one re-arm must not
   double-count — that is the failure the old value-guard accidentally
   prevented, and the explicit marker must prevent it deliberately.
3. The two fold-never-ran work units are handled explicitly, with the decision
   and reason written down. Silently outliving them is the one outcome the
   roadmap row rules out.

## Arming discipline

Checks owed before any work unit in this gate is armed.

**Runtime probe — required before arming T01.** T01 changes when a fold fires,
which is a behaviour flip, not a mechanical edit. `planning-discipline.md` §4:
apply the change locally and run the exact command the `tests` gate will run —
the full suite, not a subset — and paste the failure list here before accepting.
An un-probed arm of a default/behaviour flip is what let FEAT-2026-0049's WU
spin three times for ~$14.

**No new flags.** None of T01–T03 introduces a runtime flag or dial, so
§3's flag-scope table does not apply. Recorded here rather than omitted, so a
reviewer can tell the difference between "considered, not applicable" and
"forgotten".

**Predicate check.** Every escalation trigger in T01–T03 is satisfiable from
inside the repository — see `PLAN.md` § *Escalation-predicate satisfiability*.
Confirm that still holds at arm time; a trigger that became unsatisfiable
between drafting and arming is a halt, not a warning.

**The one thing most likely to be armed carelessly.** T01's idempotence
criterion (5) looks like a formality and is not: removing the `cost_usd > 0`
guard removes the accidental double-fold protection it provided. Do not arm T01
without confirming criterion 5 names all four accumulators, not cost alone.

### Runtime probe result (recorded at arm time)

`detect_rearm_dispatch` on HEAD, against fixture work units:

```
re-armed, prior cycle cost $2.50 -> fold owed? True    (correct)
re-armed, prior cycle cost $0.00 -> fold owed? False   <-- SPEND LOST
never re-armed                   -> fold owed? False   (correct)
```

The middle row is the defect, reproduced rather than argued. T01's criterion 1
names exactly this case, so its red test is known-red before dispatch — not
merely predicted to be.
