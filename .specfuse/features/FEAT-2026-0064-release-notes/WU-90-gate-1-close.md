---
id: FEAT-2026-0064/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0064: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict.

**Context.** Correlation ID `FEAT-2026-0064/G1-CLOSE`. Single terminal gate, so this
WU collapses retrospective, lessons, docs, and verdict into one session. Read
`PLAN.md` and `GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3 obligations is
load-bearing per `close-discipline.md`. Issue #293's case: FEAT-2026-0061 lost all 26
close criteria to an on-plan auto-close, FEAT-2026-0063 lost its roadmap retitle.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**This close is the first entry in the document it built.** T02 makes the close a
collection point, so this close must append its own §3 enumeration to `Unreleased` —
and report whether doing so felt like duplicated work or like putting an existing
artifact somewhere useful. That is the design's central bet and no test can measure
it. If it felt like writing the same thing twice, say so plainly; that is a finding
worth more than a green gate.

**The document will look thin, and that is a scope decision.** Fifty-one features and
every prior bug PR stay undocumented. State it in `## What the loop did NOT verify` so
an early reader does not mistake an almost-empty CHANGELOG for a claim that nothing
has changed. Name the number.

**A release follows immediately.** The operator has stated 0059 → 0064 → release. This
close's own enumeration is therefore not hypothetical: it is the first content a
consumer will read about this version. Enumerate precisely rather than gesturing.

**The `kind:` contract shipped one feature ago and applies here.** If this close
hedges, FEAT-2026-0059's `close-j` requires every follow-up entry to carry a `kind:`
from the four legal values, and `/accept-hedged-close` will compute a ceiling from
them. This is the second close to run under that contract; report whether classifying
was easier than prose, as 0059's own close did, so the sample grows.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root with a literal `## Gate 1` heading
   and a literal `## Cost analysis` section reconciling planned against actual — the
   $16.00 WU sum and $21.00 gate budget against the `attempt_outcome` sum in
   `events.jsonl`, which is authoritative. Both headings are checked after dispatch;
   omitting either costs a full re-attempt.
2. The deferred-verification list is written with, per entry, the criterion, why it
   was not verified in-loop, and where it actually gets checked — or the explicit
   `(nothing — every acceptance criterion was verified in-loop)` line.
3. **This close appends its own §3 enumeration to `CHANGELOG.md`'s `Unreleased`**, and
   reports whether that felt like duplicated work or like relocating an artifact it
   already had to write.
4. `## What the loop did NOT verify` names the un-backfilled history (51 features plus
   every prior bug PR) as a scope decision, and states that entry *prose quality* is a
   human read the lint cannot make.
5. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this
   WU's correlation ID. Two candidates worth assessing, both from this session:
   **(a)** whether "the material for a release note already exists at close time and
   is thrown away" generalizes to other artifacts a close produces and nothing reads;
   **(b)** the stronger one — **patch the instance, ask why, or it ships again.** A
   `pytest`-subprocess defect shipped five times across three features because the
   first instance was patched without asking what authoring shape produced it; the
   guard that would have caught all five (`tests/test_no_pytest_subprocess.py`) was
   written only after the third feature. Promote (b) even though it is not this
   feature's subject — it is the most transferable rule this session produced and
   there is no better home for it.
6. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or
   the explicit `n/a` line is written. Several are known: a new `CHANGELOG.md` every
   project inherits, a new append obligation on both the close ceremony and `fix-bug`,
   a new `closing_requirements` check, and `bump_version.py` gaining a required
   umbrella-version input.
7. The roadmap row and detail section reflect what was actually built, including the
   two-collection-points decision that widened the row.
8. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`. Source files owned
by T01–T03. Any already-`done` feature's records: no backfill, here or anywhere.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 (criterion 8) before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report a lower bound
and name the gap rather than inventing a number); appending this close's own
enumeration is refused by T02's own check, which would mean the collection point is
unsatisfiable by the feature that shipped it; or the §3 enumeration cannot be
expressed in T01's four entry classes, which is a contract gap worth stopping for.
