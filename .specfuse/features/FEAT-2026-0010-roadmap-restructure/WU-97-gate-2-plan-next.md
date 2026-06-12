---
id: FEAT-2026-0010/G2-PLAN
type: plan-next
effort: high
status: draft
attempts: 0
---

# Gate 2 plan-next — terminal verdict

**Objective.** This is the terminal gate of FEAT-2026-0010. Write the
feature-arc verdict, confirm everything in PLAN.md's Scope IN landed,
confirm everything in Scope OUT is either delivered or routed to a
named follow-up feature, and flip `PLAN.md` `status: active → done`
so the close-ceremony chain completes.

**Context.** Correlation ID `FEAT-2026-0010/G2-PLAN`. Read
`RETROSPECTIVE.md` end-to-end (both Gate 1 and Gate 2 sections).
Read `PLAN.md`'s Scope IN and Scope OUT lists. Read `GATE-01-REVIEW.md`
for the disposition this WU's predecessor recorded for each Scope OUT
item. Read the current `.specfuse/roadmap.md` row for FEAT-2026-0010 to
confirm its state matches the verdict (the row stays in the roadmap
with a Detail back-link once T05's auto-archive fires on this
feature's own completion — but that flip happens on the NEXT
`loop.py` run after PLAN.md is `done`, not during this WU).

This WU is the terminal-gate analog of FEAT-2026-0003/G4-PLAN —
follow that precedent for verdict shape if uncertain.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` gains a `## Feature verdict` section (appended
   below the Gate 2 section) that names:
   (a) every Scope IN item from PLAN.md and the WU(s) that delivered
       it,
   (b) every Scope OUT item from PLAN.md and its disposition
       (delivered in this feature / routed to a named follow-up
       feature / consciously dropped),
   (c) the per-gate cost and duration totals,
   (d) a one-paragraph close that says whether the
       `roadmap_goal` from PLAN.md frontmatter is met by what
       shipped.
2. `PLAN.md` frontmatter `status:` is flipped from `active` to `done`.
   No other PLAN.md edit (no graph change, no Scope-list edit, no
   note edit). The driver reads `PLAN.md` status after this WU's
   commit and routes to the terminal close path; mis-flipping breaks
   that handoff.
3. If any Scope OUT item is neither delivered nor routed to a named
   follow-up, this WU emits `status: blocked` rather than papering
   over the gap. Routing means a real follow-up feature is named
   (an existing FEAT-ID, or a clearly-scoped new feature the verdict
   names as the next step) — "we will think about this later" is
   not routing.
4. No new WU files are written for a notional Gate 3. This feature
   is two gates by PLAN.md design; the terminal gate ends here.
   If Gate 2's run surfaced a finding that genuinely needs an
   escalation gate (per `[FEAT-2026-0003/G4-LESSONS]`'s three-test
   bar), name it in the verdict and route to a new feature —
   do NOT extend this feature with a Gate 3.

**Do not touch.** Source code, tests, the `roadmap-archive` skill,
the `roadmap-add` skill, any Gate 1 WU file, this gate's RETRO /
LESSONS / DOCS WU files, any other feature's folder, `.git/`. The
ONLY frontmatter field this WU edits on `PLAN.md` is `status`.

**Verification.** The `plannext` gates in
`.specfuse/verification.yml` (`lint_plan.py` against this feature
folder). The lint must report clean.

**Escalation triggers.**

- If `RETROSPECTIVE.md` lacks either a Gate 1 or Gate 2 section,
  emit `status: blocked` — the verdict cannot be written without
  both halves.
- If any Scope OUT item from PLAN.md cannot be classified as
  delivered / routed / dropped (e.g. the item's text is ambiguous,
  or the necessary follow-up feature does not exist and cannot be
  proposed within this WU's scope), emit `status: blocked` and name
  the ambiguous item.
- If flipping PLAN.md `status: done` would conflict with any other
  artifact in the feature folder (e.g. an `awaiting_review` gate
  file that has not yet been flipped to `passed`), emit
  `status: blocked` — the close-ceremony handoff requires a
  consistent state.
