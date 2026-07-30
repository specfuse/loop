---
id: FEAT-2026-0054/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
# Load-bearing close (close-discipline.md): carries §1 fresh oracle re-runs and §3
# consumer-visible contract enumeration (close-discipline.md §4 itself changes for every
# scaffold consumer). The auto-close predicate must not skip it — and dispatching it
# dogfoods T03's skeleton, since this repo's driver runs from source.
auto_close_disabled: true
---

# Gate 1 close — the closing contract has one home and two cheap enforcement moments

**Objective.** Terminal close for FEAT-2026-0054: verify the registry/lint/skeleton chain
end-to-end, record the verdict, and enumerate what changed for scaffold consumers.

**Context.** Terminal gate close, depends on T04. Binding rules:
`.specfuse/rules/result-contract.md`, `verification-discipline.md`, `operator-escalation.md`.
Run `specfuse-lint --closing` on this feature before reporting — this feature shipped it;
close accordingly.

**Acceptance criteria.**

- **Oracles re-run fresh (§1):** full `python3 -m unittest discover -s tests -v`, `ruff`,
  `bandit`, coverage — commands run this session, exit codes read directly, never T01–T04
  self-reports.
- **End-to-end chain proven on a fixture feature:** dispatch a plan-next and a close WU against
  a fixture (or this feature's own close dispatch, observed) — skeleton files pre-created
  correctly, `specfuse-lint --closing` exit 1 names findings with their post-squash guard, then
  exit 0 once satisfied, and the post-squash guards pass on the same tree the lint approved
  (lint-approves ⇒ guards-pass, the property the whole feature exists for).
- **Idempotency re-verified** on a feature dir with pre-existing retrospective content (T03's
  non-destructive property, exercised fresh, not inherited from T03's tests).
- **Historical-close regression:** `specfuse-lint --closing` exits 0 on
  `FEAT-2026-0072-structural-invariant-guards`.
- A `## Cost analysis` section is present in `RETROSPECTIVE.md`, reconciling `planned_cost_usd`
  (PLAN.md $28.00 and per-WU frontmatter) against actual spend from events.jsonl, delta named.
- A `## What the loop did NOT verify` section is present, enumerating each deferred criterion
  (expected entry: the portfolio success measure — zero closing-format refusals — verifies on
  the next generator feature, not in this repo; name that re-run condition). If empty, write
  `(nothing — every acceptance criterion was verified in-loop)`. More than 2 entries or >30% of
  the gate's criteria flags single-gate sizing under `## What I'd change`.
- **Consumer-visible contract changes enumerated and blocked on operator acknowledgment (§3):**
  `close-discipline.md` §4 rewrite, `WU.template.md` close-obligations change, the new
  `specfuse-lint --closing` surface, and the new dispatch side-effect (skeleton files appearing
  in closing-WU squashes) — every scaffold consumer sees these on next upgrade. Not
  `n/a`.
- Hedged follow-up record (§2) if verdict is `met_locally` — per unmet criterion: criterion,
  why unverifiable here, exact upgrade-to-met re-run condition.
- Lessons promoted to `.specfuse/LEARNINGS.md`, or the exact phrase `nothing generalizes`
  recorded in `RETROSPECTIVE.md` (unlikely — the registry-extraction shape and the
  lint-names-the-guard pattern are durable candidates).
- Roadmap row reflects the outcome. (PLAN.md status flip is the driver's — do not write it.)

**Do not touch.** Driver code and data surfaces (`specfuse/loop/**`, `plugins/**` — T01–T04
own them; if verification finds a defect, escalate rather than patching here); other features'
folders; `.git/`.

**Verification.** Fresh full-suite run + `specfuse-lint --closing
.specfuse/features/FEAT-2026-0054-close-ceremony-skeleton` exit 0 +
`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0054-close-ceremony-skeleton`
exit 0.

**Escalation triggers.** Do not close `met` if the lint-approves ⇒ guards-pass property was
only argued from source reading — it must be observed on a real or fixture dispatch. Do not
close on T02/T03's own test runs as the evidence (§1: fresh runs only). If the end-to-end
check finds lint and guards disagreeing on any fixture, that is the feature's core defect:
`not_met`, name the diverging requirement.
