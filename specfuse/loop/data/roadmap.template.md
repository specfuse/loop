---
project: <repo / project name>
---

# Roadmap

The master plan for this repository. Each feature lives in its own folder under
`.specfuse/features/` with a `PLAN.md` (task graph), `GATE-NN.md` files, and
`WU-*.md` files. This roadmap owns *feature* definitions and *feature* status; the
PLAN owns the *graph*; GATE files own *gate* status; WU files own *work-unit* status.
One fact, one home — the same split the Specfuse Orchestrator uses, so this folds in
unchanged.

Detail a feature's first-gate work units when you are ready to start it; the gate
after that is drafted for you by the prior gate's plan-next. Until you start a
feature, a one-line entry here is enough.

Add your first feature with **`/roadmap-add`** (it auto-picks the next
`FEAT-YYYY-NNNN` ID and writes the row + detail section), or add a row by hand in
the canonical column order below.

| Feature ID     | Title | Status | Folder | Detail |
|----------------|-------|--------|--------|--------|

Status: `planned` → `active` → `done` (or `abandoned`). `deferred` = parked
by choice pending an external decision/dependency; resumable (a human flips it
back to `active` when the blocker clears), distinct from `abandoned` (dead).
`blocked` = cannot proceed because a *named* dependency is unmet — an ADR
awaiting approval, or an upstream feature that must complete first. Resumable
like `deferred`, but where `deferred` is a voluntary park with no named blocker,
`blocked` always names its blocker so the roadmap shows what it waits on and
links to it.

A `blocked` feature's detail section carries a `**Blocked by.**` block — blank
line above it, one linked blocker per clause:

**Blocked by.** [ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md) — awaiting approval; [FEAT-2026-0011](#feat-2026-0011) — scoring data must land first.

Each blocker is a Markdown link: an ADR points at its `.md` file (kept under
`docs/adr/` by convention, so from `.specfuse/roadmap.md` the link is
`../docs/adr/…`); a feature dependency points at the blocking
feature's roadmap anchor (`#feat-yyyy-nnnn`). When every blocker clears, a human
flips `blocked` → `active` (or `planned`) and removes the `**Blocked by.**` block.

## Notes

- Correlation IDs are allocated here, sequentially per year: `FEAT-YYYY-NNNN`. Work
  units take `FEAT-YYYY-NNNN/TNN`. The same scheme threads commits (trailer
  `Feature: FEAT-YYYY-NNNN/TNN`), the per-feature event log, and — at fold-in —
  GitHub issues across repos.
- The feature folder name carries the full ID plus a slug, so it greps, sorts, and
  threads cleanly.
- **Read `.specfuse/LEARNINGS.md` before detailing a new feature.** It is the
  accumulated output of every gate's lessons step and exists to make the next plan
  better than the last.
