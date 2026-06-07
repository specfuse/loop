# Gate 1 retrospective — FEAT-2026-0003

Feature: GitHub feature-pick for the loop  
Gate 1: The read path — orchestrated ID grammar + GitHub feature discovery  
Branch: `feat/FEAT-2026-0003-github-feature-pick`  
Date run: 2026-06-06 / 2026-06-07

---

## Context

This is gate 1 of the first real multi-gate feature run through the loop. The
retrospective is written against the `events.jsonl` slice (4 events: T01 start,
T01 complete, T02 start, T02 complete) and the commit diffs for the two
implementation WUs. The closing-sequence WUs (G1-RETRO through G1-PLAN) have not
yet been run; this file is produced by G1-RETRO.

---

## T01 — Admit orchestrated INIT-…/FNN[/TNN] correlation IDs

**Status:** done in 1 attempt  
**Duration:** ~3m30s (00:44:08 → 00:47:38 UTC)  
**Cost:** $0.547 | output tokens: 12,615 | cache read: 566k

### What worked

The WU was maximally specific about scope: "exactly three files"
(`lint_plan.py`, `correlation-ids.md`, `test_lint_correlation_id.py`), and
the AC listed 9 concrete test cases — each a string to match or reject — with
no ambiguity about what "admitted" or "rejected" meant. The agent hit every
criterion in one pass.

The regex implementation was correct on first attempt: top-level alternation
between the two namespace branches rather than trying to extend the existing
`FEAT-…` pattern with optional segments. The rule document now separates the
two namespaces clearly ("Component-local" / "Orchestrated") and documents the
origin-from-ID-root rule.

The escalation trigger ("if admitting INIT grammar would require changing how
`lint_plan.py` splits feature-vs-task IDs beyond the `CORRELATION_ID_RE`
pattern") was the right safety valve and did not fire — the change was
genuinely isolated to the single regex constant.

### What failed / concerns

Nothing failed. Minor observation: the combined regex is now 93 characters on
one line in the rule document — readable inline but will become unwieldy if a
third namespace is ever added. Not a problem for this feature; worth noting if
a future namespace (e.g. `TEAM-…`) is proposed.

### Missing or ambiguous rules/templates

None. The handoff doc (`docs/handoff-github-feature-pick.md` §2) specified the
grammar precisely enough that the agent needed to invent nothing. The WU's
"exactly three files" constraint prevented any scope drift.

---

## T02 — GitHub feature discovery (gh_features.py)

**Status:** done in 1 attempt  
**Duration:** ~4m22s (00:47:38 → 00:52:00 UTC)  
**Cost:** $0.676 | output tokens: 15,485 | cache read: 848k

### What worked

The WU specified the exact `gh issue list --json` field list (`number,title,
labels,url,body`) in the AC itself. This was the right call — omitting it
would have forced the agent to guess which fields to request and potentially
produce a default runner that doesn't match the test stubs. Explicit field
list = no ambiguity, no escalation.

The injectable runner pattern mirrored the loop's existing `dispatch_fn`/
`verify_fn` approach. The agent applied it correctly: `runner=None` sentinel
defaulted to `_default_runner`, making the stub path in tests identical in
shape to the live path. The `_default_runner` used an argument list (`["gh",
"issue", "list", ...]`) with `check=True` — bandit-clean as required.

The `_extract_label_value` helper is reusable and correctly handles labels
structured as `{"name": "initiative:INIT-2026-0001"}`.

### What failed / concerns

**CLI output delimiter not specified.** AC criterion 4 said "prints one line
per candidate: feature_id, task_type, autonomy, url" but did not specify the
separator. The agent chose tab (`\t`), which is machine-parseable. This was a
reasonable choice, but a future consumer of this CLI that expects space or
comma separation would need to change it. The WU should have said "tab-
separated" or "space-separated" to prevent this ambiguity propagating.

**`task_type` can be `None`.** The CLI prints `None` as a string when an issue
has no `type:` label. This is the correct Python `str()` of `None` in an
f-string but a consumer parsing the CLI output would see the literal string
`"None"` rather than an empty field. The WU did not specify what to print when
a field is absent; the library function correctly returns `None` (the Python
sentinel), but the CLI entrypoint should have normalized to an empty string or
a sentinel like `-`. Not a correctness bug in the library; a CLI ergonomics gap.

### Missing or ambiguous rules/templates

The handoff doc did not specify CLI output format details (delimiter, null
sentinel for optional fields). Everything else was sufficiently specified.

---

## Gate-level observations

### Gate-cutting

"Gate 1 = the read path, fully offline-testable" was the right cut. Both WUs:
- Required no live `gh` call (stubbed runner for T02, pure regex for T01)
- Produced artifacts that the verification gates could check without network
- Had no dependency on each other (ran sequentially but parallelizable)

This gate proved that "offline first" is a useful gate-cutting principle: when
the gate's entire scope can be unit-tested without external systems, it can be
verified deterministically and atomically. The live `gh` integration belongs
in a later gate (gate 3's smoke test).

### WU sizing

Both WUs were well-sized for 1-attempt completion:
- T01: 3 file changes, 9 test cases, bounded scope — completed in 3m30s
- T02: 2 new files (~325 lines total), 4 AC items — completed in 4m22s

Neither WU hit its escalation trigger. The "exactly N files" constraint in each
WU's Do-not-touch section was effective: the agent could not rationalize scope
creep.

### Whether the plan held

The plan held completely. PLAN.md's task graph (T01 independent of T02, both
blocking G1-RETRO) executed without deviation. The forward-design model (gate 1
details only gate 1's WUs; gate 1's plan-next will draft gate 2's WUs) is
proven at this gate boundary.

### Closing sequence

The four-WU closing sequence (RETRO → LESSONS → DOCS → PLAN) is enforced by
the linter and was present in the scaffold from the start. The WU-90+ numbering
convention for closing units is implicit in the PLAN.md notes ("90+ range so
they sort last") but is not written in any binding rule or template. If this
convention is to be followed by future `draft-feature` users, it should be
codified in the authoring guide or the WU template rather than left as a note.

### Token usage pattern

Both WUs show very high cache read (566k and 848k respectively) against a tiny
uncached input (14 and 19 tokens). This is the expected shape when the session
context is warm and the WU body fits in the prompt cache. The rising cache read
from T01 → T02 (566k → 848k) reflects T01's commit adding to the cached
context that T02 then read. No cost anomalies.

---

## Summary

Gate 1 went cleanly. Both implementation WUs finished in 1 attempt with no
escalations and no regressions. The plan held. The two gaps worth carrying
forward:

1. **CLI null-sentinel convention** — specify what to print when an optional
   field is absent (the library returning `None` is correct; the CLI rendering
   it as the string `"None"` is not).
2. **Closing-WU numbering convention** — write it in a binding rule or template
   rather than leaving it as a PLAN.md note.

The "offline-first gate" principle and the "exactly N files" Do-not-touch
constraint both proved their value here. Recommend promoting both to the
authoring guide (via G1-LESSONS).

---

# Gate 2 retrospective — FEAT-2026-0003

Feature: GitHub feature-pick for the loop  
Gate 2: The write path — adopt a GitHub issue into a feature folder  
Branch: `feat/FEAT-2026-0003-github-feature-pick`  
Date run: 2026-06-07

---

## Context

Gate 2 carried two substantive WUs: T03 (the `adopt_feature.py` scaffolding
script, its tests, and the one-line widening of `gh_features.list_features`
to expose `body`) and T04 (the `adopt-feature` skill SKILL.md). Both
completed in 1 attempt and in sequence (T04 depends on T03). The gate-2
review document (`GATE-02-REVIEW.md`), drafted by G1-PLAN (Opus), flagged
three concerns before arming: the 4-file bundle in T03, T04's fig-leaf
automated verification, and the assumption that real issue bodies are
well-formed. All three resolved without escalation.

This retrospective is written by G2-RETRO (WU-94), the first WU of gate 2's
closing sequence. G2-LESSONS (WU-95), G2-DOCS (WU-96), and G2-PLAN (WU-97)
have not yet executed at the time of writing; they are described from their
spec, not from execution evidence.

---

## T03 — Adopt a picked issue into a dispatchable feature folder (script)

**Status:** done in 1 attempt  
**Duration:** ~25m 32s (01:14:02 → 01:39:34 UTC)  
**Cost:** $2.117 | output tokens: 95,156 | cache read: 1.19M | cache creation: 88,643

### What worked

**The body-widening of `gh_features.list_features` ran completely clean.** The
change is exactly one line: `"body": issue.get("body", "")` added inside the
existing dict literal in `list_features` (gh_features.py:79). No second
`gh issue view` call was needed, no new public function was added, and the
gate-1 `_default_runner` already requested `body` in its `--json` field list —
the discard was the real bug. The "widen, not bypass" decision from
GATE-02-REVIEW.md was vindicated. The test assertion (`tests/test_gh_features.py`)
was added cleanly alongside.

**The "exactly four files" Do-not-touch constraint held.** T03 touched exactly
the four files declared in its WU: `adopt_feature.py` (new, 219 lines),
`tests/test_adopt_feature.py` (new, 260 lines), `gh_features.py` (widened
by 1 line), and `tests/test_gh_features.py` (1 assertion added). No scope
creep. The explicit file list in the Do-not-touch section is what prevented it.

**The malformed-body test case (AC 8e) was implemented correctly.** This case
was not in G1-PLAN's original draft of T03 — it was added to the WU via the
human's review of GATE-02-REVIEW.md Q4 ("does the test need a third case?").
The `TestMalformedBody` class verifies that `adopt_feature` still writes the
folder even when `body` is missing `Escalation triggers`, but `lint_plan.py`
exits non-zero on the result. This is the correct design: adopt writes
unconditionally and delegates quality enforcement to the linter.

**The injectable `runner` pattern transferred cleanly from T02.** The CLI test
(`TestCLIMain`) injects a stub runner using the same `runner(repo) -> list[dict]`
signature that `gh_features.py` defines. The stub accurately replicates the
label structure (`{"name": "specfuse:feature"}`, `{"name": "initiative:..."}`,
etc.) — the agent needed to read `gh_features.py`'s issue-parsing internals
before writing the test fixture, and did so correctly.

**`initiative: None` renders correctly.** When `candidate["initiative"]` is
`None`, the PLAN.md frontmatter omits the `initiative` key entirely
(`_plan_md` uses `if initiative is not None: fm_lines.append(...)`) per
G1-LESSONS' absent-field rule. The component-local test (`TestComponentLocalCandidate`)
asserts `self.assertNotIn("initiative", fm)`.

### What failed / concerns

**Output volume is a warning signal.** At 95,156 output tokens, T03 is the
largest single-WU output in this feature by a factor of 6x (T02, the prior
largest, produced 15,485). The WU had 8 ACs (0 through 7, with 8 having five
sub-items a-e), two new files totaling 479 lines, and a test suite requiring
intimate knowledge of `gh_features.py`'s label-parsing internals to write
correct stubs. The WU succeeded in 1 attempt, but this volume is at or near
the upper boundary of what Sonnet can reliably cover in one session without
drift. A future WU of similar scope should consider splitting at the
adoption-logic / test-coverage seam.

**The cross-gate commit remains ambiguous to future readers.** T03's squash
commit necessarily mixes "new adopt script" with "widen gate-1 module." A
reader diffing that commit sees two concerns: the new scaffolding logic and the
one-line gh_features fix. The decision to bundle (not use a hygiene WU T03H)
was the right call because the widening was not a surprise — T03 planned for it
from AC 0 — but the commit message must be explicit about the bundled intent.
The hygiene WU pattern exists for surprises during a substantive WU's grind;
this was not a surprise. The bundle was justified; the communication cost is
real.

**`_closing_wu()` generates placeholder-quality WU bodies.** The closing WU
template that `adopt_feature.py` generates for adopted features has generic
acceptance criteria ("The artifact for this unit exists and is substantive")
and generic escalation triggers. These are adequate scaffolding for gate 1's
closing WUs of any adopted feature, but a human or G1-PLAN will need to
substantially refine them before they are dispatchable. This gap was not
specified in T03's ACs — the WU asked for bodies that contain the five
mandatory sections, not bodies that are actionable. The templates are correct
in structure but weak in content.

### Missing or ambiguous rules/templates

The malformed-body test was a review addition, not in the original spec. This
suggests a gap in the authoring guide: "when a WU's acceptance criteria include
a linter integration, include a test case that proves the linter rejects a
known-bad artifact, not just the happy path." The test for the happy path
(lint_plan exits 0) was in the original spec; the failure-mode test (lint_plan
exits non-zero on a malformed body) required a review catch.

---

## T04 — Interactive pick-and-adopt skill

**Status:** done in 1 attempt  
**Duration:** ~2m 38s (01:39:34 → 01:42:12 UTC)  
**Cost:** $0.300 | output tokens: 8,237 | cache read: 211k | cache creation: 30k

### What worked

**The SKILL.md landed at the right shape and length.** At 157 lines, it is
longer than `pick-feature/SKILL.md` but shorter than `draft-feature/SKILL.md`,
which is appropriate for a 7-step flow with non-trivial hard rules. All six ACs
are met: frontmatter with `name: adopt-feature` and a descriptive `description:`;
a numbered Method section (7 steps a-g); Hard rules section; What this skill
does NOT do section; the result-contract pointer; a `**v0.1.**` version line.

**The active-feature guard (step 2) was implemented correctly.** T04 includes
the "Detect active work and respect it" step that mirrors `pick-feature`'s rule.
The guard requires an explicit user override before proceeding — consistent with
GATE-02-REVIEW.md's decision to mirror the existing rule.

**Step 6 correctly distinguishes GitHub issue `number` from the display index
`#`.** The skill explicitly documents: `where <issue-number> is the GitHub issue
number from the picked candidate row (not the display index #)`. This is a
subtle but real distinction — the display table shows rows 1-5 while the GitHub
number might be 287 — and the skill makes it explicit to avoid a human pasting
the row index into the command.

**The script-versus-programmatic invocation is both documented.** Step 3
provides both the programmatic (`from gh_features import list_features`) and the
CLI (`python3 .specfuse/scripts/gh_features.py <repo>`) paths, noting that the
programmatic route returns the full candidate dict including `body`. This is
useful because the skill invokes `adopt_feature.py` by CLI (step 6) but could
introspect candidates programmatically (step 3).

### What failed / concerns

**Automated verification tells nothing about substantive quality.** As
GATE-02-REVIEW.md (Flagged 2) predicted, the code gates (`tests`, `ruff`,
`bandit`, `coverage --fail-under=70`) pass trivially for a markdown artifact.
The driver's verification log says "pass" but cannot judge whether the 7-step
method is coherent, whether the Hard rules are complete, or whether the
not-do list is correct. This is not a T04 failure — it is an honest limitation
of the current verification architecture for skill WUs. The SKILL.md was
human-reviewed at PR time.

**The 5-candidate cap is an arbitrary constant.** T04 AC 2(d) specifies "capped
at the top 5 by `number`" — a UX constant that mirrors GATE-02-REVIEW.md Q2's
resolution ("picked 5 arbitrarily, mirroring pick-feature's three-is-the-cap
principle adapted upward"). This value will need revisiting once the skill is
used against a real repo with many `specfuse:feature` issues open.

### Missing or ambiguous rules/templates

No skill linter exists. T04's ACs prescribe shape (frontmatter keys, section
order, mandatory steps), which is a falsifiable checklist at review time, but
the check is entirely manual. The GATE-02-REVIEW.md flagged this as "accept for
v0.1" — that posture was correct given gate 2's scope, but a skill linter is
the obvious gate-3 or follow-on investment if skill quality becomes a
consistency problem.

---

## G2-RETRO — Gate-2 retrospective (this WU)

**Status:** executing (1st attempt)  
**Design:** sonnet-4-6, mirrors G1-RETRO's model choice.

The WU reads the gate-2 events slice and the produced artifacts and appends a
`## Gate 2` section to `RETROSPECTIVE.md`. Escalation: if the event log was too
sparse (zero successful T03 or T04 attempts), the WU would append an
"insufficient evidence" note rather than invent findings. Both T03 and T04
completed in 1 attempt, so the log is adequate.

*Execution data not available at time of writing — this is the current session.*

---

## G2-LESSONS — Gate-2 lessons

**Status:** pending (0 attempts)  
**Design:** sonnet-4-6, appends generalizable entries to `.specfuse/LEARNINGS.md`.

Will promote the subset of this retrospective that changes how a future WU is
written. The bar from gate 1's lessons holds: feature-specific noise stays here;
only entries that would change a future plan get promoted. Likely candidates
from gate 2: the output-volume warning signal for large bundled WUs, the
failure-mode test pattern for linter integrations, and the "closing WU bodies
need substantive ACs, not placeholder ACs" observation from `_closing_wu()`.

*No execution data — fires after this WU completes.*

---

## G2-DOCS — Gate-2 documentation update

**Status:** pending (0 attempts)  
**Design:** sonnet-4-6, reconciles surrounding docs and roadmap status with
what gate 2 delivered.

Will update `docs/handoff-github-feature-pick.md` §3 if the as-built adopt
flow diverged from the planned shape (e.g. the CLI surface, the file count
constraint), update the feature's row in `.specfuse/roadmap.md` to note gates
1 and 2 done, and update any CLAUDE.md cross-references that describe the
adopt capability. Does not edit adopt_feature.py or SKILL.md.

*No execution data — fires after G2-LESSONS completes.*

---

## G2-PLAN — Gate-2 plan-next

**Status:** pending (0 attempts)  
**Design:** claude-opus-4-7 (forward design, mirrors G1-PLAN's model choice;
runs last in the closing sequence so it can consume both retrospective and
lessons before drafting gate 3).

Will draft gate 3's WUs ("report back + smoke": `GitHubBackend(Backend)` label
transitions + end-to-end smoke of `INIT-2026-0001/F06`), populate PLAN.md's
gate 3 work_units list, and write `GATE-03-REVIEW.md` weighted toward doubt.
Applies the offline-first gate principle: gate 3 should separate offline backend
wiring from the live `gh` smoke call into distinct WUs, mirroring gate 1's
T01/T02 independence. Must also handle the terminal-case: gate 3 is the last
gate in the skeleton, so its plan-next has no further gate to draft.

Key open questions for G2-PLAN to resolve: whether `RestoManagerApp/Backend#287`
still exists and still has the expected labels; whether the `Backend` seam in
`loop.py` is wide enough for label-transition signals without forking the driver;
and whether the 90+ closing-WU numbering convention should be promoted to a
binding rule before gate 3's closing WUs are numbered.

*No execution data — fires after G2-DOCS completes.*

---

## Gate-2 observations

### Gate-cutting: did "the write path — adopt" cohere as one gate?

Yes, but with an asterisk. T03 and T04 together deliver a complete adopt
capability: a human can `python3 adopt_feature.py <repo> <number>` or invoke
`/adopt-feature` and get a dispatchable feature folder. The gate's definition
of done ("a picked issue becomes a dispatchable loop feature folder via a
scaffolding script plus an interactive pick-and-adopt skill") is satisfied.

The asterisk: the gate holds because the issue-body-as-WU-contract assumption
holds for well-formed issues. For malformed issue bodies, the adopted folder
will have a WU-01 that `lint_plan` rejects — the gate passes, but the adopted
feature is not immediately dispatchable. This is correct-by-design
(adopt-then-lint rather than lint-and-reject-before-adopt) but the seam is
visible. Gate 3's smoke test with a real issue will confirm whether the
assumption holds in practice.

### WU sizing: T03 touched four files — was that the right boundary?

The boundary held mechanically (the agent didn't drift) but the 95k output
token count signals that T03 was at the upper edge of what a single WU can
reliably contain. For context:

| WU | Files | Output tokens | Duration | Cost |
|----|-------|--------------|----------|------|
| T01 (gate 1) | 3 | 12,615 | 3m30s | $0.547 |
| T02 (gate 1) | 2 | 15,485 | 4m22s | $0.676 |
| T03 (gate 2) | 4 | 95,156 | 25m32s | $2.117 |
| T04 (gate 2) | 1 | 8,237 | 2m38s | $0.300 |

T03 is 6x T02's output. The 4-file constraint was the right shape for this WU
because the four files are tightly coupled (the test stubs must replicate
gh_features.py's label structure exactly), but a future WU with similar scope
should consider whether the `test_adopt_feature.py` coverage (5 test classes,
14 test methods, 260 lines) could be a separate `T03-test` WU authored after
T03's core script lands. The one-line gh_features widening plus its test
assertion could also have been a hygiene WU T03H, keeping T03 at exactly 2
files. The bundle worked here; it is not the safe default for WUs of this
density.

### Whether the plan held as drafted by G1-PLAN

The plan held completely. GATE-02-REVIEW.md's design — two substantive WUs
(script + skill) in dependency order, followed by a four-WU closing sequence,
models chosen as sonnet for both T03 and T04 and sonnet for G2-RETRO through
G2-DOCS and opus for G2-PLAN — executed without deviation. The three flagged
concerns from GATE-02-REVIEW.md all resolved at the levels G1-PLAN predicted:

1. **T03's 4-file bundle**: accepted, worked, commit message carries the context.
2. **T04's fig-leaf automated verification**: accepted, SKILL.md is human-reviewed.
3. **Issue-body assumption**: mitigated by AC 8e (malformed-body test), which
   was added from Q4 of the review document — confirming the review process is
   read and actionable, not ceremonial.

The open questions from GATE-02-REVIEW.md — whether `INIT-2026-0001/F06` still
has the expected labels (Q1), whether the 5-candidate cap is right (Q2), whether
the 90+ closing-WU convention gets promoted to a binding rule (Q3), and whether
a malformed-body test is needed (Q4) — were handled as follows: Q3 and Q4 were
acted on at gate 2 (Q4: AC 8e added; Q3: still not a binding rule, G2-PLAN will
decide). Q1 and Q2 are forwarded to G2-PLAN / gate 3 as open questions.

**The forward-design model is proven again.** G1-PLAN drafted gate 2 correctly
from gate 1's artifacts alone. G2-PLAN, running now from gate 2's artifacts, is
in the same position for gate 3. The multi-gate proof holds.
