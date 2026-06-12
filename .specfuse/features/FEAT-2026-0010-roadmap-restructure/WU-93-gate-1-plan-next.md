---
id: FEAT-2026-0010/G1-PLAN
type: plan-next
effort: high
status: done
attempts: 1
duration_seconds: 310.732
cost_usd: 2.409882
input_tokens: 28
output_tokens: 20563
---

# Gate 1 plan-next — detail Gate 2 or close it out

**Objective.** Either detail Gate 2's substantive work units
(driver auto-archive hook + back-link rendering polish), OR explicitly
close Gate 2 out as not-needed based on what Gate 1 actually shipped.

**Context.** Correlation ID `FEAT-2026-0010/G1-PLAN`. Read
`RETROSPECTIVE.md` (Gate 1 section), `.specfuse/LEARNINGS.md` (latest
entries), and `PLAN.md`'s scope-OUT to know what was deferred to
Gate 2 by design. Gate 2's PLAN-level placeholder is "driver
auto-archive hook + back-link rendering polish"; revisit that under
the methodology's binding rule that the prior gate's plan-next owns
the next gate's WUs.

**Acceptance criteria.**
1. `GATE-01-REVIEW.md` exists in this feature folder and contains:
   what Gate 1 delivered (one paragraph), whether Gate 2 should be
   retained or closed out (one paragraph with reasoning), and — if
   retained — the proposed substantive WUs for Gate 2 with one-line
   rationale each (drafted, not yet written).
2. If Gate 2 is retained: every WU named in the review has a
   corresponding `WU-NN-<slug>.md` file written into this feature
   folder with `status: draft`, ready for the operator to flip to
   `pending` after review. The WU files follow `.specfuse/skills/
   authoring-work-units/SKILL.md`'s five-section contract.
3. If Gate 2 is retained: `PLAN.md`'s `gate: 2` `work_units:` list is
   updated to reference the new WU files with `depends_on` edges.
4. If Gate 2 is closed out: `GATE-02.md`'s frontmatter `status:` is
   set to `passed`, and `GATE-02.md`'s body is rewritten to a single
   paragraph explaining why nothing was needed (Gate 1 covered it).
   `PLAN.md`'s `gate: 2` entry stays in the graph for audit but with
   an empty `work_units:` list.
5. Cross-repo contracts table: any value in the proposed Gate 2 WUs
   that references an external system's vocabulary is listed in the
   review document with its authoritative source and a checked /
   unchecked status. None can be marked checked unless the WU author
   actually opened the source and confirmed the value (per
   `.specfuse/skills/authoring-work-units/SKILL.md` rule 8).

**Do not touch.** Gate 1 WU files (they are done). Source code in
`.specfuse/scripts/`. Skills written in Gate 1 (T02, T03). Tests for
those skills. Templates. Rules. `.git/`. The driver. The feature
branch's commit history.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`
(`lint_plan.py` against this feature folder). All drafted WUs must
lint clean as `status: draft`.

**Escalation triggers.**
- If `RETROSPECTIVE.md` (Gate 1 section) is missing or empty, emit
  `status: blocked` — planning Gate 2 with no Gate 1 evidence is
  invention.
- If the close-out path is taken but Gate 1 did not actually deliver
  the deferred scope (e.g. driver auto-archive hook still missing
  while no Gate 2 follow-up is proposed), emit `status: blocked` —
  closing out a gate whose work is genuinely needed but un-done is the
  hollow-pass failure mode.
- If any cross-repo contract value can't be verified against an
  authoritative source, leave its row unchecked and do NOT mark the
  AC complete; close ceremony will not arm an unverified contract.
