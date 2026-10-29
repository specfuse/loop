---
feature_id: FEAT-2026-0247
title: Project-keyed feature IDs (FEAT-<KEY>-YYYY-NNNN)
slug: project-keyed-feature-ids
branch: feat/FEAT-2026-0247-project-keyed-feature-ids
roadmap_goal: A repo that sets an optional project key allocates feature IDs of the form FEAT-<KEY>-YYYY-NNNN that every loop surface accepts, while repos without a key, and every existing ID, behave exactly as today
autonomy_default: auto
status: active
planned_cost_usd: 26.50
---

# Plan: Project-keyed feature IDs (FEAT-<KEY>-YYYY-NNNN)

Each repo numbers its own features, so in a project with several repos the same
`FEAT-YYYY-NNNN` exists in more than one of them (FEAT-2026-0069 to 0071 already exist
in two repos as unrelated features). Branch names, commit messages, `events.jsonl` and
cross-repo references carry the bare ID, which does not say which repo it belongs to.

This feature adds an optional per-repo project key, `FEAT-<KEY>-YYYY-NNNN`, set once in
`.specfuse/layout.yml`. Numbering stays per repo with no central allocator. Existing IDs
stay valid permanently and are never renamed.

Drafting found three things the roadmap entry did not state:

- **No Python allocates IDs.** `/roadmap-add` and `/draft-feature` compute the next ID
  in skill prose. A keyed sequence is invisible to that prose, so allocation moves into
  a deterministic `ids next` command the skills call.
- **`gate_eval.py:461` parses the ordinal by position** (`name.split("-")[2]`). On a
  keyed folder that is the year, so a partial-ID lookup silently matches nothing.
- **The correlation-ID grammar and the event schemas are owned by the methodology
  core** (`scripts/sync-scaffold.sh` `CORE_FILES`), not by this repo. The loop vendors
  them and `sync-scaffold.sh` stops when the loop edits one. Widening them is a core
  change, carried here as the human unit T07, ordered last.

## Decisions (interview, 2026-10-29)

The operator accepted the proposal from the 2026-10-29 session ("y") and said "take your
recommendations for the rest"; every item below is a *recommendation* the operator
confirmed in that single accept.

1. **Shape.** `FEAT-<KEY>-YYYY-NNNN`, `KEY` matching `[A-Z][A-Z0-9]{1,5}`. The anchor is
   the lower-cased ID (`feat-acme-2026-0001`), folders and branches follow it. The
   ordinal continues from the repo's highest across both forms, so a legacy and a keyed
   ID in one repo never share an ordinal.
2. **Config home: `ids.key` in `.specfuse/layout.yml`.** It reuses FEAT-2026-0224's
   loader, validator and `layout get` CLI. No file or no key means today's behaviour.
   The roadmap's `project:` frontmatter was considered; nothing reads it.
3. **No operator prompt.** `specfuse upgrade` and `init.sh` never prompt, so the
   earlier "upgrade asks for the key" idea is dropped; setting the key is documented.
4. **Grandfathered.** Legacy IDs stay valid forever; no done or active feature is
   renamed (its history in commits, PRs, issues and `events.jsonl` cannot be rewritten).
5. **Lint.** With a key set, `lint_roadmap` WARNs on a `planned` row without it.
6. **Conversion.** `python -m specfuse.loop.ids migrate --planned-only` re-keys planned
   rows that have no folder (row, heading, anchor, refs). Dry-run by default; `--apply`
   writes.
7. **One gate.** Six loop-dispatched substantive units plus one human unit, under the
   12-unit threshold in `docs/methodology.md` §6.
8. **Autonomy `auto`.** T01–T02 edit judge surfaces (`lint_plan.py`, `loop.py`), so the
   terminal judge-editing stop (FEAT-2026-0246) fires at the close; the operator clears
   it with `judge_edit_acknowledged`.
9. **Core-owned grammar as a human unit (T07)**, placed last so every loop-side unit
   runs first. The operator opens the methodology-core PR and vendors it with
   `scripts/sync-scaffold.sh`.

10. **Full rename added mid-gate (2026-10-29, *operator*).** After T07 the operator
    asked for a helper that renames every existing feature in a repository, accepting
    that git history stays on the old IDs, and said "add T08". T08 adds
    `ids migrate --all` (reviewed dry run; own IDs only; released CHANGELOG sections,
    a running driver and a dirty tree refused; ambiguous prose mentions listed and
    rewritten only with `--include-prose`; writes `.specfuse/id-aliases.yml`). T09
    makes the `--feature`, `gate_eval` and `gh_features` lookups resolve old IDs
    through that map. This supersedes decision 4's "never renamed" for operators who
    opt in; nothing renames by default.

## Scope boundary

Out: `INIT-` initiative IDs (each orchestrator has its own range; they can take the same
optional key later). Enforcing key uniqueness across repos (no registry exists; the key
is the operator's choice). Setting this repository's own `ids.key` (an operator decision
after merge). Renaming any existing ID.

## Known limits

- **Uniqueness is by convention.** Two repos can pick the same key; nothing detects it.
- **Sort order is lexical** at the name-sort sites (`loop.py:1207-1311`, `arm_sweep`,
  `upgrade_merge_gate`): `FEAT-ACME-…` sorts after every `FEAT-2026-…`. Keyed IDs are
  always newer than a repo's legacy ones, so "newest" stays correct; T01's sort key is
  available where order matters.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rnE 'FEAT-\\d\{4\}|FEAT-\[0-9\]|FEAT-YYYY' specfuse/loop/*.py`,
  `grep -rnE 'max|next|allocate' specfuse/` (for an allocator),
  `grep -ln 'layout.yml' specfuse/loop/*.py`, and a sub-agent inventory of positional
  parsing and schema patterns.
- **Verdict:** `no existing ID module or allocator, building new; found layout.yml's loader and validator, extending`
- **If reusing:** `specfuse.loop.layout` (`load`, `validate`, `get`; "Contract: no file
  (or no `decisions:` block) means today's behaviour") is extended with an `ids` block.
  The twelve duplicated `FEAT-\d{4}-\d{4}` patterns are replaced by one import, not
  re-validated.

## Escalation-predicate satisfiability (§2)

T04 adds a WARN, not an ERROR. **What does it report on an input already in its intended
final state?** With no key configured: nothing, in every repo. With a key configured and
every `planned` row keyed: nothing; legacy `done`/`active`/`abandoned` rows are exempt by
design. Zero on correct input, so the rule is satisfiable.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0247/T01
        file: WU-01-ids-module-walking-skeleton.md
        depends_on: []
      - id: FEAT-2026-0247/T02
        file: WU-02-every-code-site-uses-ids.md
        depends_on: [FEAT-2026-0247/T01]
      - id: FEAT-2026-0247/T03
        file: WU-03-skills-allocate-via-ids-next.md
        depends_on: [FEAT-2026-0247/T01]
      - id: FEAT-2026-0247/T04
        file: WU-04-unkeyed-planned-row-warning.md
        depends_on: [FEAT-2026-0247/T01]
      - id: FEAT-2026-0247/T05
        file: WU-05-migrate-planned-only.md
        depends_on: [FEAT-2026-0247/T04]
      - id: FEAT-2026-0247/T06
        file: WU-06-docs.md
        depends_on: [FEAT-2026-0247/T03]
      - id: FEAT-2026-0247/T07
        file: WU-07-core-grammar-and-schemas.md
        depends_on: [FEAT-2026-0247/T02, FEAT-2026-0247/T05, FEAT-2026-0247/T06]
      - id: FEAT-2026-0247/T08
        file: WU-08-migrate-all.md
        depends_on: [FEAT-2026-0247/T05]
      - id: FEAT-2026-0247/T09
        file: WU-09-aliases-resolve-old-ids.md
        depends_on: [FEAT-2026-0247/T08]
      - id: FEAT-2026-0247/T10
        file: WU-10-broad-run-fixes.md
        depends_on: [FEAT-2026-0247/T09]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-2026-0247/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0247/T01, FEAT-2026-0247/T02, FEAT-2026-0247/T03, FEAT-2026-0247/T04, FEAT-2026-0247/T05, FEAT-2026-0247/T06, FEAT-2026-0247/T07, FEAT-2026-0247/T08, FEAT-2026-0247/T09, FEAT-2026-0247/T10]
```

## Post-merge checklist

- Decide this repository's own key (for example `LOOP`) and set `ids.key` in
  `.specfuse/layout.yml`; the next `/roadmap-add` then allocates a keyed ID.
- In each other repo of a multi-repo project, pick a distinct key and set it the same way.

## Notes

- LEARNINGS `[FEAT-2026-0101/G1-CLOSE]` and `[FEAT-2026-0054/G1-CLOSE]`: a parser that
  derives scope from an ID must be tested against real artifacts from this repository,
  not only fixtures written to match it. T01 and T02 test the parser against every
  folder name under `.specfuse/features/` and every roadmap row.
- LEARNINGS `[FEAT-2026-0015/G1]`: units touching three or more files with
  documentation coupling are `medium`, not `low`.
