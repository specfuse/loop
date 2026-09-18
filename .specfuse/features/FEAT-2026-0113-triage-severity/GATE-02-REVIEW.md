---
gate: 2
drafted_by: FEAT-2026-0113/G1-PLAN
open_questions:
  - "Q1 (T03, flagged as uncertain in PLAN.md's Assumptions): does the rubric reader belong in gate 2 at all, or should the pure extraction have landed in gate 1? Drafted into gate 2 — reasoning and the counter-argument below."
  - "Q2 (T03, T05): the rubric is vocabulary-only — a `severity:<value>` label whose value is outside SEVERITY_VALUES is not offered to the classifier even when `rules.bugs.severity_aliases` maps it (#3349). Should an operator's declared alias widen the rubric too?"
  - "Q3 (T04, T05): one `confidence` field governs both category and severity; no `severity_confidence` field is added. A low-confidence answer drops the severity entirely — no marker field, no label. Is a fourth field worth it?"
  - "Q4 (T06 criterion 2): the opt-out is proved by `gh` argv equality, with the one read-only label listing excluded from the comparison. That listing is a real new API call per run for every repository, including those that opted out. Acceptable?"
  - "Q5 (T05): a repository that defines a `severity:*` label with an empty description gets an undefined rubric entry, and T05 escalates rather than defaulting. Should the label's own value be allowed to stand in as its definition?"
---

# Gate 2 review — triage classifies severity and writes it

Written by `FEAT-2026-0113/G1-PLAN` for the human who arms gate 2. Every unit below
is `status: draft`; arming is your act, not the driver's.

**Gate 1's premise held.** `RETROSPECTIVE.md` records zero marker shapes in the wild
that the old anchored regex parsed and the new field scan does not — 15 distinct
literals swept, 6 old-parseable, 0 divergences, plus a 10-marker generated
cross-product with 0 mismatches. This unit's escalation trigger ("if a marker shape
regressed, do not draft a write path on top of it") did not fire, which is what
licenses everything below.

## What gate 2 is drafted as

Four substantive units plus the closing pair. `PLAN.md`'s graph carries the
dependencies; the shape is a layer per unit, joined by the last:

| Unit | File | What it lands | Depends on |
|---|---|---|---|
| `T03` | `WU-03-severity-rubric-reader.md` | the extracted label listing + the severity rubric | — |
| `T04` | `WU-04-marker-then-label-write-path.md` | `render_marker` / `apply_triage` record severity, marker first | — |
| `T05` | `WU-05-classify-severity-fails-closed.md` | the prompt carries the rubric; the reader fails closed | T03, T04 |
| `T06` | `WU-06-run-records-severity-end-to-end.md` | `TriageProvider.execute` wiring + the gate's `feature_oracle` | T05 |

**No unit is a tracer bullet, deliberately** (`/authoring-work-units` §14). The gate's
`feature_oracle` is red until `T06` lands, because T03–T05 each ship a complete,
separately-tested layer and T06 is the wiring that joins them. That means no unit in
this gate is permitted to stub anything — T06's body says so in its own words, so the
constraint travels with the unit rather than living only here.

**Where the `feature_oracle` sits, and why.** `GATE-02.md` left this to the drafting
agent: `apply_triage` or one level up. It is one level up —
`python3 -m unittest tests.test_triage_severity_end_to_end -v -b`, driving
`TriageProvider.execute` (`specfuse/agent/providers/triage.py:208`). `apply_triage`
never reads a label rubric, so it cannot observe the opt-out half of the milestone at
all, and a gate oracle that can only see one half of its own definition of done is the
failure `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]` records.

## If you check only three things, check these

1. **That the precedence is still marker-first when T04 dispatches.** `PLAN.md`'s
   **Record precedence** section fixes marker-authoritative, label-as-projection,
   marker-written-first, and a unit that reorders them is wrong rather than a
   variation. T04's criterion 1 asserts on the *order* of the runner's recorded calls,
   not on their presence, because presence is what a reordered implementation would
   also satisfy. If that criterion gets softened to "both calls happen", the gate has
   lost the only thing that makes a failed label write safe.
2. **T06 criterion 2 — the opt-out proved by argv equality.** The claim "a repository
   that defines no `severity:*` labels behaves byte-identically to today" is the
   feature's whole opt-out contract and the reason `LABEL_REGISTRY` gains no
   `severity:*` entry. It is drafted as a measured equality of the full `gh` argv
   sequence, not as prose. The cheap way to make that criterion pass is to weaken it
   to "behaves equivalently" — at which point the gate no longer proves the thing it
   exists to prove, and the damage is silent because every test still passes. T06's
   escalation trigger names this explicitly; hold it there.
3. **Q1 below — whether T03 belongs in this gate.** It is the one structural question
   `PLAN.md` itself flagged as uncertain at draft time, and it is cheaper to answer now
   than after T03 dispatches.

## Record precedence — how each drafted unit honours it

| Unit | Where precedence binds it | Criterion |
|---|---|---|
| `T03` | n/a — read-only; issues no write | — |
| `T04` | marker `severity=` written by the `--body` edit, `severity:<value>` projected after | #1 (call order), #4 (failed label leaves marker in place) |
| `T05` | n/a — produces a decision, writes nothing | — |
| `T06` | asserts the order at run level, through the provider | #1 |

The repair branch is drafted as *repair*, not as a second source of truth: T04's
criterion 5 adds a missing `severity:<value>` label for an issue whose marker already
carries the field, and re-writes no marker. That is the shape `apply_triage` already
uses for the category label.

## Existing-mechanism search — T03 is an extraction, not a second listing

`PLAN.md`'s **Existing-mechanism search** verdict is binding and was re-checked in
this session, not inherited: `specfuse/loop/labels.py:267` issues
`["gh", "label", "list", "--json", "name,color,description", "--limit", "1000"]`
through an injected runner, inside `provision_labels`, with fail-soft handling for an
absent binary, a non-zero exit and unparseable output. T03 **extracts** that call and
gives it two callers — `provision_labels` itself and the rubric reader. Its criterion 2
is a countable grep (`grep -c '"label", "list"' specfuse/loop/labels.py` returns `1`),
so "reusing" is asserted rather than asserted-about. A drafted unit that issued its own
listing would not have done the search, per this gate's own arming discipline.

## Rubric-presence scope table (`planning-discipline.md` §3, by analogy)

No drafted unit introduces a flag or a policy key — the opt-in is the **presence of
`severity:*` labels in the repository**, which is why §3's table is reproduced here
against that switch instead. The headline claim to check it against: *severity is
recorded only where the operator defined what severity means.*

| Code path | Gated by a non-empty rubric? | Why |
|---|---|---|
| `labels.read_severity_rubric` (T03) | n/a | it *is* the switch; returns `{}` for a repo defining none |
| `labels.provision_labels` (T03) | no | registry-only, and `LABEL_REGISTRY` gains no `severity:*` entry |
| `triage_invoke.build_invocation` prompt (T05) | yes | empty rubric ⇒ byte-identical prompt (T05 criterion 1) |
| `triage_invoke` result reader (T05) | yes | a severity outside the given rubric reads as none (T05 criterion 4) |
| `triage.render_marker` (T04) | no — gated on the decision's `severity` key | no severity given ⇒ today's two-field string, by equality |
| `triage.apply_triage` writes (T04) | no — same gate | no `severity` key ⇒ identical `gh` argv sequence |
| `providers.TriageProvider.execute` (T06) | yes | reads the rubric once per run; `{}` ⇒ today's write sequence |
| `agent_policy.meets_severity_floor` and `min_severity` | **no — untouched** | where the floor sits stays the operator's; this feature reads that vocabulary and does not extend it |

## Cross-repo contracts (`/authoring-work-units` §8)

Every value below is owned by a system outside this feature, and each was checked
against its source in this drafting session rather than recalled:

| Value | Source of truth | Checked |
|---|---|---|
| `severity:` label prefix | `specfuse/loop/agent_policy.py:340` (`SEVERITY_LABEL_PREFIX`) | read, 2026-09-17 |
| `low, medium, high, critical` | `specfuse/loop/agent_policy.py:56` (`SEVERITY_VALUES`), ranked at `:336` | read, 2026-09-17 |
| `gh label list --json name,color,description --limit 1000` | `specfuse/loop/labels.py:267` | read, 2026-09-17 |
| `<!-- specfuse:triage category={category} confidence={confidence} -->` | `specfuse/loop/triage.py:64` (`_MARKER_TEMPLATE`), published contract | read, 2026-09-17 |
| `high, low` confidences | `specfuse/loop/triage.py:36` (`CONFIDENCES`) | read, 2026-09-17 |
| `rules.bugs.min_severity`, `rules.bugs.severity_aliases` | `.specfuse/agent-policy.yml` schema, `agent_policy.py:419` / `:436` | read, 2026-09-17 — **read only, never written by this feature** |

`parse_marker`'s call sites are the one place `PLAN.md` is stale and gate 1's
retrospective is right: **six sites across five modules** — `specfuse/agent/state.py:167`,
`specfuse/agent/triage_invoke.py:70`, `specfuse/loop/triage.py:202` and `:304`,
`specfuse/loop/bug_lane_run.py:488`, `specfuse/loop/bug_lane_state.py:209`.
`specfuse/agent/providers/triage.py` is not a caller; it reaches the reader through
`triage_invoke.classify_result`. `specfuse/loop/promotion.py` greps like a caller and
is not one — it owns a separate `specfuse:promoted` marker. T04's Do-not-touch carries
both facts so a unit scoped by `PLAN.md`'s older three-caller list cannot be scoped wrong.

## Runtime probe (`planning-discipline.md` §4) — does not bind, and why

No drafted unit flips a default value or a severity. `render_marker` gains an
*optional* parameter whose absence reproduces today's output by string equality (T04
criterion 2), and `apply_triage`'s behaviour for a decision carrying no `severity` key
is asserted argv-for-argv against the existing expectation in
`tests/test_triage_apply.py` (T04 criterion 3). No lint check is raised to ERROR, no
`WARNING` is promoted to blocking, and `rules.bugs.min_severity` is read and never
written — `PLAN.md`'s **Escalation-predicate satisfiability** section already records
that the "severity" in this feature's title is the severity of an inbound issue, a
different axis from a finding's severity.

If you disagree and want the probe anyway, the command is the full `tests` gate from
`.specfuse/verification.yml` with T04's `render_marker` change applied locally, and its
failure list belongs in this file before you arm.

## Open questions

**Q1 — does T03 belong in gate 2?** `PLAN.md`'s Assumptions flagged this as genuinely
uncertain and explicitly invited the reviewer to move it: the extraction is a pure
refactor with no behaviour change, which is gate-1-shaped, but it had no consumer in
gate 1 and landing an unused extraction is exactly what `tests/test_caller_check_ratchet.py`
flags — the check that caught `severity_from_labels` on #3349. **Drafted into gate 2**,
and the draft resolves the ratchet concern differently than the assumption feared: T03
refactors `provision_labels` to call the extracted helper, so the helper has a
production caller the moment it lands, independent of the rubric reader. That makes the
gate-1-vs-gate-2 placement a scheduling question rather than a correctness one, and
gate 1 is closed. Moving it now would mean re-opening a passed gate; the cost of
leaving it here is that gate 2 carries one unit of refactor that is not about severity.
Recommendation: leave it in gate 2. You are the one who can overrule that.

**Q2 — should operator aliases widen the rubric?** `read_severity_label` already honours
`rules.bugs.severity_aliases` (#3349), so a repository can declare that its own
`severity:minor` means `low`. T03 is drafted to build the rubric from vocabulary values
only, so an aliased label is readable by the *floor* and invisible to the *classifier*.
That asymmetry is defensible (the classifier should answer in the vocabulary, not in
the operator's words) and it is also a surprise waiting for the first operator who
declares aliases and finds triage ignoring them. Naming it rather than deciding it.

**Q3 — one confidence, or two?** The marker carries one `confidence` field today, and
the draft keeps it: a low-confidence answer drops the severity entirely, so nothing is
written and the issue keeps failing closed under a floor exactly as it does now. The
alternative is a fourth marker field (`severity_confidence=`), which gate 1's reader
would tolerate without any further change. The draft's reasoning is that a severity the
classifier is unsure of, recorded in the authoritative record but not projected as a
label, would break the projection invariant — the repair branch would then see a marker
field with no label and write the label anyway. A fourth field is the only coherent way
to have both, and it is not drafted.

**Q4 — the new read for opted-out repositories.** T06 criterion 2 excludes the one
read-only label listing from its argv equality, because a rubric cannot be known empty
without reading it. So "byte-identical" is precise about writes and not about reads:
every triage run gains one `gh label list` call, including in repositories that will
never define a severity label. T06 criterion 3 bounds it to once per run rather than
once per issue. If that read is unacceptable, the alternative is a policy key to gate it
— which would reintroduce the config surface this feature deliberately does not add.

**Q5 — an empty label description.** T05 escalates rather than inventing a definition
for a `severity:*` label whose description is blank. The alternative — letting the
label's own value stand in as its own definition — is one line, and it would mean
specfuse quietly supplying the rubric the operator did not write, in the one place the
feature's risk acceptance rests on the rubric being the operator's own words.

## Carried forward from gate 1

- **`PLAN.md`'s three-caller list is stale**; the six-site list above is the one to
  scope against. Already written into T04's Do-not-touch.
- **`promotion.py` is not a triage caller.** Already written into T04's Do-not-touch.
- **Every already-marked issue becomes a two-field marker in a three-field world** the
  moment T04 lands. That asymmetry is not a gate-2 defect — it is precisely what gate 3's
  backfill exists for, and `G2-PLAN` is the unit that drafts it.
- **No oracle in this feature has yet read a real issue body outside this repository.**
  Gate 1 carried this as a stated residual rather than a deferred criterion; gate 2's
  drafted oracles are all injected-runner tests, so it is still carried. Gate 3 is the
  first surface that reads already-marked issues and is where a live-corpus check belongs.
