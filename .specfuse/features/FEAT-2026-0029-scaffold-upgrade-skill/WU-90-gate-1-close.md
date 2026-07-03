---
id: FEAT-2026-0029/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 1.25
oracle_env: macos_local
---

# Gate 1 close — terminal close ceremony

**Objective.** Close this single-gate feature in one session: produce
`RETROSPECTIVE.md`, append durable `LEARNINGS`, reconcile docs/roadmap, write the
feature-arc verdict, and include the `## Cost analysis` and
`## What the loop did NOT verify` sections. Driver-side terminal flips (gate →
passed, roadmap row → done, auto-archive) fire automatically when `verdict: met`.

**Context.** This is `FEAT-2026-0029/G1-CLOSE`. Read this feature's
`events.jsonl`, the gate's commits, root `.specfuse/LEARNINGS.md`, and PLAN.md's
`roadmap_goal`. Single-gate, so there is no next gate to forward-design. Reference
the binding rules under `.specfuse/rules/`; honor `result-contract.md` and
`never-touch.md`. The driver owns all git and owns the terminal `PLAN.md status`
flip — do not write it yourself.

Set `verdict: met` ONLY when the roadmap_goal is genuinely achieved AND T01
(helper + passing tests), T02 (SKILL.md), and T03 (symlink + docs + passing bats)
all produced their deliverables in the gate's commits AND you have audited the
`## Cost analysis` section against `events.jsonl`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in this feature folder with: per-WU outcome (T01, T02,
   T03) — what worked / what failed / attempts / final cost; a gate-level summary;
   surprises; and a `## What I'd change` section.
2. Generalizable lessons are appended to `.specfuse/LEARNINGS.md` (or an explicit
   one-line note that none generalized beyond this feature).
3. Docs and the roadmap reflect what was built: the `scaffold-upgrade` skill
   appears in both `docs/skills.md` copies (verify T03 landed it), and this
   feature's roadmap row/detail are consistent with the delivered shape.
4. A `## Cost analysis` section is present, reconciling `planned_cost_usd` (from
   PLAN.md and per-WU frontmatter) against actual spend (from `events.jsonl`),
   with the delta named.
5. A `## What the loop did NOT verify` section is present, enumerating each
   acceptance criterion whose verification was deferred (loop-sandbox limit,
   cross-repo coordination, real-system access). For each: the criterion, why
   deferred, and where verification actually happens. Expected entry: the skill's
   real `git push` / `gh pr create` / watch-CI / merge choreography cannot run
   against a live target repo inside the loop sandbox — it is exercised
   operator-side on first real use; the in-loop proof is limited to the helper's
   unit tests (T01) and the deploy bats (T03). If this list has more than 2 entries
   OR more than 30% of the gate's criteria, flag the single-gate sizing under the
   retrospective's `## What I'd change`. The section is required even if it would
   otherwise be empty (write the explicit "(nothing — …)" line).
6. `verdict:` is set in this WU's frontmatter to a value in the driver's
   `VERDICT_VALUES` (`met` when the arc is genuinely complete; a hedged value
   otherwise, which intentionally skips the terminal-flip guard).

**Do not touch.** Source files owned by T01–T03 (the gate is done; do not re-edit
them to force a pass), `.git/`, secrets. The driver owns all git and the terminal
`PLAN.md status` flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates the driver runs for `type: close`,
plus the hollow-pass guards: `assert_cost_analysis_section_when_met` (AC4),
the closing-deliverables presence checks (AC1/AC2), and
`assert_terminal_flips_fired` (fires on `verdict: met`). Confirm the whole repo
test suite still passes (`python3 -m unittest discover -s tests`).

**Escalation triggers.** If any of T01–T03 did not produce its declared
deliverable, do NOT paper over it with `verdict: met` — emit `status: blocked`
naming the gap. If the cost reconciliation cannot be built because `events.jsonl`
is missing outcome rows, emit `status: blocked`. Blocked is respectable
(`result-contract.md` rule 4).
