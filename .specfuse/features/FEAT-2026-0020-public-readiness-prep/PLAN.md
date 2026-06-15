---
feature_id: FEAT-2026-0020
title: Public-readiness prep — secrets audit + OSS hygiene before visibility flip
slug: public-readiness-prep
branch: feat/FEAT-2026-0020-public-readiness-prep
roadmap_goal: Make `main` publishable before FEAT-2026-0019's first PyPi tag — audit history + content for secrets / personal-refs / cross-pollination / license gaps, then land OSS hygiene files + a visibility-flip checklist.
autonomy_default: supervised
status: active
planned_cost_usd: 13.10
---

# Plan: Public-readiness prep

FEAT-2026-0019 ships a public PyPi wheel whose contents are public source. That is
coherent only if the GitHub repo also goes public — and a repo whose history was written
under a "this is private" assumption may carry artifacts that should not go public:
committed credentials, personal email + machine paths, in-flight comments not meant for
an external audience, cross-pollinated content from other private repos, missing
contributor-onboarding files. This feature is the one-shot cleanup that makes `main`
publishable, so 0019's first release lands on a public repo whose history is fit for the
audience.

Two gates. **Gate 1 (Audit)** produces a triage report — `AUDIT.md` — with every finding
+ a verified-clean post-remediation re-scan. Destructive operations (history rewrite,
secret rotation) are planned in-loop and executed by the operator between WU dispatches;
the loop verifies the result. **Gate 2 (Public hygiene + flip)** lands the public-facing
hygiene files (README polish, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, dependabot, issue
+ PR templates) and a `FLIP-CHECKLIST.md` enumerating the visibility-flip steps + owners
+ rollback. The visibility flip itself happens outside the loop (GitHub UI, human
decision); the loop confirms readiness.

This file owns the **shape** — gate order, which work units belong to each gate, and the
dependency edges between them. It does **not** own status. Gate 2's substantive WUs are
drafted by gate 1's `plan-next` from the retrospective + lessons.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0020/T01
        file: WU-01-secret-history-scan.md
        depends_on: []
      - id: FEAT-2026-0020/T02
        file: WU-02-personal-refs-grep.md
        depends_on: []
      - id: FEAT-2026-0020/T03
        file: WU-03-cross-pollination-check.md
        depends_on: []
      - id: FEAT-2026-0020/T04
        file: WU-04-gh-content-sweep.md
        depends_on: []
      - id: FEAT-2026-0020/T05
        file: WU-05-license-header-sweep.md
        depends_on: []
      - id: FEAT-2026-0020/T06
        file: WU-06-post-remediation-rescan.md
        depends_on:
          - FEAT-2026-0020/T01
          - FEAT-2026-0020/T02
          - FEAT-2026-0020/T03
          - FEAT-2026-0020/T04
          - FEAT-2026-0020/T05
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0020/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0020/T01
          - FEAT-2026-0020/T02
          - FEAT-2026-0020/T03
          - FEAT-2026-0020/T04
          - FEAT-2026-0020/T05
          - FEAT-2026-0020/T06
      - id: FEAT-2026-0020/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # --- closing sequence: 1-WU close (terminal gate) ---
      # Scaffold this now so lint can identify gate 1 as non-terminal.
      # G1-PLAN fills in the substantive WUs above this entry when gate 1 completes.
      - id: FEAT-2026-0020/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: []   # G1-PLAN will set real depends_on when it drafts gate 2
```

## Notes

- Destructive operations (history rewrite via `git-filter-repo` / BFG, credential
  rotation, repo-visibility flip) execute OUTSIDE the loop. WUs T01–T05 produce triage
  reports + exact remediation commands; the operator runs them between gate-1 dispatches;
  T06 verifies the result. Rationale: a re-attempt after a partial history rewrite leaves
  the working tree in a state that `git reset --hard` between attempts cannot undo.
- Autonomy is `supervised` — every WU dispatch waits for human confirmation before the
  driver fires. This matches the destructive-ops-are-operator-side posture: the human
  always sees the next WU's body before it runs.
- Dependencies live here, not in WU frontmatter.
- WU file numbers track the correlation sub-ID. Closing units use the 90+ range so they
  sort last.
