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

| Feature ID     | Title                | Status   | Folder |
|----------------|----------------------|----------|--------|
| FEAT-2026-0001 | Health-check endpoint| active   | `features/FEAT-2026-0001-health-endpoint/` |
| FEAT-2026-0002 | <title>              | planned  | — |
| FEAT-2026-0003 | <title>              | planned  | — |

Status: `planned` → `active` → `done` (or `abandoned`).

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
