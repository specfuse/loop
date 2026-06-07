---
id: FEAT-2026-0003/T07
type: implementation
model: claude-sonnet-4-6
status: done
---

# Live end-to-end smoke — adopt INIT-2026-0001/F06 and observe label transitions

**Objective.** Run the only step gates 1-2 could not: a *live*
end-to-end pass against the real target issue
`example-org/example-app#287` (initiative `INIT-2026-0001/F06`,
labels `specfuse:feature` + `initiative:INIT-2026-0001` +
`type:implementation` + `autonomy:review`). Verify discovery,
adopt, and `GitHubBackend` label transitions all work against the
real GitHub API. Produce a smoke journal (`SMOKE-INIT-2026-0001-F06.md`)
documenting observed behaviour. This is the WU the prior gates
deferred — separated per `[FEAT-2026-0003/G1-LESSONS]`
offline-first so T05/T06 land deterministically and this one
isolates the network-bound risk.

**Context.** Handoff brief §5 names the smoke target:
*"INIT-2026-0001/F06 — 'Conform exampleEndpoint to validated spec'
— example-org/example-app issue #287, label specfuse:feature +
initiative:INIT-2026-0001, type:implementation, autonomy review.
Small, mostly-already-implemented conformance task — a low-risk
first dispatch."* This WU does NOT grind #287's actual code (the
fix work happens in `example-org/example-app`'s loop, not here).
This WU only verifies the *adopt + report-back* mechanism this
feature shipped — discovery sees #287, `adopt_feature.py`
produces a valid folder, `GitHubBackend` transitions labels on
the live issue.

Read `[FEAT-2026-0003/G2-LESSONS]` on automated-code-gate
limitations for prose artifacts: this WU's verification cannot
mechanically check "the smoke actually worked against the real
GitHub" — the test of record is the journal a human reviews. Per
that lesson, name the journal's required sections so reviewer has
a falsifiable checklist.

Read `[meta/first-live-use]` scope-to-footprint: this WU does NOT
edit `example-org/example-app`'s tree. Adopt writes inside this
repo's `.specfuse/features/` (where adopt_feature.py runs); the
adopted folder is a verification artifact, not a dispatched
feature here.

**Execution note (gate-3 arming decision).** This WU mutates a real
production issue and is therefore executed **out-of-loop by the human
operator**, not dispatched as an autonomous `claude -p` session — a
deliberate blast-radius choice made at gate-3 arming time. The driver
runs T05+T06 (offline); a human runs this smoke directly (`gh` with the
sandbox disabled), then marks T07 `done` so the closing sequence can
reflect the real smoke evidence. The acceptance criteria below are the
runbook + falsifiable checklist for that human-run step.

**Safety preamble (read before acting).** This WU
mutates real GitHub state — issue labels on a real production
issue. Two safety rules override the acceptance criteria:

1. If `#287`'s current labels include anything OUTSIDE the
   expected set (`specfuse:feature`, `initiative:INIT-2026-0001`,
   `type:implementation`, `autonomy:review`, `state:ready`), STOP
   and block. (`state:ready` is the canonical pre-pickup lifecycle
   state and is expected; see the label scheme in `WU-06`.) Do NOT
   add `state:in-progress` to an issue whose state is not what
   this WU assumes.
2. If at any point the `gh` CLI returns 401/403/permission
   error, STOP and block immediately per
   `.specfuse/rules/security-boundaries.md` (do NOT
   re-authenticate; do NOT swap credentials).

**Acceptance criteria.**
1. A new file `SMOKE-INIT-2026-0001-F06.md` exists in the feature
   folder (`.specfuse/features/FEAT-2026-0003-github-feature-pick/`)
   with these top-level sections, each populated with actual
   evidence (not placeholders):
   - `## Issue state at smoke time` — output of `gh issue view
     example-org/example-app 287 --json
     number,title,labels,state` recorded verbatim
     (redact nothing — issue data is public on a public repo).
   - `## Discovery step` — `python3 .specfuse/scripts/gh_features.py
     example-org/example-app` output captured, with the row for
     #287 highlighted.
   - `## Adopt step` — the produced folder name, the PLAN.md
     frontmatter contents (`feature_id`, `source_issue_url`,
     `initiative`), and the WU-01 first 20 lines.
   - `## Label transitions observed` — the two `gh issue edit`
     invocations fired by `GitHubBackend` (manually invoked
     against the live issue from a small driver script or
     interactive Python session), the BEFORE labels, the AFTER
     labels for each transition, and a final reset restoring the
     issue to its original label state (re-add `state:ready`,
     remove `state:in-progress` and `state:done`) so the smoke
     leaves no residue.
   - `## Outcome` — a one-paragraph honest summary: did all
     three steps work? What surprised? Where did the
     specification diverge from observation?
2. The adopted feature folder produced by step 3 above is
   committed alongside the journal (it lives at
   `.specfuse/features/INIT-2026-0001-F06-<slug>/`) — this is
   evidence the adopt step succeeded, and it is the artifact a
   reviewer can spot-check. `lint_plan.py` on the adopted folder
   exits 0 (catches the malformed-body assumption flagged in
   GATE-02-REVIEW.md §"Flagged 3").
3. `#287`'s labels are restored to their pre-smoke state by
   journal-completion time (the smoke must leave no residue).
   The journal's `## Label transitions observed` section
   includes a "final restore" subsection showing the cleanup.
4. The journal's `## Outcome` section explicitly states whether
   the assumption from GATE-02-REVIEW.md §3 ("issue bodies are
   well-formed five-section WUs") holds for #287. If it does
   not, an open question is raised IN the journal (not silently
   patched in adopt_feature.py).

**Do not touch.**
- `example-org/example-app`'s repo or any file under it. The
  WU operates on the GitHub issue (labels) — not the repo's
  code, branches, or tracker beyond those labels.
- The adopted folder `INIT-2026-0001-F06-<slug>/` MAY be
  produced, but it is NOT dispatched / armed / ground here.
  Adopt + lint + leave-it. Do not run `loop.py` against it.
- `.specfuse/scripts/` — gate-1/gate-2/T05/T06 code is frozen
  by the time this WU runs; if you find a bug, block and
  document, do not patch.
- Any binding rule under `.specfuse/rules/`.
- `gh` config / credentials — see safety preamble.
- Generated directories, secrets, `.git/`.
- The driver owns git. Do not run `git`.

Numeric bound: **at most two new artifacts** in this repo —
`SMOKE-INIT-2026-0001-F06.md` and the adopted folder
`INIT-2026-0001-F06-<slug>/` (with the contents adopt_feature.py
emits — script-generated content not authored by this WU).

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (it must continue to pass — this
WU adds no code so nothing should break it), PLUS a manual
check: `python3 .specfuse/scripts/lint_plan.py
.specfuse/features/INIT-2026-0001-F06-<slug>/` exits 0.
Per `[FEAT-2026-0003/G2-LESSONS]` on prose-artifact gates: the
journal's verification IS human review at PR time; the
acceptance criteria above are the falsifiable checklist.

**Escalation triggers.**
- `#287` has changed: closed, renamed, lost any of the four
  expected labels, or gained labels not in the expected set.
  Block per safety preamble rule 1.
- `gh` returns 401/403 or any auth/permission error. Block per
  safety preamble rule 2.
- The body of #287 does NOT contain the five mandatory WU
  sections (per GATE-02-REVIEW.md §3). Adopt will still
  produce the folder (per T03's design) but `lint_plan.py`
  will exit non-zero. Document the gap in the journal's
  `## Outcome` section and emit `status: blocked` so a human
  decides: refine adopt_feature.py's body validation OR ask
  the orchestrator to fix the issue body upstream.
- `GitHubBackend` lifecycle methods fire but `gh issue view`
  AFTER the call shows the expected label set is NOT in
  effect. Block with the BEFORE/AFTER captures pasted into
  `blocked_reason` — this is the report-back contract
  failing at integration.
