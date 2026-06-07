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

---

# Gate 3 retrospective — FEAT-2026-0003

Feature: GitHub feature-pick for the loop  
Gate 3: Report back + end-to-end smoke  
Branch: `feat/FEAT-2026-0003-github-feature-pick`  
Date run: 2026-06-07

---

## Context

Gate 3 carried three substantive WUs: T05 (`Backend` seam widening with
lifecycle hooks), T06 (`GitHubBackend(Backend)` implementation + factory), and
T07 (live end-to-end smoke against `RestoManagerApp/Backend#287`). T05 and T06
were dispatched via the driver (offline, deterministic). T07 was executed
**out-of-loop by the human operator** — a deliberate gate-3 arming decision to
keep production-issue mutation under direct control.

The events.jsonl gate-3 slice:

| Event | Timestamp (UTC) | Detail |
|---|---|---|
| T05 task_started | 02:23:09 | — |
| T05 task_completed | 02:26:50 | 1 attempt, $0.651, 11,256 output tokens |
| T06 task_started | 02:26:50 | — |
| T06 task_completed | 02:32:46 | 1 attempt, $0.827, 19,108 output tokens |
| gate_reached (gate 3) | 02:32:47 | Fired after T05+T06; T07 is out-of-loop |

T07 is not in events.jsonl (human-run, no driver events). The evidence record
is the smoke journal `SMOKE-INIT-2026-0001-F06.md` and the commit sequence on
the feature branch:

- `c15b400` — feat: Widen the Backend seam (T05)
- `77d394e` — feat: GitHubBackend(Backend) implementation (T06)
- `a363060` — chore: gate 3 awaiting_review
- `370a517` — test(smoke): live smoke — discovery/adopt/report-back PASS; lint finding (T07)
- `2e3e2de` — chore: T07 done, reopen gate 3 for closing sequence

The closing-sequence WUs (G3-RETRO through G3-PLAN) have no events.jsonl data;
they fire sequentially after gate 3 is re-opened. G3-RETRO is the current session.

---

## T05 — Widen the Backend seam with feature/gate lifecycle hooks

**Status:** done in 1 attempt  
**Duration:** ~3m41s (02:23:09 → 02:26:50 UTC)  
**Cost:** $0.651 | output tokens: 11,256 | cache read: 987k | cache creation: 49k

### What worked

**The seam shape was correct on the first attempt.** Three lifecycle hooks
(`on_feature_start`, `on_gate_passed`, `on_feature_complete`) plus a module-
level factory `make_backend(feat_fm)` are exactly the right contract surface
for T06's `GitHubBackend` subclass. T06 consumed T05's seam without any
modification to T05's signatures — the seam was not under-designed.

**The "exactly two files" constraint held cleanly.** The WU produced exactly
`loop.py` and a new `tests/test_backend.py` — the agent chose the new-test-
module path (declaring it in the RESULT block as required) rather than
complicating `tests/test_loop.py`. No scope creep.

**The `on_feature_complete` call-site location was handled correctly.** GATE-03-
REVIEW.md's Flagged 3 warned that `run()` has four exit paths and
`on_feature_complete` should fire only on the "all gates passed" path. The
agent found loop.py:590-591 as the correct anchor without escalating — the
line-number anchoring in the WU's AC 5 provided sufficient precision.

**Output volume well within range.** At 11,256 tokens, T05 is the smallest
implementation WU in the feature. The mechanical nature of the task (add three
stubs + a factory + tests) maps correctly to this size.

### What failed / concerns

Nothing failed. One minor observation: `on_gate_passed` is wired as a no-op
v0.1 stub. GATE-03-REVIEW.md Q3 raised the YAGNI counter-argument (if no gate-
level label transition is needed now, the hook is dead code). The stub was kept
on the principle that adding a hook later requires re-touching the seam while
adding behavior to an existing hook is non-breaking. The question was not
escalated — the WU spec made the choice, and the agent followed it.

### Missing or ambiguous rules/templates

None. The exact line-range anchors in the WU (loop.py:586, loop.py:590-591,
loop.py:748) prevented the agent from drifting to wrong call-sites.

---

## T06 — GitHubBackend(Backend) implementation — label-transition state backend

**Status:** done in 1 attempt  
**Duration:** ~5m56s (02:26:50 → 02:32:46 UTC)  
**Cost:** $0.827 | output tokens: 19,108 | cache read: 1.14M | cache creation: 53k

### What worked

**The label-scheme correction (from G2-PLAN's draft to the orchestrator's
canonical namespace) was caught and applied at arming time.** G2-PLAN's
GATE-03-REVIEW.md proposed `loop:in-progress` / `loop:complete` labels,
invented from first principles. At gate-3 arming time, the orchestrator's docs
(`RestoManagerApp/orchestrator/docs/naming-convention.md §5.1` and
`shared/schemas/labels.md`) confirmed the canonical lifecycle namespace is
`state:*` — already in use on `#287` as `state:ready`. T06's WU spec was
updated before dispatch to use `state:in-progress` (add) / `state:ready`
(remove) on `on_feature_start`, and `state:done` (add) / `state:in-progress`
(remove) on `on_feature_complete`. The smoke confirmed these transitions fired
exactly. This is the review-before-arm checkpoint working as designed.

**The "exactly three files" constraint held.** `gh_backend.py` (new),
`tests/test_gh_backend.py` (new), and the `make_backend` body edit in
`loop.py` — exactly the three declared files.

**Offline-first held.** No network call fired during driver verification. The
injectable `_default_runner` pattern (mirroring `gh_features.py` lines 22-36)
enabled full coverage without `gh` on the test path.

**Factory selection by `source_issue_url` is the correct discriminator.**
The WU confirmed the design decision from GATE-03-REVIEW.md: selecting by
`source_issue_url` is more direct than selecting by ID origin (`INIT-…` prefix)
because `source_issue_url` is the exact signal that "this feature was adopted
from a real GitHub issue we can label." An `INIT-…/FNN` folder created by hand
(bypassing `adopt_feature.py`) would not carry a `source_issue_url` and should
get plain `Backend`. The malformed-URL graceful fallback was implemented and
tested per G2-LESSONS' failure-mode test pattern.

**Output volume well within range.** 19,108 tokens — large relative to T05
(11k) and T01/T02 (~13-16k each) but far below T03's 95k danger zone. The WU
delivered one new module, one test file, and one function-body edit.

### What failed / concerns

No failures during the driver run. One concern carried forward: the
`on_gate_passed` no-op stub passes the `check=True` subprocess call zero times,
which means if a future maintainer adds gate-level label logic, they will also
need to add test coverage that was not scaffolded here. This is an intentional
gap (the stub's docstring says why), but a future WU adding gate-level behavior
needs to remember to add the corresponding test.

### Missing or ambiguous rules/templates

The label-scheme gap (G2-PLAN invented labels without checking orchestrator
docs) is the clearest example in this feature of a review check catching a
design error before dispatch. GATE-03-REVIEW.md Flagged 2 named it; the human
acted on it at arming time. No rule currently requires "verify label names
against a cross-repo contract before locking WU ACs" — this check was
discretionary. A future WU involving cross-repo label contracts should have an
explicit pre-arm verification step in its WU spec.

---

## T07 — Live end-to-end smoke (out-of-loop, human-operated)

**Status:** done (human-operated, out-of-loop by gate-3 arming decision)  
**Evidence:** `SMOKE-INIT-2026-0001-F06.md`

### What worked

**Discovery — PASS.** `python3 .specfuse/scripts/gh_features.py
RestoManagerApp/Backend` returned 13 `specfuse:feature` candidates. Issue #287
was parsed correctly:

```
INIT-2026-0001/F06	implementation	review	https://github.com/RestoManagerApp/Backend/issues/287
```

All four fields (`feature_id`, `task_type`, `autonomy`, `url`) were correctly
extracted from title + labels.

**Adopt (folder creation) — PASS.** `python3 .specfuse/scripts/adopt_feature.py
RestoManagerApp/Backend 287` created:

```
.specfuse/features/INIT-2026-0001-F06-conform-publishroster-to-validated-spec/
```

The filesystem-safe `INIT-2026-0001/F06` → `INIT-2026-0001-F06` slug encoding
worked. The folder, WU-01 (with issue body embedded), and closing-sequence WUs
were written.

**Report-back — PASS.** The full label-transition sequence fired correctly
against the live GitHub API:

| Step | gh call | labels after |
|---|---|---|
| BEFORE | — | `state:ready` + 4 stable labels |
| `on_feature_start` | `gh issue edit 287 --add-label state:in-progress --remove-label state:ready` | `state:in-progress` + 4 |
| `on_feature_complete` | `gh issue edit 287 --add-label state:done --remove-label state:in-progress` | `state:done` + 4 |
| restore | `gh issue edit 287 --add-label state:ready --remove-label state:done` | `state:ready` + 4 |

`on_gate_passed` fired zero `gh` calls (confirmed v0.1 no-op). `make_backend`
selected `GitHubBackend` for the `source_issue_url` frontmatter and plain
`Backend` otherwise. **#287 fully restored to pre-smoke label state — no
residue.**

### What failed / concerns

**Adopted-folder lint — FAIL (section-heading format gap).** `lint_plan.py
.specfuse/features/INIT-2026-0001-F06-conform-publishroster-to-validated-spec`
reported 5 missing sections: `Context`, `Acceptance criteria`, `Do not touch`,
`Verification`, `Escalation triggers`.

Root cause: **not** missing sections. Issue #287's body contains all five, but
as Markdown ATX headings (`## Context`, `## Acceptance criteria`, etc.). The
loop's `lint_plan.py` section detector matches `^(\**)<section>` (bold or
plain), and does NOT recognize `## ATX` headings. An orchestrator issue body
embedded verbatim by `adopt_feature.py` therefore fails the linter despite
being structurally complete.

This is a **section-heading-format contract gap** between the two surfaces:

- Orchestrator issue bodies use ATX headings (`## Context`).
- The loop's WU template and linter use bold-preamble (`**Context.**`).

This was a known open question: GATE-02-REVIEW.md §3 flagged that "issue bodies
are well-formed five-section WUs the linter accepts" was an assumption; GATE-03-
REVIEW.md Q5 carried it forward. The smoke surfaced it as a real, specific,
reproducible mismatch. The capability's core paths (discovery, adopt, report-
back) work; a clean end-to-end grind is blocked until this is resolved.

**No escalation triggered** at smoke time. The finding is documented in the
journal and forwarded to G3-PLAN for branch decision (widen `lint_plan.py` vs
normalize headings in `adopt_feature.py` vs fix the orchestrator template).

**Recommended option from journal:** broaden `lint_plan.py` section detection
to accept both `^(#+\s*)` ATX headings and the existing `^(\**)` bold/plain
pattern. ATX is the more standard markdown; the loop should accept what real
issue bodies use.

### Missing or ambiguous rules/templates

The smoke confirmed that the "issue-body contract" was underspecified at T03
authoring time: the WU tested the happy path (section present) and the
malformed case (section absent entirely), but the third case — "section present
but in a different heading format" — was not anticipated. A future adopt WU
should explicitly specify which heading formats the linter accepts.

No rule governs "verify cross-repo format contracts (heading style, field
naming) against the other surface's actual examples before writing the
adapter." This check is discretionary; T07's safety preamble covers label-state
checks but not format-contract checks. The smoke journal produced the evidence
gap-detection requires.

---

## G3-RETRO — Gate-3 retrospective (this WU)

**Status:** executing (1st attempt)  
**Design:** sonnet-4-6, appends Gate 3 section to RETROSPECTIVE.md.

This WU is the current session. The events.jsonl has no G3-RETRO data at time
of writing; the WU reads the gate-3 event slice, the commits, the smoke
journal, the WU specs, and the GATE-03-REVIEW.md to synthesize against concrete
evidence.

*Execution data not available at time of writing — this is the current session.*

---

## G3-LESSONS — Gate-3 lessons

**Status:** pending (0 attempts)  
**Design:** sonnet-4-6, appends generalizable entries to `.specfuse/LEARNINGS.md`.

Will promote the subset of this retrospective that changes how a future WU is
written. Likely candidates: the label-scheme cross-repo verification gap (check
the other surface's actual label names before locking WU ACs), the section-
heading-format contract gap (specify heading format in adopt WU specs), and
the review-before-arm checkpoint's catch of G2-PLAN's `loop:*` invention.

*No execution data — fires after this WU completes.*

---

## G3-DOCS — Gate-3 documentation update

**Status:** pending (0 attempts)  
**Design:** sonnet-4-6, reconciles surrounding docs and roadmap with gate 3's
deliverables. Will update `docs/handoff-github-feature-pick.md` with the
adopt-step heading-format finding, update the feature's roadmap row status, and
add the smoke journal as the live-evidence artifact reference.

*No execution data — fires after G3-LESSONS completes.*

---

## G3-PLAN — Gate-3 plan-next (terminal case)

**Status:** pending (0 attempts)  
**Design:** claude-opus-4-7. Terminal-case handler: branch-A (feature-arc
retrospective + closure) if the smoke finding is bounded and a follow-on WU or
`FEAT-2026-0004` can own the `lint_plan.py` fix; branch-B (extend PLAN.md with
a gate 4) if the evidence demands it. The lint finding is likely a gate-4 or
follow-on feature, not a feature-reopening condition — branch-A is the expected
outcome, but the call belongs to G3-PLAN after reading this retrospective and
G3-LESSONS.

*No execution data — fires after G3-DOCS completes.*

---

## Gate-3 observations

### Gate-cutting: did "report back + smoke" cohere as one gate?

Yes. "Report back + smoke" is a single logical milestone: the deliverable is
a `GitHubBackend` that emits observable signals AND a live confirmation that
the signals reach the real GitHub API. Splitting into two gates (offline wiring
vs smoke) would have been defensible — and T05+T06+T07's internal offline/live
split already mirrors that boundary — but the gate-level granularity is correct
because both offline wiring and live smoke are needed before the roadmap goal
is evaluable. You cannot claim "report-back works" from T05+T06 alone; only
T07 closes that claim.

T07's out-of-loop execution did not create a gate-structure problem. The WU was
always designed to be human-operated; the gate boundary just means T05+T06
verify before T07 runs. The alternative (T07 as its own gate-4) would add a
gate just to wrap a single human-run step, which is overhead without benefit
at this scope.

**If gate-4 would make sense:** only if the lint-finding fix (broaden
`lint_plan.py`) needs to be verified against another live smoke. That is a
bounded scope appropriate for a gate-4 or a `FEAT-2026-0004` follow-on; the
decision belongs to G3-PLAN.

### WU sizing: did the three-WU split hold under verification?

Yes, cleanly. Token profile:

| WU | Output tokens | Duration | Cost |
|----|-------------|----------|------|
| T05 (seam widening) | 11,256 | 3m41s | $0.651 |
| T06 (GitHubBackend) | 19,108 | 5m56s | $0.827 |
| T07 (live smoke) | n/a (human) | — | — |

Neither T05 nor T06 approached the 80k+ danger zone flagged by G2-LESSONS. The
three-WU split was the explicit lesson from T03's 95k output: separate the seam
widening (T05), the subclass implementation (T06), and the live validation (T07)
so no single WU carries both the implementation and its live-API proof. The
split worked exactly as intended.

The T05→T06 handoff was clean: T06 consumed T05's seam without modifications.
This confirms the seam was correctly designed at T05 time — the fear from
GATE-03-REVIEW.md §3 (that `on_feature_complete` might not have a clean
call-site) did not materialize.

### Whether the plan held as drafted by G2-PLAN

The plan held with one substantive correction and zero escalations:

**What was corrected:** G2-PLAN's GATE-03-REVIEW.md proposed `loop:in-progress`
/ `loop:complete` as the lifecycle label names. The orchestrator's docs
(`naming-convention.md §5.1`, `labels.md`) confirmed the canonical scheme is
`state:*` (`state:ready → state:in-progress → state:done`). T06's WU spec was
updated to the canonical names before dispatch. The smoke confirmed the
corrected names are what `#287` carries and what `GitHubBackend` transitions.
GATE-03-REVIEW.md Flagged 2 explicitly named "check the orchestrator's poller
spec before arming" as the resolution path — the path was taken.

**The three flagged risks from GATE-03-REVIEW.md, resolved:**

1. **T07 mutates a real production issue (Flagged 1):** Out-of-loop + safety
   preamble + cleanup AC mitigated the risk. #287 was fully restored.
2. **Label-scheme coordination (Flagged 2):** Caught and corrected at arming
   time. The design error (invented labels) was upstream in G2-PLAN; the
   review process caught it before any code was dispatched.
3. **Backend seam call-site assumption (Flagged 3):** T05 found the correct
   anchor (loop.py:590-591) without escalation. The four exit-path analysis in
   the review document was accurate; the agent implemented it correctly.

**Open question Q5 materialized as predicted:** The section-heading-format
mismatch was flagged in GATE-03-REVIEW.md Q5 ("if #287's body is malformed")
and did materialize — though "malformed" was the wrong framing; the body is
well-formed in Markdown, just using ATX headings instead of the loop's bold-
preamble convention. The forwarding from gate 2 → gate 3 review → smoke
journal is the forward-design model producing a concrete, grounded finding
rather than a theoretical risk.

---

## Multi-gate proof

### Did plan-next drafting produce three coherent, dispatchable gates?

Yes. The evidence:

**Gate 1 → gate 2:** G1-PLAN (Opus, 01:00-01:08 UTC, 37,976 output tokens)
drafted gate 2's two WUs (T03 and T04) from gate 1's retrospective and lessons.
Gate 2 dispatched and completed both WUs in 1 attempt each. The three
pre-arm concerns from GATE-02-REVIEW.md (T03's 4-file bundle, T04's fig-leaf
automated verification, malformed-body assumption) all resolved — one
(malformed-body test) was acted on as AC 8e, strengthening T03 before dispatch.

**Gate 2 → gate 3:** G2-PLAN (Opus, 01:57-02:05 UTC, 35,861 output tokens)
drafted gate 3's three WUs (T05, T06, T07) and the GATE-03-REVIEW.md. Gate 3
dispatched T05 and T06 in 1 attempt each and ran T07 out-of-loop with a PASS
on the core paths and a concrete finding on the lint contract. The one design
error (label-scheme invention) was caught by the review-before-arm checkpoint
G2-PLAN itself named as the first action under Flagged 2.

**Gate 3 → terminal case (G3-PLAN):** G3-PLAN is pending, but the evidence
it will consume — this retrospective, the smoke journal, and G3-LESSONS — is
coherent and grounded. G3-PLAN will choose branch-A (close with feature-arc
retrospective) or branch-B (extend with gate 4 for the lint fix).

### What does the evidence say about the forward-design move?

The dogfood was set up to test whether a `plan-next` WU can draft the next
gate from only the prior gate's retrospective + lessons — no human narrative,
no re-reading of all prior artifacts. The evidence:

- G1-PLAN drafted gate 2 correctly.
- G2-PLAN drafted gate 3 correctly in shape, with one first-principles label
  scheme that needed a cross-repo correction at arming time.
- Both plan-next WUs were Opus-4-7; both consumed ~36-38k output tokens and
  ~2.3-2.4M cache-read tokens.

The forward-design move works at gate scope. The one correction (label names)
was not a structural failure of the plan — G2-PLAN named the uncertainty,
flagged the check, and the check was performed. The plan-next drafting cycle is
sound; it requires the human-in-the-loop to perform the cross-repo verification
steps that plan-next correctly names but cannot execute itself.

### Was the roadmap goal met?

**Partially.** PLAN.md's roadmap goal: *"The loop can pick a feature from a
target repo's GitHub issues (specfuse:feature) and grind it through its gate
cycle, alongside today's locally-authored features."*

- **Pick (discovery + adopt):** ✓ Fully proven live. `gh_features.py` finds
  `specfuse:feature` issues; `adopt_feature.py` creates a dispatchable folder.
- **Report back:** ✓ Fully proven live. `GitHubBackend` transitions
  `state:ready → state:in-progress → state:done` on the real GitHub issue.
- **Grind through the gate cycle:** ✗ Not yet end-to-end clean. The adopted
  folder fails `lint_plan.py` due to the ATX-heading format gap. The folder
  cannot be dispatched to the loop without first resolving the section-detector
  contract.

The capability is operational for three of four mechanisms. The blocking gap
is in a single linter detection rule, not in the core architecture. Discovery,
adopt, and report-back are proven correct against a real GitHub issue. The
`lint_plan.py` fix is a bounded follow-on; G3-PLAN will declare whether it
belongs in a gate 4 or a `FEAT-2026-0004`.

---

# Feature-arc retrospective — FEAT-2026-0003

Feature: GitHub feature-pick for the loop
Branch: `feat/FEAT-2026-0003-github-feature-pick`
Arc duration: 2026-06-06 → 2026-06-07
Author: `FEAT-2026-0003/G3-PLAN` (Opus), synthesizing across the three gate
retrospectives, the smoke journal, the three `[FEAT-2026-0003/...]` LEARNINGS
sets, and the handoff brief.

---

## Roadmap-goal verdict — NOT MET; gate 4 follows

PLAN.md `roadmap_goal`: *"The loop can pick a feature from a target repo's
GitHub issues (specfuse:feature) and grind it through its gate cycle,
alongside today's locally-authored features."*

Four mechanisms compose the goal. Three proved out live against
`RestoManagerApp/Backend#287` (`INIT-2026-0001/F06`):

| Mechanism | Status | Evidence |
|---|---|---|
| Pick (discovery) | ✓ | `SMOKE-INIT-2026-0001-F06.md` — 13 features enumerated, #287 row parsed correctly |
| Adopt (scaffold) | ✓ | Smoke journal — `INIT-2026-0001-F06-conform-publishroster-to-validated-spec/` written, body embedded |
| Report back | ✓ | Smoke journal — `state:ready → in-progress → done → ready` fired exactly, fully reverted, no residue |
| **Grind through the gate cycle** | ✗ | Adopted folder fails `lint_plan.py`: WU-01 reports 5 missing sections because #287's body uses ATX (`## Context`) headings, the linter's section detector matches only `^(\**)<section>` |

**The gap is precisely scoped.** Not architecture, not a seam, not a backend
contract — one regex in `lint_plan.py` (loop-side) OR a heading-normalisation
pass in `adopt_feature.py` (loop-side) OR an orchestrator-side template
change (other surface). The smoke journal recommends option 1 (broaden the
linter — ATX is the more standard markdown).

**Why this is not "close enough."** A dispatchable adopted folder that
fails `lint_plan.py` on its very first WU cannot be ground. The roadmap
verb is "grind through its gate cycle" — that grind is exactly what the
linter blocks. Closing the feature with the gap unfixed would ship a
capability that demos in three steps and stalls on the fourth, contradicting
its own roadmap statement.

**Why gate 4 (not FEAT-2026-0004).** The fix is one regex widening + tests
+ one re-smoke against the already-adopted `INIT-2026-0001-F06-…` folder
(no second `gh` mutation of #287 required). Smaller than any of gates 1-3.
Closing it inside this feature's branch keeps the proof contiguous: the
smoke journal that produced the finding, the adopted folder under verification,
and the linter fix all live on one branch with one PR. Splitting into
`FEAT-2026-0004` would re-discover the same issue from scratch, re-arm
discovery+adopt evidence the loop already has on hand, and lose the direct
"this regex caused that lint failure" linkage. The escalation trigger
("scope large enough to be its own feature") does not fire — this is
hours of work, not a feature's worth.

---

## Did the multi-gate forward-design move work?

This was the first multi-gate feature run through the loop and the first
empirical test of `plan-next` as a forward-design mechanism. The result is
**yes, with one named blind spot the methodology now has a rule for.**

### Each gate delivered what the prior gate's plan-next claimed

**Gate 1 (read path).** Author: human (`draft-feature`). Outcome: T01
admitted `INIT-…/FNN` IDs across rule + linter + tests in 1 attempt; T02
shipped `gh_features.py` with an injectable runner in 1 attempt. No
escalations. Plan held verbatim. The two gaps it raised (CLI
null-sentinel convention, closing-WU numbering convention) were promoted to
LEARNINGS by G1-LESSONS and consumed by every WU after.

**Gate 2 (write path — adopt).** Author: `G1-PLAN` (Opus). Outcome: T03
shipped `adopt_feature.py` (4 files, including the planned one-line widening
of gate-1's `gh_features.list_features` to expose `body`) in 1 attempt;
T04 shipped the `adopt-feature` SKILL.md in 1 attempt. No escalations.
GATE-02-REVIEW.md flagged three pre-arm risks (the 4-file bundle, T04's
fig-leaf automated verification, the malformed-body assumption); all three
resolved at the levels predicted. The malformed-body test (AC 8e of T03)
was added at arming time from Q4 of the review — **the review process
demonstrably edits a WU's ACs**, not ceremonial.

**Gate 3 (report back + smoke).** Author: `G2-PLAN` (Opus). Outcome: T05
widened the `Backend` seam (3 hooks + factory) in 1 attempt; T06 shipped
`GitHubBackend` against a stubbed runner in 1 attempt; T07 (out-of-loop
human-operated) ran the live smoke. The three review-document Flagged
risks (production-issue mutation, label-scheme coordination, seam call-site
assumption) all resolved without escalation. The Q5 carry-forward (issue
body well-formedness) materialised exactly as the gap that triggers gate 4.

### Concrete examples of forward-design — review questions becoming WU AC text

The forward-design proof is in the *traceable* edits from a gate review to
the next gate's WU body:

- **GATE-02-REVIEW.md Q4** ("does the test need a third case [malformed
  body]?") became **T03 AC 8e** — the `TestMalformedBody` class verifying
  that adopt writes the folder unconditionally but `lint_plan.py` rejects
  the result. T03 implemented it in the first attempt.
- **GATE-03-REVIEW.md Flagged 2** ("the label scheme decision is locked
  here but is a contract with the orchestrator") prompted the cross-repo
  check at arming time that found `state:ready` already in use, replacing
  G2-PLAN's invented `loop:in-progress`/`loop:complete` with the canonical
  `state:*` namespace. **T06's AC 3 was edited before dispatch** — the
  forward-design caught its own error through the review checkpoint.
- **GATE-03-REVIEW.md Flagged 3** ("`run()` has four exit paths") supplied
  the specific anchor `loop.py:590-591` for `on_feature_complete`. T05 hit
  the correct call-site in 1 attempt with zero escalation.
- **GATE-03-REVIEW.md Q5** ("if #287's body is malformed") explicitly
  predicted what gate 4 now owns. The prediction was correct in *shape*
  (an issue-body-format gap) and wrong in *framing* (the body is well-
  formed in Markdown, just using ATX headings). The forward-design surfaced
  the risk; the live smoke refined what the risk actually was.

### The one named blind spot — codified in `[FEAT-2026-0003/G3-LESSONS/multi-gate]`

`plan-next` cannot read other repos. Every cross-repo contract a plan-next
WU touches (label namespace, API field names, event schemas, shared
constants) gets invented from first principles unless the WU instructs
the human to verify before arming. G2-PLAN's `loop:*` invention proved
this in the smallest possible way — the human's pre-arm check overturned
it cleanly. The rule (every plan-next gate review must list a
"Cross-repo contracts" section with authoritative source + a check-box)
is now in LEARNINGS as the systemic mitigation. **Gate 4's review document
will be the first to test the rule prospectively.**

---

## What carries forward to gate 4

The gap is specific and the fix is bounded; gate 4's plan-next (when
authored) will draft its own WUs. From this terminal-case position, the
load-bearing observations the gate-4 author should consume:

1. **Recommended fix path** (from `SMOKE-INIT-2026-0001-F06.md` Outcome
   §): broaden `lint_plan.py` section detection to accept both ATX
   (`^#+\s*<section>`) and the existing bold/plain (`^(\**)<section>`)
   patterns. Smallest blast radius; touches one regex constant + tests.
   Alternatives (normalise in `adopt_feature.py`, change the orchestrator
   template) are documented but disfavoured.
2. **Re-smoke target** (from `SMOKE-INIT-2026-0001-F06.md` §Adopt step):
   `INIT-2026-0001-F06-conform-publishroster-to-validated-spec/` already
   exists on this branch from T07. Re-running `lint_plan.py` against that
   folder is the offline verification — no second `gh issue edit 287` is
   required for the lint fix itself.
3. **Cross-repo contract carry-over** (from
   `[FEAT-2026-0003/G3-LESSONS/multi-gate]`): is the ATX-headings
   assumption authoritative for orchestrator issue bodies? Gate 4's review
   document must verify this against the orchestrator's issue-body
   template (likely under `RestoManagerApp/orchestrator/`) before locking
   the linter regex. If the orchestrator template can also produce
   bold-style headings, the union-pattern is the right call; if only
   ATX, the same pattern still works but the "accept both" framing is
   wrong.
4. **No second live smoke required for closure.** The `state:*` label
   contract is settled; report-back is proven; the gate-4 fix is offline-
   verifiable. A re-smoke against #287 is OPTIONAL belt-and-braces — it
   adds a second production-issue mutation cycle for marginal evidence.
   Gate 4's plan-next should weigh this and probably skip it.

---

## Summary

Three gates delivered the read path, the adopt path, and the report-back +
live smoke. The smoke surfaced a single, bounded, loop-side gap (linter's
section detector doesn't accept ATX headings) that blocks the roadmap
goal's fourth mechanism — the actual grind of the adopted folder. The
multi-gate `plan-next` forward-design mechanism worked at gate scope, with
the cross-repo blind spot caught and codified into a binding LEARNING. The
arc is **not** ready for closure; gate 4 follows. Once gate 4 broadens
the section detector and `lint_plan.py` accepts the adopted folder,
the roadmap goal is met end-to-end and the feature closes.

