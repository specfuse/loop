---
gate: 1
status: awaiting_review
---

# Gate 1 — the scaffold-upgrade skill exists, deploys, and is merge-safe

## Definition of done

- `.specfuse/scripts/upgrade_merge_gate.py` exists with a `decide(...)` predicate
  that returns `halt` on any post-upgrade health FAIL or non-green CI, `merge`
  only on clean+green — with pytest coverage (T01).
- `.specfuse/skills/scaffold-upgrade/SKILL.md` exists and documents the dry-run
  (report-only) and live (branch → upgrade → commit → push → PR → watch → merge
  or halt→feature-conversion) flows against a path-arg target (T02).
- The skill is wired for discovery (`.claude/skills/` forward symlink), listed in
  both `docs/skills.md` copies, and proven to deploy readable by
  `tests/init_skills_idempotent.bats` (T03).
- Retrospective, durable lessons, docs/roadmap reconciliation, and the feature-arc
  verdict are produced by the terminal `close` WU.

Single-gate feature: the terminal `close` WU (G1-CLOSE) collapses
retrospective + lessons + docs + verdict into one session. Driver-side terminal
flips (gate → passed, roadmap row → done, auto-archive) fire when `verdict: met`.

## Reflection notes

<Written by the human at review time.>
