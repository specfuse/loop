---
id: FEAT-2026-0064/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - .specfuse/rules/close-discipline.md
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - .specfuse/skills/fix-bug/SKILL.md
  - specfuse/loop/closing_requirements.py
  - tests/test_changelog_collection.py
oracle_env: macos_local
---

# Two collection points, because bugs have no close ceremony

**Objective.** Make both surfaces that ship work append to `CHANGELOG.md`'s
`Unreleased` section: the close ceremony for features, `fix-bug` for bugs.

**Context.** Correlation ID `FEAT-2026-0064/T02`. Read `PLAN.md` first — it records
why entries are appended when work lands rather than generated at release, and why
there are two collection points rather than the row's one. T01 owns the schema and
the parser; this WU is a producer into it.

**The row says "the collection point", singular, and that is its one gap.** Bugs do
not have a close ceremony: `1 bug = 1 branch = 1 PR`, no feature folder, no §3
enumeration. Of the nine pull requests merged 2026-08-03/04, **four were bugs** —
#464, #468, #473, and a `pytest`-subprocess fix carried inside another feature's
branch. A close-only collector drops every one of them, including #473, which changed
operator-facing halt output. The document would look complete and be wrong about half
the release.

**The feature side is nearly free.** `close-discipline.md` §3 already requires the
close to enumerate every consumer-visible contract change or write the explicit `n/a`.
That enumeration is the entry. The close is not being asked to write something new —
it is being asked to put what it already writes somewhere a consumer will read it. Say
so in the rule text, because a close author who thinks this is new work will write it
twice, badly.

**The bug side needs a home that does not exist yet.** `fix-bug`'s Step 7 already
prescribes a PR body with Root cause / Fix / Tests sections. The changelog entry is
one line derived from the same understanding, appended before the PR is opened.

**An `n/a` close appends nothing, and that is correct.** A feature with no
consumer-visible change writes §3's `n/a` line and adds no entry. The check must not
demand an entry from it — a changelog padded with "no user-facing change" entries is
noise that trains readers to skip it.

**The trap, stated so it is not rediscovered.** A skill has **three surfaces**: the
canonical `plugins/specfuse/skills/fix-bug/SKILL.md`, the vendored `.specfuse/skills/`
copy, and the `.claude/skills/` discovery symlink (already present). The two file
copies must be byte-identical or the scaffold sync guard fails with an error that
reads like an unrelated problem.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `close-discipline.md`.

**Acceptance criteria.**

1. `tests/test_changelog_collection.py::TestChangelogCollection::test_bug_path_is_a_collection_point`
   exists and **fails on HEAD before this WU runs** (`fix-bug` prescribes no changelog
   append, which counts as red).
2. That test asserts `fix-bug`'s SKILL.md instructs a `CHANGELOG.md` `Unreleased`
   append carrying the issue number, before the PR is opened. It passes after this
   WU's edits.
3. A test asserts `close-discipline.md` instructs the close to append its §3
   enumeration to `Unreleased`, each entry classified and carrying the FEAT-ID — and
   states explicitly that this is the *same* material §3 already requires, not a
   second write.
4. A test asserts an `n/a` close — no consumer-visible change — appends **nothing**,
   and that the rule says so. A changelog padded with "no user-facing change" is noise.
5. A `closing_requirements` check fires when a close enumerates contract changes but
   `Unreleased` gained no entry for that FEAT-ID. Scoped to the close under lint —
   it must not read other features, and it must not demand entries for the 51
   features already `done`. A test plants a §3 enumeration with no append and asserts
   the finding; another asserts an `n/a` close produces none.
6. **No backfill, asserted.** A test asserts the check produces no finding for any
   already-`done` feature, holding `PLAN.md`'s satisfiability answer rather than
   restating it.
7. Both `fix-bug` SKILL.md copies are byte-identical (`diff`, quote the empty
   output), and `tests/test_skill_discovery_links.py` plus the scaffold sync tests
   pass. **Run them in-process via `unittest.defaultTestLoader`, never by shelling
   out to `pytest`** — pytest is a dependency of nothing here and
   `tests/test_no_pytest_subprocess.py` will fail the build if you reach for it.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/loop/changelog.py` and `CHANGELOG.md`'s schema — T01 owns
both; if a collection point needs a field the parser does not expose, that is an
escalation. `scripts/bump_version.py` — T03 owns release wiring. Any already-`done`
feature's `RETROSPECTIVE.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criteria 1–2 are load-bearing: a
WU that implements only the close side has built the thing the roadmap row described
and not the thing the release needs, and every other criterion here would still pass.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
bug-side append cannot be prescribed without changing what `fix-bug` decides (it adds
a step, it does not alter triage, the test-first rule, or the 1-bug-1-PR contract);
the close-side check cannot be scoped to the close under lint without reading other
features' folders; or §3's enumeration turns out not to map onto the four entry
classes T01 defined, which would be a real contract gap rather than a formatting
problem.
