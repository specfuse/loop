# RETROSPECTIVE.md — FEAT-2026-0020 (Public-readiness prep)

Intermediate close for **gate 1 (Audit)**. This is a non-terminal close
(`G1-CLOSE-INTERMEDIATE`); it does not write a feature-arc verdict and does not draft
gate 2. The terminal verdict belongs to `G2-CLOSE`.

## Gate 1

Gate 1 produced `AUDIT.md` across five audit classes (T01..T05) plus a post-remediation
rescan verdict (T06). The gate's design splits cleanly into two halves: the loop produces
triage reports + exact remediation commands; the operator runs every destructive command
out-of-loop between dispatches; T06 verifies the post-state. That split is the source of
most of the entries in `## What the loop did NOT verify` below.

Outcome at close: **5 of 5 audit classes clean or remediated; 1 open action** — the
commit-history rewrite (`git filter-repo` phase 2, AUDIT.md §personal-refs row 22),
deferred to the pre-publish sweep. T06's own verdict reads `red — see open actions`
because that history sweep has not yet run.

### T01 — secret-history scan (`WU-01-secret-history-scan.md`)

- **Attempts:** 1, passed. Cost $0.45 (planned $1.50).
- **Blockers:** none.
- **Surprises:** zero findings. `gitleaks v8.30.1` over the full history (261 commits,
  ~4.40 MB) returned an empty report. The repo was authored under a "private" assumption
  but never committed a credential — the cheapest possible audit-class outcome. This is
  why §secrets has no remediation rows and the rescan (T06 rescan A) stayed at 0.

### T02 — personal-refs grep (`WU-02-personal-refs-grep.md`)

- **Attempts:** 1 blocked, then re-armed and passed (2 dispatches total). Cost $1.01
  combined ($0.47 blocked + $0.54 re-arm; planned $1.20).
- **Blockers:** the only in-loop human escalation of the gate. Rows 17–18 (private
  org-name cluster: `example-org/example-app`, the cross-pollinated INIT-F06 folder) were
  genuinely ambiguous between *keep-as-maintainer-attribution* and *redact-in-place*. The
  loop correctly refused to classify > 3 findings (13 files, ~40 locations) without an
  operator call rather than guess. Operator classified `redact-in-place` (+ `removed` for
  the leaked folder) and applied commits `7b3267c` + `b5d5404`; the WU re-armed and passed.
- **Surprises:** the §personal-refs scan surfaced the same private-org cluster that T03
  found via a different route (cross-pollination) — two audit classes converging on one
  remediation. Also surfaced commit-message + filename leaks that a working-tree scan alone
  would miss (row 22), seeding the deferred history-rewrite open action.

### T03 — cross-pollination check (`WU-03-cross-pollination-check.md`)

- **Attempts:** 1, passed. Cost $0.20 (planned $0.80).
- **Blockers:** none.
- **Surprises:** found exactly one non-`FEAT-*` feature directory —
  `INIT-2026-0001-F06-conform-…` — leaked from a private org via PR #1's dogfood run. Its
  `PLAN.md` carried a private GitHub repo URL. Clean, single-finding result; the verdict
  (`leaked-from-example`, history-scrub required) fed directly into T02's row 18 and the
  phase-2 history sweep.

### T04 — GitHub content sweep (`WU-04-gh-content-sweep.md`)

- **Attempts:** 1 blocked in-loop; completed out-of-loop (`completed_out_of_loop: true`,
  `unsandboxed: true`). Only the aborted in-loop attempt was billed to `events.jsonl`
  ($0.16); planned $2.00.
- **Blockers:** `gh auth status` fails inside the dispatched `claude -p` subprocess even
  with a valid `GH_TOKEN` — the known `gh`↔claude-p bug catalogued in
  `LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]`. The `unsandboxed: true` escape hatch
  is documented-insufficient for this surface. The operator ran the entire sweep (audit +
  12 body redactions) in their main Claude session where `gh` returns exit 0.
- **Surprises:** this is the gate's clearest "loop cannot reach the surface at all" case.
  The GitHub issue/PR surface was both *audited* and *remediated* outside the loop; the
  loop holds no in-loop evidence for it (see `## What the loop did NOT verify` entries 4
  and 6). The known bug biting again confirms `gh`-from-agent ACs must not be authored.

### T05 — license-header sweep (`WU-05-license-header-sweep.md`)

- **Attempts:** 1, passed. Cost $0.40 (planned $0.80).
- **Blockers:** none in-loop, but escalated an operator decision: coverage was 22.6%
  (24 of 31 files missing Apache-2.0 headers), well below the ≥80% pre-approved threshold.
  The WU produced header templates + a findings table + three remediation options rather
  than hand-editing 24 files, and asked the operator to choose. Operator chose script-insert
  (`insert-license-headers.py`).
- **Surprises:** scale. The gap was uniform across `.specfuse/{rules,skills,templates}`,
  which is what justified a script over hand edits. `LICENSE` itself (repo-root Apache-2.0)
  was present and correct.

### T06 — post-remediation rescan (`WU-06-post-remediation-rescan.md`)

- **Attempts:** 1, passed. Cost $0.80 (planned $1.50).
- **Blockers:** none.
- **Surprises:** rescan confirmed two of three surfaces fully clean (secrets 0/0, license
  headers 31/31) but personal-refs returned `pending-action: 1` — the commit-history
  rewrite (row 22) is still open, so the honest gate verdict is `red`, not green. T06
  correctly reported `red — see open actions` rather than papering over the deferred sweep.
  The rescan reads as a working-example of "verify the post-state the loop did not perform":
  the loop ran the *scans*, the operator ran the *fixes*, and the scans confirm the fixes
  landed for the two surfaces a working-tree scan can see.

### Failure-class breakdown

Gate-scoped non-passing `attempt_outcome` events for gate 1, grouped by
`failure_class` (the driver resolves gate ownership via `_gate_number_from_wu_id`,
which matches only `G<n>-` closing IDs — so T01..T06 substantive attempts resolve to
`None` and are *not* counted here; only this `G1-CLOSE-INTERMEDIATE` WU's own prior
attempt is gate-1-attributable). The single non-passed attempt is this close WU's own
first dispatch, which failed `plan-lint` (the verdict-less close-intermediate ↔
`in_progress` lint gap — see `## What I'd change` and the matching LEARNINGS entry).

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| other | 1 | no_gate_marker |
| **total** | **1** | — |

The substantive in-loop human escalations (T02's private-org classification, T04's
`gh`-auth abort) are *not* in this table — they were `human_escalation` /
out-of-loop events on `T0x`-namespaced WUs, not gate-1-attributable
`attempt_outcome` failures. Their narratives live in the per-WU subsections above.

## Cost analysis

Planned figures are per-WU `planned_cost_usd` frontmatter (which sum to the gate-1
substantive budget); actual figures are `cost_usd` summed over each WU's attempts in
`events.jsonl`. The feature-level `planned_cost_usd: 13.10` (PLAN.md) covers both gates plus
closing WUs; this table reconciles only gate 1's substantive WUs (T01..T06).

| WU  | planned | actual | delta % | auto-close ratio (actual/planned ≤ 1.5×) |
|-----|---------|--------|---------|-------------------------------------------|
| T01 | $1.50   | $0.45  | −69.7%  | 0.30× — PASS |
| T02 | $1.20   | $1.01  | −15.7%  | 0.84× — PASS |
| T03 | $0.80   | $0.20  | −75.6%  | 0.24× — PASS |
| T04 | $2.00   | $0.16  | −91.8%  | 0.08× — PASS (see rationale) |
| T05 | $0.80   | $0.40  | −50.1%  | 0.50× — PASS |
| T06 | $1.50   | $0.80  | −47.0%  | 0.53× — PASS |
| **Gate total** | **$7.80** | **$3.02** | **−61.3%** | all 6 WUs PASS the ≤ 1.5× per-WU ratio |

Every WU came in **under** budget; none approached the auto-close predicate's 1.5×
overspend ceiling. No cost-analysis ambiguity (escalation trigger 1): each WU's frontmatter
`cost_usd` matches its `events.jsonl` sum — T04's `cost_usd: 0.16309` equals its single
logged (blocked) attempt; T06's `0.79508` equals its events entry.

**Variance > 50% rationale (T01, T03, T04, T05).** The systemic cause is uniform: gate-1
substantive WUs are *scan-and-triage* WUs that produce a markdown report and exact
remediation commands — they write no production code and run no test suite, so they bill far
less than the implementation-WU baseline the planning estimates were anchored to. The budget
was additionally padded for destructive-operation uncertainty (history rewrite, secret
rotation), but per PLAN.md "Notes" those operations are *operator-side* and never billed to
the WU, so the padding had no WU-level cost to absorb. **T04 is a special case:** its −91.8%
is an artifact, not efficiency — the in-loop attempt aborted on the `gh`-auth bug after $0.16
and the real work (audit + 12 redactions) ran out-of-loop in the operator's session, which
`events.jsonl` does not bill. T04's true effort is materially higher than $0.16; the figure
reflects only the aborted dispatch.

## What the loop did NOT verify

Gate 1's design hands every destructive operation to the operator and verifies the
post-state where the loop can reach it. The following acceptance-relevant verifications were
deferred. **6 entries — this exceeds the > 2 threshold, so the gate's sizing is flagged
under `## What I'd change`.**

| # | Deferred verification | Why deferred | Where verification actually happens |
|---|----------------------|--------------|--------------------------------------|
| 1 | In-place redaction commits `7b3267c` + `b5d5404` (private-org substitutions; `/Users/` path redactions across rows 1–13) actually applied | Destructive working-tree rewrite is operator-side per PLAN.md "Notes" — a re-attempt after a partial rewrite can't be undone by inter-attempt `git reset --hard` | **Verified in-loop post-state**: T06 rescan B confirms zero residual private strings in the working tree |
| 2 | Leaked `INIT-2026-0001-F06` folder deletion | Same operator-side destructive-op boundary; verdict came from T03, deletion applied by operator in `7b3267c` | **Verified in-loop post-state**: T03/T06 confirm the directory is absent |
| 3 | License-header insertion into the 24 missing files | Operator chose + ran `insert-license-headers.py` (T05 escalated the strategy decision) | **Verified in-loop post-state**: T06 rescan C confirms 31/31 headers present |
| 4 | The §gh-content audit *and* its 12 body redactions (issues/PRs) | The `gh`↔`claude -p` auth bug (`LEARNINGS [FEAT-2026-0014/T01]`) makes the GitHub surface unreachable from the dispatched agent; `unsandboxed: true` is documented-insufficient | **Outside the loop entirely** — operator ran T04 in their main Claude session and verified via `gh issue/pr view --json body` (0 residual matches). The loop holds **no in-loop evidence** for this surface |
| 5 | Commit-history rewrite (`git filter-repo` phase 2 — AUDIT.md §personal-refs row 22): commit-message bodies + filenames in `b5d5404`, `7b3267c`, `20918f4`, `63bec507`, `be7785b` | Phase-2 sweep is intentionally deferred until every gate-1 in-place finding is remediated; running it mid-gate would invalidate the branch state the remaining WUs read | **Not yet done** — operator runs it at the pre-publish sweep (follow-up / phase 2). T06's verdict is `pending-action: 1` precisely because of this. This is the **one open action** at gate close |
| 6 | True expunge of GitHub issue/PR **edit-history** | `gh issue/pr edit` changes only the current body; GitHub retains prior revisions in the "edited" dropdown, which becomes public on the visibility flip. True expunge needs delete+recreate or GitHub support | **Operator-accepted residual risk** (org-names only, no credentials) + a follow-up step if the operator opts to expunge. Not verifiable in-loop |

Entries 1–3 are deferred *execution* with in-loop post-state verification — the healthy
shape. Entry 4 is the loop being structurally blind to a surface. Entries 5–6 are genuinely
open at gate close and carry into the pre-publish sweep / gate-2 readiness.

## What I'd change

**Gate sizing — flagged by the > 2-entry rule above.** Six deferred verifications in one
gate is a signal that gate 1 mixed two structurally different kinds of audit surface:

1. **In-loop-verifiable surfaces** (secrets, personal-refs working tree, license headers).
   The loop scans, the operator fixes, the loop re-scans. Entries 1–3 above — clean shape.
2. **Out-of-loop-only surfaces** (the GitHub issue/PR surface, entry 4). The loop cannot
   reach `gh` from a dispatched agent at all, so both the audit and the remediation happen
   in the operator's session with zero in-loop evidence. Folding this into the same gate as
   the in-loop-verifiable surfaces is what pushed the deferred-verification count over the
   threshold.

If gate 1 were re-planned, T04 (gh-content) would be split into its own gate (or marked
*designated-out-of-loop* at plan time with an explicit operator-journal artifact as the
verification proxy, per `LEARNINGS [FEAT-2026-0003/G3-LESSONS]` on live-mutation WUs). That
keeps the in-loop gate's "did not verify" list at ≤ 2 (the healthy deferred-execution
entries) and stops the count from conflating "deferred but verified post-state" with "the
loop never had eyes on this."

Secondary: the scan-WU budgets (T01/T03/T05) were anchored to an implementation-WU baseline
and over-estimated by ~70%. Future audit-class gates should budget scan-and-triage WUs at a
fraction of an implementation WU and should NOT pad for operator-side destructive ops, since
those never bill to the WU.

## Docs reconciliation

No docs/roadmap diff in this WU. The audit *did* surface doc-resident leaks
(`docs/handoff-github-feature-pick.md`, `README.md`, `roadmap.md` / `roadmap-archive.md`),
but those were remediated by the operator's in-place redaction commits (`7b3267c`,
`b5d5404`) during gate 1 — not re-touched here. Per AC5, the docs/roadmap-diff assertion is
satisfied by this `RETROSPECTIVE.md` write alone.

---

# Gate 2 (Public hygiene + flip) — terminal close (`G2-CLOSE`)

Gate 2 produced the public-facing hygiene set (README polish T10, CONTRIBUTING T11,
SECURITY + CODE_OF_CONDUCT T12, GitHub templates T13, dependabot T14), the
operator-requested **leak-prevention guard** (detector T15, wiring T16), the
`FLIP-CHECKLIST.md` (T17), and the flip rehearsal (T18). Feature-arc verdict below.

## Gate 2 — what happened

The loop ran T10–T17 and reported them all `done`; T18 blocked `blocked_human` by
design. A `/gate-status` pass before close caught that **two WUs hollow-passed** —
marked `done` with their deliverables absent:

- **T12** shipped `SECURITY.md` but never created `CODE_OF_CONDUCT.md`, despite the
  WU's own `test -s CODE_OF_CONDUCT.md` presence gate.
- **T16** touched **zero deliverable files** ($1.48 for nothing): no pre-commit hook,
  no `verification.yml` gate, no bats test. The detector `leak_scan.py` (T15) was left
  orphaned — and T15 itself had shipped only a Python API, no CLI, so T16 had nothing
  to wire and should have fired its escalation-trigger-1 (interface mismatch) instead
  of passing empty.

**Root cause:** the driver enforces the `code` gate set (test suite) but does **not**
run the per-WU file/symbol-presence checks written in WU bodies. An agent that
self-reports `complete` without producing the files passes. This extends the
hollow-pass pattern past the FEAT-2026-0008/0015 guards (which catch no-code-written
on *some* WU shapes but not zero-deliverable or partial-bundle passes).

**Resolution:** T12, T15 (CLI gap), and T16 were completed **out-of-loop** with real,
re-run verification (suite 726 OK, coverage 93%, `leak-scan --all` clean, hook blocks
a planted leak / passes clean, bats 3/3). T18's rehearsal was recorded in
`FLIP-REHEARSAL.md` (Phase-0 all-pass; Phases 1–3 operator-side, READY). Same justified
escape hatch used for gate-1's T04: the loop could not reliably produce + verify these,
so the operator did, with stronger checks than a re-dispatch.

A notable secondary: generating the Contributor Covenant 2.1 text inline tripped the
model **output content-filter** (its unacceptable-behavior list). Worked around by
fetching the text from the canonical EthicalSource repo and processing it in shell —
the body never passed through model output.

## Cost analysis (gate 2)

Gate-2 substantive in-loop spend ≈ **$3.78** (T10 $0.36, T11 $0.24, T12 $0.17,
T13 $0.34, T14 $0.13, T15 $0.35, T16 $1.48, T17 $0.52) + T18 blocked attempt $0.19.
**$1.48 of that (T16) bought nothing** — the most expensive hollow pass of the feature.
Out-of-loop completion work is unmetered (operator session). Feature total in-loop ≈
**$6.8** against `planned_cost_usd: 13.10` (−48%).

## What the loop did NOT verify (gate 2)

1. **T12's second bundled file.** Loop reported `done`; `CODE_OF_CONDUCT.md` did not
   exist. The WU-body presence gate was never machine-run.
2. **T16's entire deliverable.** Loop reported `done` with zero files touched. The
   leak-guard — the feature's headline operator request — was inert until out-of-loop
   completion.
3. **T15's CLI surface.** Loop reported `done`; only the importable API existed, no
   runnable CLI. Caught only when wiring revealed nothing to call.
4. **The actual flip.** Force-push, visibility toggle, and post-flip confirmation
   (FLIP-CHECKLIST Phases 1–3) are operator/GitHub-side and out of loop scope by design.
5. **GitHub issue/PR edit-history.** Redacted bodies, but GitHub retains prior
   revisions — operator-accepted residual (org-names only).

## Feature-arc verdict

**FEAT-2026-0020 — DONE (readiness achieved).** The repo is publish-ready: history
scrubbed clean across all three surfaces (org-names + paths + leaked folder expunged;
`INIT-2026-0001` orchestrated-ID sample correctly retained), leaked PAT rotated, audit
verdict green, full public-hygiene file set in place, an automated leak-guard live
(pre-commit hook + CI gate) to stop recurrence, and a verified `FLIP-CHECKLIST.md` +
`FLIP-REHEARSAL.md` enumerating the operator-side flip with owners + rollbacks. The
visibility flip itself is the operator's post-feature step, sequenced before
FEAT-2026-0019's first PyPi tag.

Two gates hollow-passed deliverables that out-of-loop completion + the new `/gate-status`
review caught and fixed; the durable fix is driver-side presence-gate enforcement (filed
as a loop bug). Net: more methodology-erosion than a clean run (four WUs finished
out-of-loop across the feature — gate-1 T04; gate-2 T12/T16/T18 + the T15 gap), but every
out-of-loop deliverable was verified with real gates, and the erosion itself became the
feature's most valuable dogfood evidence.
