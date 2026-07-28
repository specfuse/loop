---
id: FEAT-2026-0040/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Close gate 3 and the feature — terminal ceremony and verdict

**Objective.** Close the feature: re-run every oracle fresh, write the terminal
retrospective, promote lessons, update the roadmap, and record the terminal verdict.

**Context.** Correlation ID `FEAT-2026-0040/G3-CLOSE`. **This is a `status: draft`
placeholder.** It exists so the linter reads gate 3 as the terminal gate and gate 1
as non-terminal; without it, every later gate's `work_units` would be empty and gate
1 would be misread as terminal, rejecting its `close-intermediate` → `plan-next`
sequence.

Gate 2's `plan-next` inserts gate 3's substantive work units **before** this entry
and updates its `depends_on`. Whoever arms gate 3 should rewrite this body against
what gate 3 actually contains — the acceptance criteria below are the floor every
terminal close in this project carries, not a finished specification.

**What gate 3 is expected to own**, per `PLAN.md`: the fingerprint-keyed issue
lifecycle, the `specfuse-monitor run` CLI, and the local plus GitHub Actions runner
surfaces.

**Two things gate 3 inherits and must not rediscover.**

`escalation.py` already ships the issue machinery — `_correlation_marker`,
`_find_existing_issue`, `_default_runner`, idempotent find-then-create — and gate 3
**reuses it** rather than building a parallel one. It also inherits its known
weakness, recorded in FEAT-2026-0046's retrospective: GitHub's issue search index
does not reliably tokenise HTML-comment content, so a search returning nothing
silently files a duplicate on every retry. That is the one property the issue
lifecycle cannot afford to get wrong, and gate 3 must address it rather than adopt it
unexamined.

`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`: `gh` returns auth errors inside
`claude -p`, so this gate's central surface produces **zero in-loop evidence**. Gate
3 was isolated for exactly this reason. A hedged verdict here is the expected
outcome, not a failure — what would be a failure is claiming `met` on the strength of
a stubbed runner.

**Close obligations.**

1. **Oracles re-run fresh (§1)** — every oracle the feature's criteria name, across
   all three gates, with full commands and exit codes read directly.
2. **Hedged follow-up record (§2)** — on `met_locally`, a named record per unmet
   criterion: the criterion, why it is unverifiable here, and the exact re-run
   condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3)** — enumerate every addition, removal,
   and rename across all three gates. This feature adds a package, a CLI entry point,
   a schema field, and a GitHub Actions workflow surface, so the list will be long
   and at least one entry is breaking.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists and is non-empty.
2. A `## Cost analysis` section reconciles `planned_cost_usd` across all three gates
   against actual spend from `events.jsonl`, with the delta named and the per-gate
   split shown — a feature-wide figure that blends three gates hides where the
   variance came from.
3. A `## What the loop did NOT verify` section enumerates each deferred criterion
   with why and where it is actually verified. **This will not be empty.** The real
   `gh` issue lifecycle and the adapters against a live Azure environment are both
   unverifiable here.
4. Every oracle named by gates 1–3 is re-run with its command and exit code recorded.
5. A consumer-visible contract-change enumeration is present per obligation 3, with
   breaking entries marked.
6. The fingerprint contract is verified end to end: a run producing findings from two
   different targets on one component yields **two** issues, not one. This is the
   binding constraint inherited from FEAT-2026-0069 and the single thing most worth
   proving before this feature is called done.
7. The duplicate-filing risk inherited from FEAT-2026-0046 is addressed and the
   evidence recorded — not deferred silently.
8. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
9. The roadmap detail section for FEAT-2026-0040 reflects what was actually built,
   and the features it unblocks — 0038, 0041, 0042, 0043 — are named.
10. This unit's **frontmatter** carries a `verdict:` field, one of `met`,
    `met_locally`, `partially_met`, `not_met`.
11. If any work unit recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by any substantive work unit — this unit closes
the feature, it does not patch the work. `PLAN.md`'s `status` field: the driver owns
the terminal flip via `fire_terminal_flips`, gated on the verdict. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus the oracle re-runs in criterion 4 and
the end-to-end fingerprint check in criterion 6.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle cannot be re-run; criterion 6 cannot be exercised even against a stub, which
would mean the fingerprint contract was never actually proven; or the
contract-change list requires a human acknowledgment that has not been given. Record
`met_locally` with the §2 follow-up record rather than claiming `met` for anything a
stubbed runner is the only evidence for.
