---
gate: 1
status: open
---

# Gate 1 — Audit

Produces `AUDIT.md` — a triage report covering every audit class (secrets in history,
personal/internal refs, cross-pollination, GitHub PR + issue content, license headers) —
with every finding's triage decision recorded and a post-remediation re-scan verifying
the operator's destructive ops landed clean.

## Definition of done

- Every implementation work unit (T01..T06) is `done`.
- `AUDIT.md` exists with the five audit-class sections (secrets, personal-refs,
  cross-poll, gh-content, licenses) AND a §verification section recording the
  post-remediation re-scan verdict.
- The §verification verdict line reads `audit verdict: green` (no open actions).
- A retrospective exists (feature-local `RETROSPECTIVE.md`), folded with lessons + docs
  by `G1-CLOSE-INTERMEDIATE`. RETROSPECTIVE.md includes `## Cost analysis` AND `## What
  the loop did NOT verify` subsections per the methodology contract.
- Generalizable lessons promoted to `.specfuse/LEARNINGS.md`.
- Documentation + roadmap status reflect what was actually built.
- Gate 2's substantive work units are drafted by `G1-PLAN`, and `GATE-02-REVIEW.md` is
  written.

The closing sequence (`close-intermediate` → `plan-next`) is enforced by the linter. The
driver runs the gate under `supervised` autonomy, then stops here for human review-and-arm.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong.>
