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
