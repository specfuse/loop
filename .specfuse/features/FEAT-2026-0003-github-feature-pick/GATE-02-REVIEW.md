# Gate 2 review — FEAT-2026-0003

Drafted by `FEAT-2026-0003/G1-PLAN` (Opus). Read this before arming.
Weighted toward DOUBT: if I had to bet which decision you'll overturn at review,
those calls are in **Flagged for attention** first.

This file is **advisory**. It owns no state. Status lives in WU files; the
graph lives in `PLAN.md`. If you change a decision, edit the WU and the graph
directly.

---

## Decisions & rationale

### Two substantive WUs, not three

- **T03 = scaffolding script** (`adopt_feature.py` + tests + the one-line
  widening of `gh_features.list_features`).
- **T04 = interactive `adopt-feature` skill** (`SKILL.md` only).

I considered splitting T03 further (e.g. T03 = issue-body parser, T04 =
folder author, T05 = skill — three WUs) but the issue body is already in
the five-section WU contract per `docs/handoff-github-feature-pick.md` §2,
so the "parser" reduces to a verbatim embed. A separate WU for it would be
a one-liner — worse than bundling. Source: handoff §2 (issue body =
WU contract), `RETROSPECTIVE.md` "WU sizing" subsection (both gate-1 WUs
sized correctly at ~2-5 ACs).

### T03 widens `gh_features.list_features` to expose `body`

A genuine forward-design call. The gate-1 default runner already requests
`body` in its `--json` field list, but `list_features` discards it before
returning. Three options were on the table:

1. **Widen `list_features` to pass `body` through** (chosen) — one-line dict
   addition + one test assertion. T03 owns the change with a hard "exactly
   four files" boundary.
2. Have `adopt_feature.py` do a second `gh issue view` call to fetch body —
   wasteful (we already fetched it once) and requires a second
   `subprocess`-shells-`gh` site to maintain.
3. Add a new `get_feature_body()` function to `gh_features.py` — same edit
   surface as option 1 but adds an API that exists only to plug a gap option
   1 closes for free.

Option 1 wins on net file-count and on coupling: `list_features` already
fetches body, so the discard was the bug. The risk: it violates the
"feature folder owns its own changes" instinct by touching gate-1 code from
gate 2. Mitigated by stating the bound explicitly in T03's "Do not touch"
(one line in `list_features`, one assertion in its test). Source: read of
`.specfuse/scripts/gh_features.py:30,71-79`.

### Filesystem encoding: `INIT-YYYY-NNNN/FNN` → `INIT-YYYY-NNNN-FNN`

The handoff brief calls this out as "pick a filesystem-safe encoding, e.g.
`INIT-2026-0001-F03-<slug>`" (§3.2). Single `/` → `-`. T03 AC 1 nails it
down so two adopt runs of the same issue do not produce different folder
names. Source: handoff §3.2 example.

### `gh_features.list_features` invoked once, filtered by `number`

T03's CLI calls `list_features(repo)` then filters by `--label
specfuse:feature --state open` already at the gh layer; the filter-by-number
is in Python. Cost: small repos only (the orchestrator's target is a single
component repo with O(10) open features). If the cost ever bites, the WU
that addresses it is gate 3 or later, not this gate.

### Skill mirrors `pick-feature`'s "honor active features" rule

T04 AC 2 (step b) requires the skill to read `.specfuse/roadmap.md` and
warn if another feature is `active`. Source: `pick-feature/SKILL.md:71-81`
("Detect active work and respect it"). Picked because: gate-1 LEARNINGS
already promoted "honor active" thinking via the pick-feature design, and
double-active drifts the loop driver into ambiguity (requires `--feature`).
Same risk applies here; reuse the rule.

### Models

| WU | Model | Reason |
|---|---|---|
| T03 | sonnet-4-6 | Mechanical: script + tests, contract well-bounded by ACs. Both gate-1 implementation WUs (T01, T02) hit "done in 1 attempt" with sonnet at this shape. |
| T04 | sonnet-4-6 | Authoring a SKILL.md against two existing exemplars (`pick-feature`, `draft-feature`) is synthesis, not novel design. |
| G2-RETRO, G2-LESSONS, G2-DOCS | sonnet-4-6 | Synthesis / reconciliation; mirrors gate 1's closing-sequence model choices. |
| G2-PLAN | opus-4-7 | Forward design — drafting gate 3 (the smoke test). Mirrors G1-PLAN's choice; the cost is worth it once per gate boundary. |

### Closing-WU file numbering 94-97

Continues gate 1's `WU-90`..`WU-93`. The convention is documented in
LEARNINGS `[FEAT-2026-0003/G1-LESSONS]` ("90+ range so closing units sort
last"). Worth flagging: that lesson recommended promoting the convention
into a binding rule or template. **That is not done yet** (waiting on a
deliberate authoring-guide edit) — I am following the convention by hand
here. See **Open questions** below.

### Dependency edges

`T04 depends_on: [T03]` because the skill names `adopt_feature.py`'s CLI
surface verbatim. T03 and T04 are NOT parallelizable — T03 ships the
contract T04 documents. This differs from gate 1's T01/T02 independence
(intentional; the script/skill cut has a real dependency).

---

## Flagged for attention — check these three first

### (1) T03 touches FOUR files, not the gate-1 norm of "exactly 2-3"

Gate 1 used "exactly N files" as a sizing constraint (LEARNINGS
`[FEAT-2026-0003/G1-LESSONS]`). T03 touches four because it widens
`gh_features.list_features` (the gate-1 module) by one line. **The risk
shape**: a future reader of the gate-2 squash commit sees two unrelated
changes mixed (new adopt script + a tiny gh_features change) and asks "why".

**Two ways to resolve at review:**
- **Accept the bundle** (recommended): widen T03's Do-not-touch comment to
  state explicitly that the gh_features touch is intentional and bounded to
  the single line. T03 already does this — re-read its "Do not touch"
  section before arming.
- **Split into a hygiene WU** named `T03H` per the hygiene-WU pattern
  (`.specfuse/skills/authoring-work-units/SKILL.md` §7). One-line widening
  of `gh_features` ahead of T03's substantive work. Hygiene WUs were
  designed for exactly this "the next WU is blocked on a small fix in a
  forbidden path." If you take this path, T03's depends_on becomes
  `[T03H]` and T03 reverts to "exactly two files."

I went with the bundle because the one-line widening does not block T03 —
T03 plans for it from the start and tests it. The hygiene pattern is for
*surprises* during a substantive WU's grind. But the call is yours.

### (2) T04's `code` gate verification is a fig-leaf

T04 produces a single markdown file (`SKILL.md`). The `code` gate set
(`tests`, `ruff`, `bandit`, `coverage`) does not exercise markdown. T04
"passes" verification trivially — the driver's automated check tells you
nothing about whether the skill is good. **Quality of T04's output is
human-judged at PR review.**

**Mitigation options:**
- **Accept this** (recommended for v0.1): mirror the existing skills
  (`pick-feature`, `draft-feature`) — they were also human-reviewed for
  quality. T04's ACs prescribe shape (frontmatter, mandatory sections,
  Method steps a-g, Hard rules, NOT-do, version line) so a reviewer has a
  falsifiable checklist.
- **Add a skill linter** — out of scope for gate 2. If you want one, draft
  it as a gate-3 WU or a follow-up feature.

### (3) Assumption made to proceed: issue bodies are well-formed

T03 AC 4 says it embeds `candidate["body"]` verbatim into WU-01. This
assumes real `specfuse:feature` issue bodies actually contain the five
mandatory sections (Context / Acceptance criteria / Do not touch /
Verification / Escalation triggers) at heading levels `lint_plan.py` will
accept (`^#+\s*<section>`).

**The handoff brief asserts this contract** (§2: "Issue body = the
five-section work-unit contract"), but I have not read the smoke target
issue (`example-org/example-app#287`) to confirm it actually follows the
contract. If it does not, T03's verbatim-embed strategy produces a
malformed WU-01 that `lint_plan.py` rejects when the adopted feature is
linted later — visible only at the smoke gate, not at gate 2's own
verification.

**Mitigation:** T03's escalation triggers handle this (block if body
structure varies). For a stronger guarantee, you could add an AC to T03
that requires it run `lint_plan` against the scaffolded folder AND assert
the five `^#+\s*` section headings exist in WU-01. T03 AC 6 already
requires lint_plan exit 0, which catches the missing-section case (the
linter checks `REQUIRED_SECTIONS` for `draft`/`pending`/`ready` WUs). So
this is largely covered — but only if the linter check correctly fires
against WU-01's draft status. Worth verifying in T03's tests.

---

## Roadmap anchor

Gate 2 directly serves the feature's `roadmap_goal`: *The loop can pick a
feature from a target repo's GitHub issues (specfuse:feature) and grind it
through its gate cycle.* Gate 1 delivered the read path (discovery + ID
grammar); gate 2 delivers the write path (adoption) — the missing half. After
gate 2, a human can `gh issue list → /adopt-feature → loop.py` end-to-end on
an offline-stubbed pipeline. Gate 3 (live `gh` smoke test + backend signals)
closes the loop on the real example-org/example-app#287.

**Goal-change escalation?** The gate-1 retrospective does NOT imply the
roadmap goal should change. Gate 1 went cleanly in one attempt per WU; the
"offline-first gate" principle (now promoted to LEARNINGS) reinforces the
existing skeleton. No escalation needed.

---

## Open questions (mapped to WUs)

### Q1. Should the `INIT-2026-0001/F06` smoke target be re-validated before gate 3? (affects G2-PLAN, then gate-3 smoke WU)

The handoff brief names `INIT-2026-0001/F06` (example-org/example-app #287)
as the smoke target. I did not verify the issue still exists or still has
labels `specfuse:feature` + `initiative:INIT-2026-0001` + `type:implementation`
+ `autonomy:review`. If the issue moved or its labels drifted, gate 3's
drafting will discover it. G2-PLAN's Context names this — it should re-check
before drafting gate 3's smoke WU.

### Q2. Should T04's skill present candidates limited to the top 5 by `number`? (affects T04)

T04 AC 2 step (d) says "capped at the top 5 by `number` (most recent issues
first)." I picked 5 arbitrarily, mirroring `pick-feature`'s "three is the
cap" principle adapted upward because a GitHub issue list is typically
busier than a roadmap. If 3 (matching pick-feature) is the right cap, edit
the AC. If "show all" is the right default, edit the AC. This is a UX call,
not a correctness call.

### Q3. Is the closing-WU 90+ numbering convention going to migrate into a binding rule before gate 3? (affects G2-PLAN's drafting of gate-3 closing WUs)

LEARNINGS `[FEAT-2026-0003/G1-LESSONS]` flagged this for promotion to a
binding rule or template. If you do not promote it, G2-PLAN will perpetuate
the convention by hand (file names `WU-98`..`WU-101` for gate-3 closing).
If you DO promote it (between now and gate 2's plan-next firing), G2-PLAN
should follow the new rule. No action required at gate 2 arming time, but
worth flagging because the work that follows-on from gate 2 will repeat the
convention.

### Q4. Does the test fixture for T03 need a third case (a candidate whose body lacks one of the five sections)? (affects T03)

T03's tests cover an orchestrated INIT candidate and a component-local FEAT
candidate. Neither test covers the malformed-body case. T03's escalation
triggers say "block if body structure varies," but the test does not
verify the linter actually rejects a malformed WU-01. If you want belt-and-
suspenders coverage of the assumption-made-to-proceed in **Flagged (3)**,
add an AC requiring a third test case (stubbed body missing
`Escalation triggers`) where `adopt_feature` still writes the folder but
`lint_plan` exits non-zero. This shifts the contract from "T03's tests
prove the happy path" to "T03's tests prove the failure mode too."

---

## Summary

Two substantive WUs (script + skill) + standard closing sequence, total six
WUs in gate 2. T03 carries the only non-obvious scope decision (4-file bundle
with a 1-line widening of gate-1 code) — that's where to look first at
review. T04's auto-verification is weak by design (markdown artifact); read
the SKILL.md the run produces with the same care you'd give a PR review.
Models hold sonnet for synthesis and opus for the next plan-next, same as
gate 1.
