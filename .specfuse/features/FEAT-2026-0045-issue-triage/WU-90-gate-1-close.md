---
id: FEAT-2026-0045/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.9.3
started_at: 2026-08-09T22:51:24.271926+00:00
verdict: met_locally
duration_seconds: 1084.647
cost_usd: 5.229417
input_tokens: 110
output_tokens: 36688
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0045: write the retrospective, promote
generalizable lessons, reconcile documentation and the roadmap, and record the terminal
verdict with its hedged follow-up record.

**Context.** Correlation ID `FEAT-2026-0045/G1-CLOSE`. Single terminal gate, so this WU
collapses retrospective, lessons, docs, and verdict into one session. Read `PLAN.md` and
`GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying `close-discipline.md`
§1–§3 obligations is load-bearing. Issue #293's cases: FEAT-2026-0061 lost all 26 close
criteria to an on-plan auto-close, and FEAT-2026-0063 lost its roadmap retitle.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`, `human-output.md`.

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — `close-discipline.md` §4.

## What this close must get right, specific to this feature

**The verdict is expected to be `met_locally`, and PLAN.md says so.** Two acceptance
surfaces are unreachable from inside a dispatched session, and both were named at draft
time rather than discovered here. Do not upgrade the verdict to `met` because the gates
are green — green here means the mechanism works over fixtures, which is a smaller claim
than "triage works."

**The two hedged entries, each needing a `kind:`** per `close-discipline.md` §2:

1. *Triage against a live GitHub repository.* Not verifiable in-loop: `gh` fails inside a
   dispatched `claude -p` session (sandbox — `[FEAT-2026-0014/T01/gh-claudeP-broken]` as
   corrected by FEAT-2026-0041). Re-run condition: the operator runs `/triage-issues`
   against this repository's own open issues post-merge and confirms markers and labels
   land as designed.
2. *"An agent following T03's prose reproduces the module's routing on an unseen issue."*
   Not verifiable by any test in this repository — the drift test binds prose to
   constants and nothing composes the skill with the module. This is the gap
   `[FEAT-2026-0069/G2-CLOSE]` names, and it is `inherent` to a skill-shaped deliverable
   unless someone builds skill-composition testing, which is not this feature.

Assign each a `kind:` from the four allowed values, written as ``- **kind:** `<value>` ``.
`specfuse lint --closing` refuses a hedged close whose record has an entry with no
`kind:` or an unrecognised one.

**Consumer-visible contract changes (§3) — at least three are known.** Enumerate them
and block on human acknowledgment:

- `specfuse/monitor/issues.has_finding_marker` — a **new public symbol** in the monitor
  package, added by T01 so `triage.py` need not re-type the finding-marker literal.
- **Four new labels** in `LABEL_REGISTRY` (`triage:bug`, `triage:feature`,
  `triage:duplicate`, `triage:wontfix`). Every consumer repository must run
  `provision_labels` to get them — and per PLAN.md's decision, triage is designed to work
  without them, so this is a cosmetic-degradation contract, not a hard requirement. Say
  which it is.
- **The triage marker format** `<!-- specfuse:triage category=… confidence=… -->`, which
  FEAT-2026-0048 will read. Once an issue carries one, changing the format orphans it.

**Report the `auto` dial's home as an unfinished handoff, not a shipped feature.** The
dial is a function argument because `.specfuse/agent-policy.yml` does not exist yet.
FEAT-2026-0044 must wire its policy file to this parameter. Record that explicitly so
0044's drafting session finds it rather than re-deciding it.

**Do not claim this unblocks FEAT-2026-0048 without checking.** 0048's `**Blocked by.**`
block names this feature and FEAT-2026-0046 (done). If this feature's close makes 0048's
remaining blocker set empty, say so and name the roadmap edit the operator should make —
but the flip itself is the operator's, not this WU's.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root with a literal `## Gate 1` heading and a
   literal `## Cost analysis` section reconciling planned against actual — the $18.00 WU
   sum and $23.00 gate budget against the `attempt_outcome` sum in `events.jsonl`, which
   is authoritative. Both headings are checked after dispatch; omitting either costs a
   full re-attempt.
2. Every oracle the feature's criteria name is **re-run fresh** in this session, with full
   commands and exit codes read directly — never a producing WU's self-report
   (`close-discipline.md` §1). This includes `tests.test_skills_vendored_in_sync`.
3. The hedged follow-up record is written with both entries above: criterion, why it was
   not verifiable here, the exact re-run condition that upgrades it to `met`, and a
   `kind:`.
4. `## What the loop did NOT verify` names both deferred surfaces, and additionally names
   that `duplicate` shipped with no detection mechanism by operator decision.
5. Consumer-visible contract changes are enumerated per the section above, with human
   acknowledgment — or the explicit `n/a` line if the enumeration genuinely comes up
   empty, which it should not.
6. The terminal verdict is recorded. If it is `met` rather than `met_locally`, the close
   must justify why both deferred surfaces became verifiable, against PLAN.md's
   expectation that they do not.
7. The handoff to FEAT-2026-0044 (wire `agent-policy.yml` to the `auto` parameter) is
   recorded where 0044's drafting will find it.
8. FEAT-2026-0048's remaining blocker set is stated as measured, with the roadmap edit
   named for the operator if it is now empty. This WU does not perform that flip.
9. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this WU's
   correlation ID. Candidates worth assessing: whether "declare precedence between two
   redundant records rather than treating them as peers" generalizes beyond
   marker-vs-label; and whether the verb-check table PLAN.md carries should become a
   standard section rather than a one-off.
10. `specfuse lint --closing` exits 0.

**Do not touch.** `.git/`, secrets, other features' folders, the roadmap **status column**
for FEAT-2026-0048 (criterion 8 names the edit; the operator makes it). Do **not** flip
`PLAN.md status` to `done` — the driver owns the terminal flips via `fire_terminal_flips`,
on both the dispatched-close and auto-close paths. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus every oracle re-run fresh per criterion 2,
plus `specfuse lint --closing` exiting 0.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:

- An oracle cannot be re-run fresh in this session. Do not substitute a producing WU's
  self-report — that is the §1 failure this criterion exists to prevent.
- The consumer-visible contract enumeration reveals a change nobody planned. Surface it;
  do not fold it into the retrospective prose as if it were expected.
- The cost reconciliation cannot be completed because `events.jsonl` is missing or
  malformed.

Blocked is a respectable outcome — `result-contract.md` rule 4.
