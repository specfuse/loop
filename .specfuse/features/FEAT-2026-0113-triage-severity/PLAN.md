---
feature_id: FEAT-2026-0113
title: Triage assigns a severity
slug: triage-severity
branch: feat/FEAT-2026-0113-triage-severity
roadmap_goal: Triage assigns a severity, so `min_severity` routes instead of stranding
autonomy_default: review
status: active
planned_cost_usd: 20.50
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
      - id: FEAT-2026-0113/T02
        file: WU-02-marker-corpus-and-round-trip.md
        depends_on: [FEAT-2026-0113/T01]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0113/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0113/T01, FEAT-2026-0113/T02]
      - id: FEAT-2026-0113/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units: []
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

- **Gate 2 (classification and the write path)** and **gate 3 (backfill)** are
  deliberately skeletal. Gate 1's `plan-next` drafts gate 2 from what gate 1's
  retrospective actually learned about the marker's shape in the wild.
- **Gate 2's sketch, not its plan.** Extract a label reader from `labels.py`; read the
  rubric from each `severity:*` label's own `description`; fold severity into the
  existing triage call so no extra session is dispatched; write marker then label per
  the precedence above; a low-confidence severity writes **no** label and fails closed
  to a human, the same shape `apply_triage` already uses when `auto=True` downgrades a
  low-confidence category to `question`. A repository that has defined no `severity:*`
  labels gets no severity classification and behaves byte-identically to today —
  defining the labels is how a project opts in.
- **Gate 3's sketch, not its plan.** The 31 measured issues are already marked, so the
  marker's idempotency means nothing revisits them. Backfill re-reads already-marked
  issues carrying no severity field, under an explicit mode rather than on every run.
  Without it this feature classifies new issues and leaves the measured backlog exactly
  as stranded, which is the problem that motivated it.
- **Risk accepted deliberately.** This puts an agent on the value that gates unattended
  merges, in a repository where `rules.bugs.automerge` is `"on"`. Bounding it: the
  rubric is the operator's own label descriptions, low confidence fails closed, the
  label stays visible and human-overridable, and `max_open_prs` (#3351) plus
  `max_diff_lines` cap blast radius regardless. `autonomy_default: review` is set for
  the same reason — a wrong arm on a marker format change orphans every issue written
  under it.

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
- **No `severity:*` entry is added to `LABEL_REGISTRY`.** Severity labels are
  repo-owned, and not defining them is how a project opts out.
- **Planned costs:** T01 $3.00, T02 $2.00. The closing units take the floors
  `planning-discipline.md` §5 sets rather than a guess — $4.50
  `close-intermediate`, $6.00 `plan-next` — and the gate-3 terminal close is
  scaffolded at its $5.00 floor. Feature total $20.50.
