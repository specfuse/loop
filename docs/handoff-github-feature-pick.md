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

**Delivery status (as of gate 2):** Steps 1 and 2 are shipped. Step 3 uses the existing
loop unchanged. Step 4 is gate 3's scope — not yet delivered.

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
   (the orchestrator's "state backend" seam — see methodology §10). At minimum: emit
   feature started/completed signals the orchestrator can observe (issue label transitions
   and/or the per-feature event log). The RESULT block already maps to the orchestrator's
   `task_completed`. **Not yet delivered; gate 3's scope.**

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

Once GitHub-pick works, dispatch one real orchestrated feature end-to-end:
- **`INIT-2026-0001/F06`** — "Conform publishRoster to validated spec" — `RestoManagerApp/Backend`
  issue #287, label `specfuse:feature` + `initiative:INIT-2026-0001`, `type:implementation`,
  autonomy `review`. Small, mostly-already-implemented conformance task — a low-risk first dispatch.
  (The roster pilot initiative INIT-2026-0001 has features F01–F14; F06 is the simplest.)

## 6. Out of scope here
- The orchestrator-side poller/dispatcher (separate, orchestrator repo).
- Rewriting the orchestrator architecture addendum to Model B (deferred until this proof lands).
- `specfuse/methodology` extraction (deferred until contracts stop moving — charter §4).
