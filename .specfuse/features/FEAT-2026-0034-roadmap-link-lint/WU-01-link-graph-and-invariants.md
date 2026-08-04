---
id: FEAT-2026-0034/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - specfuse/loop/lint_roadmap.py
  - tests/test_lint_roadmap.py
produces_driver_helper:
  - lint_roadmap
oracle_env: macos_local
---

# One link graph, four invariants, findings not exceptions

**Objective.** Ship `specfuse/loop/lint_roadmap.py`: load `roadmap.md` and
`roadmap-archive.md` as a single link graph and return findings for the four
invariants the roadmap row specifies, plus the orphan-section WARN.

**Context.** Correlation ID `FEAT-2026-0034/T01`. Read `PLAN.md` first — it records
why this is a sibling module rather than an extension of `lint_plan`, why it ships in
the package, and that the tree is green at authoring time so red tests must use
fixtures. Do not reopen those decisions.

**The trap, stated so it is not rediscovered.** The rot is **bidirectional**, and a
one-file linter misses half of it. A `#feat-…` ref inside `roadmap-archive.md`
resolves against the *archive's* anchors; the same ref written
`roadmap.md#feat-…` resolves against the *roadmap's*. Both files load as one graph and
every ref is checked against the anchor set of the file it actually names. The two
live violations found before drafting were one of each direction, produced by a single
archive run.

**Read `auto_archive_feature` first, and do not import it.** That function in `loop.py`
already parses the `<a id="feat-…"></a>` / `## FEAT-…` pairing this lint asserts on —
and it is the *producer* of shapes 3 and 4. The two must agree on what an
anchor/heading pair is, but a check that shares its subject's parser inherits its bugs.
Read it, then write an independent parser.

**Findings, not exceptions.** Return a list of structured findings with a severity, the
file, the line, and a message naming the mechanical fix. A malformed roadmap must
produce findings rather than a traceback — this runs in a gate, and a linter that
crashes cannot distinguish "found a problem" from "could not look."
`LEARNINGS [FEAT-2026-0072/G1-CLOSE]` is that lesson.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The four invariants

1. **Blocked-by presence and resolution.** Every row at `status: blocked` has a detail
   section carrying a `**Blocked by.**` block with at least one link; each link
   resolves — an ADR path exists on disk or is a well-formed URL, a feature link points
   at a live anchor in either file. Symmetrically **WARN** on a `**Blocked by.**` block
   attached to a non-`blocked` row.
2. **Ref resolution, both directions.** Every `#feat-…` ref in either file resolves
   against the anchor set of the file it names; a bare `#…` resolves same-file. The
   ERROR message names the correct cross-file form, because the mechanical repair is a
   prefix rewrite.
3. **Anchor adjacency.** Every `<a id="feat-YYYY-NNNN">` is immediately followed (blank
   lines allowed) by a `## FEAT-YYYY-NNNN` heading whose ID matches. An anchor followed
   by a different feature's heading, or by another anchor, is an ERROR.
4. **Cross-file ID uniqueness.** No `feat-…` ID is defined in both files, and none
   twice within a file. This is the one that catches the *resolvable-but-wrong* case,
   which is worse than a dead link because nothing visibly breaks.

Plus a **WARN** for a row whose Detail cell is `—` while a detail section for that ID
exists — the reverse of link rot: a live section nothing points at.

**Acceptance criteria.**

1. `tests/test_lint_roadmap.py::TestLintRoadmap::test_bidirectional_ref_rot_is_caught_in_both_directions`
   exists and **fails on HEAD before this WU runs** (`specfuse/loop/lint_roadmap.py`
   does not exist, which counts as red).
2. That test builds a two-file fixture carrying **one violation of each direction** —
   a bare `#feat-X` in the archive whose anchor lives in the roadmap, and a
   `roadmap.md#feat-Y` in the archive whose anchor lives in the archive — and asserts
   both are found. One direction passing while the other is missed must fail this test.
3. One test per invariant 1, 3, and 4, each asserting the finding's severity and that
   its message names the mechanical fix.
4. A test asserts invariant 4 catches an ID defined in **both** files, and a separate
   test asserts it catches one defined **twice within** one file.
5. A test asserts the orphan-section WARN fires on a `—` Detail cell whose section
   exists, and does **not** fire when the cell carries a link.
6. A test asserts a `**Blocked by.**` block on a non-`blocked` row is a WARN, not an
   ERROR — the asymmetry is deliberate.
7. **Malformed input produces findings, not a traceback.** One test each: a truncated
   file, an anchor with no heading anywhere after it, and a row whose status cell is
   missing. None may raise.
8. `specfuse/loop/lint_roadmap.py` does not import `loop.py`. Assert with
   `grep -n "^from \|^import \|^from specfuse" specfuse/loop/lint_roadmap.py` and quote
   the output.
9. **Run against the real tree and record the findings.** As of authoring the tree is
   clean on all four invariants (30 anchors in `roadmap.md`, 39 in the archive). If the
   run finds anything, report exactly what — a non-empty result is new data, not a
   failure of this WU.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/loop.py` — `auto_archive_feature` is read as
reference, never edited; fixing the archiver is explicitly out of scope per `PLAN.md`.
`specfuse/loop/lint_plan.py` — this is a sibling, not an extension.
`.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md` — this WU writes a checker,
not a repair; the tree is already clean. `.specfuse/verification.yml` — T02 owns it.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Criterion 2 is the load-bearing one — a
linter that catches one ref direction and not the other looks correct on this tree
today and misses half the rot on the next archive run.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
invariant cannot be checked without importing `auto_archive_feature`'s parser (say
which — that is a real coupling problem, not a wording one); the real-tree run finds
violations that cannot be explained as new rot since authoring, since `PLAN.md` records
the tree as clean and a discrepancy means one of the two readings is wrong; or
invariant 1 cannot distinguish an unresolvable ADR path from an ADR that exists but is
unapproved — the latter is deliberately **not** checked and must not be conflated.
