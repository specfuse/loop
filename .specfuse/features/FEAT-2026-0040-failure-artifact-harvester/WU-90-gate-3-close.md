---
id: FEAT-2026-0040/G3-CLOSE
type: close
status: done
attempts: 1
verdict: met
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.6.0
started_at: 2026-07-29T11:58:59.442883+00:00
duration_seconds: 818.557
cost_usd: 7.022222
input_tokens: 98
output_tokens: 59114
---

# Close gate 3 and the feature — terminal ceremony and verdict

**Objective.** Close the feature: re-run every oracle across all three gates fresh,
write the terminal retrospective, promote lessons, update the roadmap, enumerate the
consumer-visible contract changes, and record the terminal verdict.

**Context.** Correlation ID `FEAT-2026-0040/G3-CLOSE`. **This body was rewritten by
`FEAT-2026-0040/G2-PLAN` against what gate 3 actually contains** — it is no longer
the feature-drafting placeholder that asked to be rewritten. Gate 3's four
substantive units are:

| WU | what it shipped, and what its evidence is worth |
|---|---|
| `T08` | The `queue-stalled` broker adapter — queue depth plus age-of-oldest, extending `T05`'s Service Bus surface. **Fully in-loop**; stub transport only |
| `T09` | The fingerprint-keyed issue lifecycle, reusing `escalation.py`'s runner seam and find-then-create while **replacing** its `--search` finder. **Stub-runner evidence only** — deferred criterion D-9 |
| `T10` | `specfuse-monitor run` — config load, target enumeration, provider dispatch, the `resolve_telemetry` seam, watermark fallback, run summary, `--dry-run`. **Dry-run path in-loop; write path stub only** — deferred criterion D-10 |
| `T11` | The local and GitHub Actions runner surfaces plus the `runner` dial. **Local half in-loop; the shipped workflow asserted structurally and never executed** — deferred criterion D-11 |

`auto_close_disabled: true` is set and is load-bearing: this close carries the
`close-discipline.md` §3 contract enumeration, the auto-close-debt reconciliation
below, and a deferred list that no predicate can compute.

**Three things this close inherits and must not rediscover.**

**1. `gate 1` must be named literally.** `RETROSPECTIVE.md` carries
`<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=32 predicate=v1 -->`.
Gate 1 auto-closed at `attempts: 0`, so its ceremony never ran.
`G2-CLOSE-INTERMEDIATE` already reconciled that debt in full — all 32 criteria
dispositioned, 29 re-run fresh — and **deliberately left the marker in place**,
because `assert_autoclose_debt_reconciled` fires on the terminal `close` and matches
the literal string. So this close's `## What the loop did NOT verify` section
**must name `gate 1` literally**, pointing at the completed reconciliation rather
than repeating it. A section that says "the predecessor gate's debt is settled"
without the two words `gate 1` is refused *after* this WU has run, which costs a
full re-dispatch (`close-discipline.md` §4).

**2. The verdict is not `met_locally` by construction any more — and that is a
change from what gate 2 expected.** `GATE-02-REVIEW.md` §6.1 answer 4 records the
operator confirming that **an operator run against the downstream .NET backend is
planned**. That run is the named condition that upgrades the verdict. So:

- If the operator run **has happened** and its record is in the feature folder, the
  deferred items it discharges may be reported as verified, with the record cited.
- If it **has not**, the verdict is `met_locally` and the §2 hedged follow-up record
  is mandatory — one entry per unmet criterion, naming the exact re-run condition.
  That is an honest outcome, not a failure; `accept-hedged-close` exists for it.

Do not claim `met` on the strength of a stubbed runner or a structurally-asserted
workflow. That is the single failure this gate was isolated to prevent.

**3. The deferred list will be long, and most of it is known now.**
`RETROSPECTIVE.md` already carries D-1 … D-8 from gate 2 (the adapters against a
live Azure environment, and DST observed in production). Gate 3 adds **D-9** (a
second harvest against a real repository files no duplicate), **D-10**
(`specfuse-monitor run` against a real repository and environment files the issues
the dry run predicted), and **D-11** (the shipped workflow completes a scheduled run
in a consumer repository). D-9, D-10, and D-11 each name an **operator-journal
artifact** as their verification proxy; this close reads that journal if it exists
and says plainly that it does not if it does not.

**Close obligations** (`close-discipline.md`).

1. **Oracles re-run fresh (§1)** — every oracle the feature's criteria name, across
   all three gates, run in this session with exit codes read directly. Never
   inherited from a producing WU's `done` status.
2. **Hedged follow-up record (§2)** — on `met_locally`, a named record per unmet
   criterion: the criterion verbatim, why it is unverifiable in this environment,
   and the exact re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3)** — enumerated across all three gates and
   **blocked on explicit human acknowledgment**. Gate 2's list is already written and
   acknowledged in `RETROSPECTIVE.md`; gate 3 adds at least a new CLI entry point
   (`specfuse-monitor`), a new module (`specfuse.monitor.issues`), a shipped workflow
   template, and the `queue-stalled` adapter's `stall_after` grammar. The gate-2
   `dialect` entry is **breaking** and stays in the enumeration.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists and is non-empty, and carries a `## Gate 3` section for
   this gate alongside the existing gate-1 and gate-2 material.
2. A `## Cost analysis` section reconciles `planned_cost_usd` across all three gates
   against actual spend from `events.jsonl`, **with the per-gate split shown** — a
   feature-wide figure that blends three gates hides where the variance came from.
   Report the **as-drafted** plan figures, not a plan re-based onto its own outcome
   (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`). Gate 3's drafted total is $23.00
   against `GATE-03.md`'s `cost_budget_usd: 28.00`.
3. A `## What the loop did NOT verify` section enumerates each deferred criterion
   with why it is deferred and where it is actually verified. **This will not be
   empty**: D-1 … D-8 carry forward from gate 2, and D-9, D-10, and D-11 are gate
   3's. **This section names `gate 1` literally**, per the auto-close-debt
   reconciliation described above.
4. Every oracle named by gates 1–3 is re-run in this session with its command and
   exit code recorded — including `python3 -m unittest` over each of the feature's
   test modules and the full `code` gate set. State which sandbox each gate ran
   under: several `bats` suites fail in `setup` on `mktemp` under the default
   sandbox, and `tests/test_autosync_no_cwd_leak.py` errors on inherited commit
   signing. Both are recorded environment effects, not regressions
   (`[FEAT-2026-0072/G1-CLOSE]`, `RETROSPECTIVE.md` gate-2 section).
5. A consumer-visible contract-change enumeration is present per obligation 3, with
   breaking entries marked and the human acknowledgment recorded. A feature with no
   such change writes exactly `n/a — no consumer-visible contract change`; this
   feature has several, so that line would be false here.
6. **The fingerprint contract is verified end to end.** A run producing findings from
   **two different targets on one component yields two issues, not one.** This is the
   binding constraint inherited from FEAT-2026-0069 and the single thing most worth
   proving before this feature is called done. It is exercisable against `T10`'s
   fixture plus `T09`'s stub runner — recorded as **two** create calls — and that
   in-loop result is reported as what it is: proof of the composition, not of GitHub.
7. **The duplicate-filing risk inherited from FEAT-2026-0046 is addressed and the
   evidence recorded** — not deferred silently. `T09` replaced the HTML-comment
   `--search` with a client-side filter over an explicitly-limited listing; this
   close records the in-loop evidence for that (criteria `T09` 4, 5, 6, 7) **and**
   states plainly that D-9 — the same property against a real repository — is
   discharged only by the operator-journal record, citing it if it exists.
8. **The `stall_after` threshold-units gap is dispositioned, not left implicit.**
   `T08` settled the grammar in the adapter and deliberately did **not** tighten the
   validator, because that is a severity flip needing a `planning-discipline.md` §4
   probe. This close records the disposition and carries "make `stall_after` required
   and bounded at lint time" as a named follow-up with its home, or says it was
   dropped and why.
9. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`. Feature-specific
   observations stay in the retrospective and are not promoted.
10. The roadmap detail section for FEAT-2026-0040 reflects what was actually built,
    including which surfaces were never executed, and names the features it unblocks —
    0038, 0041, 0042, 0043.
11. This unit's **frontmatter** carries a `verdict:` field, one of `met`,
    `met_locally`, `partially_met`, `not_met`. In the frontmatter, not the body.
12. If any work unit recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present — three hashes — with the
    classes named. Gate 2 had none and said so explicitly; do the same rather than
    omitting the section silently.
13. The carried-forward follow-ups from gate 2 are dispositioned rather than dropped:
    **FU-A** (`tests/test_autosync_no_cwd_leak.py` fixtures should set
    `commit.gpgsign=false`), **FU-B** (`queue-stalled` had no adapter — discharged by
    `T08`), and **FU-C** (`azure_service_bus.py` line coverage). Each is closed,
    re-carried with a home, or explicitly dropped with a reason.

**Do not touch.** Source files owned by any substantive work unit — this unit closes
the feature, it does not patch the work. If an oracle fails, that is a finding to
report, not a file to fix. `PLAN.md`'s `status` field: the driver owns the terminal
flip, gated on the verdict. `GATE-01.md`, `GATE-02.md`, and their review documents —
gates 1 and 2 are closed. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus the oracle re-runs in criterion 4 and
the end-to-end fingerprint check in criterion 6. Re-read `close-discipline.md` §4's
guard table before writing anything: by measured cost, a closing-WU refusal is more
often a format mismatch than hard work — `## Cost analysis` (two hashes),
`### Failure-class breakdown` (three), a `verdict:` in frontmatter, and `gate 1`
spelled literally in `## What the loop did NOT verify`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle cannot be re-run at all; criterion 6 cannot be exercised even against a stub,
which would mean the fingerprint contract was never actually proven and is the one
finding worth halting the terminal close for; the contract-change list requires a
human acknowledgment that has not been given; or the operator-journal artifacts D-9,
D-10, and D-11 name are absent **and** the retrospective cannot honestly describe
what remains unverified without them. Record `met_locally` with the §2 follow-up
record rather than claiming `met` for anything a stubbed runner or a structural
assertion is the only evidence for.
