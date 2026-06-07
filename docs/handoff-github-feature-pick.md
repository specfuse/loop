# Handoff brief — GitHub feature-pick for Specfuse Loop

**Audience:** the agent (and human) working in `specfuse/loop` (this repo). You have no memory of
the design conversation that produced this; everything you need is below or linked. Read it whole
before acting.

**One-line goal:** teach the loop to pick a *feature* from GitHub issues (so the orchestrator can
dispatch a feature to a component repo and the component's loop grinds it), in addition to today's
locally-authored `.specfuse/features/` flow.

---

## 1. Why this exists — the decision that was made

Specfuse is three projects (`codegen`, `loop`, `orchestrator`) sharing one gate-cycle methodology
(`docs/methodology.md`). A design decision was taken (human sign-off) about **where gates live**:

- **Gates live in loop, per component — NOT in the orchestrator PM.** The orchestrator coordinates
  one level up: it decomposes an **initiative** into **features**, dispatches each feature to one
  component repo, and owns only cross-repo dependency ordering + the spec/generated interface
  contracts. The receiving component's **loop** takes that feature and decomposes it into gates +
  work units and grinds it — its normal gate cycle.
- So: **an orchestrator-dispatched feature == a loop feature.** This is the unit the loop picks up.

This replaces the older "gates in the PM" design (orchestrator's architecture addendum §A.5). The
full rationale is in the orchestrator repo:
- `/Users/christian/RestoManagerApp/orchestrator/docs/gate-placement-proposal.md` (Model A vs B; B chosen)
- `/Users/christian/RestoManagerApp/orchestrator/docs/specfuse-collaboration-charter.md` (how the two surfaces relate)
- `/Users/christian/RestoManagerApp/orchestrator/docs/naming-convention.md` (the ID/label/branch/trailer contract — read this; summarized in §3)

## 2. Unit hierarchy + the naming convention (the contract you must honor)

```
initiative      orchestrator top; cross-repo            INIT-YYYY-NNNN
  feature       single-repo goal == a LOOP feature      INIT-YYYY-NNNN/FNN   (orchestrated)
                                                         FEAT-YYYY-NNNN       (component-local, today's loop)
    gate        loop milestone partition                G<n>
      work unit one session                             …/FNN/TNN  or  FEAT-…/TNN
```

- **Origin is read from the ID root.** `INIT-…` = orchestrated (threads to an initiative). `FEAT-…`
  = component-local (today's standalone loop features). The loop treats both identically as "a
  feature to grind"; only the namespace differs. Collisions are structurally impossible.
- **GitHub labels** (already applied on real issues):
  - `specfuse:feature` — marks a loop-pickable feature issue. **This is your pick query.**
  - `initiative:INIT-YYYY-NNNN` — present only on orchestrated features; absent ⇒ component-local.
  - `type:<task-type>` — implementation / qa_authoring / qa_execution / qa_curation / (closing types).
- Issue **title**: `[INIT-2026-0001/F03] <summary>`. Issue **body** = the five-section work-unit
  contract (Context / Acceptance criteria / Do not touch / Verification / Escalation triggers) —
  same five sections methodology §4 already defines.
- **Branch/PR:** one branch + one PR **per feature** (`feat/INIT-2026-0001-F03-<slug>`); squash one
  commit per work unit onto it; trailer `Feature: INIT-2026-0001/F03/T01`.

## 3. What to build

**Delivery status (as of gate 3):** All four steps shipped. Step 3 uses the existing
loop unchanged. Step 4 delivered in gate 3 — see §3.4 for as-built details and the
one outstanding finding (lint-format gap) blocking a fully clean end-to-end grind.

A GitHub feature-pick capability for the loop. Behaviorally:

1. **Discover:** query a target repo's open issues labelled `specfuse:feature`. Each is a
   feature. **Shipped (gate 1):** `.specfuse/scripts/gh_features.py` — run
   `python3 .specfuse/scripts/gh_features.py <repo>` or call `list_features('<repo>')`
   programmatically from `.specfuse/scripts/`.

2. **Adopt:** turn a picked issue into a loop feature folder under `.specfuse/features/`,
   using the issue ID as the feature ID (`INIT-2026-0001/FNN` → folder on disk).
   **Shipped (gate 2):**

   - CLI: `python3 .specfuse/scripts/adopt_feature.py <repo> <issue-number>`
   - Interactive: `/adopt-feature` skill (enumerates candidates, accepts pick, runs script)

   The script names the folder `{encoded-id}-{slug}` where slashes are replaced with
   dashes (`INIT-2026-0001/FNN` → `INIT-2026-0001-FNN-<slug>`; `FEAT-YYYY-NNNN` stays
   unchanged). It writes: `PLAN.md` (frontmatter + 3-gate skeleton with empty work-unit
   lists for gates 2 and 3), `GATE-01.md`, `GATE-02.md`, `WU-01-<slug>.md` (seeded
   verbatim with the raw issue body), and gate-1 closing WUs 90–93 (generic placeholder
   bodies — structurally correct, not immediately dispatchable; expect human or `plan-next`
   refinement before arming). `source_issue_url` and `initiative` (omitted when absent) are
   recorded in `PLAN.md` frontmatter. The new feature folder starts with `status: planned`;
   arm it via `/pick-feature` or by editing the roadmap directly.

   **Divergence from planned shape:** the original description said "the issue body's five
   sections seed the feature's gate-1 authoring." The as-built behavior is narrower: only
   WU-01 receives the raw issue body; the gate-1 closing WUs (G1-RETRO through G1-PLAN)
   receive generic placeholder text.

3. **Decompose + grind:** the loop's existing gate cycle takes over — decompose into gates
   + WUs, dispatch fresh sessions, verify-as-oracle, squash per WU. No change to the core
   loop here.

4. **Report back:** state lives in GitHub issue labels + the feature's correlation thread
   (the orchestrator's "state backend" seam — see methodology §10). **Delivered (gate 3).**

   **As-built shape:**

   - **`Backend` seam** (`loop.py`): three lifecycle hooks added to the `Backend` base
     class — `on_feature_start(feat_fm)`, `on_gate_passed(feat_fm, gate_n)`,
     `on_feature_complete(feat_fm)` — plus a module-level factory `make_backend(feat_fm)`.
     The base `Backend` provides no-op implementations; the loop driver calls all three at
     the appropriate milestones (`run()` start, gate boundary, all-gates-passed exit).

   - **Factory selection** (`make_backend`): inspects `feat_fm["source_issue_url"]`. If
     present (i.e. the feature was adopted from a real GitHub issue via `adopt_feature.py`),
     returns a `GitHubBackend` instance wired to that URL. If absent (component-local
     features without `source_issue_url` in PLAN.md frontmatter), returns plain `Backend`
     (no-op). A malformed URL falls back gracefully to plain `Backend`.

   - **`GitHubBackend`** (`.specfuse/scripts/gh_backend.py`): subclasses `Backend`; uses
     the injectable `_default_runner` pattern (matching `gh_features.py` lines 22–36) so
     tests run fully offline. Label transitions via `gh issue edit`:
     - `on_feature_start`: adds `state:in-progress`, removes `state:ready`
     - `on_feature_complete`: adds `state:done`, removes `state:in-progress`
     - `on_gate_passed`: v0.1 no-op stub — no gate-level label transition defined

   - **Label scheme** (canonical per orchestrator `naming-convention.md §5.1` and
     `shared/schemas/labels.md`): `state:ready → state:in-progress → state:done`. The
     pre-pickup lifecycle state on a GitHub issue is `state:ready`; the loop sets
     `state:in-progress` when a feature starts grinding and `state:done` when all gates
     pass. *(Note: G2-PLAN's gate-3 draft proposed `loop:in-progress`/`loop:complete` as
     first-principles label names; these were corrected to the canonical `state:*` namespace
     at gate-3 arming time after verification against orchestrator docs.)*

   **Live smoke result (T07, 2026-06-06, out-of-loop by human operator):**

   | Mechanism | Result |
   |-----------|--------|
   | Discovery (`gh_features.py RestoManagerApp/Backend`) | **PASS** — 13 candidates; `#287` parsed correctly |
   | Adopt (`adopt_feature.py RestoManagerApp/Backend 287`) | **PASS** — folder + encoding + body embed worked |
   | Report-back (label transitions against live `#287`) | **PASS** — `state:ready → in-progress → done`; fully restored |
   | Adopted-folder lint (`lint_plan.py`) | **FINDING** — see below |

   **Outstanding finding — lint-format gap:** `#287`'s body contains all five mandatory
   sections but uses `## ATX` Markdown headings (`## Context`, `## Acceptance criteria`,
   …). The loop's `lint_plan.py` section detector matches `^(\**)<section>` (bold or plain
   text) and does **not** recognise `## ATX` headings. An issue body embedded verbatim by
   `adopt_feature.py` therefore fails the linter despite being structurally complete. This
   blocks a clean end-to-end grind for any adopted feature whose body uses ATX headings.

   **Fix options** (tracked for follow-on; decision by G3-PLAN):
   1. **Broaden `lint_plan.py`** to accept ATX headings — smallest, loop-side, recommended.
   2. **Normalize headings in `adopt_feature.py`** when embedding (`## X` → `**X.**`).
   3. **Fix the orchestrator issue-body template** to emit bold sections (cross-surface).

   Evidence: `SMOKE-INIT-2026-0001-F06.md` (smoke journal) and `RETROSPECTIVE.md §T07`.

### Decisions already locked (don't re-litigate)
- **Uniform:** every dispatched unit IS a loop feature; small ones are trivially single-gate /
  single-WU. No hybrid "bare WU" path.
- **Autonomy flows orchestrator → loop:** `review`/`supervised` ⇒ the loop stops at each gate and
  reports back for a human to arm (it does NOT self-arm). `auto` ⇒ may self-arm safe gates only
  under the full conjunction (lint passes, skeleton unrevised, no supervised task in the gate,
  no escalation) — see orchestrator addendum §A.6.1.1. Escalation always overrides.
- **Load-bearing assumption (already provisioned):** every component repo forbids editing generated
  files. The loop grinds hand-code only, against frozen generated boundaries. A needed interface
  change is an ESCALATION to the orchestrator/specs — never decided inside the grind.

### Seams to respect (charter §5: port-and-strip, never copy-paste)
- Do **not** import orchestrator code. The orchestrator builds its own poller; `loop.py` is the
  reference, not a shared library. Keep the GitHub state-backend behind loop's existing `Backend`
  seam (`.specfuse/scripts/loop.py`) — subclass/extend it, don't fork the driver.
- Branch/merge genuinely differs from single-repo (per-feature PR) — that's intended.
- The shared contract (correlation-ids, RESULT block, verification-as-oracle, five-section WU) must
  keep meaning the same on both surfaces. Update `.specfuse/rules/correlation-ids.md` to accept the
  `INIT-…/FNN[/TNN]` grammar alongside `FEAT-…/TNN`, and teach `lint_plan.py` both.

## 4. Suggested approach — dogfood it (highest leverage)

Run this build **as the loop's first real multi-gate feature**, through the gate cycle itself. That
simultaneously: (a) delivers GitHub-pick, and (b) produces the evidence the charter §6 critical path
needs — proof that `plan-next` drafts a real next gate you'd actually arm. All gate work to date has
been single-gate; this is the unproven thing gating everything downstream. Two birds.

## 5. Smoke test target

**Completed (gate 3, 2026-06-06).** The smoke against `INIT-2026-0001/F06` —
`RestoManagerApp/Backend` issue #287 — was run out-of-loop by the human operator.

- **`INIT-2026-0001/F06`** — "Conform publishRoster to validated spec" — `RestoManagerApp/Backend`
  issue #287, labels `specfuse:feature` + `initiative:INIT-2026-0001` + `type:implementation` +
  `autonomy:review` + `state:ready`. Discovery, adopt, and report-back all PASS. Lint finding
  (ATX heading format gap) noted — see §3.4 for details and the follow-on fix options.

## 6. Out of scope here
- The orchestrator-side poller/dispatcher (separate, orchestrator repo).
- Rewriting the orchestrator architecture addendum to Model B (deferred until this proof lands).
- `specfuse/methodology` extraction (deferred until contracts stop moving — charter §4).
