---
feature_id: FEAT-2026-0064
title: Release notes maintained as work lands, tied to versions and tags
slug: release-notes
branch: feat/FEAT-2026-0064-release-notes
roadmap_goal: Maintain a CHANGELOG per project, written incrementally as features and bug fixes land rather than reconstructed at release time, and tie its sections to the version tags they shipped in — so a consumer can answer "what changed, and will it break me" from one document.
autonomy_default: review
status: active
planned_cost_usd: 16.00
---

# Plan: Release notes maintained as work lands

Eight tagged releases, no release-notes document of any kind. A consumer running
`pipx upgrade specfuse` cannot learn what moved, or whether it breaks them.

## The material already exists and is thrown away

`close-discipline.md` §3 *requires* every feature's close to enumerate consumer-visible
contract changes or write an explicit `n/a`. That enumeration is written at the moment
the person who made the change still remembers why — the only moment it is cheap.
Nothing collects it.

The quality difference is measurable, not theoretical. FEAT-2026-0042's close produced
this, with blast radius established by grep rather than reasoned about:

> *"**New entry point: `python3 -m specfuse.monitor.autofix_run`.** Not registered in
> `pyproject.toml`'s `[project.scripts]` and not a `specfuse-monitor` subcommand
> (`grep -n "autofix" specfuse/monitor/cli.py` → no hits). No installed console script
> can reach the firing path. This is the single most consequential line in this
> enumeration: it is why upgrading to this version cannot cause anything to fire."*

A release-time generator walking PR titles would have produced "autofix wiring". That
is precisely how a breaking change gets downgraded into a one-liner.

## Decisions taken at draft time by the agent, on the operator's instruction

**1. Close-appended, not release-time generated.** The row named this as the first
open decision and preferred the former; the evidence above settles it. Entries are
appended when the work lands, by the surface that already wrote the enumeration.

**2. Two collection points, not one — the row's gap.** The row says "the collection
point", singular, and describes only the close ceremony. **Bugs do not have a close
ceremony.** `1 bug = 1 branch = 1 PR`, no feature folder, no §3 enumeration.

This is not hypothetical. Of the nine pull requests merged on 2026-08-03/04, **four
were bugs** — #464, #468, #473, and a `pytest`-subprocess fix carried inside another
feature's branch. A close-only collector would have silently dropped every one,
including #473, which changed operator-facing halt output. The document would have
looked complete and been wrong about half the release.

So: features collect via the close ceremony's §3; bugs collect via `fix-bug`, which
already writes a root-cause and fix description into its PR body by convention.

**3. The umbrella gets its own line in every release heading.** The row's second named
decision. Releasing `specfuse-loop` alone documents half a release: `pipx upgrade
specfuse` resolves through the umbrella package, so a driver version nobody can install
is not a release. This repository cannot bump the umbrella, but it can refuse to
pretend a driver version is the whole story — each release heading carries both, and
the umbrella version is filled at release time.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: find . -iname "CHANGELOG*" -not -path "./.venv/*" -not -path "./.git/*"
         grep -rniE "changelog|release.?note" specfuse/ scripts/ .specfuse/skills/ docs/

Verdict: NOTHING. No changelog file, no release-note machinery, no skill that writes
         one. The only record of what a version changed is the git log.

Reuse:   scripts/bump_version.py already sets all four version sources atomically
         (pyproject.toml, DRIVER_VERSION, .specfuse/VERSION,
         specfuse/loop/data/VERSION) and is the natural release hook — cutting a
         version is exactly when `Unreleased` should be stamped.

         close-discipline.md §3 is the feature-side collection point and already
         produces the material; closing_requirements.py is where a "did you append"
         check would live, alongside FEAT-2026-0059's close-j.

         .specfuse/skills/fix-bug/ is the bug-side collection point; its Step 7
         already prescribes a PR body with Root cause / Fix / Tests sections.
```

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Answered before drafting, because the obvious lint is unsatisfiable on this tree.

A lint requiring a CHANGELOG entry per shipped unit of work is red on arrival.
Fifty-one features are `done` and every one predates this feature; so does every bug
PR ever merged. A check demanding retrospective coverage could not pass without
fabricating fifty-one entries from git archaeology, which is exactly the re-derivation
this feature exists to avoid.

So the check is scoped to **work landing after this ships**: a close (or a bug fix)
that runs under the new contract must append; anything already `done` is out of scope
and explicitly unread. No backfill. Same shape as FEAT-2026-0059's `close-j`, which is
one feature old and has the same reasoning written into it.

The close must say plainly that history was **not** audited, so a reader does not
mistake an empty early CHANGELOG for a claim that nothing changed.

## A lint warning that is expected, recorded so it is not "fixed"

`lint_plan` warns that T01's `produces: CHANGELOG.md` is a bare filename with no such
file at the repo root. That is correct and intentional: the file does not exist yet
because **T01 creates it**, and the bare spelling is the required one — `git diff
--name-only` emits root paths bare, and a `./` prefix makes the in-diff cross-check
fail every attempt (#259, #77). The warning clears the moment T01 runs. Do not add a
`./`, and do not pre-create an empty file to silence it.

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value, threshold, or severity is flipped. A new document
and a new append obligation are added; nothing that passes today begins failing except
work landing after this ships, which is the intended behaviour.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced.

## Scope boundary — explicitly OUT

- **Backfilling history.** Fifty-one features and every prior bug PR stay
  undocumented. Reconstructing them from commit subjects would produce exactly the
  low-quality summaries this feature exists to prevent, and would read as authoritative.
- **Bumping or tagging the umbrella package.** A different repository. This feature
  makes the umbrella version *representable and required* in a release heading; the
  operator supplies it.
- **Automating the release itself.** `bump_version.py` gains a CHANGELOG step; it does
  not gain `git tag`, `git push`, or a PyPI upload.
- **Judging entry prose quality.** The lint checks an entry exists, is classified, and
  carries its FEAT-ID or issue number. Whether the sentence is *good* is a human read,
  and a linter pretending otherwise would invite writing for the linter.

## Two traps that will otherwise be rediscovered mid-attempt

**It ships in the scaffold, so this repo's conventions are not a target project's.**
The tag-name convention (`v*`) and the four-version-source list are specific to this
repository. Both must be configuration a target project can set, or every downstream
project inherits a release process shaped like ours. FEAT-2026-0064's row names this
as its fourth part and it is the part most likely to be skipped, because the feature
works locally without it.

**A released section must become immutable, and that has to be enforced, not asked
for.** The whole value is that a consumer can trust a released section describes that
release. If `Unreleased` can be edited into a shipped section — by a close appending
late, or by a human tidying — the document becomes a moving record of the past.

## Gates

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0064/T01
        file: WU-01-changelog-schema-and-lint.md
        depends_on: []
      - id: FEAT-2026-0064/T02
        file: WU-02-two-collection-points.md
        depends_on: [FEAT-2026-0064/T01]
      - id: FEAT-2026-0064/T03
        file: WU-03-release-wiring-and-portability.md
        depends_on: [FEAT-2026-0064/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0064/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0064/T01
          - FEAT-2026-0064/T02
          - FEAT-2026-0064/T03
```
