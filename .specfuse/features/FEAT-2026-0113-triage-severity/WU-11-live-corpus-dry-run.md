---
id: FEAT-2026-0113/T11
type: human
status: done
attempts: 0
evidence: "Ran the read-only dry run (--apply not passed) as 'python3 -m specfuse.agent.severity_backfill --repo clabonte/generator --limit 5' on 2026-09-18 — module form, since T07's console script is not on PATH until a reinstall. Selected 5 candidates (#1902 #1895 #1893 #1883 #1876), every one carrying a triage marker with no severity= field; #1883 classified severity=critical, the other four returned no usable classification against this repository's single-entry rubric. Selection and per-row markers pasted into GATE-03-REVIEW.md under '## Live-corpus dry run'. This run found the two defects T08H then fixed: --limit bounded the gh issue list window rather than the candidate count (--limit 5 gave 0 candidates, --limit 100 gave 74, --limit 200 gave 84, against 191 open issues), and a zero-candidate run printed nothing. Finding carried to the close and recorded as a prerequisite on issue 3355: #1902 #1895 #1893 already carry a human-applied severity label, so backfill would contradict a person's judgment once a fuller rubric exists."
planned_cost_usd: 0.50
---

# T11 — run the backfill dry-run against the repository where the 31 were measured

**Objective.** You run the backfill in its read-only form against the real
repository, and paste what it selected into `GATE-03-REVIEW.md` — so that at
least one oracle in this feature has read real issue bodies before anything
amends them in bulk.

**Context.** `FEAT-2026-0113/T11`, gate 3. This unit discharges gate 1's carried
residual, which gate 2's retrospective restated rather than retired: *no oracle
in this feature has yet read a real issue body outside this repository.* Gate 2
made it larger — every gate-2 oracle injects a runner, so the `gh label list`
JSON, the classification answer and every write were authored by a test. The
marker shapes, the label sets and the issue bodies a backfill will meet are all
real, and none of them has been read.

It is placed **before** `G3-CLOSE` on purpose (`close-discipline.md` §2): a step
only a person can perform is recorded as work, not softened into the terminal
verdict afterwards. The driver halts here and prints the brief; nothing is
dispatched.

The command is read-only by construction — `T10` criterion 4 is what makes that
true: without `--apply` the run issues zero `gh issue edit` calls and only
prints. Nothing in this unit amends a marker.

**Acceptance criteria.**

1. `specfuse-backfill-severity --repo <OWNER/NAME> --limit 5` is run
   against the repository where `PLAN.md`'s 31 stranded issues were measured, and
   its printed selection is pasted into `GATE-03-REVIEW.md` under a
   `## Live-corpus dry run` heading, with issue numbers and the marker line each
   row was selected on.
2. You confirm on that paste that every selected issue carries a triage marker
   with no `severity=` field, and name any issue that appears there and should
   **not** be touched — a selection that surprises you is the finding this unit
   exists to surface, and is a reason to re-arm `T08` rather than to proceed.
3. The unit is closed with
   `/unblock-wu FEAT-2026-0113/T11 --done --evidence "<the command you ran, the
   repository, and how many issues it selected>"`, which is the evidence
   `G3-CLOSE` quotes.

**Do not touch.** Nothing to bound — this unit runs one read-only command and
edits one review file. Do not pass `--apply`: the writing run is the operator's
decision after the close, not part of this unit.

**Verification.** None dispatched. The driver halts on a `type: human` unit and
never spawns a session for it; `/unblock-wu --done --evidence` is what records it.

**Escalation triggers.** If the dry run selects issues outside the measured set —
issues carrying a harvester finding marker, agent-authored escalations, or issues
whose marker carries a severity already — do not mark this unit done. That is
`T08`'s selection predicate failing against real data, which is exactly what this
unit was placed here to catch, and re-arming `T08` is the response.
