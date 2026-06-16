---
id: FEAT-2026-0024/G1-PLAN
type: plan-next
status: done
attempts: 2
generated_surfaces: []
oracle_env: macos_local
planned_cost_usd: 2.00
duration_seconds: 820.065
cost_usd: 5.234128
input_tokens: 19516
output_tokens: 60120
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 plan-next — draft gate 2's substantive WUs (issue/PR-body Action, #46)

**Objective.** Author gate 2's substantive WU files and write
`GATE-02-REVIEW.md` summarizing what gate 1 produced, what gate 2 should
produce, and any open verifications for the operator. Update `PLAN.md`'s gate-2
`work_units` graph with real `depends_on` edges. Gate 2 is terminal — closing
sequence is a single `close` (`G2-CLOSE`), not `close-intermediate`.

**Context.** This is `FEAT-2026-0024/G1-PLAN`. Follows G1-CLOSE-INTERMEDIATE.
Drafts gate 2 (issue #46) from gate 1's retrospective + lessons + PLAN.md. Gate
2 ships a GitHub Action that scans GitHub **issue/PR titles, bodies, and
comments** for leaks, reusing the gate-1 scanner and the committed
`leak_denylist.hashes`.

Gate 2's expected scope (per PLAN.md "Gate-2 oracle" + issue #46):
- **The Action workflow** — `.github/workflows/leak-scan-content.yml` (or
  similar), triggered on `issues` (opened/edited) + `pull_request`
  (opened/edited) and optionally `schedule`. On a hit it fails the check and/or
  posts a comment naming the offending field.
- **A scan-runner script** the Action invokes — reads the issue/PR title +
  body + comments from the event payload (or via `gh`/the API), runs
  `leak_scan` structural patterns + the committed hashed denylist + gitleaks,
  exits non-zero on a hit. This is the unit-testable seam.
- **Docs** — the documented limitation that edit-history is NOT expunged by the
  guard (GitHub retains body revisions); the Action stops new leaks only.
- **Terminal close (`G2-CLOSE`)** — writes the terminal feature-arc verdict.

The gate-2 oracle is operator-confirmed (PLAN.md): in-loop coverage is unit
tests over the scan-runner against fixture issue/PR JSON (planted hit + clean);
the live `issues`/`pull_request` trigger is operator-verified post-merge and
logged in G2-CLOSE's `## What the loop did NOT verify`. Do NOT plan `act`/Docker
emulation in-loop.

Binding rules: `.specfuse/rules/*.md`. Per-WU craft:
`.specfuse/skills/authoring-work-units/SKILL.md`. The driver owns all git; edit
files only.

**Acceptance criteria.**

1. **Gate 2 substantive WU files drafted** (status: `draft`). Exact set at this
   WU's discretion guided by the gate-1 retrospective + issue #46. Plausible
   shape (operator confirms at arming):
   - `WU-01-content-scan-runner.md` — the unit-testable runner script that
     scans title/body/comments and exits non-zero on a hit. Red-test-first: a
     fixture issue JSON with a planted denylisted string → exit non-zero; clean
     → exit 0.
   - `WU-02-github-action-workflow.md` — the `.github/workflows/*.yml` that
     wires the runner to `issues` + `pull_request` (+ optional `schedule`)
     triggers and the fail/comment behavior. Likely `Red-test exempt: workflow
     YAML — the runner (WU-01) carries the behavioral test; the live trigger is
     operator-verified post-merge`.
   - `WU-03-docs-and-limitation.md` — documents the guard + the edit-history
     limitation (MAY bundle into WU-01/WU-02 if sizing supports it).
   Bundling smaller WUs is acceptable per the sizing rule.

2. Each WU file follows `.specfuse/templates/WU.template.md` and
   `/authoring-work-units`:
   - Five required sections (Context, Acceptance criteria, Do not touch,
     Verification, Escalation triggers).
   - Numeric file-count bounds in Do-not-touch.
   - Acceptance bullets name what the WU PRODUCES; bounded to the feature
     footprint, not repo-wide.
   - Symbol/file-existence checks for new symbols/files.
   - `produces:` declared on each implementation WU.
   - `Red-test exempt: <reason>` line on any WU not introducing verifiable new
     behavior (the workflow-YAML WU is the likely exempt; the runner is NOT
     exempt).
   - `/authoring-work-units` §11 (operator-script gate) applies if the runner is
     a committed shell script: `shellcheck` clean + `bash -n` + a bats
     happy-path with external commands stubbed. If the runner is Python, the
     `code` gate set covers it; note which.

3. **`PLAN.md` gate-2 `work_units` graph updated** with real `depends_on` edges:
   - Runner WU → `depends_on: []` (gate 1 is the barrier; the hashed denylist
     already exists).
   - Workflow WU → depends on the runner WU.
   - Docs WU (if separate) → depends on the workflow WU.
   - `G2-CLOSE` → depends on every gate-2 substantive WU.
   Update the pre-existing `G2-CLOSE` scaffold entry; do not replace its
   identity.

4. **`GATE-02-REVIEW.md`** written at the feature folder root. Sections:
   - **Gate-1 summary** — one paragraph: what shipped (#45 hashed denylist + CI
     coverage), gate verdict, total cost.
   - **Gate-2 substantive WUs** — one paragraph per WU.
   - **Open verifications** — operator decisions before arming: whether the
     runner is Python vs shell; whether to add `schedule:` to the triggers;
     whether the Action should fail the check, post a comment, or both; how the
     Action reads comments (event payload vs `gh api`) given `gh` reliability
     caveats (LEARNINGS `[FEAT-2026-0014/T01/gh-claudeP-broken]`).
   - **Cross-repo / invented strings** — any workflow field names, permissions
     scopes, or token names flagged for operator confirm.

5. **Existence check** before declaring complete:
   ```bash
   FEAT=.specfuse/features/FEAT-2026-0024-hashed-denylist-leak-guard
   ls "$FEAT"/WU-0[1-9]-*.md 2>/dev/null | grep -q .
   test -s "$FEAT/GATE-02-REVIEW.md"
   awk '/gate: 2/,0' "$FEAT/PLAN.md" | grep -qE 'FEAT-2026-0024/T0[1-9]'
   python3 .specfuse/scripts/lint_plan.py "$FEAT"
   for f in "$FEAT"/WU-0[1-9]-*.md; do
     for sec in '\*\*Context\.\*\*' '\*\*Acceptance criteria\.\*\*' '\*\*Do not touch\.\*\*' '\*\*Verification\.\*\*' '\*\*Escalation triggers\.\*\*'; do
       grep -qE "$sec" "$f" || { echo "missing $sec in $f"; exit 1; }
     done
   done
   ```
   If any check fails, emit `status: blocked` naming the failing check.

**Do not touch.** Files this WU may edit/create:
- `WU-0N-*.md` files for gate 2's substantive WUs (new, status `draft`).
- `GATE-02-REVIEW.md` (new).
- `PLAN.md` (gate-2 `work_units` graph only — NOT feature frontmatter, gate-1
  work_units, or the G2-CLOSE scaffold's identity).

No edits to: gate-1 WU files, `leak_scan.py`, `.github/workflows/`, other
features, skills, secrets, `.git/`. Driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** `plannext` gate set in `.specfuse/verification.yml`. Plus AC5
existence checks. Plus `lint_plan.py` clean on the feature folder.

**Escalation triggers.**
1. **Gate-2 scope ambiguity surfaced by gate-1 retrospective.** If the gate-1
   close revealed the hashing core cannot serve the Action surface (e.g. the
   runner needs a different match contract), emit `status: blocked`. The
   operator updates scope; this WU does not unilaterally re-scope.
2. **gh-reliability coupling.** If the Action's comment-reading approach depends
   on `gh`/`claude -p` surfaces that LEARNINGS flags as unreliable, surface the
   risk in GATE-02-REVIEW.md Open Verifications — do NOT silently commit to a
   brittle path.
3. **Runner-vs-workflow split unclear.** If the unit-testable seam (runner) and
   the un-loop-verifiable seam (workflow trigger) cannot be cleanly separated,
   flag in GATE-02-REVIEW.md rather than collapsing them into one
   un-testable WU.
