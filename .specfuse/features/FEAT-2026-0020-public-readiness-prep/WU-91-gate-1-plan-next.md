---
id: FEAT-2026-0020/G1-PLAN
type: plan-next
status: pending
attempts: 0
generated_surfaces: []
oracle_env: macos_local
planned_cost_usd: 1.80
---

# Gate 1 plan-next — draft gate 2's substantive WUs

**Objective.** Author gate 2's substantive WU files and write `GATE-02-REVIEW.md`
summarizing what gate 1 produced, what gate 2 should produce, and any open verifications
for the operator. Update `PLAN.md`'s gate-2 `work_units` graph with real `depends_on`
edges. Gate 2 is terminal — closing sequence is single `close` (not `close-intermediate`).

**Context.** This is `FEAT-2026-0020/G1-PLAN`. Follows G1-CLOSE-INTERMEDIATE. Drafts
gate 2 from gate 1's retrospective + lessons + this feature's overall design (PLAN.md).

Gate 2's expected scope (per roadmap detail + PLAN.md):
- **Public-facing hygiene files**: README polish (60-second pitch + quickstart),
  CONTRIBUTING.md (issues/PRs/tests/methodology-dogfood expectation), SECURITY.md
  (GitHub Security Advisories + email fallback), CODE_OF_CONDUCT.md (Contributor
  Covenant 2.1 unmodified).
- **`.github/` machinery**: ISSUE_TEMPLATE (bug, feature, methodology-question),
  pull_request_template.md, dependabot.yml (actions + pip, weekly).
- **`FLIP-CHECKLIST.md`**: every visibility-flip step + owner + rollback. Final
  substantive WU = "operator runs the checklist" (the flip itself is operator-side, not
  in-loop).
- **Terminal close (`G2-CLOSE`)**: writes terminal verdict.

Binding rules: `.specfuse/rules/*.md`. Per-WU craft: `.specfuse/skills/
authoring-work-units/SKILL.md`. The driver owns all git; edit files only.

**Acceptance criteria.**

1. **Gate 2 substantive WU files drafted** (status: `draft`). Exact set is at this WU's
   discretion guided by gate-1 retrospective + roadmap detail. Plausible shape (operator
   confirms at arming):
   - `WU-01-readme-polish.md`
   - `WU-02-contributing.md`
   - `WU-03-security-md.md`
   - `WU-04-code-of-conduct.md`
   - `WU-05-github-templates.md` (issue templates + pull_request_template)
   - `WU-06-dependabot.md`
   - `WU-07-flip-checklist.md` (writes FLIP-CHECKLIST.md)
   - `WU-08-flip-rehearsal.md` (operator-runs-checklist verification — likely a
     `blocked_human` checkpoint by design)
   Bundling smaller files together (e.g. CODE_OF_CONDUCT + SECURITY into one WU) is
   acceptable when the per-WU sizing rule supports it.

2. Each WU file follows `.specfuse/templates/WU.template.md` and `/authoring-work-units`:
   - Five required sections (Context, Acceptance criteria, Do not touch, Verification,
     Escalation triggers).
   - Numeric file-count bounds in Do-not-touch (`[FEAT-2026-0003/G1-LESSONS]`).
   - Acceptance bullets name what the WU PRODUCES (`[meta/first-live-use]`).
   - Acceptance bounded to the feature's footprint, not repo-wide.
   - Symbol-existence checks for any new symbols introduced.
   - `Red-test exempt: <reason>` line on any WU that does not introduce verifiable new
     behaviour (most of gate 2's WUs are content/config files — exempt is the likely
     outcome; flag any that aren't).

3. **`PLAN.md` gate-2 `work_units` graph updated** with real `depends_on` edges. Pattern:
   - Substantive WUs that do not block each other → `depends_on: []` (gate 1 is the
     barrier).
   - `WU-07-flip-checklist.md` depends on all hygiene-file WUs (the checklist references
     them).
   - `WU-08-flip-rehearsal.md` depends on `WU-07`.
   - `G2-CLOSE` depends on every substantive WU.
   The pre-existing `G2-CLOSE` scaffold entry in PLAN.md is updated, not replaced.

4. **`GATE-02-REVIEW.md`** written at the feature folder root. Sections:
   - **Gate-1 summary** — one paragraph: what shipped, audit verdict, total cost.
   - **Gate-2 substantive WUs** — one paragraph per WU summarizing scope.
   - **Open verifications** — operator-decisions before arming:
     - File-bundle decisions (which small files combine into one WU).
     - Exact text snippets that need legal/maintainer review before WU dispatch (e.g.
       SECURITY.md disclosure channel — gh advisories OR direct email).
     - Whether FLIP-CHECKLIST.md should include the PyPi-tag step (cross-feature with
       FEAT-2026-0019) or stop strictly at the GitHub visibility flip.
   - **Cross-repo contracts** — any invented strings (issue-template field names,
     dependabot package ecosystems) flagged for operator confirm.

5. **Existence check** before declaring complete:

   ```bash
   FEAT=.specfuse/features/FEAT-2026-0020-public-readiness-prep
   # a. Every drafted gate-2 WU file exists
   ls "$FEAT"/WU-0[1-9]-*.md 2>/dev/null | grep -q .
   # b. GATE-02-REVIEW.md exists and is non-empty
   test -s "$FEAT/GATE-02-REVIEW.md"
   # c. PLAN.md gate-2 work_units carry at least one real FEAT-2026-0020/T* id beyond
   #    the G2-CLOSE scaffold
   awk '/gate: 2/,0' "$FEAT/PLAN.md" | grep -qE 'FEAT-2026-0020/T0[1-9]'
   # d. lint_plan.py clean on the feature folder
   python3 .specfuse/scripts/lint_plan.py "$FEAT"
   # e. Each drafted gate-2 WU has all five required sections
   for f in "$FEAT"/WU-0[1-9]-*.md; do
     for sec in '\*\*Context\.\*\*' '\*\*Acceptance criteria\.\*\*' '\*\*Do not touch\.\*\*' '\*\*Verification\.\*\*' '\*\*Escalation triggers\.\*\*'; do
       grep -qE "$sec" "$f" || { echo "missing $sec in $f"; exit 1; }
     done
   done
   ```

   If any check fails, emit `status: blocked` naming the failing check.

**Do not touch.** Files this WU may edit/create:
- `WU-0N-*.md` files for gate 2's substantive WUs (new).
- `GATE-02-REVIEW.md` (new).
- `PLAN.md` (gate-2 `work_units` graph only — do NOT modify feature frontmatter, gate-1
  work_units, or the G2-CLOSE scaffold's identity).

No edits to: gate-1 WU files, `loop.py`, other features, skills, secrets, `.git/`.
Driver owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.** `plannext` gate set in `.specfuse/verification.yml`. Plus AC5
existence checks. Plus `lint_plan.py` clean on the feature folder.

**Escalation triggers.**

1. **Gate-2 scope ambiguity surfaced by gate-1 retrospective.** If the audit retro
   revealed that gate 2's premise needs revision (e.g. a finding requires a different
   hygiene file class), emit `status: blocked`. The operator updates scope; this WU does
   not unilaterally re-scope.
2. **Cross-feature coupling with FEAT-2026-0019.** The roadmap detail names a sequencing
   constraint (0020 must precede 0019's first PyPi tag). If gate-1 retrospective surfaces
   ordering tension (e.g. PyPi tag tooling needs to land here, not in 0019), flag in
   GATE-02-REVIEW.md Open Verifications. Do NOT silently pull 0019 scope into gate 2.
3. **Operator-decision items in FLIP-CHECKLIST.** The checklist enumerates owner +
   rollback per step; any step whose owner is unclear or whose rollback is "not
   recoverable" must be flagged in GATE-02-REVIEW.md, not papered over in WU-07's draft.
