# Gate 3 review — FEAT-2026-0003

Drafted by `FEAT-2026-0003/G2-PLAN` (Opus). Read this before arming.
Weighted toward DOUBT: if I had to bet which decision you'll overturn at
review, those calls are in **Flagged for attention** first.

This file is **advisory**. It owns no state. Status lives in WU files; the
graph lives in `PLAN.md`. If you change a decision, edit the WU and the graph
directly.

This is gate 3 — the *last* gate in the skeleton. The closing-sequence WU
`G3-PLAN` therefore has no next gate to draft; its terminal-case handling is
documented in §Terminal-case handling at the bottom.

---

## Decisions & rationale

### Three substantive WUs, split along the offline/live boundary

- **T05 = `Backend` seam widening** (lifecycle hooks + factory; offline).
- **T06 = `GitHubBackend` implementation** (subclass + label transitions
  via stubbed `gh` runner; offline).
- **T07 = live end-to-end smoke** (against real
  `example-org/example-app#287`; the only network-bound step).

The WU spec itself directed this cut: *"The smoke WU must be a separable
WU (offline backend wiring vs live `gh` smoke is the right cut, mirroring
gate 1's offline-first principle in `[FEAT-2026-0003/G1-LESSONS]`)."*
T05 vs T06 is a further split — separating the *seam widening* from the
*subclass implementation* — because T05's contract change is what T06
consumes, and a future maintainer who only wants the lifecycle hooks (a
different state backend, say a JSON log) gets a clean seam to plug into.
T06 owns the subclass + factory wiring; the seam itself is independent
mechanism.

Source: WU spec AC 1, `[FEAT-2026-0003/G1-LESSONS]` offline-first, and the
seam-don't-fork directive in `docs/handoff-github-feature-pick.md`
§"Seams to respect" (charter §5).

### Lifecycle hook shape: three methods on `Backend`, no event-bus

The narrowest extension of the existing `Backend` class
(loop.py:219-231) that satisfies handoff §3.4's "feature
started/completed signals" is three no-op methods on the existing class:

- `on_feature_start(feature_id, feat_fm)` — fires once at top of `run()`
- `on_gate_passed(feature_id, gate_number)` — fires after
  `set_gate(awaiting_review)` (the v0.1 stub is a no-op; documented why)
- `on_feature_complete(feature_id)` — fires once on the all-gates-passed
  exit path at loop.py:590-591.

I considered an event-bus (a generic `on_event(event_type, payload)`)
but rejected it: the driver already has an event log
(`events.jsonl`); duplicating event semantics in the Backend seam
violates one-fact-one-home. Named methods name *which lifecycle moments*
the backend cares about; an opaque event-bus would force every backend
to filter the same events from a stream.

Source: read of loop.py:219-231 (`Backend`), 580-755 (`run()`).

### Label scheme: `loop:in-progress` / `loop:complete`

Distinct from `specfuse:feature` (discovery label set in gate 1) so the
orchestrator can query for in-flight features without conflating with
adoption candidates. `loop:` namespace mirrors `specfuse:` and
`initiative:` namespaces already in use; the orchestrator's poller
addendum will own the label-query side of the contract.

`on_gate_passed` is a v0.1 documented no-op: I did not introduce a
gate-level label transition because the methodology already exposes
gate progression via the per-feature `events.jsonl` and via the
`awaiting_review` status flip on the GATE file. A label-per-gate would
require a per-feature enumeration of gates (`loop:gate-1-done`,
`loop:gate-2-done`, …) which is brittle as gate counts vary by feature.
The hook is wired so a future label scheme can land without re-touching
the seam.

Source: handoff brief §3 (label naming convention), gate-1 LEARNINGS on
specifying label/field details explicitly
(`[FEAT-2026-0003/G1-LESSONS]`).

### Factory selects by `source_issue_url`, not by ID origin

`make_backend(feat_fm)` returns `GitHubBackend` when `feat_fm` declares
a parseable `source_issue_url`; otherwise plain `Backend`. I considered
selecting by ID origin (`INIT-…` → GitHubBackend) but rejected it:

- `source_issue_url` is the *direct* signal that "this feature was
  adopted from a real GitHub issue we can edit labels on."
  ID-origin is correlated but indirect — an `INIT-…/FNN` feature folder
  created by-hand (bypassing `adopt_feature.py`) would not have an
  issue URL and shouldn't be back-labeled.
- The adopt script already writes `source_issue_url` (gate-2 work).
- A malformed URL falls back gracefully to plain `Backend` — degraded
  fallback over crashed run.

Source: gate-2 retrospective on `adopt_feature.py` frontmatter, gate-2
GATE-02-REVIEW.md decision on the URL recording.

### T07's smoke does NOT grind #287's code

T07 verifies adopt + label transitions against a real GitHub issue.
It does NOT actually grind the code change `INIT-2026-0001/F06` ("Conform
exampleEndpoint to validated spec") asks for — that work lives in
`example-org/example-app`'s tree, not this repo's. T07's deliverable is
a smoke journal (`SMOKE-INIT-2026-0001-F06.md`) plus the adopted feature
folder (`INIT-2026-0001-F06-<slug>/`) — both inside this repo as
verification artifacts.

The grind of #287's code is downstream of this feature — it happens
when an orchestrator dispatches #287 to `example-org/example-app`'s
loop, which then runs against its own tree. Conflating the "smoke
proves adopt+report-back" with "smoke proves the full pipeline grinds"
would blow this gate's scope past one feature.

Source: handoff brief §3.3 ("Decompose + grind: the loop's existing
gate cycle takes over — no change to the core loop here") and the
single-repo grind contract.

### Models

| WU | Model | Reason |
|---|---|---|
| T05 | sonnet-4-6 | Mechanical: add three methods + a factory + tests. Pattern mirrors gate-1's T02 injectable-runner work. |
| T06 | sonnet-4-6 | Subclass implementation against stubbed runner — synthesis against gate-1's `gh_features.py` exemplar. |
| T07 | sonnet-4-6 | Live smoke + journal writing. The decision-load is in safety preamble (block-or-proceed); sonnet handles the journal-writing capably and the safety rules are pre-stated. |
| G3-RETRO, G3-LESSONS, G3-DOCS | sonnet-4-6 | Synthesis / reconciliation; mirrors gates 1-2 closing-sequence model choices. |
| G3-PLAN | opus-4-7 | Terminal-case handling: branch-A or branch-B decision against gate-3 evidence. Mirrors G1-PLAN / G2-PLAN's choice. Cost is worth it once per gate boundary even when the "next gate" is a feature-closure step. |

### Closing-WU file numbering 98-101

Continues gates 1 (90-93) and 2 (94-97). Per
`[FEAT-2026-0003/G1-LESSONS]`, this convention should migrate to a
binding rule or template — that is still NOT done; G1-PLAN's
GATE-02-REVIEW.md §"Open question Q3" flagged it; G2-PLAN flags it
again here. **No action required at gate 3 arming time** since gate 3
is the last gate, but if a hypothetical FEAT-2026-0004 is started
without the rule promotion happening, the convention will go invisible
to its `draft-feature` run.

### Dependency edges

- T05 → []
- T06 → [T05]
- T07 → [T06]
- G3-RETRO → [T05, T06, T07]
- G3-LESSONS → [G3-RETRO]
- G3-DOCS → [G3-LESSONS]
- G3-PLAN → [G3-DOCS]

T05/T06/T07 are strictly sequential — each step's contract is the
prior step's deliverable. T05 and T06 cannot run in parallel (T06
imports the seam T05 widens). T07 cannot run before T06 (the smoke
exercises `GitHubBackend`).

---

## Flagged for attention — check these three first

### (1) T07's live smoke mutates a real production GitHub issue

T07 fires `gh issue edit --add-label loop:in-progress` on
`example-org/example-app#287` — a real issue in a real production
repo. The safety preamble adds two stop conditions (label state
unexpected → block; auth error → block) and the AC requires a final
cleanup restoring the issue to its pre-smoke label state. **But** the
sequence "add label → adopt → verify → add complete label → remove
labels" leaves a real audit trail in the issue's event log that
@cbonte99 (the issue's likely owner) will see in their GitHub
notifications.

**The risk shape:** an honest mistake during the agent's session
(e.g. the cleanup step fails halfway through) leaves the issue in an
inconsistent label state. The orchestrator's later poller would then
see `loop:in-progress` on an issue that is NOT actually being
ground, and dispatch logic could diverge.

**Two ways to resolve at review:**

- **Accept** (recommended for v0.1): the safety preamble is the
  best mitigation available, and the cleanup AC names the failure
  mode. Human-runs-the-WU-with-eyes-open is a tolerable v0.1
  posture for a one-time live integration.
- **Restructure T07** to operate against a *test* issue (not
  #287) created for this purpose, with a separate manual smoke
  against #287 after T07 passes. This adds one more issue to the
  tracker but moves the production-issue risk out of the loop's
  automated dispatch path.

I went with "accept" because the WU spec named `INIT-2026-0001/F06`
(== #287) explicitly as the smoke target, and creating a test issue
adds a new artifact the orchestrator-side proof would have to
account for. The call is yours.

### (2) The label scheme decision is locked here but is a contract with the orchestrator

`loop:in-progress` / `loop:complete` are written into T06's ACs.
Once T06 ships, the orchestrator's poller (separate work, separate
repo) will query against these label names. **If they change later,
both surfaces have to change together — a fork in the contract.**

**The risk shape:** I picked these label names from first principles
(handoff brief §3 names the namespace convention but not the
specific labels). The orchestrator team — or its addendum docs —
may have already named different labels.

**Two ways to resolve at review:**

- **Confirm first**: before arming, check the orchestrator's
  addendum (`example-org/orchestrator/docs/`)
  or the orchestrator repo's open issues for whether
  `loop:in-progress` / `loop:complete` are already named OR whether
  different names (e.g. `feature:in-flight`, `feature:done`) are
  preferred. Edit T06's AC 3 if so.
- **Accept the chosen names**: they're consistent with the
  `specfuse:`, `initiative:`, `type:`, `autonomy:` patterns already
  in use; a divergence is unlikely. If divergence emerges later,
  it's a one-line edit in `GitHubBackend`.

I went with "accept" because checking the orchestrator's docs
exceeds gate 3's footprint (charter §5: port-and-strip, never
copy-paste — the contract is named once on each surface). But this
is the call most worth checking before arming.

### (3) The `Backend` seam widening assumes `run()` has clean lifecycle exit points

T05 wires `on_feature_complete` to fire at loop.py:590-591 (the "all
gates passed — feature complete" early return). **But** the driver's
`run()` function has FOUR exit paths (loop.py:741-755 region):
- All gates passed (the lifecycle exit T05 targets)
- A WU was `blocked_human` (return 1)
- Dry-run completion (return 0)
- Gate marked `awaiting_review` (the normal-completion exit T05 fires
  `on_gate_passed` from)

The "feature complete" hook fires ONLY on path 1. That's correct in
shape (the feature isn't complete on a blocked or dry-run exit) but
it means a feature whose final gate passes WITHOUT the all-gates-
passed early return — i.e. the gate flips to `awaiting_review`,
human arms, human re-runs, then it hits the early return — does
fire on the eventual re-run. This is the intended sequence; I'm
flagging it because a reader of T05's code might wonder "why isn't
this hook in the gate-completion path?" The answer is the human-arm
checkpoint sits between gate-passed and feature-complete.

**Mitigation:** T05's AC 5 names the loop.py:590-591 anchor
explicitly so the agent doesn't drift to a wrong call-site. If the
agent finds the line range is different (e.g. someone refactored
since I read), the WU's escalation trigger names that as a stop
condition.

---

## Roadmap anchor

Gate 3 directly closes the loop on the feature's `roadmap_goal`:
*"The loop can pick a feature from a target repo's GitHub issues
(specfuse:feature) and grind it through its gate cycle, alongside
today's locally-authored features."*

- Gate 1 (read path) — discover via `gh_features.py`. ✓ shipped.
- Gate 2 (write path) — adopt via `adopt_feature.py` +
  `/adopt-feature` skill. ✓ shipped.
- Gate 3 (report back + smoke) — `GitHubBackend` label
  transitions + live verification against
  `example-org/example-app#287`. **This gate.**

After gate 3, the answer to "does the loop grind an
orchestrator-dispatched feature end-to-end?" is a yes-or-no the smoke
journal records definitively. If yes, the feature is `done`. If no,
the smoke journal names the gap and either gate-4 (branch B of
G3-PLAN) or a follow-on feature owns the fix.

**Goal-change escalation?** Neither gate-1 nor gate-2 retrospective
implies the roadmap goal should change. Gate 1 went cleanly; gate 2
went cleanly with three pre-arm review questions all resolved
without escalation. The multi-gate proof is on track. **No
escalation needed** at gate 3 arming time.

---

## Open questions (mapped to WUs)

### Q1. Is `example-org/example-app#287` still the smoke target? (affects T07)

The handoff brief and GATE-02-REVIEW.md both name `INIT-2026-0001/F06`
== issue #287. **I did not verify the issue still exists with all
four expected labels** (`specfuse:feature`, `initiative:INIT-2026-0001`,
`type:implementation`, `autonomy:review`) before drafting T07. The
verification belongs in T07's safety preamble — but if the human
already knows the issue moved (closed, re-labelled, transferred),
edit T07's ACs to name the new target rather than discover the
mismatch mid-grind. Manual check before arming:

```
gh issue view example-org/example-app 287 --json
number,title,labels,state
```

### Q2. Is the orchestrator's poller specification stable enough to lock the label scheme? (affects T06)

See **Flagged 2** above. The decision to use `loop:in-progress` /
`loop:complete` is locked in T06 ACs 3, 5. If the orchestrator addendum
specifies different names, T06's AC 3 needs editing before arm. This is
a coordination concern that lives outside this repo.

### Q3. Should T05's `on_gate_passed` be a documented no-op v0.1, or removed? (affects T05, T06)

I kept it as a no-op stub (T05 AC 1, T06 AC 4) on the principle
that adding a hook later requires re-touching the seam, but adding
behavior to an existing hook is a non-breaking change. **Counter-
argument:** YAGNI — if we don't have a use for gate-level label
transitions today, the v0.1 hook is dead code that someone will
have to delete later. If you prefer YAGNI, remove the hook from
T05 AC 1 (`on_feature_start` and `on_feature_complete` only) and
T06 AC 4 entirely; T05 AC 4 (`on_gate_passed` call in run()) goes
away. The orchestrator-side decision on gate-level labels would
then be the trigger to re-add it.

### Q4. Should the closing-WU 90+ numbering convention finally migrate to a binding rule? (affects future features only)

LEARNINGS `[FEAT-2026-0003/G1-LESSONS]` flagged this; GATE-02-REVIEW
re-flagged; this gate is the last one in this feature, so no
action is forced on us, but a hypothetical FEAT-2026-0004 will
hit this gap if `draft-feature` runs without the rule promotion.
Recommend: a one-line edit to `.specfuse/templates/PLAN.md.template`
(if such a template exists) or the `draft-feature` skill, naming the
convention. Out of scope for this WU; raising as a meta-concern.

### Q5. The smoke journal's "outcome" verdict on the issue-body well-formedness assumption (affects T07 → potentially adopt_feature.py)

GATE-02-REVIEW.md §3 flagged that real issue bodies might not match
the five-section WU contract. T07 AC 4 makes this an explicit
journal section — but T07 doesn't *fix* a malformed body, it
escalates. If #287's body is malformed, gate-3 closure depends on
a human deciding whether to patch the issue, patch adopt_feature.py
to handle the variant, or both. That decision is downstream of
G3-PLAN's branch-A vs branch-B fork.

---

## Terminal-case handling

Gate 3 is the LAST gate in `PLAN.md`'s skeleton. G3-PLAN therefore
has no further gate to draft.

**The chosen handling** is branch-A by default: G3-PLAN writes a
`## Feature-arc retrospective — FEAT-2026-0003` section in
`RETROSPECTIVE.md` synthesizing the three-gate arc and declaring
whether the `roadmap_goal` was met. PLAN.md's graph is unchanged.
The feature is then ready for closure (G3-DOCS will have flipped
the roadmap row to `done`).

**The escalation** is branch-B: if gate-3 retrospective evidence
shows the roadmap goal is NOT met AND a bounded gate-4 scope is
identifiable, G3-PLAN may extend PLAN.md with a `gate: 4` entry
and create `GATE-04.md` + `GATE-04-REVIEW.md`. This is NOT the
default; it requires gate-3 evidence to demand it. Perpetually
extending a feature with new gates corrodes the methodology's
"feature ends" contract.

The decision is made BY G3-PLAN at gate-3 closure time, not now —
this review document just declares the rule. The reason it's a
G3-PLAN decision rather than a human-only call: G3-PLAN runs
*after* G3-DOCS and the smoke journal exist, so it has the
evidence to make the call honestly. If G3-PLAN is uncertain
(ambiguous evidence), it escalates per its own escalation
triggers.

WU-101 (G3-PLAN) documents both branches in its ACs. Read it
before arming gate 3 so you know what the closing step will
actually do.

---

## Summary

Three substantive WUs split offline/live (T05 seam widening, T06
GitHubBackend impl, T07 live smoke) + standard closing sequence,
total seven WUs in gate 3. The non-obvious calls are: lifecycle-
hook shape on `Backend` (not event-bus), label-scheme choice
(`loop:in-progress`/`loop:complete`), factory selection by
`source_issue_url` (not ID origin), and T07's safety preamble
governing live mutation of a production issue.

**Check first:** T07's production-issue risk (Flagged 1), the
label-scheme coordination with the orchestrator (Flagged 2), and
the `Backend` seam's call-site assumption in T05 (Flagged 3).

**Models hold sonnet for synthesis/implementation and opus for
G3-PLAN.** Same pattern as gates 1-2.

**Terminal case** is handled in G3-PLAN by branch-A default
(feature-arc retrospective + closure) or branch-B escalation
(extend with gate 4 if evidence demands).
