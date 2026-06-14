# Gate 3 review — FEAT-2026-0016

Drafted by `FEAT-2026-0016/G2-PLAN` (Opus). Read this before
arming. This file is **advisory**. It owns no state. Status
lives in WU files; the graph lives in `PLAN.md`. If you change a
decision, edit the WU and the graph directly.

---

## Gate-2 summary

Gate 2 (consumer layer) shipped clean and well under plan.
Substantive total $1.43 actual vs $4.70 planned (0.30×) — T04
spinning-detector landed in a single attempt at $0.76 vs $2.00
planned (0.38×), T05 `/gate-status` per-attempt surface at $0.27
vs $1.20 (0.22×), T06 `/unblock-wu` mandatory-rationale + history
write at $0.40 vs $1.50 (0.27×). The G2-CLOSE-INTERMEDIATE was
auto-closed by the predicate (`auto=True, gate_total_cost: $1.43,
gate_budget: $12.00`) — this feature's own consumer surface was
on-plan enough to trip the deterministic predicate, and the
close-intermediate ceremony dispatch was skipped. Predicate
self-check below is captured against gate 2 directly.

The auto-close is itself a recursive-dogfood data point: the
predicate (FEAT-2026-0018) inspecting `events.jsonl` containing
T01's `attempt_outcome` records for this very feature's gate-2
WUs found nothing to flag — no blocked_human in chain, no
per-WU overrun, no gate-total miss. Three small consumer WUs
moving at half their planned size is a quieter shape than the
gate-1 data layer (which tripped on T03's spec-bug-then-re-arm).

## Gate-3 substantive WUs

### T07 — Close-ceremony `### Failure-class breakdown` ($1.00, medium)

Adds two top-level symbols to `loop.py`:
`summarize_attempt_failure_classes(feature_dir, gate_n=None) -> str`
(reads `events.jsonl`, filters non-passing `attempt_outcome`
records, groups by `(failure_class, failure_signature)`, renders
a deterministic markdown table) and
`assert_failure_class_breakdown_when_failures_present(wu,
feature_dir, repo_root, head_before)` (close-guard alongside
`assert_cost_analysis_section_when_met`, requires the
`### Failure-class breakdown` subsection in RETROSPECTIVE.md
whenever the gate's events.jsonl contains any non-passing
`attempt_outcome`). Wired into `CLOSE_GUARDS` immediately after
the existing cost-analysis-when-met guard so the new error
doesn't shadow the more foundational missing-section error.
Legacy-event tolerant: pre-T01 features render the
"(no non-passing attempts in scope)" sentinel and the guard
passes. First exercised on this feature's own G3-CLOSE — the
recursive-dogfood smoke test for T07 itself.

### T08 — `/learnings-suggest` skill ($1.20, medium)

New read-only skill at
`.specfuse/skills/learnings-suggest/SKILL.md` discovered via
`.claude/skills/learnings-suggest` symlink. Scans every
`.specfuse/features/FEAT-*/events.jsonl`, clusters non-passing
`attempt_outcome` records by `(failure_class,
failure_signature)`, threshold-filters to clusters spanning
≥ 2 distinct WUs (the `--min-wus` flag, default 2 — a single WU
spinning on one signature is a per-WU bug, not a general
lesson), and propose-and-confirms candidate LEARNINGS entries
per cluster. Mirrors `/gate-status`'s "Hard rules" shape:
read-only, trace-every-claim, propose-and-confirm before any
write. The skill body documents the four-step flow (scan,
cluster, threshold + render, propose-and-confirm); the
discovery symlink topology mirrors existing
`.claude/skills/<name>` → `../../.specfuse/skills/<name>/SKILL.md`
patterns.

### T09 — Docs methodology.md + roadmap-archive ($0.50, low)

Two additive subsections in `docs/methodology.md`: a §3 sibling
(or subsection) `### Per-attempt outcome events (FEAT-2026-0016)`
naming the locked-at-v1 `outcome` + `failure_class` taxonomies
and pointing at PLAN.md for the field-by-field payload schema; a
paragraph (placement at author's discretion, near §2 or §4)
naming the six new re-arm WU-frontmatter fields and pointing at
`.specfuse/templates/WU.template.md` notes for the field-level
spec. Plus the roadmap-archive move: cut the
`## FEAT-2026-0016 — Re-arm contract + audit trail` detail
section from `.specfuse/roadmap.md` (lines ~293+), paste verbatim
into `.specfuse/roadmap-archive.md` under a `<a
id="feat-2026-0016"></a>` anchor, and update the roadmap row's
Detail cell to `[→ archive](roadmap-archive.md#feat-2026-0016)`
matching the convention used by every other archived row. Note
the type is `implementation` (not `docs`) — `docs` as a WU type
is reserved for the legacy four-WU closing sequence; the linter
treats trailing `docs` + `close` as a malformed closing
sequence. The work IS documentation; the type encodes
scheduling-role, not work-nature.

## Open verifications

Pre-arm checks the operator runs before flipping these from
`draft` to `pending`. Each is a quick read, not a
re-implementation.

### `CLOSE_GUARDS` registration site is single-source

T07 AC3/AC4 assume `CLOSE_GUARDS` (loop.py line ~1990) is the
one registration point that dispatches close-guards for BOTH
`close-intermediate` and `close` WU types. If close-intermediate
and close maintain separate guard lists, T07's new guard must
wire into both. **Confirm before arming T07**: `grep -nE
'CLOSE_GUARDS|CLOSE_INTERMEDIATE_GUARDS|close_guards' loop.py`.
If two lists exist, T07's AC4 already covers the case (add to
both); document the topology in the WU's RESULT for the
retrospective.

### Skill-discovery symlink topology

T08 AC2 spec creates `.claude/skills/learnings-suggest` as a
relative symlink pointing to
`../../.specfuse/skills/learnings-suggest/SKILL.md`. The path
topology matches existing skill symlinks; the §10 pre-flight
(`ls -la .claude/skills/`) confirms before authoring. **Confirm
acceptable shape**: `ls -la .claude/skills/gate-status
.claude/skills/unblock-wu` and verify the new symlink mirrors
both. A discovery surface that doesn't mirror existing skills
ships an undiscoverable skill.

### Methodology.md section structure is stable

T09 AC1/AC2 attach prose to existing sections in
`docs/methodology.md`. If methodology.md is being concurrently
restructured by another feature (e.g. predicate-v2 design
deferred per PLAN.md "Scope OUT" might land before this
feature's terminal close), the attachment site shifts. **Confirm
before arming T09**: `grep -nE '^## ' docs/methodology.md` and
verify §3 ("Deterministic auto-close path (FEAT-2026-0018)")
exists with the expected structure. T09's escalation #2 is the
correct response to detected restructure — emit `status:
blocked` and let the operator sequence the two changes.

### Roadmap-archive anchor convention

T09 AC3 spec uses `<a id="feat-2026-0016"></a>` as the anchor
form. The §10 pre-flight (`grep -nE '<a id=' roadmap-archive.md`)
confirms whether this matches the existing archive convention.
**Confirm before arming T09**: if existing archive sections use
a different anchor format (e.g. lowercase with hyphens, or
plain heading-anchors without explicit `<a>` tags), T09 must
match the prevailing format. AC3's escalation trigger names
this as a stop condition.

### T07 first-exercise hazard on G3-CLOSE

T07's `assert_failure_class_breakdown_when_failures_present`
runs for the first time against this feature's own G3-CLOSE
WU. If T07's regex (`^#{3} Failure-class breakdown\b`) doesn't
match the heading T07's helper renders (because the helper's
output uses a different prefix or the regex's word-boundary
behavior differs from intent), the guard misfires on the very
WU it was designed for. **Confirm before arming G3-CLOSE**:
read T07's helper output (`### Failure-class breakdown`)
against the guard's match regex; the dispatch is the smoke
test, but the smoke test happens on a single WU's commit and
recovering from a misfire is one re-arm cycle at minimum. G3
escalation #5 names this exact shape as a stop condition.

## Cross-repo contracts

Invented values introduced by gate 3. The "Source" column is
where the contract lives; the "Used by" column lists the
consumers downstream. Verify each before arming.

| Value | Type | Source | Used by | Status |
|-------|------|--------|---------|--------|
| `### Failure-class breakdown` | RETROSPECTIVE.md heading literal | T07 AC2 (`assert_...present` regex); T07 AC1 (`summarize_attempt_failure_classes` output) | G3-CLOSE renders it; future close WUs of every feature render it via the guard | **unverified** — first use; lock at v1 literal string |
| `summarize_attempt_failure_classes(feature_dir, gate_n=None) -> str` | driver helper signature | T07 AC1 | G3-CLOSE invokes (per AC3); future close WUs may import directly | **unverified** — first use; lock at v1 signature |
| `assert_failure_class_breakdown_when_failures_present` | `CLOSE_GUARDS` entry name | T07 AC2/AC3 | driver dispatch on every close-intermediate + close WU dispatch | **unverified** — first use; lock at v1 string |
| `[meta/learnings-suggest]` tag prefix | LEARNINGS.md entry tag | T08 §4 candidate-draft template | operator-promoted entries inherit; future readers grep for the tag | **unverified** — first use; lock at v1 form |
| `learnings-suggest` skill name | filesystem + skill-discovery name | T08 AC1 SKILL.md frontmatter `name:`; AC2 symlink basename | discovery layer at `.claude/skills/learnings-suggest`; operator invocation `/learnings-suggest` | **unverified** — first use; lock at v1 string |
| `--min-wus N` flag (default 2) | T08 skill argument | T08 §3 documentation | operator's threshold override at invocation time | **unverified** — first use; v1 default value |

The new cross-repo contracts column this gate introduces is
**heavy** — six unverified-at-v1 strings vs. gate-2's one. This
is structural: gate 3 is where the data layer's downstream
surfaces crystallize, and crystallization means new vocabulary.
The operator's arm-time review should ratify each string
explicitly; once gate-3 ships, future features grepping for
these strings see them as load-bearing.

## Predicate self-check

```
FEAT-2026-0016  predicate=v1
  G01  auto=False
    reasons:
      - blocked_human_in_chain: T03 escalated 2026-06-14
      - plan_next_overrun: G1-PLAN actual=$3.56 planned=$1.50 ratio=2.37x
      - gate_budget_exceeded: total=$10.17 budget=$10.00
    metrics:
      gate_total_cost: $10.17
      gate_budget: $10.00

FEAT-2026-0016  predicate=v1
  G02  auto=True
    metrics:
      gate_total_cost: $1.43
      gate_budget: $12.00
```

Two recursive-dogfood data points on the predicate this
feature's data layer underwrites. **Gate 1 auto=False on three
reasons**: T03's correct spec-bug-blocked diagnosis
(blocked_human_in_chain, intermediate-close informational),
G1-PLAN's $3.56 vs $1.50 plan (plan_next_overrun at 2.37×
crosses criterion 5's 1.5× ceiling), and gate-1's total $10.17
narrowly exceeding the $10.00 budget (criterion 6). Each is a
real signal; the operator chose re-arm with revised spec rather
than abandon — the predicate's auto-false was the right call.
**Gate 2 auto=True**: clean three-consumer surface, T04+T05+T06
all under-plan, gate-total $1.43 of $12.00 budget. The
auto-close was correct; the close-intermediate ceremony was
skipped via `evaluate_auto_close` and `plan-next` (this WU's
parent G2-PLAN session) dispatched directly.

**Gate-3 prediction.** If T07/T08/T09 each land cleanly in one
attempt with cost ≤ 1.5× plan and G3-CLOSE itself stays under
$2.25 (1.5× of $1.50), the predicate self-fires on G3-CLOSE's
own terminal-gate-boundary evaluation and the close WU's
dispatch is skipped — the stub-retrospective path runs instead.
The recursive-dogfood property at terminal scale: the predicate
auto-closes a feature whose own data layer it consumes for the
first time at full payload fidelity. Whether the close path
runs ceremony or stub, G3-CLOSE's spec is unchanged — both
paths satisfy AC1/AC2/AC3 by different mechanisms (agent
authors vs. driver writes the stub).

## Summary

Three substantive WUs (T07 close-ceremony breakdown surface +
guard, T08 `/learnings-suggest` cross-feature signature
clusterer skill, T09 methodology docs + roadmap-archive of the
folded original 0016 scope) consuming the gate-1 data layer at
the close-ceremony / cross-feature / docs surfaces. T07 is the
single forward-design code WU here (two new driver functions +
one CLOSE_GUARDS wire; medium effort, $1.00); T08 is skill-side
file creation + one new symlink ($1.20, medium); T09 is
documentation + roadmap edits ($0.50, low). All three depend
only on gate-1 contracts (T01 events, T02 frontmatter, T07's
helper consumed by G3-CLOSE) — no inter-WU ordering required;
T07/T08/T09 can dispatch in parallel from the ready frontier.
G3-CLOSE then depends on all three.

The Cross-repo contracts table's six **unverified** entries are
all first-use strings (T07's helper signature + guard name +
heading literal; T08's skill name + tag prefix + flag) — lock
each at v1 string-literal during arm-time review; future
consumers branch on the exact literals. The recursive-dogfood
hazard noted under "Open verifications" (T07 first-exercise on
G3-CLOSE) is the single highest-risk item in this gate; the
mitigation is the §10 helper-duplication pre-flight discipline
T07 already requires, plus G3-CLOSE's escalation #5 (don't
hand-author the breakdown to placate a regex misfire).
