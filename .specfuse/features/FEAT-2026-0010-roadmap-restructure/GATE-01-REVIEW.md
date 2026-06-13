---
feature: FEAT-2026-0010
gate: 1
correlation_id: FEAT-2026-0010/G1-PLAN
written_by: WU-93-gate-1-plan-next
---

# Gate 1 plan-next review — does Gate 2 stand or close out?

## What Gate 1 delivered

Gate 1 shipped the structural foundation of the roadmap restructure: the
`.specfuse/roadmap-archive.md` file with its conventions section and
literal anchor/back-link strings (T01); the `roadmap-archive` skill with
per-ID and `--auto` batch modes and a self-test (T02); the `roadmap-add`
skill with three-source next-ID scan (T03); and the dogfood migration of
FEAT-2026-0003..0008's detail sections from the main roadmap into the
archive with back-links populated in the Detail column (T04). The main
roadmap shed 223 lines (647 → 424); the archive file holds 6 anchored
sections plus the scaffold header (275 lines). All four substantive WUs
landed; T03 took 2 attempts, the rest landed in 1. Closing sequence
(G1-RETRO, G1-LESSONS, G1-DOCS) all completed in one attempt apiece.

## Verdict: retain Gate 2

`PLAN.md`'s Scope OUT explicitly defers the **driver auto-archive hook**
to a follow-up after Gate 1 lands ("manual-first cut; auto follow-up
after this feature lands"). Gate 1 did not deliver it, and verification
of `.specfuse/scripts/loop.py` confirms no `roadmap-archive` invocation
exists anywhere in the driver. The hook is the only Scope OUT item small
enough to land on this branch (one driver function + a smoke test); the
remaining Scope OUT items (new roadmap columns, scoring framework,
orchestrator aggregation) all belong to FEAT-2026-0011 or later
features. Closing Gate 2 out without delivering the hook would be the
hollow-pass failure mode the escalation trigger names — deferred work
that needs doing, no follow-up proposed.

**Back-link rendering polish** — the second item in Gate 2's
placeholder — is dropped from the proposed substantive WU list. The
Gate 1 retrospective surfaced no concrete rendering issue: the back-link
form `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)` renders correctly
in every Markdown surface the project uses (GitHub web, local viewers,
`grep`-readable). The only behavioural change RETRO noted (Detail
narrative no longer visible inline on a `cat`/scroll of `roadmap.md`)
was anticipated by the design and addressed by G1-DOCS. Padding Gate 2
with a polish WU on no concrete scope inflates the WU count for
symmetry, against `[FEAT-2026-0003/G4-LESSONS]` ("let the work drive
the WU count").

## Proposed Gate 2 substantive WUs

- **T05 — Driver auto-archive hook in `loop.py`.** When the driver
  detects a feature's gates are all `passed` and flips PLAN.md
  `status: complete`, invoke the `roadmap-archive` algorithm against
  the just-completed feature ID before returning. Idempotent — the
  skill already returns `already archived` if the Detail cell already
  carries a back-link, so re-runs and pre-archived features no-op
  cleanly. One new helper in `loop.py`, edit at the existing
  `gate is None` completion branch, plus a unit test exercising the
  helper against a temp-repo fixture with one `done` row.

## Out of scope for Gate 2 (route to separate features)

- **Driver event-emission gap (T02 missed `task_started` /
  `task_completed`).** Surfaced in RETRO §Structural gap 1; root cause
  unidentified from the read-only retro vantage. The fix lives in
  `loop.py`'s event-emission loop and is a driver-correctness concern,
  not a roadmap-structure concern. Recommend a new feature (probably
  FEAT-2026-NNNN scoped to "driver event-emission consistency") — this
  branch's scope is roadmap restructure, and bundling driver-internal
  bookkeeping into Gate 2 would muddy the feature boundary.
- **Attempt-failure evidence not preserved (RETRO §Structural gap 2).**
  Same disposition: route to the same driver-correctness follow-up
  feature. The fix is to append a `task_attempt_failed` event (or
  `reason` field on the attempt payload), and it belongs alongside the
  event-emission gap above.
- **T03 next-ID scan source-list under-specification (RETRO §Structural
  gap 3).** A rules file enumerating authoritative ID sources would
  belong under `.specfuse/rules/` and is touched by FEAT-2026-0011
  (which adds new columns and may add new ID surfaces). Defer to that
  feature's design or, if it doesn't land it, open a small follow-up
  feature.

## Cross-repo contracts

This is a single-repo feature touching the loop driver and the in-tree
`roadmap-archive` skill. The proposed Gate 2 WUs reference no external
system vocabulary. Every value the WUs name is authored in this repo and
its source is the in-tree file. No row requires pre-arm verification
against an external surface.

| Value | Used in | Authoritative source | Status |
|---|---|---|---|
| `<a id="feat-yyyy-nnnn"></a>` (anchor literal) | T05 (via the skill) | `.specfuse/skills/roadmap-archive/SKILL.md` (also `.specfuse/roadmap-archive.md` Conventions section, written by FEAT-2026-0010/T01) | ✓ verified — read at draft time, in-repo |
| `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)` (back-link literal) | T05 (via the skill) | `.specfuse/skills/roadmap-archive/SKILL.md` | ✓ verified — read at draft time, in-repo |
| `status: complete` (PLAN.md frontmatter terminal value) | T05 (hook trigger) | `.specfuse/scripts/loop.py:1005` (`write_frontmatter_field(... "status", "complete")` in the `gate is None` branch) | ✓ verified — read at draft time, in-repo |
| `Detail` (roadmap column header) | T05 (skill reads this column) | `.specfuse/roadmap.md` table header (added by FEAT-2026-0010/T01) | ✓ verified — read at draft time, in-repo |

All in-repo, all read at draft time. None require external verification
before Gate 2 is armed.

## Closing sequence

Gate 2 is the terminal gate of this two-gate feature. Per methodology, a
multi-gate feature uses the four-WU closing sequence
(`retrospective → lessons → docs → plan-next`), not the `close`
alternative. G2-PLAN's terminal role is to write the feature-arc
verdict and flip PLAN.md `status: done`; the existing precedent for the
terminal-gate plan-next (e.g. FEAT-2026-0003/G4-PLAN) covers the shape.

Proposed closing WUs (all drafted, all `status: draft`):

- G2-RETRO (`WU-94-gate-2-retrospective.md`) — Gate 2 RETROSPECTIVE.md
  section covering T05.
- G2-LESSONS (`WU-95-gate-2-lessons.md`) — promote any Gate 2
  generalizable observations to `.specfuse/LEARNINGS.md`.
- G2-DOCS (`WU-96-gate-2-docs.md`) — reconcile any docs that mention
  the auto-archive trigger (skill SKILL.md, methodology doc, README).
- G2-PLAN (`WU-97-gate-2-plan-next.md`) — terminal verdict: write
  feature-arc summary into RETROSPECTIVE.md, flip PLAN.md
  `status: done`.

## Arming note for the operator

Before flipping the four drafts to `pending`:

1. Re-read T05's spec against `.specfuse/scripts/loop.py`'s current
   shape — the line numbers in the spec are advisory; the structural
   claim ("at the `gate is None` completion branch, after the
   `status: complete` flip, before return") is load-bearing. Confirm
   that branch still exists.
2. Confirm the `roadmap-archive` skill still exports the per-ID
   algorithm in a form T05 can call (currently SKILL.md prescribes the
   algorithm but is a markdown skill — T05's WU spec proposes a Python
   helper that re-implements the same algorithm directly, mirroring
   what T04 did, rather than subprocess-invoking the skill). The
   contract note in `[FEAT-2026-0010/G1]` LEARNINGS entry on
   "subprocess vs re-implement" applies.
3. No cross-repo contract row above is unchecked. Arm at will.
