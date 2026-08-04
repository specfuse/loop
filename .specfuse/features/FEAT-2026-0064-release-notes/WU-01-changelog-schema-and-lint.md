---
id: FEAT-2026-0064/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - CHANGELOG.md
  - specfuse/loop/changelog.py
  - tests/test_changelog_schema.py
produces_driver_helper:
  - ENTRY_CLASSES
  - parse_changelog
oracle_env: macos_local
---

# The document, its schema, and a parser that reads it back

**Objective.** Create `CHANGELOG.md` in Keep-a-Changelog shape with an `Unreleased`
section, and ship `specfuse/loop/changelog.py` that parses it — entries classified,
each carrying its FEAT-ID or issue number, released sections distinguishable from
`Unreleased`.

**Context.** Correlation ID `FEAT-2026-0064/T01`. Read `PLAN.md` first — it records
why entries are appended when work lands rather than generated at release, why there
are two collection points, and why no history is backfilled. Do not reopen those.

**The four classes.** `added` / `changed` / `fixed` / **`breaking`**. `breaking` is
its own class rather than a flag on the others, because the question a consumer is
actually asking is *"will this break me"* and that answer must be findable by reading
one heading, not by scanning prose for a warning.

**Every entry traces to its evidence.** A FEAT-ID or an issue number, so an entry is
never the only record of what happened — a reader can always get from the one-line
summary to the retrospective or issue that explains it. An entry without a trace is
a claim with no provenance and the lint rejects it.

**The document starts nearly empty, and that is correct.** Fifty-one features are
`done` and none is represented. `PLAN.md` records why: reconstructing them from commit
subjects produces exactly the low-quality summaries this feature exists to prevent,
and it would read as authoritative. Seed `Unreleased` with the work landing from this
feature onward and nothing else.

**Parse, do not just validate.** T02 appends and T03 stamps; both need to read the
document's structure back. A regex-only validator would leave each of them
reimplementing the parse, and they would drift. One parser, three consumers.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_changelog_schema.py::TestChangelogSchema::test_entry_without_a_trace_is_rejected`
   exists and **fails on HEAD before this WU runs** (`specfuse/loop/changelog.py` does
   not exist, which counts as red).
2. That test asserts an entry carrying neither a `FEAT-YYYY-NNNN` nor an issue number
   is a finding, and one carrying either is accepted. It passes after this WU's edits.
3. A test per entry class asserts `added` / `changed` / `fixed` / `breaking` parse,
   and that an unrecognised class is a finding naming the four legal values.
4. A test asserts `Unreleased` is distinguishable from a released section, and that a
   released section's version and date are both readable.
5. **Malformed input produces findings, not a traceback** — one test each: a truncated
   file, a section with no entries, an entry under no section heading. None may raise.
   A parser that crashes cannot distinguish "found a problem" from "could not look"
   (`LEARNINGS [FEAT-2026-0072/G1-CLOSE]`).
6. A test asserts the shipped `CHANGELOG.md` parses clean and contains an `Unreleased`
   section — the document this feature creates must satisfy its own schema.
7. **No backfill.** A test asserts the shipped document contains no entry for a
   feature that closed before this one, and the file itself says why in a comment a
   reader will meet before the first entry.
8. `specfuse/loop/changelog.py` does not import `loop.py`. Assert with
   `grep -n "^from \|^import \|^from specfuse" specfuse/loop/changelog.py` and quote
   the output.
9. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `close-discipline.md`, `closing_requirements.py`, and
`.specfuse/skills/fix-bug/` — T02 owns both collection points.
`scripts/bump_version.py` — T03 owns the release wiring. Any existing feature's
`RETROSPECTIVE.md`: this WU reads none of them and backfills nothing.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criteria 5 and 7 are the
load-bearing pair — a parser that raises turns a release-time stamp into a crash, and
a backfilled document would ship fifty-one summaries nobody wrote.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
four classes cannot express a change shape §3 already requires closes to enumerate
(say which — that is a real gap, not a naming problem); or the Keep-a-Changelog shape
cannot carry both a driver version and an umbrella version in one release heading,
which `PLAN.md` requires and T03 depends on.
