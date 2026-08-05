---
id: FEAT-2026-0056/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/loop/data/rules/close-discipline.md
  - specfuse/loop/data/templates/GATE.template.md
  - specfuse/loop/data/templates/WU.template.md
generated_surfaces:
  - .specfuse/rules/close-discipline.md
  - .specfuse/templates/GATE.template.md
  - .specfuse/templates/WU.template.md
---

# Document the per-criterion state contract and re-baseline the roadmap claim

**Objective.** Add `close-discipline.md` §5 describing per-criterion state and the
narrow/broad oracle contract, point `GATE.template.md` and `WU.template.md` at it,
and correct FEAT-2026-0056's benefit paragraph in `.specfuse/roadmap.md` to what this
design can actually deliver.

**Context.** This is `FEAT-2026-0056/T04`, the last substantive unit of gate 1. T01,
T02, and T03 built the schema, the driver seeding, and the lint; this unit makes the
contract readable by the humans and agents that have to satisfy it. Read `PLAN.md` in
this folder — § *Scope decision: what invalidates a cached green* is the substance of
the new rule section — and `GATE-01.md`.

**`Red-test exempt: pure-doc/data WU.`** This unit adds no behaviour; every criterion
below is a structural assertion or a synchronization check, per
`/authoring-work-units` §12's carve-out.

**Canonical copy first, then propagate.** The rules and templates under `.specfuse/`
are *vendored*, not authored. The canonical copies live in
`specfuse/loop/data/rules/` and `specfuse/loop/data/templates/`, and
`scripts/sync-scaffold.sh` copies them into `.specfuse/` — its manifest already lists
`rules/close-discipline.md`, `templates/GATE.template.md`, and
`templates/WU.template.md`. Edit the canonical copy and run the sync script; **do not
hand-edit the `.specfuse/` copy**, or the next sync silently reverts your work.

The new `close-discipline.md` section documents three things and nothing more:

- what the per-gate `GATE-NN-CRITERIA.md` artifact is and what an entry carries;
- the `narrow` / `broad` oracle contract — that a `narrow` green may be carried
  forward across close attempts and a `broad` one may never be, with the one-line
  reason (a broad oracle has no knowable scope, so a carried-forward green is an
  unsound coverage claim);
- that `kind` and `state` are written by the close that ran the oracle and never
  inferred by a reader — the same posture §2 already takes on the hedged-record
  `kind:`.

Do not restate the guard's format or the requirement IDs. `close-discipline.md` §4 is
explicit that `closing_requirements.py` is the registry of record and that a second
copy drifts. Point at `specfuse-lint --closing`; let the lint be the check.

**The roadmap re-baseline is not cosmetic.** The row's current `**Benefits.**`
paragraph claims the feature "roughly halves close cost on multi-attempt gates." That
was written against diff-scoped test selection, which `PLAN.md` rejects: this repo's
`tests` gate is `python3 -m unittest discover -s tests -v -b`, a `broad` oracle that
re-runs on every close attempt. What the design saves is the per-criterion agent
reasoning, the regeneration, and the scenario matrix. Rewrite the paragraph to say
that, and say plainly that the suite is excluded and why. Leave the `**Why.**` and
`**Goal.**` paragraphs alone — they are still accurate.

`[FEAT-2026-0031/G1-CLOSE]` is why this is a substantive work unit and not a bullet
in the close: a deliverable that matters independently of reflection quality must
live in a WU that always dispatches, because an auto-closed close WU's acceptance
criteria go unfulfilled with `attempts: 0` and nothing fails.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `specfuse/loop/data/rules/close-discipline.md` gains a section headed
   `## 5. Per-criterion state and the narrow/broad oracle contract`, placed after §4
   and before `## Split with project-local rules`.
2. That section states that a `narrow` oracle's green may be carried forward across
   close attempts and a `broad` oracle's may not, and gives the reason in one
   sentence.
3. That section states that `kind` and `state` are written by the close, never
   inferred by a reader, and names `specfuse-lint --closing` as the check — with no
   requirement ID and no guard function name restated in the prose.
4. `specfuse/loop/data/templates/GATE.template.md`'s `## Definition of done` block
   carries a one-line pointer to the new section.
5. `specfuse/loop/data/templates/WU.template.md`'s `**Close obligations**` block
   carries a one-line pointer to the new section, added to the existing numbered
   list.
6. `bash scripts/sync-scaffold.sh` exits 0, and afterwards
   `diff specfuse/loop/data/rules/close-discipline.md .specfuse/rules/close-discipline.md`
   exits 0. The same `diff` for both templates exits 0.
7. `.specfuse/roadmap.md`'s `## FEAT-2026-0056` detail section has a `**Benefits.**`
   paragraph that no longer contains the phrase `halves close cost`, and that names
   the full test suite as an oracle which re-runs on every attempt.
8. The `**Why.**` and `**Goal.**` paragraphs of that same detail section are
   byte-identical to their state before this WU — verified with
   `git diff .specfuse/roadmap.md` and reported in the RESULT block.
9. No other feature's row or detail section in `.specfuse/roadmap.md` is modified —
   `git diff --stat .specfuse/roadmap.md` shows changes confined to the
   FEAT-2026-0056 section.
10. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0056-per-criterion-dod-state`
    exits 0.

**Do not touch.** `specfuse/loop/criteria_state.py`, the driver dispatch module under
`specfuse/loop/`, `specfuse/loop/closing_requirements.py`, and
`specfuse/loop/lint_closing.py` — T01, T02, and T03 own those, and this unit adds no
code and no driver wiring. The `.specfuse/` copies of the rules
and templates directly (edit the canonical `specfuse/loop/data/` copies and sync).
Any roadmap row or detail section other than FEAT-2026-0056's. Any other feature's
folder under `.specfuse/features/`. `.specfuse/verification.yml`. Generated
directories, secrets, `.git/`. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run criterion 6's
sync-and-diff sequence and criterion 10's `lint_plan.py` invocation verbatim. Note
that `leak-scan` reads prose surfaces including the roadmap — keep real paths,
org names, and `~`-home strings out of the text you add.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`scripts/sync-scaffold.sh` does not carry `rules/close-discipline.md` or either
template in its manifest, so the canonical-to-`.specfuse` propagation cannot be
verified; the roadmap's FEAT-2026-0056 detail section is not in the expected format
and criterion 8's byte-identity check cannot be made (a roadmap edit the linter would
reject is an operator matter); `git diff` shows changes outside the FEAT-2026-0056
section after your edit; or `lint_plan.py` fails on the feature folder for a reason
this WU did not introduce — name the failing rule rather than repairing another
unit's file.
