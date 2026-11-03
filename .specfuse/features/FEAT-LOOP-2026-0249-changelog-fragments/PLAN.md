---
feature_id: FEAT-LOOP-2026-0249
title: "Changelog fragments: stop concurrent PRs conflicting on CHANGELOG.md"
slug: changelog-fragments
branch: feat/FEAT-LOOP-2026-0249-changelog-fragments
roadmap_goal: Two open PRs that each add a changelog entry no longer conflict when one merges, in any project that opts in, and every entry still reaches the released section.
autonomy_default: auto
status: done
planned_cost_usd: 20.50
---

# Plan: Changelog fragments

Every writer of `CHANGELOG.md` appends at one insertion point (`## [Unreleased]`), so any
two open PRs conflict as soon as one merges, and a conflicted PR gets no CI run. On this
repository 62 of the 75 commits on `main` since 2026-10-01 touch the file. `merge=union`
makes local rebases clean, but GitHub's merge button ignores merge drivers. Rebasing at PR
time (FEAT-LOOP-2026-0200) helps only the agent at that moment. Issue #3563 asks for
fragments here because an adopter cannot move locally: the writers and the guards live in
this repository.

## Decisions (2026-11-02)

The operator said "take your recommendations" after the first interview question and then
accepted this list. Each item is a recommendation applied on that instruction.

1. **Opt-in lives in `.specfuse/layout.yml`:** `changelog.mode: single | fragments`, absent
   means `single`. Not the existence of `changelog.d/`: collation empties that directory
   every release, so it is a poor place to store a setting.
2. **Reads accept both forms in every mode; only writes follow the mode.** A stray fragment
   in a `single` project is still read and collated, never lost.
3. **New module `specfuse/loop/changelog_fragments.py`**, CLI subcommands `add`, `collate`,
   `check`. `changelog.py` stays pure text-to-text; #3451's "collate inside `stamp_release`"
   does not fit that function, so collation runs first and `stamp_release` is unchanged.
4. **One writer.** `add` routes by mode and calls `append_entry` in `single`. Skill and rule
   prose say "run this command" with no branching. Today `append_entry` has no production
   caller: agents hand-edit.
5. **Fragment shape:** `changelog.d/<normalized-trace>-<slug>.md`, `class` and `trace` in
   frontmatter, one-line summary as body. The slug allows several entries per FEAT, which
   `close-discipline.md` §3 needs. Frontmatter is the source of truth, not the filename.
6. **Collation is all-or-nothing.** Everything is validated before any write or delete. A
   parser finding on the result refuses the release, only when fragments were consumed, so
   a `single` project's release is unchanged.
7. **PR-time validation** is `check`, wired as a gate in this repository's
   `.specfuse/verification.yml`; adopters get a docs line to add the same gate.
8. **One gate**, seven substantive units, under the 12-unit threshold
   (`docs/methodology.md` §6). **Autonomy `auto`**: a fresh judge session writes the
   terminal verdict. `loop.py`, `closing_requirements.py`, `lint_closing.py` and shipped
   rules are judge surfaces, so the terminal judge-editing stop fires before the close.
9. **This repository opts in as the last unit**, so this feature's own close passes on a
   fragment-only entry.

**Out of scope:** `.specfuse/roadmap.md` and `.specfuse/LEARNINGS.md` conflicts on close PRs
(issue #3563's first done-when narrows to changelog conflicts); FEAT-LOOP-2026-0201's release
backstop, which can build on the shared reader later; moving existing `Unreleased` entries
into fragments; any adopter removing its local override.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -rIn --exclude-dir=.git --exclude=CHANGELOG.md -iE 'changelog\.d|changelog fragment' .`
  and `git grep -nE 'append_entry|stamp_release|parse_changelog\(|released_section_drift' -- 'specfuse/*.py' 'scripts/*' '.github/*' 'plugins/*'`
- **Verdict:** no fragment mechanism exists, building new. Found and reusing `parse_changelog`
  and `append_entry` for shape and collation, `changelog_has_entry_for` for trace matching
  (FEAT-ID or sub-WU), and `layout.py` for the setting.
- **If reusing:** `changelog.py`'s `append_entry`: "Append one entry under `Unreleased`'s
  `entry_class` subheading." The three `CHANGELOG.md` readers are `close-k`
  (`loop.py:10547`), `lint_closing.py:281` and `_unreleased_has_entry_for` (`loop.py:9374`).

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

No existing check changes severity. The new `check` gate and collation's refusal are blocking:

- **What does the rule report on an input already in its intended final state?** Zero. An
  absent or empty `changelog.d/` and well-formed fragments report nothing, and collation
  runs its parser check only when it consumed fragments.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0249/T01
        file: WU-01-writer-and-oracle.md
        depends_on: []
      - id: FEAT-LOOP-2026-0249/T02
        file: WU-02-one-reader.md
        depends_on: [FEAT-LOOP-2026-0249/T01]
      - id: FEAT-LOOP-2026-0249/T03
        file: WU-03-collate-at-release.md
        depends_on: [FEAT-LOOP-2026-0249/T02]
      - id: FEAT-LOOP-2026-0249/T04
        file: WU-04-check-gate.md
        depends_on: [FEAT-LOOP-2026-0249/T03]
      - id: FEAT-LOOP-2026-0249/T05
        file: WU-05-ids-migrate.md
        depends_on: [FEAT-LOOP-2026-0249/T04]
      - id: FEAT-LOOP-2026-0249/T06
        file: WU-06-prose.md
        depends_on: [FEAT-LOOP-2026-0249/T05]
      - id: FEAT-LOOP-2026-0249/T07
        file: WU-07-this-repo-opts-in.md
        depends_on: [FEAT-LOOP-2026-0249/T06]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0249/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0249/T01, FEAT-LOOP-2026-0249/T02, FEAT-LOOP-2026-0249/T03, FEAT-LOOP-2026-0249/T04, FEAT-LOOP-2026-0249/T05, FEAT-LOOP-2026-0249/T06, FEAT-LOOP-2026-0249/T07]
```

## Post-merge checklist

- Open two real PRs that each add a fragment and merge one. Confirm GitHub does not mark the
  other as conflicting. The oracle uses real `git merge`, not GitHub's merge button.
- Decide FEAT-LOOP-2026-0200's optional append-only re-apply: fragments make it unnecessary
  for the changelog.

## Notes

- LEARNINGS `[FEAT-LOOP-2026-0058/G1-CLOSE]`: the close's Do not touch must permit the
  surfaces its obligations write; G1-CLOSE names `changelog.d/`.
- LEARNINGS `[FEAT-LOOP-2026-0023/G1-CLOSE]`: seam bugs need the real boundary, so the oracle
  drives real git merges and the real guards.
- Fixture names use placeholders; keep real org names and paths out of fragments and tests.
