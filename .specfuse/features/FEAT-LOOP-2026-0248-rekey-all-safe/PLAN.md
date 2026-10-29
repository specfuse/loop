---
feature_id: FEAT-LOOP-2026-0248
title: Make ids migrate --all safe on a real repository
slug: rekey-all-safe
branch: feat/FEAT-LOOP-2026-0248-rekey-all-safe
roadmap_goal: After ids migrate --all --apply, a repository is valid — configuration and lookups resolve old IDs, only real structural paths are rewritten, prose inclusion is scoped, the tree is validated after apply, and this repository's own full suite passes a rehearsal of the rename
autonomy_default: auto
status: active
planned_cost_usd: 21.00
---

# Plan: Make ids migrate --all safe on a real repository

FEAT-2026-0247 shipped `python3 -m specfuse.loop.ids migrate --all`. A rehearsal on this
repository (2026-10-29, key `LOOP`, throwaway worktree, nothing applied to the real tree)
re-keyed 109 features, moved 93 folders and edited 1222 files, then left 44 of 4925 tests
failing (21 failures, 23 errors). Grouped:

1. **Configuration and code keyed by an old ID do not follow.** `.specfuse/agent-policy.yml`'s
   queue names `FEAT-2026-0082`, and `agent_policy` validation errors with "has no row in
   roadmap.md" because it never consults `.specfuse/id-aliases.yml`.
   `lint_plan.DONE_FEATURE_GATE_EXCLUSIONS` is keyed by old folder names, so two done
   features lose their exemption and fail `lint_plan`.
2. **Fixture-only paths are rewritten as structural.** `ids.py`'s rule treats any text after
   `features/` as structural (`ids.py:361`), so `tests/test_deliverable_presence_gate.py`'s
   expected `.specfuse/features/FEAT-2026-0028-green-path` was re-keyed while the fixture
   that creates the folder was not. The real folder is `FEAT-2026-0028-umbrella-cli-wiring`.
3. **`--include-prose` is all-or-nothing.** 7760 mentions were flagged (4719 in feature
   folders, 1388 in tests, 635 in code, 411 in LEARNINGS). An operator cannot include this
   repository's own docs without also rewriting any mention of another repository's feature.
4. **Nothing validates the tree after `--apply`.** The breakage above surfaced only when
   the suite ran.
5. **This repository's tests read real feature folders by their old paths** (real-corpus
   tests, live dogfood checks, sentinel strings).

This is the first feature allocated with this repository's `ids.key: LOOP` (set on this
branch), so it also dogfoods a keyed feature through the driver end to end.

## Decisions (2026-10-29)

The operator said "fix the gaps first and try again after"; following the earlier "take
your recommendations" posture for this work, every item below is a *recommendation*
applied on that instruction and surfaced in the session report.

1. **Fix in the tool, not by hand-editing this repository.** Every gap is closed in
   `ids.py` or the lookups, so any consumer repository gets the same safety.
2. **Old-ID lookups go through `ids.resolve`**, the one-hop alias resolver T09 of
   FEAT-2026-0247 added; no second alias reader.
3. **Structural means a real folder.** Inside code, config and tests, a
   `features/<ID>-<slug>` path or a bare `<ID>-<slug>` string is rewritten only when that
   exact folder exists in the repository. Everything else stays prose.
4. **Prose scoping:** `--include-prose` with no argument keeps today's meaning (all prose);
   with paths or globs it includes only those. `--exclude-id` (repeatable) leaves every
   mention of an ID alone, for IDs this repository shares with another one.
5. **`--apply` validates.** It ends by running `lint_plan` over every feature,
   `lint_roadmap`, and agent-policy validation, and exits non-zero on any error, naming
   them. It does not roll back: the tree is under git, and the report says to
   `git checkout -- .` to undo.
6. **`--rehearse`** applies the same options to a throwaway worktree of `HEAD`, runs the
   repository's `tests` gate command from `.specfuse/verification.yml` there (or
   `--rehearse-command`), reports the result and the failing tests, and removes the
   worktree. The real tree is never touched. This is how an operator, and this feature's
   last unit, proves a rename before applying it.
7. **One gate**, five substantive units, under the 12-unit threshold
   (`docs/methodology.md` §6). **Autonomy `auto`**; `agent_policy.py` and `ids.py` are
   judge surfaces, so the terminal judge-editing stop fires before the close.
8. **Applying the rename to this repository's `main` is out of scope** — a separate
   operator decision after this merges.

9. **Re-plan after T05 blocked (2026-10-29).** Two operator rehearsals showed (a) the
   prescribed prose scope rewrote fixtures and illustrative example IDs in `tests/`,
   `specfuse/`, `docs/` and `plugins/` (78 and 32 failures, vendored core files changed),
   and (b) `_validate_tree` validated a rehearsal with the real checkout's modules. T06 runs
   validation in a fresh process on the target tree; T05's prose scope is narrowed to this
   repository's own history (feature folders, roadmap, archive, LEARNINGS) and it no longer
   declares a fixed `produces:` list.

## Scope boundary

Out: applying `--all` to `main`; detecting automatically which prose mention cites another
repository (the operator names those IDs with `--exclude-id`); rewriting git history,
GitHub titles or other repositories; #3551 (judge-path staleness in the pinned build).

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -nE '_STRUCTURAL|structural|def resolve|_dirty|loop.lock' specfuse/loop/ids.py`,
  `grep -rnlE 'FEAT-2026-[0-9]{4}-[a-z]' specfuse/loop/*.py .specfuse/*.yml`,
  `grep -nE 'DONE_FEATURE_GATE_EXCLUSIONS' specfuse/loop/lint_plan.py`.
- **Verdict:** `found ids.resolve, ids.migrate's rewrite and refusal paths, and lint_plan/lint_roadmap/agent_policy validators; extending all, building only --rehearse`
- **If reusing:** `ids.resolve` ("the ID itself when it has a folder, else its
  `.specfuse/id-aliases.yml` target"); `lint_plan`, `lint_roadmap` and
  `agent_policy.validate_agent_policy` as the post-apply checks rather than new ones.

## Escalation-predicate satisfiability (§2)

The post-apply check turns existing lint ERRORs into a non-zero exit. **On a tree already
in its intended final state** (renamed and valid) it reports zero errors: it runs the same
validators the repository's own gates run, which pass on `main` today.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0248/T01
        file: WU-01-policy-resolves-and-apply-validates.md
        depends_on: []
      - id: FEAT-LOOP-2026-0248/T02
        file: WU-02-structural-means-a-real-folder.md
        depends_on: [FEAT-LOOP-2026-0248/T01]
      - id: FEAT-LOOP-2026-0248/T03
        file: WU-03-scoped-prose.md
        depends_on: [FEAT-LOOP-2026-0248/T02]
      - id: FEAT-LOOP-2026-0248/T04
        file: WU-04-rehearse.md
        depends_on: [FEAT-LOOP-2026-0248/T03]
      - id: FEAT-LOOP-2026-0248/T06
        file: WU-06-validate-in-fresh-process.md
        depends_on: [FEAT-LOOP-2026-0248/T04]
      - id: FEAT-LOOP-2026-0248/T05
        file: WU-05-this-repo-survives-rehearsal.md
        depends_on: [FEAT-LOOP-2026-0248/T06]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0248/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0248/T01, FEAT-LOOP-2026-0248/T02, FEAT-LOOP-2026-0248/T03, FEAT-LOOP-2026-0248/T04, FEAT-LOOP-2026-0248/T05, FEAT-LOOP-2026-0248/T06]
```

## Post-merge checklist

- Run `python3 -m specfuse.loop.ids migrate --all --include-prose <paths> --rehearse`
  on `main`, review the report, then decide whether to `--apply` it.

## Notes

- LEARNINGS `[FEAT-2026-0247/G1-CLOSE]` (pending promotion): a unit adding a public helper
  must give it a non-test caller and keep the module classified; T04's `--rehearse` helper
  is called from the CLI.
- LEARNINGS `[FEAT-2026-0101/G1-CLOSE]`: guards scoped by parsing must be tested against
  this repository's real artifacts — T05 is exactly that, at full scale.
