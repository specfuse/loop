<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0073: the envelope accepts the IDs the methodology documents

Single terminal gate, two implementation work units, one close. The feature's headline
claim is that the driver's event log now validates against the envelope **end to end**,
not in the `event_type` dimension alone. It does: the corpus is green at close time and
the gate that proves it checks every field.

## Gate 1 — the event log validates end to end

### What was built

**T01 — the correlation-ID override (`done`, 2 attempts, $4.98 against $4.00).**
Widened `correlation_id` through the driver-local registry that FEAT-2026-0060 built for
`event_type`, on the same deep copy, in the same `load_validator` fall-through. The
registry (`specfuse/loop/data/schemas/driver-event.schema.json`) gained a
`correlation_id` block holding `closing_names` and `hygiene_suffix_pattern`;
`load_driver_correlation_patterns` reads it and degrades to the vendored pattern when
the file is missing or unparseable, matching `load_driver_event_types`'s existing
contract. `.specfuse/rules/correlation-ids.md` was reconciled in the same WU, because
the entire defect was that the rules file and the schema stated different contracts —
widening one without the other would have shifted the disagreement rather than closing
it. Oracle: `tests/test_correlation_id_override.py` (304 lines), red on HEAD.

**T02 — the gate widened from one field to the whole envelope (`done`, 1 attempt after
re-arm, 4 attempts total, $7.12 against $3.50).** `.specfuse/scripts/event_type_gate.py`
checked `event_type` errors only, deliberately, and said so in its own docstring: the
scoping existed because 279 `correlation_id` errors made a whole-envelope gate
impossible. T01 removed that reason. The gate now reports every envelope error; the
stale scoping paragraph is gone from both the docstring and `verification.yml`'s comment
on the `event-type-gate` entry. Oracle: `tests/test_event_gate_full_envelope.py` (170
lines), red on HEAD.

### The corpus numbers, as measured at close time

`PLAN.md` recorded **285 errors across 38 folders** at drafting time and warned that the
figure grows with every feature that closes. It did. Re-measured in this session, using
`PLAN.md`'s exact methodology (driver-local `event_type` override in force, vendored
`correlation_id` pattern):

```
PRE-T01 (vendored correlation_id pattern): 288 errors across 39 folders
by kind: {'correlation_id': 288}
shapes : G<n>-CLOSE 101, G<n>-PLAN 87, G<n>-CLOSE-INTERMEDIATE 28,
         G<n>-DOCS 23, G<n>-RETRO 22, G<n>-LESSONS 20,
         T03H 3, T08H 2, T11H 2
corpus : 47 events.jsonl files
```

The delta from 285 is **+3, entirely `G<n>-CLOSE`** (98 → 101) — three features closed
between drafting and now, each emitting a `G1-CLOSE` event stream. Nothing else moved:
the other five closing shapes are unchanged at 87 / 28 / 23 / 22 / 20, and the three
hygiene shapes (`T03H` 3, `T08H` 2, `T11H` 2, seven events) were always in the total but
were omitted from `PLAN.md`'s shape list, which summed to 278 of the 285. That accounts
for the whole corpus: 281 closing-sequence + 7 hygiene = 288. **No new error class
appeared**, which is the condition `GATE-01.md` said actually mattered.

Post-T01, measured fresh in this session:

```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 47 events.jsonl file(s), 1102 event(s) checked
EXIT=0
```

**What T01 and T02 themselves reported — and the gap.** T02's criterion 4 was "the gate
exits 0 on this tree", re-confirmed above. T01's own measured before/after numbers
(criterion 9) are **not recoverable from this repository**: its squash commit body is
the bare `feat:` subject with no RESULT block, and `work/FEAT-2026-0073_T01/` was never
created because neither of its attempts escalated. The only in-repo record of T01's
figure is the re-arm commit (`609325b`), which says "0 errors across 0 folders, down
from **285 across 38**" — and 285/38 is `PLAN.md`'s drafting-time figure restated, not a
measurement. That is precisely the defect FEAT-2026-0063 was created to fix, reproduced
in a commit body. The 288/39 above is this close's own measurement and supersedes it.
See the lessons entry on RESULT-block durability.

### The vendored file is untouched

The feature's central boundary, asserted rather than claimed:

```
$ git diff --exit-code specfuse/loop/data/schemas/event.schema.json
EXIT=0

$ git diff --exit-code main -- specfuse/loop/data/schemas/event.schema.json
EXIT_VS_MAIN=0
```

Empty output, exit 0, both against the working tree and against `main`. The vendored
envelope is byte-identical; the widening lives entirely in `load_validator`'s deep copy.

### The decision the roadmap left open

The roadmap row named two options and declined to pick. **A driver-local override was
chosen**, extending FEAT-2026-0060's mechanism. The deciding evidence was inside the
vendored file: its `$id` is `https://specfuse.dev/orchestrator/schemas/event.schema.json`
— another repository owns it — and its `$comment` is that repository's changelog, which
already records a prior upstream widening of this exact field. Editing it here forks a
file with live upstream history, and the next vendor sync reverts the fix **silently**,
reinstating 288 failures with no signal that anything regressed.

The row's counter-argument was not dismissed: ID *format* really is more plausibly a
shared protocol concern than event vocabulary is. The answer was not to make an unowned
edit but to record the upstream need explicitly — see below.

### The upstream need, filed

**[specfuse/orchestrator#81](https://github.com/specfuse/orchestrator/issues/81)** —
"envelope: correlation_id rejects closing-sequence (G<n>-<NAME>) and hygiene (TNNH)
work-unit IDs".

It cites `correlation-ids.md` as the contract, this feature as the local implementation,
carries the 288/39 measurement, quotes the pattern the override produces, and flags the
namespace looseness noted below so an upstream fix does not inherit it unexamined. It
also records that once the widening lands upstream, the `correlation_id` block in
`driver-event.schema.json` becomes redundant and should be retired in the same vendor
sync. The override is now a documented bridge, not a silent divergence.

### Consumer-visible contract changes

Enumerated per `close-discipline.md` §3. Two, both real:

1. **`specfuse/loop/data/schemas/driver-event.schema.json` gains a `correlation_id`
   surface.** The driver-local registry previously held one key consumers could read
   (`event_types`, FEAT-2026-0060). It now also holds `correlation_id` with
   `closing_names` (a six-element array) and `hygiene_suffix_pattern` (a regex
   fragment). Additive — nothing was removed or renamed, and a consumer reading only
   `event_types` is unaffected. `specfuse/loop/validate_event.py` gains
   `load_driver_correlation_patterns` alongside the existing
   `load_driver_event_types`, with the same missing-or-unparseable-degrades-safely
   contract.

2. **The `event-type-gate` verification gate widens from one field to the whole
   envelope — this one can newly fail a downstream project.** The gate keeps its name
   (`event-type-gate`) and its command, so no configuration changes; what changed is
   what it *reports*. A project whose `events.jsonl` carries envelope errors in any
   field other than `event_type` — a missing required key, a wrong-typed payload, a
   malformed timestamp — previously passed this gate silently and now fails it. That is
   the intended behaviour and it is still a breaking change in the "a gate that was
   green goes red" sense. The name is now a poor fit for the scope; renaming it is a
   one-line follow-up bug, explicitly out of scope here (see the failure-class
   breakdown for why that boundary was drawn in blood).

   *Mitigation for a downstream hitting this:* the errors were always real. The gate
   output names the file, line, and field of each offender. The correct response is to
   fix the emissions, not to re-narrow the gate.

Human acknowledgment of this list is the gate review's business
(`autonomy_default: review`, gate 1 lands at `awaiting_review`).

## Cost analysis

`events.jsonl`'s `attempt_outcome` sum is authoritative. Reconciled against every WU
frontmatter figure, exactly — **no gap, no lower bound needed**.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — correlation-ID override | $4.00 | 2 | **$4.984844** | +$0.98 (+25%) |
| T02 — widen the gate | $3.50 | 4 (3 + 1 after re-arm) | **$7.115892** | +$3.62 (+103%) |
| G1-CLOSE — this session | $5.00 | 1 (in flight) | not yet in `events.jsonl` | — |
| **Implementation subtotal** | **$7.50** | **6** | **$12.100736** | **+$4.60 (+61%)** |
| WU sum incl. close | $12.50 | — | $12.10 + close | — |
| Gate budget | $17.50 | — | headroom before close: **$5.40** | — |

Per-attempt ledger, in emission order:

```
T01 attempt 1  produces_not_in_diff      $2.1675309
T01 attempt 2  passed                    $2.8173132   -> task_completed cost_usd 4.984844
T02 attempt 1  deliverable_missing       $1.2570930
T02 attempt 2  files_changed_mismatch    $1.8859599
T02 attempt 3  files_changed_mismatch    $2.3261775   -> human_escalation; cumulative 5.46923
T02 attempt 1  passed (after re_arm)     $1.6466619   -> task_completed cost_usd 1.646662
                                        -----------
attempt_outcome sum                      $12.1007364
```

Frontmatter reconciliation, each line checked independently:

- T01 `cost_usd: 4.984844` = 2.1675309 + 2.8173132 ✔
- T02 `cumulative_cost_usd: 5.46923` = 1.257093 + 1.8859599 + 2.3261775 ✔
- T02 `cost_usd: 1.646662` = the post-re-arm attempt ✔
- Sum of both WUs = $12.100736 = the `attempt_outcome` total ✔

**The close WU's own spend is not in this total.** `G1-CLOSE` is in flight as this file
is written; the driver appends its `attempt_outcome` after the session. The $12.10 is
therefore a complete figure for implementation and a **lower bound for the gate**. At
$5.40 of remaining budget against a $5.00 close estimate, the gate lands inside $17.50
only if the close comes in at or near estimate — the padding that budget carried for a
close re-attempt (#260) was consumed by T02's escalation instead.

**Where the money went.** $7.64 of $12.10 — **63%** — was spent on four non-passing
attempts, and every one of them failed on the same mechanical guard rather than on the
substance. The feature's actual technical work landed in two passing attempts costing
$4.46 combined, under the $7.50 planned for it. The estimate was not wrong about the
work; it was wrong about the authoring.

### Failure-class breakdown

Four non-passing attempts across two WUs, $7.6367613 (63.1% of spend). Three distinct
driver outcomes, **one root cause**: a path in `produces:` that showed no diff against
HEAD.

| Class | Count | Cost | WU | What actually happened |
|---|---|---|---|---|
| `produces_not_in_diff` | 1 | $2.1675309 | T01 | `.specfuse/rules/correlation-ids.md` did not appear in the squash diff. Recovered unaided on attempt 2. |
| `deliverable_missing` | 1 | $1.2570930 | T02 | The WU body invited a rename; the agent renamed `event_type_gate.py`, making the declared `produces:` path absent. |
| `files_changed_mismatch` | 2 | $4.2121374 | T02 | Kept the name, so the declared path had no honest diff — the only real change lived in `validate_event.py`, which T02's **Do not touch** forbade. Escalated `spinning_detected` at attempt 3. |

**T02's three failures were an authoring defect, not an execution defect.** The body
said "rename it if the name no longer fits" while `produces:` declared
`.specfuse/scripts/event_type_gate.py`. Those are mutually exclusive: rename and the
deliverable is absent; keep the name and the declared path is unchanged. No correct
execution could satisfy both, which is why three fresh sessions converged on the same
signature. The agent behaved correctly at every step — it escalated rather than deleting
the `produces:` entry to make the guard pass. The re-arm (`re_arm_count: 1`,
agent-authored on the operator's standing overnight instruction, and labelled as such in
`re_arm_history` rather than presented as the operator's) **amended the body** rather
than retrying it: the rename invitation was withdrawn with its withdrawal explained
inline, and criterion 6 was rewritten to name the exact `verification.yml` comment to
change — guaranteeing the declared path shows a real diff. The next attempt passed
first try at $1.65.

Same class as the defect that halted FEAT-2026-0042's baseline: **an instruction that
contradicts a machine-checked declaration**. That is now two features; see the lessons
entry.

T01's single failure is a milder instance of the same shape — a `produces:` entry whose
change was real but landed outside the squash diff — and it self-corrected, which is why
it cost one attempt rather than three.

## Deferred verification

Per acceptance criterion 2, one entry per criterion not verified in-loop.

**1. The two `correlation_id` definitions cannot drift apart.**
- *Why not verified in-loop:* the upstream definition lives in another repository. This
  repository has no copy of it beyond the vendored file, and no mechanism compares the
  vendored pattern against the driver-local widening on sync.
- *Where it actually gets checked:* nowhere automatically — this is the honest answer.
  Partially by the vendor-sync process, if a human reads the diff;
  [specfuse/orchestrator#81](https://github.com/specfuse/orchestrator/issues/81) is the
  record that makes it a reviewable divergence rather than an invisible one. See *What
  the loop did NOT verify* below.

**2. The widened envelope is looser than `correlation-ids.md` in the namespace
dimension.**
- *Why not verified in-loop:* T01's criterion 4 required the widening to be **strictly
  additive** — every shape validating on HEAD must still validate, explicitly including
  `FEAT-2026-0001/F01`. The vendored pattern's `(/F\d{2})?` is optional on both
  namespaces, so preserving additivity necessarily preserves that looseness. Tightening
  it would have violated criterion 4.
- *Where it actually gets checked:* `specfuse/loop/lint_plan.py`'s `CORRELATION_ID_RE`
  enforces the tighter documented contract on PLAN.md graphs, so a malformed ID is
  caught at plan time even though the envelope would accept it at emit time. Recorded in
  the upstream issue so an upstream fix does not inherit it unexamined. Measured in this
  session:

  ```
  INIT-2026-0001         envelope=True  rules_md=False
  FEAT-2026-0001/F01     envelope=True  rules_md=False
  FEAT-2026-0001/F01/T01 envelope=True  rules_md=False
  ```

  The looseness predates this feature and was not introduced by it.

**3. The gate has never met a downstream project's malformed non-`event_type` event.**
- *Why not verified in-loop:* this repository's corpus is green, so every red-before test
  in `tests/test_event_gate_full_envelope.py` is a **fixture** — a planted event, not
  real producer output. The suite's green proves the gate fires on a constructed
  offender, not that it fires on one a real project would emit.
- *Where it actually gets checked:* the first downstream project that runs the widened
  gate against a corpus with real envelope rot. This is the consumer-visible change
  enumerated as item 2 above, and it is why that item carries a mitigation note.

**4. `re_arm_history`'s cost and duration figures for T02's pre-re-arm attempts.**
- *Why not verified in-loop:* they were carried forward by the re-arm tooling, not
  re-derived.
- *Where it actually gets checked:* reconciled in *Cost analysis* above against the
  `attempt_outcome` events — `cumulative_cost_usd: 5.46923` = 1.257093 + 1.8859599 +
  2.3261775. They are correct. Listed here because the check happened at close time
  rather than at re-arm time.

## What the loop did NOT verify

**The two definitions of `correlation_id` can drift, and nothing in this repository
detects that.** This is the feature's principal residual risk and it is structural, not
an oversight.

The widening lives in `specfuse/loop/data/schemas/driver-event.schema.json` and is
applied to a deep copy of the vendored envelope at validation time. The vendored file is
untouched, which is what makes the fix survive a vendor sync — but it also means the two
patterns are now **independent**. If the orchestrator widens `correlation_id` upstream
with a different set of closing names, or tightens the namespace dimension, or adds a
shape the driver-local registry does not know, the next vendor sync pulls in the new
vendored file and the driver-local block keeps widening it the old way. Nothing
compares them. Nothing warns. The failure mode is silent by construction:

- The corpus stays green either way, because the driver-local widening is a *superset*
  applied on top of whatever the vendored pattern says.
- A consumer reading both logs — one validated upstream, one validated here — would see
  two different notions of a valid ID, and neither validator would complain.
- The `$comment` changelog in the vendored file is the only signal a sync would carry,
  and reading it is a human act, not a gate.

Three things bound this and none of them is a detector:
`specfuse/loop/lint_plan.py`'s `CORRELATION_ID_RE` independently enforces the documented
contract on PLAN.md graphs, so drift shows up at plan time for IDs the loop *authors*
(not for IDs it merely *reads*); the driver-local registry's `description` states the
"must state the same set of shapes as `correlation-ids.md`" requirement in prose, which
is a note to a reader, not an assertion; and
[specfuse/orchestrator#81](https://github.com/specfuse/orchestrator/issues/81) records
the need so the eventual upstream fix retires the override rather than layering on it.

**A test asserting the driver-local registry and `correlation-ids.md`'s combined pattern
state the same shape set exists** (T01 criterion 8, mechanically enumerated rather than
eyeballed). A test asserting the *vendored* pattern has not changed shape under it does
**not**, and that is the missing detector. It is a plausible follow-up: assert the
vendored `correlation_id` pattern matches a recorded fingerprint, so a vendor sync that
changes it fails loudly instead of being silently over-widened.

**No auto-close debt was inherited.** This feature has one gate and one close; no
predecessor gate auto-closed, and no `specfuse:autoclose-debt` marker exists anywhere in
the feature folder (grepped; no matches).

## Lessons promoted

Three entries appended to `.specfuse/LEARNINGS.md`, all tagged
`FEAT-2026-0073/G1-CLOSE`:

1. **Measure every error class before asserting zero errors.** Assessed as generalizable
   and promoted — this is the check FEAT-2026-0060 skipped at a cost of $4.48 and a
   blocked attempt, and the check this feature made first. It generalizes past validators
   to any "zero X corpus-wide" criterion.
2. **A WU body that invites a change its `produces:` list forbids cannot be executed.**
   Two features have now burned attempts on this exact shape (FEAT-2026-0042's baseline,
   FEAT-2026-0073/T02 at $5.47). Promoted with the concrete authoring rule.
3. **A passing WU's measurements die with its session unless an artifact carries them.**
   T01's corpus numbers were unrecoverable at close time because passing attempts write
   no `work/` note and the squash commit body carries no RESULT. Promoted.

## Verdict

**`met`.** Every acceptance criterion of gate 1 is verified by a command run fresh in
this session, not inherited from a producing WU's self-report: the corpus validates at
zero errors over the full envelope (47 files, 1102 events, exit 0), the vendored schema
is byte-identical to HEAD and to `main`, the full `code` gate set is green, and the
upstream need is filed at specfuse/orchestrator#81.

The residual risks are named rather than resolved — upstream drift is undetectable here
by construction, and the widened gate has met only fixture offenders. Both are recorded
above with where they actually get checked. Neither is an unmet criterion; both are the
honest boundary of what a single-repository loop can verify about a two-repository
contract.
