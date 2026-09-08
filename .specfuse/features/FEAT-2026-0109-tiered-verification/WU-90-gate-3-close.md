---
id: FEAT-2026-0109/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 8.00
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/RETROSPECTIVE.md
---

# Gate 3 close — terminal close of FEAT-2026-0109

**Objective.** Terminal close of the feature: demonstrate gate 3's definition of
done, enumerate the consumer-visible contract this feature changed across all
three gates, reconcile the whole feature's cost, and record the lessons.
Measure; a separate judge session reads the evidence and decides.

**Context.** Depends on T08. Binding: `.specfuse/rules/close-discipline.md` —
all five sections, not only §1. Append to the existing `RETROSPECTIVE.md` under
a `## Gate 3` heading; gate 1's and gate 2's sections are not yours to edit
(this is the incremental edit the `produces:` path names — the file exists and
each close adds one gate's section to it). Run `specfuse lint --closing` before
reporting `complete`. The driver owns the terminal `PLAN.md` and roadmap flips.

**This is the terminal close, and three obligations follow from that.**

1. **A feature-level `verdict` in this WU's frontmatter, written from the
   measurements.** On a terminal gate the driver dispatches a separate judge
   session once this close has passed its deliverable guards; it is given the
   definition of done, the per-criterion state, the gate diff and your
   `## Measurements` — and deliberately not your `## Verdict` or
   `## Retrospective`. So write the measurements in full, with commands and exit
   codes, and treat your own `verdict:` as advisory (`close-discipline.md` §1).
2. **The `close-discipline.md` §3 enumeration spans all three gates, not just
   gate 3.** Gate 2's `RETROSPECTIVE.md` already staged its seven-item list
   under `### Contract surface gate 2 changed`, explicitly so this close does
   not re-derive it; gate 1's section carries its own. Add gate 3's, reconcile
   the three into one list, and append each item to `CHANGELOG.md`'s
   `Unreleased` section classified `added` / `changed` / `fixed` / `breaking`
   and carrying `FEAT-2026-0109`. Write it once, from one understanding, in both
   places. If the reconciled list is genuinely empty, write the exact `n/a` line
   rather than an empty enumeration — but a feature that added a
   `verification.yml` key, a gate frontmatter block and driver event types is
   not that case.
3. **`close-discipline.md` §2 is binary and unfinished work is tracked, not
   hedged.** There is no partial credit. If any criterion is not met, write
   `FOLLOW-UPS.md` with one `### `-headed entry per failed criterion carrying
   the criterion verbatim, the command run and its exit code, and the re-run
   condition that would satisfy it; the driver files one tracked issue per
   entry. A criterion only observable in production is a `## Post-merge
   checklist` line in `PLAN.md`, never an acceptance criterion.

**The restart count is this feature's headline number, and gate 3 predicts it.**
Gate 1 paid 3 restarts, gate 2 paid 4 — 7 across the feature, against 49
repo-wide across 14 features (`GATE-03.md` § "What this is worth"). Gate 3's own
count should be exactly **1**: T08's squash touches the driver while `G3-CLOSE`
is still pending, so the pre-T08 halt fires once, and the restarted driver is
the first one to pin. Report the actual count against that prediction, and say
plainly whether this close itself ran from a pinned build — that is the one
observation only the terminal close is positioned to make.

**Three things gate 1 and gate 2 both deferred to "the next failure".** Both
closes recorded `baseline_attribution` firing **zero** times in production, one
genuinely-narrowed attempt at n=1, and no broad run ever going red. If those are
still zero, say zero plainly and say what a zero over three gates does and does
not establish — do not let three gates of "checked instead by unit tests" close
as though it were production evidence.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 3` and a `## Measurements` table: for each bullet of `GATE-03.md`'s definition of done, the command run in this session and its exit status.
- This gate's `feature_oracle` verdict recorded in `## Measurements` as a `### feature_oracle: PASS` / `FAIL` line (`close-discipline.md` §1; closing lint `close-n`).
- `## Measurements` states gate 3's restart count against the predicted 1, the feature's total across all three gates, and whether this close session itself ran from a pinned build — with the evidence for the last.
- `## Measurements` restates, across all three gates, the counts gate 1 and gate 2 each deferred: `baseline_attribution` firings, attempts that genuinely narrowed, and broad runs that went red on narrow-passed work — each with what the number establishes and what it does not.
- `## Consumer-visible contract changes`: the reconciled enumeration across gates 1, 2 and 3, built from gate 1's and gate 2's staged lists rather than re-derived, with the matching `CHANGELOG.md` `Unreleased` entries carrying `FEAT-2026-0109`.
- `## Cost analysis` reconciling `PLAN.md`'s `planned_cost_usd` and every WU's `planned_cost_usd` against `events.jsonl` across all three gates, naming the delta. `GATE-02-REVIEW.md` Q4 and `GATE-03-REVIEW.md` Q3 flag `planned_cost_usd` as stale; report the arithmetic and say whether it was corrected.
- `## What the loop did NOT verify`: criterion, reason, and where each actually gets checked.
- `## Lessons`: at most two entries.
- Per-criterion state recorded per `close-discipline.md` §5 — each criterion's oracle, its `kind` (`narrow` / `broad`) and its `state`, written by this close and never inferred (closing lint `close-l`).
- Oracles re-run fresh, exit codes read directly in this session: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR; the three gates' `feature_oracle` commands each report `OK`.
- `specfuse lint --closing` passes before this unit reports `complete`.

**Do not touch.** `specfuse/`, `tests/`, `.specfuse/rules/`,
`.specfuse/templates/` — T08 owns gate 3's implementation and this unit writes
no code. `RETROSPECTIVE.md`'s `## Gate 1` and `## Gate 2` sections;
`GATE-01.md`, `GATE-02.md`, and gate 1's and gate 2's work units. `.git/`,
secrets. This WU writes its close record, `CHANGELOG.md`'s `Unreleased`
entries, and — only if a criterion is not met — `FOLLOW-UPS.md`.

**Verification.** The `plannext` gate set, plus gate 3's `feature_oracle` and
the fresh oracle re-runs named above.

**Escalation triggers.** Emit `status: blocked` if the consumer-visible
enumeration cannot be reconciled across the three gates without editing gate 1's
or gate 2's `RETROSPECTIVE.md` sections — the staged lists are inputs to be read,
and rewriting them is outside this unit's boundary. Also block if this session
cannot determine which build it is running from: a terminal close that cannot
answer that question cannot honestly report on a gate whose whole subject is
that question.
