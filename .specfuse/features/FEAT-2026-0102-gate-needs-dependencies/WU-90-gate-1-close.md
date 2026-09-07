---
id: FEAT-2026-0102/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 10.00
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0102-gate-needs-dependencies/RETROSPECTIVE.md
model: opus
effort: high
gate_set: plannext
driver_version: 0.15.0
verdict: met
started_at: 2026-09-07T20:13:56.994165+00:00
duration_seconds: 1671.98
cost_usd: 7.733794
input_tokens: 162
output_tokens: 59375
---

# Gate 1 close — demonstrate `needs:`, measure the saving, revise the lesson it falsifies

**Objective.** Terminal close of FEAT-2026-0102: demonstrate each behaviour in
`GATE-01.md`'s definition of done in this session, record the measurements
against the recorded baseline, and document the new key for target projects.
Measure; do not decide the verdict.

**Context.** Depends on T01, T02, T03. Binding:
`.specfuse/rules/close-discipline.md`. The driver owns the terminal `PLAN.md`
status flip and the roadmap flip; a separate judge session reads the evidence
after this close's squash and decides. `PLAN.md` § Notes holds the baseline this
feature set out to beat: 118s across the `code` set, 93% of it duplicated test
execution, from `[FEAT-2026-0051/G1-CLOSE]`. Run `specfuse lint --closing`
before reporting `complete`.

**One lesson this feature falsifies, and it must be revised, not merely cited.**
`[FEAT-2026-0051/G1-CLOSE]` closes with "expect probe cost to be dominated by
whichever gates duplicate each other's work, which is a `verification.yml`
authoring concern rather than a driver one." The measurement half of that entry
stands and should be preserved. The conclusion half is what this feature
disproves — the duplication was a gap in the gate-set contract, and the fix was
in the driver. Amend the entry in `.specfuse/LEARNINGS.md` in place rather than
appending a contradicting one; a corpus holding both readings teaches neither.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table: for each bullet in `GATE-01.md`'s definition of done, the command run in this session and its exit status; the `code`-set wall clock before and after, next to the 118s baseline, with the percentage reduction stated; and the count of `Ran <N> tests` lines in a full smoke run (expected: 1).
- `## Retrospective`: whether the inert-first ordering (T01/T02 before T03) actually held the oracle stable — read the `attempt_outcome` events for T01 and T02 and say whether either was verified under a gate set it had itself changed.
- `## Cost analysis` reconciling `planned_cost_usd` ($29.00, per-WU) against `events.jsonl`, naming the delta and any restart count.
- `## What the loop did NOT verify`: at minimum, whether the Maven/jacoco shape from specfuse/specfuse#162 was exercised anywhere — this repo has no Java gate, so the downstream case is deferred to clabonte/generator#1713. State criterion, reason, and where it actually gets checked, for each entry.
- `## Consumer-visible contract changes`: the `needs:` key is new scaffold-visible surface for every target project. Enumerate it, update the shipped `verification.yml.example` and the `CHANGELOG.md` entry, and confirm the reworded authoring rule reached the canonical `plugins/` copy.
- `## Lessons`: the `[FEAT-2026-0051/G1-CLOSE]` amendment above, plus at most one new entry.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, `verification.yml`, the verification skill
(T01-T03 own them); `.git/`, secrets. This WU writes only its close record and
the documentation the criteria above name.

**Verification.** The `plannext` gate set plus the oracles above.

**Escalation triggers.** Emit `status: blocked` if the measured `code`-set wall
clock is not materially below the 118s baseline — a close that reports the
headline saving without the measurement backing it is the hollow shape this
feature exists to remove. Also block if amending `[FEAT-2026-0051/G1-CLOSE]`
would contradict a second LEARNINGS entry not identified here; name it.
</content>
