---
feature_id: FEAT-2026-0034
title: Roadmap link-integrity lint
slug: roadmap-link-lint
branch: feat/FEAT-2026-0034-roadmap-link-lint
roadmap_goal: Read roadmap.md and roadmap-archive.md as one link graph and check four invariants — blocked-by presence and resolution, ref resolution in both directions, anchor adjacency, and cross-file ID uniqueness — so the four rot shapes fail a gate instead of a human clicking a dead link.
autonomy_default: review
status: done
planned_cost_usd: 12.50
---

# Plan: Roadmap link-integrity lint

`lint_plan` validates feature directories, PLAN frontmatter, and the gate/WU graph.
Nothing validates the roadmap's own prose. So `blocked` can display without naming
what it waits on, and a `#feat-…` ref can rot silently — or worse, resolve cleanly to
the *wrong* feature.

## Decisions taken at draft time by the agent, on the operator's standing instruction

The operator was away and authorized proceeding on recommendations. Each choice below
is recorded so it can be audited rather than inferred from the output.

**A sibling linter, not an extension of `lint_plan.py`.** The roadmap row left this
open ("extend `lint_plan.py` or a sibling roadmap linter"). `lint_plan` takes a
`feature_dir` argument and answers questions about one feature; the roadmap is
repo-scoped and belongs to no feature. Folding a repo-scoped check into a
feature-scoped entry point would mean either running it once per feature (N identical
findings) or bolting a second mode onto a tool with one job. The precedent is two
features deep: `event_type_gate.py` and `arm_sweep_gate.py` are both sibling gate
scripts over repo-scoped corpora.

**The module ships in the package.** Every Specfuse project has a
`.specfuse/roadmap.md` and every one of them archives features, so every one of them
grows this rot. Repo-internal hygiene would be the wrong shelf — this is
`arm_sweep.py`'s situation, not `leak_scan.py`'s.

**The archiver is not fixed here.** Shapes 3 and 4 are `auto_archive_feature`
misfiring on every run. The roadmap row is explicit that the lint failing on the next
archive run *is* the durable fix, and that repairing instances by hand is not. This
feature makes the corruption visible and loud; whoever fixes the archiver does it with
a failing check in hand.

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Answered before drafting rather than discovered during it.

The gate this feature ships must be green on this tree, so the four invariants were
checked by hand first. Two violations existed, both created hours earlier by
FEAT-2026-0041's archive run, and both rotting in *opposite* directions from that one
run:

```
roadmap-archive.md:53   [FEAT-2026-0074](#feat-2026-0074)        -> anchor is in roadmap.md
roadmap-archive.md:235  [FEAT-2026-0041](roadmap.md#feat-...)    -> anchor moved INTO the archive
```

They are repaired in a separate commit ahead of this feature, so its acceptance
criterion "the new lint exits 0 on this tree" is satisfiable on arrival rather than
unsatisfiable — the shape that cost FEAT-2026-0060 two blocked attempts and $4.48.
Red tests therefore use fixtures, not live rot.

The state the gate inherits: 30 anchors in `roadmap.md`, 39 in the archive, zero
cross-file duplicates, zero within-file duplicates, every anchor adjacent to its
matching heading, all four `blocked` rows carrying a `**Blocked by.**` block, and all
four ref directions resolving.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: ls .specfuse/scripts/ | grep -iE "roadmap|link"
         grep -rln "roadmap" specfuse/loop/*.py

Verdict: NO roadmap linter exists. The modules that mention the roadmap
         (loop.py, scaffold.py, adopt_feature.py, lint_plan.py) read or write rows;
         none validates the link graph.

Reuse:   auto_archive_feature (loop.py) already parses the `<a id="feat-…"></a>` /
         `## FEAT-…` pairing this lint asserts on — it is the producer of shapes 3
         and 4. The lint must not import it (a check that shares its subject's parser
         inherits its bugs) but should be read first so the two agree on what an
         anchor/heading pair is.

Precedent: event_type_gate.py (FEAT-2026-0060/T02) and arm_sweep_gate.py
         (FEAT-2026-0063/T02) are the sibling-gate-script shape this follows —
         repo-scoped sweep, exit 0/1, wired into verification.yml, scoping reason in
         the docstring.
```

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value, threshold, or severity is flipped; this feature adds
a new check that did not previously exist. Nothing that currently passes begins
failing except by the new gate's own findings, and the tree is green at authoring
time.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced.

## Scope boundary — explicitly OUT

- **Fixing `auto_archive_feature`.** Reasoned above. The lint is the durable fix; the
  archiver repair is someone's next bug.
- **Repairing rot instances.** Done ahead of this feature, in its own commit, so the
  feature ships a check rather than a cleanup.
- **Validating roadmap prose beyond the link graph.** No row-ordering check, no
  status-vocabulary check, no detail-section content rules. Four invariants plus the
  orphan-section WARN, exactly as the roadmap row scoped them.
- **ADR link resolution beyond existence.** A `**Blocked by.**` ADR link is checked
  for a file that exists on disk or a well-formed URL. Whether that ADR is *approved*
  is not machine-readable today and is not inferred.

## The trap that will otherwise be rediscovered

**The rot is bidirectional and a one-file linter misses half of it.** A ref inside
`roadmap-archive.md` written as a bare `#feat-…` resolves against the *archive's*
anchors; the same ref written as `roadmap.md#feat-…` resolves against the roadmap's.
Both files must be loaded as one graph, and each ref checked against the anchor set of
the file it actually names. The two live violations found before drafting were one of
each direction, from a single archive run.

## Gates

```yaml
# Single terminal gate: 2 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0034/T01
        file: WU-01-link-graph-and-invariants.md
        depends_on: []
      - id: FEAT-2026-0034/T02
        file: WU-02-gate-and-wiring.md
        depends_on: [FEAT-2026-0034/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0034/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0034/T01
          - FEAT-2026-0034/T02
```
