---
feature_id: FEAT-2026-0113
title: Triage assigns a severity
slug: triage-severity
branch: feat/FEAT-2026-0113-triage-severity
roadmap_goal: Triage assigns a severity, so `min_severity` routes instead of stranding
autonomy_default: review
status: active
planned_cost_usd: 43.50
---

# Plan: Triage assigns a severity

Triage classifies an inbound issue into a category (`bug | feature | duplicate |
question | wontfix`) and a confidence, and assesses no severity. Nothing else in the
loop does either: `severity:*` is absent from `labels.LABEL_REGISTRY`, and the triage
marker carries `category` and `confidence` only.

That was survivable while `rules.bugs.min_severity` was unread. It is not now. #3339
made the floor enforce and #3349 let an operator declare what their own labels mean —
and both only reach issues that already carry a severity label, which nothing writes.
Measured on a consumer repository (2026-09-17): of 56 bug-marked, non-human-owned
issues, **31 carry no severity label at all**. Every one was triaged as `bug` by the
agent, left unlabelled, and fails closed under a `medium` floor **permanently** — the
marker is the idempotency key and it is already written, so nothing re-triages them
(#3352).

Two decisions are tangled in "severity" and only the first is automated here.
**Severity-as-labelled is a technical classification**: the consumer repository's own
labels define it as "Does not compile / runtime crash" / "Wrong behavior / missing
element" / "Cosmetic / suboptimal", which are observable properties of an issue body
and the same kind of judgment triage already makes for `category`. **Where the floor
sits stays the operator's** — `rules.bugs.min_severity` is not touched by this feature.

## Record precedence (plan-time declaration — `[FEAT-2026-0045/G1-CLOSE/declare-precedence-between-redundant-records]`)

Severity needs two records: a machine-readable one and a human-visible one. That
lesson requires three declarations at plan time rather than in an implementation WU,
"by implementation time it reads as an arbitrary detail and gets reordered." For
severity they are the same three `category` already has:

- **Authoritative record:** the `severity=` field inside the body marker.
- **Projection:** the `severity:<value>` label, re-derived from the marker, never
  independently authored.
- **Write order:** marker first, label second.

The order follows from the precedence and is what makes the failure mode safe: a
failed label write leaves an issue correctly classified and merely lacking a swatch,
while the reverse order would produce an issue that is labelled and still scans as
carrying no severity. Re-labelling is then idempotent repair, not a second source of
truth — which is exactly how `apply_triage`'s existing "marker present, label missing"
branch already treats the category label.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rn "severity" --include="*.py" specfuse/ | grep -v build/` and
  `grep -rn "label list\|label_list" --include="*.py" specfuse/ | grep -v build/`
- **Verdict:** `found gh label list in labels.py, reusing; no severity writer exists`
- **If reusing:** `specfuse/loop/labels.py:267` already issues
  `gh label list --json name,color,description --limit 1000` through an injected
  runner, inside `provision_labels`, with fail-soft handling for a missing `gh`
  binary, a non-zero exit, and unparseable output. That is exactly the call the
  rubric reader needs, descriptions included. Gate 2 **extracts** that listing into a
  reusable reader rather than issuing a second `gh label list` — FEAT-2026-0049 spent
  two gates building enforcement that already existed one grep away.
- **On the severity half:** every hit is a *reader* — `read_severity_label`,
  `meets_severity_floor`, `resolve_severity_aliases`, `resolve_min_severity`, and
  their `SEVERITY_ORDER` / `SEVERITY_VALUES` vocabulary. No code anywhere writes a
  `severity:*` label or a severity marker field, so the write path is new. This
  feature reads that vocabulary and does not extend it.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

`n/a — this feature flips no lint check to ERROR, promotes no WARNING to blocking,
and asserts no "zero issues" close predicate.` The word "severity" here is the
severity **of an inbound issue**, a different axis from a finding's severity, which is
what §2 governs. `rules.bugs.min_severity` is read, never changed.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0113/T01
        file: WU-01-dual-shape-marker-reader.md
        depends_on: []
      - id: FEAT-2026-0113/T01H
        file: WU-01H-parse-marker-fails-closed.md
        depends_on: [FEAT-2026-0113/T01]
      - id: FEAT-2026-0113/T02
        file: WU-02-marker-corpus-and-round-trip.md
        depends_on: [FEAT-2026-0113/T01H]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0113/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0113/T01, FEAT-2026-0113/T01H, FEAT-2026-0113/T02]
      - id: FEAT-2026-0113/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0113/T02H
        file: WU-02H-oracle-tracer-bullet.md
        depends_on: []
      - id: FEAT-2026-0113/T03
        file: WU-03-severity-rubric-reader.md
        depends_on: [FEAT-2026-0113/T02H]
      - id: FEAT-2026-0113/T04
        file: WU-04-marker-then-label-write-path.md
        depends_on: [FEAT-2026-0113/T02H]
      - id: FEAT-2026-0113/T05
        file: WU-05-classify-severity-fails-closed.md
        depends_on: [FEAT-2026-0113/T03, FEAT-2026-0113/T04]
      - id: FEAT-2026-0113/T06
        file: WU-06-run-records-severity-end-to-end.md
        depends_on: [FEAT-2026-0113/T05]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0113/G2-CLOSE-INTERMEDIATE
        file: WU-90-gate-2-close-intermediate.md
        depends_on: [FEAT-2026-0113/T02H, FEAT-2026-0113/T03, FEAT-2026-0113/T04, FEAT-2026-0113/T05, FEAT-2026-0113/T06]
      - id: FEAT-2026-0113/G2-PLAN
        file: WU-91-gate-2-plan-next.md
        depends_on: [FEAT-2026-0113/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      # Scaffolded now so lint reads gate 1 as non-terminal.
      # G2's plan-next fills in the substantive WUs above this entry.
      - id: FEAT-2026-0113/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on: []
```

## Notes

- **Gate 3 (backfill)** is deliberately skeletal; gate 2's `plan-next` drafts it.
  **Gate 2 was drafted by `FEAT-2026-0113/G1-PLAN`** from what gate 1's
  retrospective learned about the marker's shape in the wild — four substantive
  units (T03 rubric reader, T04 write path, T05 classification, T06 the run) plus
  its closing pair. The drafting decisions and the questions left open for the
  arming reviewer are in `GATE-02-REVIEW.md`, not restated here.
- **Gate 2's sketch, not its plan.** Extract a label reader from `labels.py`; read the
  rubric from each `severity:*` label's own `description`; fold severity into the
  existing triage call so no extra session is dispatched; write marker then label per
  the precedence above; a low-confidence severity writes **no** label and fails closed
  to a human, the same shape `apply_triage` already uses when `auto=True` downgrades a
  low-confidence category to `question`.

  **Rubric source — revised at the gate-2 arm checkpoint.** The rubric has two
  sources and the repository always wins. A repository defining any `severity:*`
  label supplies the rubric through its own label descriptions, and specfuse
  provisions nothing there — so a project already labelling `severity:major` /
  `severity:minor` is never handed a second overlapping set. A repository defining
  **none** gets specfuse's published `DEFAULT_SEVERITY_RUBRIC` and the four labels
  provisioned on first use, through the same `gh label create … --force` shape
  #3244 established — required rather than cosmetic, since `gh issue edit
  --add-label` fails against a label that does not exist.

  The draft originally read label-absence as an opt-out. That made the feature inert
  by default: a repository that never invented its own severity labels would get no
  severity forever, so `min_severity` would keep stranding exactly the issues #3352
  measured. The reasoning conflated two things — **where the floor sits**
  (`rules.bugs.min_severity`) must be the operator's, since it gates unattended
  merges, but **what `high` means** need not be; severity schemes in wide use ship
  vendor-written definitions and let the operator pick the threshold against them.
  Only the first constraint is load-bearing, and it is untouched by either branch.
- **Gate 3's sketch, not its plan.** The 31 measured issues are already marked, so the
  marker's idempotency means nothing revisits them. Backfill re-reads already-marked
  issues carrying no severity field, under an explicit mode rather than on every run.
  Without it this feature classifies new issues and leaves the measured backlog exactly
  as stranded, which is the problem that motivated it.
- **Risk accepted deliberately.** This puts an agent on the value that gates unattended
  merges, in a repository where `rules.bugs.automerge` is `"on"`. Bounding it: the
  rubric is a written definition per value — the operator's own words where they
  defined labels, specfuse's published defaults where they did not — the floor
  itself stays the operator's in both branches, low confidence fails closed, the
  label stays visible and human-overridable, and `max_open_prs` (#3351) plus
  `max_diff_lines` cap blast radius regardless. `autonomy_default: review` is set for
  the same reason — a wrong arm on a marker format change orphans every issue written
  under it.

## Mid-gate insertions

- **`FEAT-2026-0113/T01H` (hygiene, inserted after T02 escalated).** T02 reported
  `agent_reported_blocked`: T01's tolerant reader made `parse_marker` raise
  `KeyError` on a marker missing `confidence`, where the anchored regex it
  replaced returned `None` — a regression against T01's own "byte-identical"
  criterion, and a fail-open one, since `parse_marker`'s three callers sweep
  every open issue. T02 obeyed its Do-not-touch clause and escalated rather than
  patching a sibling unit's code. T01H carries the fix as its own dispatched and
  verified unit; T02 re-runs unmodified behind it and its corpus is what proves
  the fix. This is `authoring-work-units` §7's hygiene pattern, chosen over
  re-arming a `done` T01 or widening T02's boundary — the boundary is what
  produced the correct escalation, and eroding it teaches the next unit to patch
  quietly instead of reporting.

## Assumptions (drafted under the interview's escape hatch)

The operator asked for recommendations on every remaining decision. Each choice below
was taken by this draft, not made by them, and is here for the gate-1 reviewer:

- **Gate 1 is two work units, not three.** The reader change is small; the only
  meaningful seam is splitting the corpus proof from the tracer.
- **`parse_marker` keeps its `(category, confidence)` return type.** Its callers in
  `triage.py`, `bug_lane_state.py` and `providers/triage.py` are untouched; severity
  arrives through a new `parse_marker_fields`. **Watch the caller ratchet** — if
  `parse_marker` ends up with no production caller it fails `tests/
  test_caller_check_ratchet.py`, which is what caught `severity_from_labels` on #3349.
- **The rubric reader sits in gate 2, not gate 1.** It is a pure extraction with no
  behaviour change, which is gate-1-shaped, but it has no consumer until gate 2 and
  landing an unused extraction is exactly what the caller ratchet flags. Flagged as
  genuinely uncertain at draft time; the reviewer may move it.
- **Red-test-first (§12) applies to both gate-1 units**, no exemption claimed — both
  introduce behaviour.
- **`judge_disabled` is not set.** Every gate-1 criterion is judgable from the gate's
  diff and a test run.
- **Severity labels are provisioned only into a repository that defines none.**
  Revised at the gate-2 arm checkpoint: the original assumption ("repo-owned, and
  not defining them is how a project opts out") made the feature inert by default
  and is withdrawn. The four specs live as their own named collection rather than
  being folded into `LABEL_REGISTRY`'s existing entries, so no existing caller of
  `provision_labels` starts creating severity labels as a side effect.
- **Planned costs:** gate 1 — T01 $3.00, T01H $1.00, T02 $2.00. Gate 2 (drafted by
  `G1-PLAN`) — T03 $3.00, T04 $3.00, T05 $2.50, T06 $3.00. The closing units take
  the floors `planning-discipline.md` §5 sets rather than a guess — $4.50
  `close-intermediate`, $6.00 `plan-next`, per gate — and the gate-3 terminal close
  is scaffolded at its $5.00 floor. Feature total $43.50. Gate 1's implementation
  came in at 0.27× its estimate (`RETROSPECTIVE.md`); gate 2's estimates are
  deliberately left at the same scale rather than re-anchored on one gate of
  under-run, since `planning-discipline.md` §5's own lesson is that a floor is a
  distribution question.
